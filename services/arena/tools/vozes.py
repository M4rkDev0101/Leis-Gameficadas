"""Dublagem do Modo Tribunal: ElevenLabs (nuvem) ou VoiceStudio/OmniVoice (local, sem cota).

    python services/arena/tools/vozes.py exportar --saida vozes/          # roteiro.csv + elenco.csv
    python services/arena/tools/escalar_vozes.py --saida vozes/ --vozes conta.json   # (ElevenLabs) voice_id por perfil
    python services/arena/tools/vozes.py perfis --saida vozes/            # (VoiceStudio) cria 1 perfil de voz por personagem
    python services/arena/tools/vozes.py gerar --saida vozes/ --motor voicestudio [--sem-voce] [--casos ep1-celular]

Motor local (VoiceStudio, http://localhost:3900): ``perfis`` desenha a voz de cada personagem a partir de
gênero, idade e tom (``elenco.csv``), grava uma amostra de referência e a salva como perfil (coluna
``perfil_vs``). ``gerar --motor voicestudio`` clona esse perfil em todas as falas, que é o modo estável do
OmniVoice (o desenho por descrição só é usado uma vez, na referência).

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
VS = os.environ.get("VOICESTUDIO_URL", "http://localhost:3900")
REF_TEXT = ("Boa tarde. Eu estive lá naquela noite e vi tudo o que aconteceu. "
            "Posso explicar com calma, do começo ao fim, se o senhor me permitir.")
IDADE_EN = {"crianca": "child", "jovem": "young adult", "adulto": "young adult", "maduro": "middle-aged", "idoso": "elderly"}
TOM_EN = {"grave": "low pitch", "médio": "moderate pitch", "agudo": "high pitch"}


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
    old: dict[str, dict] = {}
    if (out / "elenco.csv").exists():  # preserva voice_id, perfis do VoiceStudio e classificação já feitos
        with open(out / "elenco.csv", encoding="utf-8-sig") as f:
            old = {r["personagem"]: r for r in csv.DictReader(f, delimiter=";")}
    stats: dict[str, list[int]] = {}
    for ln in lines:
        s = stats.setdefault(ln["personagem"], [0, 0])
        s[0] += 1
        s[1] += len(ln["texto"])
    rows = []
    for q, (n, chars) in sorted(stats.items(), key=lambda kv: -kv[1][1]):
        p = data["personagens"].get(q, {})
        tom = "conforme o avatar" if q == "voce" else "grave" if p.get("voz", 300) < 260 else "agudo" if p.get("voz", 300) > 430 else "médio"
        rows.append({**old.get(q, {}), "personagem": q, "nome": p.get("nome") or q.capitalize(), "cargo": p.get("cargo", ""),
                     "falas": n, "caracteres": chars, "tom_sugerido": tom, "voice_id": old.get(q, {}).get("voice_id", "")})
    _write_cast(out, rows)
    total = sum(s[1] for s in stats.values())
    print(f"{len(lines)} falas únicas, {total} caracteres, {len(stats)} personagens -> {out}")


def _read_cast(out: Path) -> list[dict]:
    with open(out / "elenco.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _write_cast(out: Path, rows: list[dict]) -> None:
    cols = list(dict.fromkeys([k for r in rows for k in r]))
    with open(out / "elenco.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        w.writerows(rows)


def _vs_speech(body: dict, timeout: int = 1800) -> bytes:
    req = urllib.request.Request(VS + "/v1/audio/speech", data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = "----vade" + hashlib.sha1(os.urandom(8)).hexdigest()
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode("utf-8"))
    for k, (name, data, ctype) in files.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{name}"\r\n'
                     f"Content-Type: {ctype}\r\n\r\n".encode("utf-8") + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def perfis(out: Path, so: set[str], passos: int, unicos: int = 30) -> None:
    """VoiceStudio: desenha a voz de cada personagem e salva como perfil (retomável).

    Os ``unicos`` personagens com mais texto ganham voz própria; os demais compartilham um perfil por
    combinação de gênero, idade e tom (no CPU, cada referência custa minutos)."""
    rows = _read_cast(out)  # já vem ordenado por caracteres
    (out / "referencias").mkdir(exist_ok=True)
    shared = {r["instruct_vs"]: r["perfil_vs"] for r in rows if r.get("perfil_vs") and r.get("compartilhado") == "sim"}
    rank = 0
    for r in rows:
        q = r["personagem"]
        if q == "voce":
            continue
        rank += 1
        if r.get("perfil_vs") or (so and q not in so):
            continue
        genero = {"mulher": "female", "homem": "male"}.get(r.get("genero"), "male")
        instruct = ", ".join([genero, IDADE_EN.get(r.get("idade"), "middle-aged"), TOM_EN.get(r.get("tom_sugerido"), "moderate pitch")])
        own = rank <= unicos or q == "narrador"
        if not own and instruct in shared:
            r["perfil_vs"], r["instruct_vs"], r["compartilhado"] = shared[instruct], instruct, "sim"
            _write_cast(out, rows)
            continue
        key = q if own else "arquetipo-" + instruct.replace(", ", "-").replace(" ", "_")
        seed = int(hashlib.sha1(key.encode()).hexdigest()[:8], 16) % 2_000_000_000
        t0 = time.time()
        wav = _vs_speech({"model": "omnivoice", "input": REF_TEXT, "voice": "default", "instructions": instruct,
                          "language": "pt", "response_format": "wav", "seed": seed, "num_step": passos})
        (out / "referencias" / f"{key}.wav").write_bytes(wav)
        body, ctype = _multipart({"name": f"Vade · {r.get('nome') or q}" if own else f"Vade · {instruct}", "ref_text": REF_TEXT, "language": "pt",
                                  "instruct": instruct, "personality": r.get("cargo", "")},
                                 {"ref_audio": (f"{q}.wav", wav, "audio/wav")})
        req = urllib.request.Request(VS + "/profiles", data=body, method="POST", headers={"Content-Type": ctype})
        with urllib.request.urlopen(req, timeout=300) as resp:
            perfil = json.loads(resp.read())
        r["perfil_vs"] = perfil.get("id") or perfil.get("profile_id") or ""
        r["instruct_vs"] = instruct
        r["compartilhado"] = "" if own else "sim"
        if not own:
            shared[instruct] = r["perfil_vs"]
        _write_cast(out, rows)  # grava a cada perfil: pode parar e retomar
        print(f"  {q}: {instruct} -> perfil {r['perfil_vs']} ({time.time() - t0:.0f}s)")


def gerar(out: Path, sem_voce: bool, limite: int, so: set[str], chave_arquivo: str | None, modelo: str,
          casos: set[str] = frozenset(), motor: str = "elevenlabs", passos: int = 8) -> None:
    if motor == "voicestudio":
        voices = {r["personagem"]: r["perfil_vs"] for r in _read_cast(out) if r.get("perfil_vs")}
        key = ""
    else:
        key = os.environ.get("ELEVENLABS_API_KEY") or (Path(chave_arquivo).read_text(encoding="utf-8").strip() if chave_arquivo else "")
        if not key:
            sys.exit("Defina ELEVENLABS_API_KEY ou use --chave-arquivo.")
        voices = {r["personagem"]: r["voice_id"].strip() for r in _read_cast(out) if r.get("voice_id", "").strip()}
    with open(out / "roteiro.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    gastos = feitos = faltando_voz = 0
    for r in rows:
        q, path = r["personagem"], out / r["arquivo"]
        if path.exists() or (sem_voce and q == "voce") or (so and q not in so) or (casos and r["primeira_cena"].split("/")[0] not in casos):
            continue
        if q not in voices:
            faltando_voz += 1
            continue
        if gastos + len(r["texto"]) > limite:
            break
        if motor == "voicestudio":
            try:
                path.write_bytes(_vs_speech({"model": "omnivoice", "input": r["texto"], "voice": voices[q], "language": "pt",
                                             "response_format": "mp3", "num_step": passos}))
            except urllib.error.HTTPError as exc:
                sys.exit(f"VoiceStudio recusou ({exc.code}) na fala {r['arquivo']}: {exc.read()[:300]!r}")
            gastos += len(r["texto"])
            feitos += 1
            if feitos % 10 == 0:
                print(f"  {feitos} áudios, {gastos} caracteres")
            continue
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
    pf = sub.add_parser("perfis", help="VoiceStudio: cria o perfil de voz de cada personagem")
    pf.add_argument("--saida", default="vozes")
    pf.add_argument("--so", default="")
    pf.add_argument("--passos", type=int, default=16, help="passos do OmniVoice na amostra de referência")
    pf.add_argument("--unicos", type=int, default=30, help="quantos personagens (os que mais falam) têm voz própria")
    g = sub.add_parser("gerar")
    g.add_argument("--saida", default="vozes")
    g.add_argument("--sem-voce", action="store_true", help="não dubla o protagonista (economiza ~37%% dos caracteres)")
    g.add_argument("--limite", type=int, default=10_000_000, help="máximo de caracteres nesta rodada")
    g.add_argument("--so", default="", help="só estes personagens (ids separados por vírgula)")
    g.add_argument("--chave-arquivo", help="arquivo de texto com a chave da API")
    g.add_argument("--modelo", default="eleven_multilingual_v2")
    g.add_argument("--casos", default="", help="só falas que estreiam nestes casos (ids separados por vírgula)")
    g.add_argument("--motor", choices=["elevenlabs", "voicestudio"], default="elevenlabs")
    g.add_argument("--passos", type=int, default=8, help="VoiceStudio: passos do OmniVoice por fala (menos = mais rápido)")
    a = ap.parse_args()
    out = Path(a.saida)
    if a.cmd == "exportar":
        exportar(out)
    elif a.cmd == "perfis":
        perfis(out, {s for s in a.so.split(",") if s}, a.passos, a.unicos)
    else:
        gerar(out, a.sem_voce, a.limite, {s for s in a.so.split(",") if s}, a.chave_arquivo, a.modelo,
              {c for c in a.casos.split(",") if c}, a.motor, a.passos)


if __name__ == "__main__":
    main()
