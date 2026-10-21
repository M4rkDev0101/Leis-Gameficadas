"""Simulados: montagem da prova, correção pela regra da banca e XP.

O cliente nunca recebe gabarito antes de entregar: ``public_view`` tira gabarito, explicação e
fundamentos. A correção acontece no servidor (``grade``).
"""

from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass, field

from vade_learning import gamification as g

from .bank import LEVELS, Bank

GRACE_SECONDS = 30  # tolerância de rede/relógio no tempo da prova


@dataclass
class ExamSession:
    id: str
    concurso_id: str
    nivel: str
    question_ids: list[str]
    # para provas de 4 alternativas: letra exibida → letra original, por questão
    letter_maps: dict[str, dict[str, str]]
    time_limit_s: int
    started_at: float
    meta: float
    finished: bool = False
    result: dict | None = field(default=None, repr=False)


def _letter_map(q: dict, n_alts: int) -> dict[str, str]:
    """Exibe n alternativas. Retira as últimas erradas (nunca a certa) e reetiqueta A, B, C…"""
    keys = list(q["alternativas"])
    drop = len(keys) - n_alts
    keep = list(keys)
    for k in reversed(keys):
        if drop <= 0:
            break
        if k != q["gabarito"]:
            keep.remove(k)
            drop -= 1
    return {"ABCDE"[i]: orig for i, orig in enumerate(keep)}


def build(bank: Bank, concurso_id: str, nivel: str, seen: set[str] | None = None,
          seed: int | None = None) -> ExamSession:
    concurso = bank.concurso(concurso_id)
    if nivel not in LEVELS:
        raise ValueError(f"nível inválido: {nivel}")
    minimo = concurso.get("nivel_minimo")
    if minimo and LEVELS.index(nivel) < LEVELS.index(minimo):
        raise ValueError(f"{concurso['nome']} começa no nível {bank.niveis[minimo]['nome']}")
    cfg = bank.niveis[nivel]
    rng = random.Random(seed)
    target = LEVELS.index(nivel)
    seen = seen or set()

    pool = [q for q in bank.questoes if q["formato"] == concurso["formato"] and q["area"] in concurso["areas"]]
    if not pool:
        raise ValueError("banco sem questões para este concurso")
    # prioridade: não vista > nível mais próximo do pedido > sorteio
    ranked = sorted(pool, key=lambda q: (q["id"] in seen, abs(LEVELS.index(q["nivel"]) - target), rng.random()))
    chosen = ranked[: cfg["questoes"]]
    rng.shuffle(chosen)  # intercala áreas e níveis (interleaving ajuda a retenção)

    maps = {}
    if concurso["formato"] == "multipla":
        n_alts = concurso.get("alternativas", 5)
        maps = {q["id"]: _letter_map(q, n_alts) for q in chosen}
    limit = int(len(chosen) * concurso["segundos_por_questao"] * cfg["fator_tempo"])
    # concurso com regra de aprovação própria (OAB: 50%) usa a regra real em vez da meta do nível
    meta = concurso.get("meta_fixa", cfg["meta"])
    return ExamSession(uuid.uuid4().hex, concurso_id, nivel, [q["id"] for q in chosen], maps, limit,
                       time.time(), meta)


def public_view(bank: Bank, s: ExamSession) -> dict:
    concurso = bank.concurso(s.concurso_id)
    cfg = bank.niveis[s.nivel]
    items = []
    for n, qid in enumerate(s.question_ids, start=1):
        q = bank.by_id[qid]
        item = {"n": n, "id": qid, "formato": q["formato"], "area": q["area"], "tema": q["tema"],
                "nivel": q["nivel"], "enunciado": q["enunciado"]}
        if q["formato"] == "multipla":
            item["alternativas"] = {shown: q["alternativas"][orig] for shown, orig in s.letter_maps[qid].items()}
        items.append(item)
    return {
        "sessao": s.id, "concurso": concurso["nome"], "banca": concurso["banca"], "formato": concurso["formato"],
        "regra": concurso["regra_descricao"], "nivel": s.nivel, "nivel_nome": cfg["nome"], "nivel_icone": cfg["icone"],
        "meta": s.meta, "tempo_limite_s": s.time_limit_s, "questoes": items,
    }


def grade(bank: Bank, s: ExamSession, answers: dict[str, str | None], lookup=None) -> dict:
    """Corrige. ``lookup(chave_resolvida)`` devolve o texto do dispositivo no catálogo (ou None)."""
    if s.finished and s.result:
        return s.result
    concurso = bank.concurso(s.concurso_id)
    elapsed = time.time() - s.started_at
    late = elapsed > s.time_limit_s + GRACE_SECONDS

    acertos = erros = brancos = 0
    combo = best_combo = xp = 0
    por_area: dict[str, dict[str, int]] = {}
    detalhes = []
    for n, qid in enumerate(s.question_ids, start=1):
        q = bank.by_id[qid]
        raw = answers.get(qid)
        given = raw.strip().upper() if isinstance(raw, str) and raw.strip() else None
        if q["formato"] == "multipla":
            mapping = s.letter_maps[qid]
            given_orig = mapping.get(given) if given else None
            shown_gabarito = next(k for k, v in mapping.items() if v == q["gabarito"])
        else:
            given_orig = given if given in ("C", "E") else None
            shown_gabarito = q["gabarito"]
        area = por_area.setdefault(q["area"], {"acertos": 0, "total": 0})
        area["total"] += 1
        if given_orig is None:
            brancos += 1
            status = "branco"
            combo = 0
        elif given_orig == q["gabarito"]:
            acertos += 1
            area["acertos"] += 1
            status = "certa"
            xp += g.xp_for_answer(True, q["nivel"], combo)
            combo += 1
            best_combo = max(best_combo, combo)
        else:
            erros += 1
            status = "errada"
            xp += g.xp_for_answer(False, q["nivel"])
            combo = 0
        detalhes.append({
            "n": n, "id": qid, "status": status, "resposta": given, "gabarito": shown_gabarito,
            "enunciado": q["enunciado"], "tema": q["tema"], "area": q["area"], "nivel": q["nivel"],
            "alternativas": ({k: q["alternativas"][v] for k, v in s.letter_maps[qid].items()}
                             if q["formato"] == "multipla" else None),
            "explicacao": q["explicacao"], "pegadinha": q.get("pegadinha"),
            "fundamentos": [_fundamento(bank, f, lookup) for f in q["fundamentos"]],
        })

    total = len(s.question_ids)
    if concurso["regra"] == "cebraspe":
        pontos = acertos - erros  # cada erro anula um acerto
        nota = max(0, pontos) / total
    else:
        pontos = acertos
        nota = acertos / total
    aprovado = nota >= s.meta and not late
    if aprovado:
        xp += bank.niveis[s.nivel]["bonus_xp"]

    s.finished = True
    s.result = {
        "sessao": s.id, "concurso": concurso["nome"], "nivel": s.nivel, "nivel_nome": bank.niveis[s.nivel]["nome"],
        "regra": concurso["regra"], "acertos": acertos, "erros": erros, "brancos": brancos, "total": total,
        "pontos": pontos, "nota": round(nota, 4), "meta": s.meta, "aprovado": aprovado, "tempo_esgotado": late,
        "tempo_gasto_s": int(elapsed), "melhor_combo": best_combo, "xp": xp,
        "por_area": por_area, "questoes": detalhes,
    }
    return s.result


def _fundamento(bank: Bank, f: dict, lookup) -> dict:
    chave = bank.resolve(f["chave"])
    found = lookup(chave) if lookup else None
    out = {"chave": f["chave"], "trecho": f["trecho"], "no_catalogo": bool(found)}
    if found:
        out.update(found)
    return out
