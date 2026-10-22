"""Escala as vozes da ElevenLabs para o elenco: gênero e faixa etária de cada personagem.

    python services/arena/tools/escalar_vozes.py --saida vozes --vozes vozes_conta.json

``vozes_conta.json`` é a resposta de ``GET /v1/voices`` da sua conta. Preenche ``genero``, ``idade`` e
``voice_id`` no ``elenco.csv`` (só onde ``voice_id`` está vazio, para respeitar escolhas manuais) e grava a
tabela de escalação em ``escalacao.csv``. O protagonista (``voce``) fica sem voz: é o avatar do jogador.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vade_arena import tribunal  # noqa: E402

FEM_PREFIX = ("Dra.", "Dona", "Desa.")
NARRADOR_PREFERIDA = "brazilian"


def classificar(q: str, p: dict) -> tuple[str, str]:
    nome, cargo = p.get("nome", ""), p.get("cargo", "")
    genero = "f" if p.get("voz", 0) >= 395 or nome.startswith(FEM_PREFIX) else "m"
    m = re.search(r"(\d{1,2}) anos", cargo)
    anos = int(m.group(1)) if m else None
    cor = ((p.get("visual") or {}).get("corCabelo") or "#000000").lower()
    cinza = len(cor) == 7 and cor[1:3] == cor[3:5] == cor[5:7]
    tom = int(cor[1:3], 16) if cinza else 0
    if anos is not None and anos < 14:
        idade = "crianca"
    elif (anos and anos >= 60) or re.search(r"aposentad|viúva", cargo, re.I) or tom >= 0xc0 or nome.startswith(("Des.", "Desa.")):
        idade = "idoso"
    elif anos is not None and anos <= 25 or "estudante" in cargo.lower():
        idade = "jovem"
    elif tom >= 0x55:
        idade = "maduro"
    else:
        idade = "adulto"
    return genero, idade


# pools por (gênero, idade), em ordem de preferência; caem para a faixa vizinha se faltar voz
VIZINHAS = {"crianca": ["crianca", "jovem"], "jovem": ["jovem", "adulto"], "adulto": ["adulto", "maduro", "jovem"],
            "maduro": ["maduro", "adulto", "idoso"], "idoso": ["idoso", "maduro"]}


def pools(voices: list[dict]) -> dict[tuple[str, str], list[str]]:
    out: dict[tuple[str, str], list[str]] = {}
    for v in voices:
        lab = v.get("labels") or {}
        g = {"female": "f", "male": "m"}.get(lab.get("gender"))
        idade = {"young": "jovem", "middle_aged": "adulto", "old": "idoso"}.get(lab.get("age"))
        if not g or not idade:
            continue
        out.setdefault((g, idade), []).append(v["voice_id"])
        if idade == "adulto":
            out.setdefault((g, "maduro"), []).append(v["voice_id"])
        if g == "f" and idade == "jovem" and "cute" in str(lab).lower():
            out.setdefault((g, "crianca"), []).append(v["voice_id"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="vozes")
    ap.add_argument("--vozes", required=True)
    a = ap.parse_args()
    out = Path(a.saida)
    voices = json.loads(Path(a.vozes).read_text(encoding="utf-8"))["voices"]
    names = {v["voice_id"]: v["name"].split(" - ")[0] for v in voices}
    narr = next((v["voice_id"] for v in voices if (v.get("labels") or {}).get("accent") == NARRADOR_PREFERIDA), None)
    P = pools([v for v in voices if v["voice_id"] != narr])
    data = tribunal.load()
    with open(out / "elenco.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    uso: Counter[str] = Counter()
    # quem contracena no mesmo caso não deve ter a mesma voz
    juntos: dict[str, set[str]] = {}
    for ep in data["episodios"]:
        elenco = set(ep.get("posicoes", {}))
        for q in elenco:
            juntos.setdefault(q, set()).update(elenco - {q})
    voz_de: dict[str, str] = {r["personagem"]: r["voice_id"] for r in rows if r.get("voice_id")}
    for r in rows:  # já ordenado por caracteres: protagonistas escolhem primeiro
        q = r["personagem"]
        g, idade = classificar(q, data["personagens"].get(q, {}))
        r["genero"], r["idade"] = ("-", "-") if q in ("voce", "narrador") else ({"f": "mulher", "m": "homem"}[g], idade)
        if q == "voce" or r.get("voice_id"):
            continue
        if q == "narrador":
            r["voice_id"] = narr or ""
            continue
        cand = [vid for faixa in VIZINHAS[idade] for vid in P.get((g, faixa), [])]
        if cand:
            conflito = Counter(voz_de[o] for o in juntos.get(q, ()) if o in voz_de)
            r["voice_id"] = min(dict.fromkeys(cand), key=lambda vid: (conflito[vid], uso[vid], cand.index(vid)))
            voz_de[q] = r["voice_id"]
            uso[r["voice_id"]] += int(r["caracteres"]) // 1000 + 1  # quem fala muito "pesa" mais na rotação
    base = ["personagem", "nome", "cargo", "genero", "idade", "falas", "caracteres", "tom_sugerido", "voice_id", "voz"]
    cols = list(dict.fromkeys(base + [k for r in rows for k in r]))  # preserva colunas de outras ferramentas (perfil_vs…)
    for r in rows:
        r["voz"] = names.get(r.get("voice_id", ""), "")
    with open(out / "elenco.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        w.writerows(rows)
    print(Counter((r["genero"], r["idade"]) for r in rows).most_common())
    print("vozes usadas:", len({r["voice_id"] for r in rows if r.get("voice_id")}))


if __name__ == "__main__":
    main()
