"""Agendador de revisão espaçada baseado no FSRS-5 (Free Spaced Repetition Scheduler).

Modelo DSR: cada cartão tem Dificuldade (1–10), Estabilidade (dias até a lembrança cair
para 90%) e Retenção prevista R(t). O FSRS supera o SM-2 em previsão de memória e, por
dar R(t) explicitamente, responde direto a "probabilidade de esquecer este artigo".

Os 19 pesos padrão vêm do FSRS-5. Em produção os pesos são otimizados por usuário (com
histórico suficiente) a partir de ``ReviewLog`` — ver docs/02-arquitetura.md, "Serviço de
aprendizagem". Este módulo é puro (sem I/O) e determinístico, para rodar igual no servidor e,
portado, no cliente offline; ``tests/vectors.json`` garante a paridade entre as implementações.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, replace
from enum import IntEnum

DECAY = -0.5
FACTOR = 0.9 ** (1 / DECAY) - 1  # = 19/81: faz R(S) = 0.9

DEFAULT_W: tuple[float, ...] = (
    0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046, 1.54575, 0.1192,
    1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898, 0.51655, 0.6621,
)


class Grade(IntEnum):
    AGAIN = 1  # errou / não lembrou
    HARD = 2
    GOOD = 3
    EASY = 4


class State(IntEnum):
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


@dataclass(frozen=True)
class Card:
    key: str  # chave natural do conteúdo: "<norma>#<caminho>" ou id do flashcard
    state: State = State.NEW
    difficulty: float = 0.0
    stability: float = 0.0
    due: dt.datetime | None = None
    last_review: dt.datetime | None = None
    reps: int = 0
    lapses: int = 0


@dataclass(frozen=True)
class ReviewLog:
    key: str
    grade: Grade
    reviewed_at: dt.datetime
    elapsed_days: float
    retrievability: float | None  # R no momento da revisão (None para cartão novo)
    stability_before: float
    stability_after: float
    difficulty_after: float
    duration_ms: int | None = None


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass(frozen=True)
class Scheduler:
    w: tuple[float, ...] = DEFAULT_W
    desired_retention: float = 0.9
    maximum_interval_days: int = 36500
    relearning_step: dt.timedelta = dt.timedelta(minutes=10)
    learning_step: dt.timedelta = dt.timedelta(minutes=10)

    def __post_init__(self) -> None:
        if len(self.w) != 19:
            raise ValueError("FSRS-5 exige 19 pesos")
        if not 0.7 <= self.desired_retention <= 0.97:
            raise ValueError("retenção desejada fora da faixa útil (0.70–0.97)")

    # ---------------------------------------------------------------- fórmulas
    @staticmethod
    def retrievability(elapsed_days: float, stability: float) -> float:
        if stability <= 0:
            return 0.0
        return (1 + FACTOR * max(0.0, elapsed_days) / stability) ** DECAY

    def interval_days(self, stability: float) -> int:
        raw = stability / FACTOR * (self.desired_retention ** (1 / DECAY) - 1)
        return int(_clamp(round(raw), 1, self.maximum_interval_days))

    def init_stability(self, g: Grade) -> float:
        return max(self.w[g - 1], 0.1)

    def init_difficulty(self, g: Grade) -> float:
        return _clamp(self.w[4] - math.exp(self.w[5] * (g - 1)) + 1, 1, 10)

    def next_difficulty(self, d: float, g: Grade) -> float:
        delta = -self.w[6] * (g - 3)
        damped = d + delta * (10 - d) / 9  # "linear damping": perto de 10, muda pouco
        reverted = self.w[7] * self.init_difficulty(Grade.EASY) + (1 - self.w[7]) * damped
        return _clamp(reverted, 1, 10)

    def stability_after_recall(self, d: float, s: float, r: float, g: Grade) -> float:
        hard = self.w[15] if g == Grade.HARD else 1.0
        easy = self.w[16] if g == Grade.EASY else 1.0
        inc = math.exp(self.w[8]) * (11 - d) * s ** (-self.w[9]) * (math.exp(self.w[10] * (1 - r)) - 1)
        return s * (1 + inc * hard * easy)

    def stability_after_forget(self, d: float, s: float, r: float) -> float:
        new = self.w[11] * d ** (-self.w[12]) * ((s + 1) ** self.w[13] - 1) * math.exp(self.w[14] * (1 - r))
        return min(new, s)

    def stability_short_term(self, s: float, g: Grade) -> float:
        return s * math.exp(self.w[17] * (g - 3 + self.w[18]))

    # ---------------------------------------------------------------- API
    def forgetting_probability(self, card: Card, now: dt.datetime) -> float:
        """1 − R(agora). Alimenta 'artigos esquecidos' e a fila de revisão do dia."""
        if card.state == State.NEW or card.last_review is None:
            return 1.0
        elapsed = (now - card.last_review).total_seconds() / 86400
        return 1 - self.retrievability(elapsed, card.stability)

    def review(self, card: Card, grade: Grade, now: dt.datetime, duration_ms: int | None = None) -> tuple[Card, ReviewLog]:
        if now.tzinfo is None:
            raise ValueError("use datetime com fuso horário (UTC)")
        g = Grade(grade)
        if card.state == State.NEW:
            elapsed, r = 0.0, None
            s, d = self.init_stability(g), self.init_difficulty(g)
        else:
            elapsed = max(0.0, (now - card.last_review).total_seconds() / 86400) if card.last_review else 0.0
            r = self.retrievability(elapsed, card.stability)
            d = self.next_difficulty(card.difficulty, g)
            if elapsed < 1:  # revisão no mesmo dia: atualização de curto prazo
                s = self.stability_short_term(card.stability, g)
            elif g == Grade.AGAIN:
                s = self.stability_after_forget(card.difficulty, card.stability, r)
            else:
                s = self.stability_after_recall(card.difficulty, card.stability, r, g)
        s = _clamp(s, 0.1, float(self.maximum_interval_days))

        lapses = card.lapses + (1 if g == Grade.AGAIN and card.state == State.REVIEW else 0)
        if g == Grade.AGAIN:
            state = State.LEARNING if card.state in (State.NEW, State.LEARNING) else State.RELEARNING
            due = now + (self.learning_step if state == State.LEARNING else self.relearning_step)
        else:
            state = State.REVIEW
            due = now + dt.timedelta(days=self.interval_days(s))

        new = replace(card, state=state, difficulty=d, stability=s, due=due, last_review=now,
                      reps=card.reps + 1, lapses=lapses)
        log = ReviewLog(card.key, g, now, elapsed, r, card.stability, s, d, duration_ms)
        return new, log

    def preview(self, card: Card, now: dt.datetime) -> dict[Grade, dt.datetime]:
        """Próxima data para cada botão — o que a UI mostra sob 'Errei/Difícil/Bom/Fácil'."""
        return {g: self.review(card, g, now)[0].due for g in Grade}  # type: ignore[misc]


def grade_from_answer(correct: bool, response_ms: int, expected_ms: int, used_hint: bool = False) -> Grade:
    """Converte uma resposta de questão em nota FSRS (questões também alimentam a memória).

    Errou → AGAIN. Acertou com dica ou devagar (> 1,5x o tempo esperado) → HARD.
    Acertou rápido (< 0,5x) → EASY. Senão → GOOD.
    """
    if not correct:
        return Grade.AGAIN
    if used_hint or response_ms > 1.5 * expected_ms:
        return Grade.HARD
    if response_ms < 0.5 * expected_ms:
        return Grade.EASY
    return Grade.GOOD
