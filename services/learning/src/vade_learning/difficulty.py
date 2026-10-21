"""Dificuldade dinâmica de conteúdo (🟢 básico, 🟡 intermediário, 🔴 avançado, ⚫ especialista).

Combina quatro sinais, como pedido no escopo:

1. **taxa de erro** dos usuários, com suavização bayesiana (prior Beta) para itens com
   poucas respostas não oscilarem;
2. **incidência em provas** (quantas vezes o dispositivo foi cobrado), que *reduz* o nível:
   o que mais cai é base e deve entrar cedo na trilha;
3. **complexidade textual** (tamanho, remissões a outros artigos, exceções como "salvo", "exceto");
4. **carreira-alvo** das questões históricas (magistratura/MP puxam para especialista).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .gamification import TIERS

PRIOR_ERRORS, PRIOR_ATTEMPTS = 3.0, 10.0  # prior: 30% de erro, peso de 10 respostas
_EXCEPTION_RE = re.compile(r"\b(salvo|exceto|ressalvad|não se aplica|sem prejuízo|ainda que|desde que)\b", re.I)
_REMISSION_RE = re.compile(r"\b(art\.|arts\.|§|inciso|alínea)\s*\d", re.I)
EXPERT_CAREERS = frozenset({"magistratura", "ministerio-publico", "defensoria", "delegado", "auditor-fiscal", "procuradoria"})


@dataclass(frozen=True)
class DifficultySignals:
    errors: int
    attempts: int
    exam_incidence: int  # nº de questões históricas que cobram o dispositivo
    text: str
    expert_share: float = 0.0  # fração das questões históricas de carreiras de elite


def smoothed_error_rate(errors: int, attempts: int) -> float:
    return (errors + PRIOR_ERRORS) / (attempts + PRIOR_ATTEMPTS)


def text_complexity(text: str) -> float:
    """0–1: comprimento + exceções + remissões."""
    words = len(text.split())
    length = min(words / 120, 1.0)
    exceptions = min(len(_EXCEPTION_RE.findall(text)) / 3, 1.0)
    remissions = min(len(_REMISSION_RE.findall(text)) / 4, 1.0)
    return round(0.4 * length + 0.35 * exceptions + 0.25 * remissions, 4)


def difficulty_score(s: DifficultySignals) -> float:
    err = smoothed_error_rate(s.errors, s.attempts)
    incidence_discount = 0.15 * min(math.log1p(s.exam_incidence) / math.log1p(50), 1.0)
    score = 0.55 * err + 0.3 * text_complexity(s.text) + 0.25 * s.expert_share - incidence_discount
    return round(max(0.0, min(1.0, score)), 4)


def tier(s: DifficultySignals) -> str:
    x = difficulty_score(s)
    if x < 0.25:
        return TIERS[0]
    if x < 0.40:
        return TIERS[1]
    if x < 0.55:
        return TIERS[2]
    return TIERS[3]
