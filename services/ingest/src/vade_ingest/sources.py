"""Fontes de leitura do acervo.

``GitSource`` lê direto do object store do git, sem checkout. Motivos (medidos):

* o acervo tem ~1,06 milhão de arquivos e mais de 2,5 GB; checkout completo é lento;
* há nomes de arquivo com ``"`` que o Windows não aceita, o que faz o checkout abortar;
* com ``--filter=blob:none`` os blobs são buscados em lote pelo OID (~2 mil arquivos em 3 s);
* o OID do blob é um hash do conteúdo: serve de chave de mudança para importação incremental.

``FsSource`` lê um diretório já extraído (útil em testes e em servidores Linux).
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    path: str  # caminho relativo com "/", ex.: "federal/leis-ordinarias/2018/lei-13709-2018-08-14.md"
    oid: str  # hash do conteúdo (blob OID no git, sha1 do arquivo no FsSource)


def is_norm_path(path: str) -> bool:
    """Só normas: ``.md`` fora de pastas/arquivos internos (prefixo ``_``) e fora da raiz,
    exceto ``constituicao.md``."""
    if not path.endswith(".md"):
        return False
    parts = path.split("/")
    if len(parts) == 1:
        return path == "constituicao.md"
    if parts[0] in ("scripts", "fonte", ".githooks"):
        return False
    return not any(p.startswith("_") for p in parts)


class GitSource:
    def __init__(self, repo: str | os.PathLike, rev: str = "HEAD") -> None:
        self.repo = str(repo)
        self.rev = rev

    def _git(self, *args: str, input: bytes | None = None) -> bytes:
        return subprocess.run(
            ["git", "-C", self.repo, "-c", "core.longpaths=true", *args],
            input=input, check=True, capture_output=True,
        ).stdout

    def commit(self) -> str:
        return self._git("rev-parse", self.rev).decode().strip()

    # ---------------------------------------------------------------- remoto
    # Medido no acervo real: ls-remote ~0,5 s (não baixa nada); fetch de 3 commits com ~5 mil
    # arquivos alterados ~1 s (num clone --filter=blob:none vêm só commits e árvores).

    @classmethod
    def tracking(cls, repo: str | os.PathLike, remote: str = "origin") -> "GitSource":
        """Fonte apontando para o ramo remoto rastreado (ex.: ``origin/main``), que é o que o
        ``fetch`` atualiza. Usar ``HEAD`` num clone ``--no-checkout`` congelaria a importação."""
        probe = cls(repo)
        try:
            ref = probe._git("symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD").decode().strip()
        except subprocess.CalledProcessError:
            branch = probe._git("rev-parse", "--abbrev-ref", "HEAD").decode().strip()
            ref = f"{remote}/{branch}"
        return cls(repo, ref)

    def remote_head(self) -> str:
        """Último commit do remoto, sem baixar nada."""
        remote, _, branch = self.rev.partition("/")
        out = self._git("ls-remote", remote, f"refs/heads/{branch or 'main'}").decode().split()
        if not out:
            raise RuntimeError(f"ramo {self.rev} não encontrado no remoto")
        return out[0]

    def fetch(self) -> None:
        """Traz commits e árvores novos (sem conteúdo de arquivos num clone parcial)."""
        remote, _, branch = self.rev.partition("/")
        self._git("fetch", "--no-tags", remote, branch or "main")

    def count_commits(self, since: str) -> int:
        return int(self._git("rev-list", "--count", f"{since}..{self.rev}").decode().strip())

    def commit_info(self, rev: str | None = None) -> dict[str, str]:
        out = self._git("log", "-1", "--format=%H%x00%cI%x00%s", rev or self.rev).decode("utf-8").strip()
        sha, date, subject = out.split("\x00", 2)
        return {"sha": sha, "data": date, "mensagem": subject}

    def recent_commits(self, since: str, limit: int = 20) -> list[dict[str, str]]:
        out = self._git("log", f"--max-count={limit}", "--format=%H%x00%cI%x00%s", f"{since}..{self.rev}").decode("utf-8")
        rows = []
        for line in out.splitlines():
            sha, date, subject = line.split("\x00", 2)
            rows.append({"sha": sha, "data": date, "mensagem": subject})
        return rows

    def list(self, prefixes: Iterable[str] = ()) -> list[Entry]:
        out = self._git("ls-tree", "-r", "-z", self.rev, "--", *prefixes)
        entries = []
        for rec in out.split(b"\0"):
            if not rec:
                continue
            meta, path = rec.split(b"\t", 1)
            _mode, kind, oid = meta.decode().split()
            p = path.decode("utf-8")
            if kind == "blob" and is_norm_path(p):
                entries.append(Entry(p, oid))
        return entries

    def children(self, prefix: str = "", limit: int = 400) -> list[dict[str, str]]:
        """Conteúdo imediato de uma pasta do acervo (para escolher o recorte). Lê só a árvore."""
        spec = f"{prefix.strip('/')}/" if prefix.strip("/") else "."
        out = self._git("ls-tree", "-z", self.rev, "--", spec)
        items = []
        for rec in out.split(b"\0"):
            if not rec:
                continue
            meta, path = rec.split(b"\t", 1)
            kind = meta.decode().split()[1]
            p = path.decode("utf-8")
            name = p.rsplit("/", 1)[-1]
            if name.startswith((".", "_")) or name == "scripts" or name == "fonte":
                continue
            if kind == "tree":
                items.append({"caminho": p, "tipo": "pasta"})
            elif is_norm_path(p):
                items.append({"caminho": p, "tipo": "arquivo"})
            if len(items) >= limit:
                break
        return items

    def changes(self, since: str) -> tuple[list[Entry], list[str]]:
        """(adicionados/modificados, removidos) entre ``since`` e ``self.rev``."""
        # --no-abbrev: hash abreviado não resolve blob ainda não baixado num clone parcial
        out = self._git("diff", "--no-renames", "--no-abbrev", "--raw", "-z", since, self.rev)
        upserts, deletes = [], []
        fields = out.split(b"\0")
        i = 0
        while i + 1 < len(fields):
            meta, path = fields[i].decode(), fields[i + 1].decode("utf-8")
            i += 2
            if not meta.startswith(":"):
                continue
            _m1, _m2, _o1, new_oid, status = meta[1:].split()
            if not is_norm_path(path):
                continue
            if status.startswith("D"):
                deletes.append(path)
            else:
                upserts.append(Entry(path, new_oid))
        return upserts, deletes

    def prefetch(self, entries: list[Entry], chunk: int = 5000) -> None:
        """Busca em lote os blobs ausentes num clone parcial (no-op em clone completo)."""
        for k in range(0, len(entries), chunk):
            oids = "\n".join(e.oid for e in entries[k : k + chunk]).encode()
            subprocess.run(
                ["git", "-C", self.repo, "-c", "fetch.negotiationAlgorithm=noop", "fetch", "origin",
                 "--no-tags", "--no-write-fetch-head", "--recurse-submodules=no",
                 "--filter=blob:none", "--stdin"],
                input=oids, capture_output=True, check=False,
            )

    def read(self, entries: list[Entry]) -> Iterator[tuple[Entry, str | None]]:
        """Lê o conteúdo via ``git cat-file --batch`` (um processo para o lote inteiro).

        Blob ausente devolve ``None``: quem chama registra a falha (nunca pular em silêncio,
        senão o commit avança e a atualização daquele arquivo se perde)."""
        proc = subprocess.Popen(
            ["git", "-C", self.repo, "cat-file", "--batch"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        )
        assert proc.stdin and proc.stdout
        try:
            for e in entries:
                proc.stdin.write(e.oid.encode() + b"\n")
                proc.stdin.flush()
                header = proc.stdout.readline().split()
                if len(header) < 3 or header[1] == b"missing":
                    yield e, None
                    continue
                size = int(header[2])
                data = proc.stdout.read(size)
                proc.stdout.read(1)  # "\n" final
                yield e, data.decode("utf-8", errors="replace")
        finally:
            proc.stdin.close()
            proc.stdout.close()
            proc.wait()


class FsSource:
    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root)

    def list(self, prefixes: Iterable[str] = ()) -> list[Entry]:
        import hashlib

        bases = [self.root / p for p in prefixes] or [self.root]
        out = []
        for base in bases:
            files = [base] if base.is_file() else base.rglob("*.md")
            for f in files:
                rel = f.relative_to(self.root).as_posix()
                if is_norm_path(rel):
                    out.append(Entry(rel, hashlib.sha1(f.read_bytes()).hexdigest()))
        return sorted(out, key=lambda e: e.path)

    def prefetch(self, entries: list[Entry]) -> None:  # interface comum
        return None

    def read(self, entries: list[Entry]) -> Iterator[tuple[Entry, str]]:
        for e in entries:
            yield e, (self.root / e.path).read_text(encoding="utf-8", errors="replace")
