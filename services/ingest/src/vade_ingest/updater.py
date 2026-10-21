"""Verificação e aplicação de atualizações do acervo (o botão "Verificar atualização").

O acervo ``ctresb/leis`` recebe commits a cada poucos minutos, com milhares de arquivos cada.
Em vez de perseguir cada commit, separamos duas operações de custo muito diferente:

* **verificar** (``check``): ``git ls-remote`` (~0,5 s, não baixa nada). Se houver novidade,
  ``git fetch`` só de commits e árvores (~1 s para ~5 mil arquivos alterados num clone parcial) e
  calcula o diff: quantos commits, quantos arquivos, **quantos caem no seu recorte**;
* **atualizar** (``start_update``): baixa só o conteúdo dos arquivos do recorte que mudaram e
  aplica o diff no catálogo. N commits pendentes viram um único diff, e não importa quantos
  aconteceram desde a última vez.

Só uma atualização roda por vez (trava no processo). O SQLite em WAL deixa a busca funcionando
enquanto a atualização grava.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .loader import Catalog, in_scope
from .sources import GitSource


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


@dataclass
class CheckResult:
    verificado_em: str
    commit_local: str | None
    commit_remoto: str
    atualizado: bool
    commits_novos: int = 0
    arquivos_alterados: int = 0
    no_recorte: int = 0
    por_area: list[tuple[str, int]] = field(default_factory=list)
    commits: list[dict[str, str]] = field(default_factory=list)
    primeira_importacao: bool = False
    recorte_adicionar: list[str] = field(default_factory=list)  # pastas novas ainda não importadas
    recorte_remover: list[str] = field(default_factory=list)


@dataclass
class Job:
    estado: str = "parado"  # parado | rodando | concluido | erro
    etapa: str = ""
    feito: int = 0
    total: int = 0
    iniciado_em: str | None = None
    concluido_em: str | None = None
    resultado: dict | None = None
    erro: str | None = None


class Updater:
    def __init__(self, repo: str | Path, db: str | Path) -> None:
        self.repo = str(repo)
        self.db = str(db)
        self._lock = threading.Lock()
        self._job = Job()
        self._job_lock = threading.Lock()
        self.last_check: CheckResult | None = None

    # ------------------------------------------------------------ util
    def _catalog(self) -> Catalog:
        return Catalog(self.db)  # uma conexão por operação/thread

    def _source(self) -> GitSource:
        return GitSource.tracking(self.repo)

    def recorte(self) -> list[str]:
        cat = self._catalog()
        try:
            raw = cat.get("recorte")
        finally:
            cat.close()
        return json.loads(raw) if raw else []

    def set_recorte(self, prefixes: list[str]) -> None:
        """Salva o recorte. Pastas adicionadas depois da 1ª importação não aparecem no diff
        (não mudaram no GitHub), então ficam como pendência para a próxima atualização; o mesmo
        para as removidas, cujas normas saem do catálogo."""
        new = sorted(set(p.strip().strip("/") for p in prefixes if p.strip()))
        cat = self._catalog()
        try:
            old = json.loads(cat.get("recorte") or "[]")
            if cat.get("ultimo_commit"):
                prev_add, prev_rem = self._pending(cat)
                # adicionar: o que entrou e continua no recorte; remover: o que saiu e não voltou
                add = (set(prev_add) | (set(new) - set(old))) & set(new)
                rem = (set(prev_rem) | (set(old) - set(new))) - set(new)
                cat.set("recorte_adicionar", json.dumps(sorted(add)))
                cat.set("recorte_remover", json.dumps(sorted(rem)))
            cat.set("recorte", json.dumps(new))
            cat.db.commit()
        finally:
            cat.close()

    def _pending(self, cat: Catalog) -> tuple[list[str], list[str]]:
        return json.loads(cat.get("recorte_adicionar") or "[]"), json.loads(cat.get("recorte_remover") or "[]")

    # ------------------------------------------------------------ status
    def status(self) -> dict:
        cat = self._catalog()
        try:
            local = cat.get("ultimo_commit")
            counts = cat.counts()
            history = cat.history(10)
            raw = cat.get("recorte")
        finally:
            cat.close()
        info = None
        if local:
            try:
                info = self._source().commit_info(local)
            except Exception:  # commit fora do clone (ex.: clone refeito)
                info = {"sha": local, "data": "", "mensagem": ""}
        with self._job_lock:
            job = asdict(self._job)
        return {
            "commit_local": info,
            "contagens": counts,
            "recorte": json.loads(raw) if raw else [],
            "ultima_verificacao": asdict(self.last_check) if self.last_check else None,
            "job": job,
            "historico": history,
        }

    # ------------------------------------------------------------ verificar
    def check(self) -> CheckResult:
        src = self._source()
        cat = self._catalog()
        try:
            local = cat.get("ultimo_commit")
            raw = cat.get("recorte")
            add, rem = self._pending(cat)
        finally:
            cat.close()
        prefixes = json.loads(raw) if raw else []
        remote = src.remote_head()

        if local == remote:
            result = CheckResult(_now(), local, remote, atualizado=not (add or rem))
        else:
            if src.commit() != remote:
                src.fetch()
            if local is None:
                result = CheckResult(_now(), None, remote, atualizado=False, primeira_importacao=True,
                                     no_recorte=len(src.list(prefixes)) if prefixes else 0,
                                     commits=[src.commit_info()])
            else:
                upserts, deletes = src.changes(local)
                paths = [e.path for e in upserts] + deletes
                areas = Counter("/".join(p.split("/")[:2]) for p in paths)
                result = CheckResult(
                    _now(), local, remote, atualizado=False,
                    commits_novos=src.count_commits(local),
                    arquivos_alterados=len(paths),
                    no_recorte=sum(1 for p in paths if in_scope(p, prefixes)),
                    por_area=areas.most_common(8),
                    commits=src.recent_commits(local, 10),
                )
        if add or rem:
            result.recorte_adicionar, result.recorte_remover = add, rem
            if add:  # conta só o que ainda não está no catálogo com o mesmo conteúdo
                cat = self._catalog()
                try:
                    known = cat.hashes()
                finally:
                    cat.close()
                missing = sum(1 for e in src.list(add) if known.get(e.path[:-3]) != e.oid)
                result.no_recorte += missing
                if local == remote and not missing and not rem:
                    result.atualizado = True
        self.last_check = result
        return result

    # ------------------------------------------------------------ atualizar
    def job(self) -> dict:
        with self._job_lock:
            return asdict(self._job)

    def _guard_scope(self, allow_all: bool) -> None:
        if not self.recorte() and not allow_all:
            raise ValueError("recorte vazio: isso importaria o acervo inteiro (~1 milhão de arquivos). "
                             "Defina um recorte ou confirme com allow_all.")

    def start_update(self, full: bool = False, allow_all: bool = False) -> bool:
        """Dispara a atualização em segundo plano. False se já houver uma rodando."""
        self._guard_scope(allow_all)
        if not self._lock.acquire(blocking=False):
            return False
        with self._job_lock:
            self._job = Job(estado="rodando", etapa="buscando commits", iniciado_em=_now())
        threading.Thread(target=self._run_update, args=(full,), daemon=True).start()
        return True

    def run_update_blocking(self, full: bool = False, allow_all: bool = False) -> dict:
        self._guard_scope(allow_all)
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("já existe uma atualização em andamento")
        with self._job_lock:
            self._job = Job(estado="rodando", etapa="buscando commits", iniciado_em=_now())
        self._run_update(full)
        return self.job()

    def _progress(self, etapa: str, feito: int, total: int) -> None:
        with self._job_lock:
            self._job.etapa, self._job.feito, self._job.total = etapa, feito, total

    def _run_update(self, full: bool) -> None:
        try:
            src = self._source()
            src.fetch()
            cat = self._catalog()
            try:
                raw = cat.get("recorte")
                prefixes = json.loads(raw) if raw else []
                add, rem = self._pending(cat)
                report = cat.sync(src, prefixes, full=full, on_progress=self._progress,
                                  add_prefixes=add, remove_prefixes=rem)
                cat.set("recorte_adicionar", "[]")
                cat.set("recorte_remover", "[]")
                cat.db.commit()
            finally:
                cat.close()
            result = {k: v for k, v in asdict(report).items() if k not in ("failures",)}
            result["falhas_exemplos"] = report.failures[:10]
            with self._job_lock:
                self._job.estado, self._job.etapa = "concluido", "pronto"
                self._job.resultado, self._job.concluido_em = result, _now()
            if self.last_check:
                self.last_check = CheckResult(_now(), report.commit, report.commit or "", atualizado=True)
        except Exception as exc:
            with self._job_lock:
                self._job.estado, self._job.erro, self._job.concluido_em = "erro", repr(exc), _now()
        finally:
            self._lock.release()
