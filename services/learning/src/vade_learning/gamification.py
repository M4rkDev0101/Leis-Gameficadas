"""Regras de gamificação: XP, níveis, sequência (streak), ligas e moedas.

Princípio de design: a gamificação recompensa **aprendizagem**, não volume. Por isso:
* XP depende da dificuldade e é maior para revisão no prazo (o que consolida memória);
* errar dá XP de esforço (pouco), para não punir quem tenta questões difíceis;
* o combo tem teto, para não premiar chute rápido;
* o XP diário tem rendimento decrescente acima da meta, contra maratonas que geram esquecimento.

Funções puras: o servidor é a fonte da verdade (anti-trapaça); o cliente usa as mesmas
regras para mostrar o resultado na hora, offline, e o servidor recalcula na sincronização.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, replace

TIERS = ("basico", "intermediario", "avancado", "especialista")
BASE_XP = {"basico": 10, "intermediario": 15, "avancado": 25, "especialista": 40}
EFFORT_XP = 2
COMBO_STEP, COMBO_CAP = 0.1, 2.0
ON_TIME_REVIEW_BONUS = 1.25

LEAGUES = ("bronze", "prata", "ouro", "platina", "diamante", "mestre", "grao-mestre")
LEAGUE_SIZE = 30
PROMOTE, DEMOTE = 7, 5


# ---------------------------------------------------------------- XP


def combo_multiplier(combo: int) -> float:
    """Acertos seguidos: +10% cada, até 2x."""
    return min(1 + COMBO_STEP * max(0, combo), COMBO_CAP)


def xp_for_answer(correct: bool, tier: str, combo: int = 0, on_time_review: bool = False) -> int:
    if tier not in BASE_XP:
        raise ValueError(f"nível desconhecido: {tier}")
    if not correct:
        return EFFORT_XP
    xp = BASE_XP[tier] * combo_multiplier(combo)
    if on_time_review:
        xp *= ON_TIME_REVIEW_BONUS
    return round(xp)


def daily_xp_after_cap(raw_today: int, daily_goal: int) -> int:
    """Até 3x a meta: integral. Acima disso, 25% — o resto do dia vale menos."""
    soft_cap = 3 * daily_goal
    if raw_today <= soft_cap:
        return raw_today
    return soft_cap + math.floor((raw_today - soft_cap) * 0.25)


# ---------------------------------------------------------------- níveis


def xp_for_level(level: int) -> int:
    """XP acumulado para atingir o nível (nível 1 = 0). Curva quadrática: 2→100, 10→4.500, 50→122.500."""
    if level < 1:
        raise ValueError("nível começa em 1")
    return 50 * (level - 1) * level


def level_from_xp(total_xp: int) -> int:
    # inverso de 50·n·(n−1) = xp
    n = int((1 + math.sqrt(1 + 8 * max(0, total_xp) / 100)) / 2)
    while xp_for_level(n + 1) <= total_xp:
        n += 1
    while n > 1 and xp_for_level(n) > total_xp:
        n -= 1
    return n


# ---------------------------------------------------------------- sequência


@dataclass(frozen=True)
class Streak:
    current: int = 0
    longest: int = 0
    last_day: dt.date | None = None
    freezes: int = 0  # protetores de sequência (comprados na loja ou ganhos em missões)


def register_activity(s: Streak, day: dt.date) -> Streak:
    """Registra que o usuário cumpriu a meta em ``day`` (data LOCAL do usuário, não UTC)."""
    if s.last_day is None:
        cur = 1
        freezes = s.freezes
    else:
        gap = (day - s.last_day).days
        if gap <= 0:
            return s  # mesmo dia (ou relógio voltou): nada muda
        missed = gap - 1
        if missed == 0:
            cur, freezes = s.current + 1, s.freezes
        elif missed <= s.freezes:
            cur, freezes = s.current + 1, s.freezes - missed  # protetores cobrem os dias perdidos
        else:
            cur, freezes = 1, s.freezes
    return replace(s, current=cur, longest=max(s.longest, cur), last_day=day, freezes=freezes)


def is_alive(s: Streak, today: dt.date) -> bool:
    """A sequência ainda pode continuar hoje (serve para o aviso 'sua sequência acaba hoje')."""
    if s.last_day is None:
        return False
    return (today - s.last_day).days - 1 <= s.freezes


# ---------------------------------------------------------------- ligas


def resolve_league_week(standings: list[tuple[str, int]], league: str) -> dict[str, str]:
    """Fim da semana: os 7 primeiros sobem, os 5 últimos descem (só quem fez XP > 0 sobe).

    ``standings``: [(user_id, xp_da_semana)], em qualquer ordem. Empate: ordem de entrada estável.
    """
    idx = LEAGUES.index(league)
    ranked = sorted(standings, key=lambda t: -t[1])
    out: dict[str, str] = {}
    n = len(ranked)
    for pos, (uid, xp) in enumerate(ranked):
        if pos < PROMOTE and xp > 0 and idx + 1 < len(LEAGUES):
            out[uid] = LEAGUES[idx + 1]
        elif pos >= n - DEMOTE and n > PROMOTE + DEMOTE and idx > 0:
            out[uid] = LEAGUES[idx - 1]
        else:
            out[uid] = league
    return out


# ---------------------------------------------------------------- moedas


def coins_for_day(goal_met: bool, streak: int, perfect_lessons: int) -> int:
    """Moedas da loja (skins, avatares, protetores). Marco de sequência a cada 7 dias."""
    if not goal_met:
        return 0
    return 5 + 2 * perfect_lessons + (20 if streak > 0 and streak % 7 == 0 else 0)
