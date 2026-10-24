"""Regras puras de recompensa do Tribunal: nota por caso, combo, baú de autos, cartas e desafio do dia.

Princípios (ver docs/DOPAMINA.md): recompensa por aprender e jogar bem; nunca por gastar, nunca punição por ausência.
Tudo é determinístico (data ou ``run_id`` como semente) e calculado no servidor, com tetos.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import random

NOTAS = ("C", "B", "A", "S")  # da pior para a melhor
COMBO_TETO = 10
COMBO_PASSO = 0.02        # +2% de XP por acerto seguido, até +20%
BONUS_MELHORA = 15        # XP por degrau de nota que o jogador melhora ao rejogar
DIA_QUESTOES = 3
DIA_XP_ACERTO = 10
DIA_XP_COMPLETO = 20
PROTETORES_MAX = 2
RARIDADE_POR_NIVEL = {"basico": "incomum", "intermediario": "incomum", "avancado": "rara", "especialista": "epica",
                      "impossivel": "lendaria"}


def nota_do_caso(venceu: bool, erros: int) -> str | None:
    """S: sem erros. A: 1 erro. B: até 3. C: venceu com mais erros. Tempo não entra: ler devagar não é defeito."""
    if not venceu:
        return None
    return "S" if erros <= 0 else "A" if erros == 1 else "B" if erros <= 3 else "C"


def rank(nota: str | None) -> int:
    return NOTAS.index(nota) if nota in NOTAS else -1


def bonus_combo(xp: int, combo_max: int) -> int:
    """Multiplicador de XP por acertos seguidos (teto de +20%). Quebrar o combo só zera o contador, nunca tira XP."""
    return round(xp * COMBO_PASSO * max(0, min(int(combo_max), COMBO_TETO)))


def bau(run_id: str, nota: str | None) -> dict:
    """Baú de autos ao vencer: sempre abre; às vezes tem algo a mais. Nunca perde nada. Semente = run_id (auditável)."""
    if nota is None:
        return {"tipo": "vazio", "xp": 0, "carta_dourada": False}
    r = random.Random(int(hashlib.sha256(run_id.encode()).hexdigest()[:12], 16)).random()
    chance_rara = 0.08 + 0.04 * rank(nota)  # 8% (C) a 20% (S): jogar bem aumenta a chance, mas todos têm
    if r < chance_rara:
        return {"tipo": "raro", "xp": 40, "carta_dourada": True}
    if r < chance_rara + 0.25:
        return {"tipo": "bom", "xp": 15, "carta_dourada": False}
    return {"tipo": "comum", "xp": 0, "carta_dourada": False}


def raridade_carta(niveis: list[str], n_casos: int = 1) -> str:
    """Dispositivo que aparece em 2+ casos é "clássico" (comum). Os demais: pelo caso mais difícil que o cita."""
    if n_casos >= 2:
        return "comum"
    ordem = list(RARIDADE_POR_NIVEL)
    return RARIDADE_POR_NIVEL[max(niveis, key=ordem.index)]


def semana(day: dt.date) -> str:
    y, w, _ = day.isocalendar()
    return f"{y}-W{w:02d}"


def dia_questoes(questoes: list[dict], day: dt.date) -> list[str]:
    """Três questões do dia (básica, intermediária e avançada/especialista), iguais para todos na mesma data."""
    rng = random.Random(day.toordinal())
    out = []
    for grupo in (("basico",), ("intermediario",), ("avancado", "especialista")):
        pool = sorted(q["id"] for q in questoes if q["nivel"] in grupo)
        out.append(rng.choice(pool))
    return out
