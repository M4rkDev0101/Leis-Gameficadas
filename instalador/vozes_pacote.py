"""Pacote de vozes (dublagem opcional): manifesto, download com retomada, verificação e extração.

Usado pelo lançador (vade_launcher.py) e pelo gerador (gerar_pacote_vozes.py). Só biblioteca padrão.

Formato publicado num GitHub Release com tag ``vozes-vN`` (N inteiro crescente):
  - ``vozes-manifesto.json``  {"formato":1, "versao":N, "tag":"vozes-vN", "total_arquivos":..., "tamanho_total":...,
                               "partes":[{"nome":"vozes-parte-0.zip","tamanho":..,"sha256":"..",
                                          "arquivos":{"<id>.mp3":{"sha256":"..","tamanho":..}, ...}}, ...]}
  - ``vozes-parte-*.zip``     mp3 na raiz do zip (sem pastas).
A divisão em partes é por prefixo do nome (estável): numa versão nova só as partes cujos arquivos mudaram
são baixadas de novo.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

REPO_API = "https://api.github.com/repos/M4rkDev0101/Leis-Gameficadas/releases?per_page=30"
MANIFESTO_NOME = "vozes-manifesto.json"
ESTADO_NOME = "pacote_vozes.json"  # dentro da pasta de vozes: {"versao": N}
TAG_RE = re.compile(r"^vozes-v(\d+)$")
NOME_MP3_RE = re.compile(r"^[A-Za-z0-9_.-]+\.mp3$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
Progress = Callable[[str, float], None]  # (texto, fração 0..1)


class PacoteErro(Exception):
    pass


def sha256_arquivo(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


# ------------------------------------------------------------------ manifesto
def validar_manifesto(m: dict) -> dict:
    """Levanta PacoteErro se o manifesto for inválido ou inseguro (nomes com caminho etc.)."""
    try:
        if m.get("formato") != 1 or not isinstance(m["versao"], int) or not m["partes"]:
            raise PacoteErro("manifesto de vozes em formato desconhecido")
        vistos: set[str] = set()
        for parte in m["partes"]:
            if not re.fullmatch(r"[A-Za-z0-9_.-]+\.zip", parte["nome"]):
                raise PacoteErro(f"nome de parte inválido: {parte['nome']!r}")
            if not SHA_RE.match(parte["sha256"]) or int(parte["tamanho"]) <= 0:
                raise PacoteErro(f"parte {parte['nome']}: sha256/tamanho inválidos")
            for nome, info in parte["arquivos"].items():
                if not NOME_MP3_RE.match(nome) or nome in vistos:
                    raise PacoteErro(f"arquivo inválido ou repetido no manifesto: {nome!r}")
                if not SHA_RE.match(info["sha256"]):
                    raise PacoteErro(f"sha256 inválido para {nome}")
                vistos.add(nome)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise PacoteErro(f"manifesto de vozes incompleto: {exc}") from exc
    return m


def versao_instalada(pasta: Path) -> int | None:
    try:
        return int(json.loads((pasta / ESTADO_NOME).read_text(encoding="utf-8"))["versao"])
    except Exception:
        return None


def partes_pendentes(m: dict, pasta: Path) -> list[dict]:
    """Partes que têm algum arquivo ausente ou diferente (tamanho, depois sha256) na pasta de vozes."""
    pend = []
    for parte in m["partes"]:
        for nome, info in parte["arquivos"].items():
            p = pasta / nome
            if not p.is_file() or p.stat().st_size != info["tamanho"] or sha256_arquivo(p) != info["sha256"]:
                pend.append(parte)
                break
    return pend


def tamanho_pendente(m: dict, pasta: Path) -> int:
    return sum(p["tamanho"] for p in partes_pendentes(m, pasta))


# ------------------------------------------------------------------ rede
def _abrir(url: str, headers: dict | None = None, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": "VadeTribunal", **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)


def buscar_release(api_url: str = REPO_API) -> dict | None:
    """Release publicado (não rascunho) com a maior tag vozes-vN, ou None."""
    with _abrir(api_url) as r:
        releases = json.loads(r.read().decode("utf-8"))
    melhor, n_melhor = None, -1
    for rel in releases:
        mt = TAG_RE.match(str(rel.get("tag_name", "")))
        if mt and not rel.get("draft") and not rel.get("prerelease") and int(mt.group(1)) > n_melhor:
            melhor, n_melhor = rel, int(mt.group(1))
    return melhor


def asset_url(release: dict, nome: str) -> str:
    for a in release.get("assets", []):
        if a.get("name") == nome:
            return a["browser_download_url"]
    raise PacoteErro(f"o release {release.get('tag_name')} não tem o arquivo {nome}")


def buscar_manifesto(release: dict) -> dict:
    with _abrir(asset_url(release, MANIFESTO_NOME)) as r:
        m = validar_manifesto(json.loads(r.read().decode("utf-8")))
    if m.get("tag") not in (None, release.get("tag_name")):
        raise PacoteErro("manifesto não corresponde à tag do release")
    return m


def baixar_retomavel(url: str, destino: Path, tamanho: int, sha256: str,
                     progresso: Callable[[int], None] | None = None) -> None:
    """Baixa para ``destino`` (via ``destino.part``), retomando de onde parou (Range) e conferindo o sha256.
    Se o servidor ignorar o Range recomeça do zero; se o sha256 não bater, apaga e levanta PacoteErro."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    part = destino.with_name(destino.name + ".part")
    if destino.is_file() and destino.stat().st_size == tamanho and sha256_arquivo(destino) == sha256:
        if progresso:
            progresso(tamanho)
        return
    have = part.stat().st_size if part.exists() else 0
    if have > tamanho:
        part.unlink()
        have = 0
    if have < tamanho:
        try:
            resp = _abrir(url, {"Range": f"bytes={have}-"} if have else None)
        except urllib.error.HTTPError as exc:
            if exc.code == 416:  # .part inconsistente: descarta; a próxima tentativa recomeça
                part.unlink(missing_ok=True)
                raise PacoteErro("download parcial inválido; recomeçando") from exc
            raise
        with resp:
            if have and resp.status != 206:  # servidor ignorou o Range
                have = 0
            with open(part, "ab" if have else "wb") as f:
                feito = have
                while True:
                    bloco = resp.read(1 << 18)
                    if not bloco:
                        break
                    f.write(bloco)
                    feito += len(bloco)
                    if progresso:
                        progresso(feito)
    if part.stat().st_size < tamanho:  # conexão caiu: mantém o .part para retomar na próxima tentativa
        raise OSError(f"{destino.name}: download interrompido em {part.stat().st_size}/{tamanho} bytes")
    if part.stat().st_size != tamanho or sha256_arquivo(part) != sha256:
        part.unlink(missing_ok=True)
        raise PacoteErro(f"{destino.name}: arquivo corrompido (sha256 não confere)")
    os.replace(part, destino)


def extrair_parte(zip_path: Path, parte: dict, pasta: Path) -> int:
    """Extrai só os mp3 listados no manifesto (nada fora dele), confere o sha256 de cada um e troca atomicamente."""
    n = 0
    with zipfile.ZipFile(zip_path) as z:
        nomes = set(z.namelist())
        for nome, info in parte["arquivos"].items():
            if nome not in nomes:
                raise PacoteErro(f"{zip_path.name} não contém {nome}")
            tmp = pasta / (nome + ".tmp")
            h = hashlib.sha256()
            with z.open(nome) as src, open(tmp, "wb") as dst:
                for bloco in iter(lambda: src.read(1 << 20), b""):
                    h.update(bloco)
                    dst.write(bloco)
            if h.hexdigest() != info["sha256"]:
                tmp.unlink(missing_ok=True)
                raise PacoteErro(f"{nome}: sha256 diferente do manifesto")
            os.replace(tmp, pasta / nome)
            n += 1
    return n


def instalar(manifesto: dict, release: dict, pasta: Path, progresso: Progress | None = None,
             tentativas: int = 3) -> dict:
    """Baixa e extrai as partes pendentes. Retorna {"baixadas": k, "arquivos": n, "bytes": b}. Retomável."""
    pasta.mkdir(parents=True, exist_ok=True)
    prog = progresso or (lambda t, f: None)
    pend = partes_pendentes(manifesto, pasta)
    total = sum(p["tamanho"] for p in pend) or 1
    feitos, arquivos = 0, 0
    cache = pasta / ".baixando"
    for parte in pend:
        url = asset_url(release, parte["nome"])
        zip_path = cache / parte["nome"]
        for t in range(1, tentativas + 1):
            try:
                baixar_retomavel(url, zip_path, parte["tamanho"], parte["sha256"],
                                 lambda b, base=feitos, nome=parte["nome"]: prog(f"Baixando vozes: {nome}", (base + b) / total))
                arquivos += extrair_parte(zip_path, parte, pasta)
                break
            except (OSError, PacoteErro, zipfile.BadZipFile):
                if t == tentativas:
                    raise
        zip_path.unlink(missing_ok=True)
        feitos += parte["tamanho"]
    shutil.rmtree(cache, ignore_errors=True)
    (pasta / ESTADO_NOME).write_text(json.dumps({"versao": manifesto["versao"]}), encoding="utf-8")
    prog("Dublagem instalada", 1.0)
    return {"baixadas": len(pend), "arquivos": arquivos, "bytes": sum(p["tamanho"] for p in pend)}


# ------------------------------------------------------------------ decisão (usada pelo lançador)
def _config(cfg: Path) -> dict:
    try:
        return json.loads(cfg.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sincronizar(pasta: Path, cfg: Path, perguntar: Callable[[str, str], bool], dizer: Progress,
                api_url: str = REPO_API, forcar: bool = False) -> str:
    """Oferece/instala/atualiza a dublagem. Nunca levanta: sem internet, sem release ou erro => o jogo segue
    sem (ou com a) dublagem que já existe. Retorna: 'sem-pacote' | 'atual' | 'recusada' | 'instalada' | 'erro'."""
    try:
        release = buscar_release(api_url)
        if release is None:
            return "sem-pacote"
        m = buscar_manifesto(release)
    except Exception:
        return "sem-pacote"  # sem internet / API fora do ar / manifesto inválido
    try:
        inst = versao_instalada(pasta)
        conf = _config(cfg)
        if inst is not None and inst >= m["versao"] and not forcar:
            return "atual"
        if inst is None:
            if conf.get("vozes") == "recusou" and not forcar:
                return "recusada"
            mb = tamanho_pendente(m, pasta) / 1e6
            if not perguntar("Dublagem do jogo", f"Há um pacote opcional com a dublagem das falas ({m['total_arquivos']} falas, "
                             f"cerca de {mb:.0f} MB de download). Baixar agora?\n\n"
                             "Sem ele o jogo funciona normalmente, com bipes."):
                cfg.parent.mkdir(parents=True, exist_ok=True)
                cfg.write_text(json.dumps({**conf, "vozes": "recusou"}), encoding="utf-8")
                return "recusada"
        instalar(m, release, pasta, dizer)
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps({**conf, "vozes": "aceitou"}), encoding="utf-8")
        return "instalada"
    except Exception as exc:
        dizer(f"Dublagem: não consegui baixar agora ({str(exc)[:120]}). Tentarei de novo na próxima abertura.", 0)
        return "erro"
