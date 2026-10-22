"""Dublagem do Modo Tribunal com a ElevenLabs.

    python services/arena/tools/vozes.py exportar --saida vozes/          # roteiro.csv + elenco.csv
    python services/arena/tools/vozes.py gerar --saida vozes/ [--sem-voce] [--limite 50000] [--so dani,lacerda]

1. ``exportar`` gera ``roteiro.csv`` (uma linha por fala, com o arquivo de áudio esperado) e ``elenco.csv``
   (um personagem por linha, com contagem de caracteres e uma coluna ``voice_id`` para preencher).
2. Preencha ``voice_id`` no ``elenco.csv`` (ids da sua biblioteca de vozes da ElevenLabs).
3. ``gerar`` lê a chave da variável de ambiente ``ELEVENLABS_API_KEY`` (ou do arquivo indicado em
   ``--chave-arquivo``), nunca de argumento de linha de comando, e grava ``<id>.mp3``. É retomável: pula os
   arquivos que já existem, então dá para gerar aos poucos, dentro da cota do mês.

O id de cada fala é ``sha1("personagem|texto")[:12]``: falas repetidas viram um só arquivo, e mexer na
ordem das cenas não invalida o que já foi gerado. O jogo procura os áudios em
``%LOCALAPPDATA%/VadeTribunal/vozes`` (ou em ``VADE_VOZES``) e usa os bipes quando não há áudio.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vade_arena import tribunal  # noqa: E402

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_64"


def voice_id(q: str, t: str) -> str:
    return hashlib.sha1(f"{q}|{t}".encode("utf-8")).hexdigest()[:12]


def all_lines(data: dict) -> list[dict]:
    """Falas únicas (personagem + texto), na ordem em que aparecem na carreira."""
    seen: dict[str, dict] = {}
    for ep in data["episodios"]:
        for sid, c in ep["cenas"].items():
            items = [(f["q"], f.get("e", "normal"), f["t"]) for f in tribunal._falas(c)]
            items += [(c["testemunha"], a.get("e", "normal"), a["t"]) for a in c.get("afirmacoes", [])]
            for q, e, t in items:
                vid = voice_id(q, t)
                if vid in seen:
                    seen[vid]["casos"].add(ep["id"])
                    continue
                seen[vid] = {"id": vid, "personagem": q, "expressao": e, "texto": t, "casos": {ep["id"]}, "cena": f"{ep['id']}/{sid}"}
    return list(seen.values())


def exportar(out: Path) -> None:
    data = tribunal.load()
    out.mkdir(parents=True, exist_ok=True)
    lines = all_lines(data)
    with open(out / "roteiro.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["arquivo", "personagem", "nome", "expressao", "texto", "primeira_cena", "casos"])
        for ln in lines:
            nome = data["personagens"].get(ln["personagem"], {}).get("nome", ln["personagem"])
            w.writerow([ln["id"] + ".mp3", ln["personagem"], nome, ln["expressao"], ln["texto"], ln["cena"], len(ln["casos"])])
    old = {}
    if (out / "elenco.csv").exists():  # preserva os voice_id já preenchidos
        with open(out / "elenco.csv", encoding="utf-8-sig") as f:
            old = {r["personagem"]: r.get("voice_id", "") for r in csv.DictReader(f, delimiter=";")}
    stats: dict[str, list[int]] = {}
    for ln in lines:
        s = stats.setdefault(ln["personagem"], [0, 0])
        s[0] += 1
        s[1] += len(ln["texto"])
    with open(out / "elenco.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["personagem", "nome", "cargo", "falas", "caracteres", "tom_sugerido", "voice_id"])
        for q, (n, chars) in sorted(stats.items(), key=lambda kv: -kv[1][1]):
            p = data["personagens"].get(q, {})
            tom = "conforme o avatar" if q == "voce" else "grave" if p.get("voz", 300) < 260 else "agudo" if p.get("voz", 300) > 430 else "médio"
            w.writerow([q, p.get("nome") or q.capitalize(), p.get("cargo", ""), n, chars, tom, old.get(q, "")])
    total = sum(s[1] for s in stats.values())
    print(f"{len(lines)} falas únicas, {total} caracteres, {len(stats)} personagens -> {out}")


def gerar(out: Path, sem_voce: bool, limite: int, so: set[str], chave_arquivo: str | None, modelo: str) -> None:
    key = os.environ.get("ELEVENLABS_API_KEY") or (Path(chave_arquivo).read_text(encoding="utf-8").strip() if chave_arquivo else "")
    if not key:
        sys.exit("Defina ELEVENLABS_API_KEY ou use --chave-arquivo.")
    with open(out / "elenco.csv", encoding="utf-8-sig") as f:
        voices = {r["personagem"]: r["voice_id"].strip() for r in csv.DictReader(f, delimiter=";") if r["voice_id"].strip()}
    with open(out / "roteiro.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    gastos = feitos = faltando_voz = 0
    for r in rows:
        q, path = r["personagem"], out / r["arquivo"]
        if path.exists() or (sem_voce and q == "voce") or (so and q not in so):
            continue
        if q not in voices:
            faltando_voz += 1
            continue
        if gastos + len(r["texto"]) > limite:
            break
        body = json.dumps({"text": r["texto"], "model_id": modelo, "language_code": "pt",
                           "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25}}).encode()
        req = urllib.request.Request(API.format(voice=voices[q]), data=body, method="POST",
                                     headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        for tentativa in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    path.write_bytes(resp.read())
                break
            except urllib.error.HTTPError as exc:
                msg = exc.read()[:300].decode("utf-8", "replace")
                if exc.code == 429 and tentativa < 3:
                    time.sleep(5 * (tentativa + 1))
                    continue
                sys.exit(f"ElevenLabs recusou ({exc.code}) na fala {r['arquivo']}: {msg}")
        gastos += len(r["texto"])
        feitos += 1
        if feitos % 25 == 0:
            print(f"  {feitos} áudios, {gastos} caracteres")
    pend = sum(1 for r in rows if not (out / r["arquivo"]).exists() and not (sem_voce and r["personagem"] == "voce"))
    print(f"Gerados agora: {feitos} ({gastos} caracteres). Ainda faltam {pend} falas; {faltando_voz} sem voice_id no elenco.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("exportar")
    e.add_argument("--saida", default="vozes")
    g = sub.add_parser("gerar")
    g.add_argument("--saida", default="vozes")
    g.add_argument("--sem-voce", action="store_true", help="não dubla o protagonista (economiza ~37%% dos caracteres)")
    g.add_argument("--limite", type=int, default=10_000_000, help="máximo de caracteres nesta rodada")
    g.add_argument("--so", default="", help="só estes personagens (ids separados por vírgula)")
    g.add_argument("--chave-arquivo", help="arquivo de texto com a chave da API")
    g.add_argument("--modelo", default="eleven_multilingual_v2")
    a = ap.parse_args()
    out = Path(a.saida)
    if a.cmd == "exportar":
        exportar(out)
    else:
        gerar(out, a.sem_voce, a.limite, {s for s in a.so.split(",") if s}, a.chave_arquivo, a.modelo)


if __name__ == "__main__":
    main()
