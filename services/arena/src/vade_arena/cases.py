"""Casos narrativos: advogado, promotor ou juiz.

O cliente recebe uma cena por vez, sem os efeitos e o destino das escolhas. Assim não dá para
"espiar" o melhor caminho, como num jogo de verdade.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from .bank import Bank, best_score

ROLE_LABEL = {"advogado": "Advogado(a)", "promotor": "Promotor(a)", "juiz": "Juiz(a)"}


@dataclass
class CaseRun:
    id: str
    caso_id: str
    scene: str | None
    argumento: int = 0
    credibilidade: int = 0
    escolhas: list[dict] = field(default_factory=list)
    final: dict | None = None


def start(bank: Bank, caso_id: str) -> CaseRun:
    caso = bank.caso(caso_id)
    return CaseRun(uuid.uuid4().hex, caso_id, caso["inicio"])


def summary(bank: Bank, caso: dict) -> dict:
    return {"id": caso["id"], "titulo": caso["titulo"], "papel": caso["papel"], "papel_nome": ROLE_LABEL[caso["papel"]],
            "nivel": caso["nivel"], "nivel_nome": bank.niveis[caso["nivel"]]["nome"],
            "nivel_icone": bank.niveis[caso["nivel"]]["icone"], "area": caso["area"], "sinopse": caso["sinopse"],
            "cenas": len(caso["cenas"])}


def scene_view(bank: Bank, run: CaseRun) -> dict:
    caso = bank.caso(run.caso_id)
    cena = caso["cenas"][run.scene]
    order = list(caso["cenas"]).index(run.scene) + 1
    return {
        "sessao": run.id, "caso": summary(bank, caso), "cena": run.scene, "etapa": order, "etapas": len(caso["cenas"]),
        "local": cena.get("local", ""),
        "falas": [{"quem": bank.elenco[f["quem"]]["nome"], "cargo": bank.elenco[f["quem"]]["cargo"],
                   "cor": bank.elenco[f["quem"]].get("cor", "muted"), "texto": f["texto"]} for f in cena["falas"]],
        "pergunta": cena["pergunta"],
        "escolhas": [{"indice": i, "texto": e["texto"]} for i, e in enumerate(cena["escolhas"])],
        "medidores": {"argumento": run.argumento, "credibilidade": run.credibilidade},
    }


def choose(bank: Bank, run: CaseRun, index: int, lookup=None) -> dict:
    if run.final is not None or run.scene is None:
        raise ValueError("caso já encerrado")
    caso = bank.caso(run.caso_id)
    cena = caso["cenas"][run.scene]
    if not 0 <= index < len(cena["escolhas"]):
        raise ValueError("escolha inválida")
    e = cena["escolhas"][index]
    ef = {"argumento": e.get("efeito", {}).get("argumento", 0), "credibilidade": e.get("efeito", {}).get("credibilidade", 0)}
    run.argumento += ef["argumento"]
    run.credibilidade += ef["credibilidade"]
    run.escolhas.append({"cena": run.scene, "indice": index})

    fundamentos = []
    for f in e.get("fundamentos", []):
        item = {"chave": f["chave"], "trecho": f["trecho"]}
        found = lookup(bank.resolve(f["chave"])) if lookup else None
        if found:
            item.update(found)
        fundamentos.append(item)

    out = {"feedback": e["feedback"], "efeito": ef, "fundamentos": fundamentos,
           "medidores": {"argumento": run.argumento, "credibilidade": run.credibilidade},
           "melhor_escolha": ef["argumento"] + ef["credibilidade"] == max(
               sum(x.get("efeito", {}).values()) for x in cena["escolhas"])}
    run.scene = e.get("proxima")
    if run.scene is None:
        run.final = _final(caso, run)
        out["final"] = run.final
    else:
        out["proxima"] = scene_view(bank, run)
    return out


def _final(caso: dict, run: CaseRun) -> dict:
    score = run.argumento + run.credibilidade
    best = best_score(caso)
    ordered = sorted(caso["finais"], key=lambda f: -f["min"])
    for i, f in enumerate(ordered):
        if score >= f["min"]:
            faixa = "otimo" if i == 0 else ("ruim" if i == len(ordered) - 1 else "medio")
            return {**f, "faixa": faixa, "pontuacao": score, "maximo": best,
                    "aproveitamento": round(max(score, 0) / best, 4),
                    "argumento": run.argumento, "credibilidade": run.credibilidade}
    raise AssertionError("finais devem cobrir qualquer pontuação (validado em bank.validate_structure)")
