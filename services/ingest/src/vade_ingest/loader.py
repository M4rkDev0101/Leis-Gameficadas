"""Carga no catálogo SQLite e importação completa/incremental."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from . import document
from .sources import Entry, GitSource


@dataclass
class ImportReport:
    commit: str | None = None
    seen: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    failed: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)
    changed: list[dict[str, str]] = field(default_factory=list)  # [{id, titulo, acao}] (até 200)

    def note(self, norma_id: str, titulo: str, acao: str) -> None:
        if len(self.changed) < 200:
            self.changed.append({"id": norma_id, "titulo": titulo, "acao": acao})


SCHEMA_VERSION = 2
# Suba ao mudar o resultado do parser (structure/precedent/quality/classify): força reprocessamento.
PARSER_VERSION = "2026.10.21-2"


def in_scope(path: str, prefixes: list[str]) -> bool:
    """O arquivo está no recorte? Sem recorte, tudo está."""
    return not prefixes or any(path == p or path.startswith(p.rstrip("/") + "/") for p in prefixes)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class Catalog:
    def __init__(self, db_path: str | Path) -> None:
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.execute("PRAGMA synchronous = NORMAL")
        self.db.execute("PRAGMA busy_timeout = 5000")  # leitura (busca) e escrita (atualização) ao mesmo tempo
        rebuild_fts = self._migrate()
        self.db.executescript(resources.files(__package__).joinpath("schema.sql").read_text("utf-8"))
        if rebuild_fts:
            # índice recriado vazio sobre linhas existentes: precisa ser reconstruído, senão o
            # primeiro DELETE em cascata corrompe o FTS ("database disk image is malformed")
            self.db.execute("INSERT INTO dispositivo_fts(dispositivo_fts) VALUES ('rebuild')")
        self.db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self._check_parser_version()
        self.db.commit()

    def _check_parser_version(self) -> None:
        """Parser melhorou → o mesmo arquivo do acervo gera dispositivos diferentes. Sem isso, só os
        arquivos que mudaram no GitHub seriam reprocessados e o resto ficaria com o parse antigo."""
        stored = self.get("versao_parser")
        if stored == PARSER_VERSION:
            return
        if stored is not None or self.db.execute("SELECT 1 FROM norma LIMIT 1").fetchone():
            self.db.execute("UPDATE norma SET content_hash = ''")
            self.db.execute("DELETE FROM kv WHERE chave = 'ultimo_commit'")  # próxima sync lista o recorte
        self.set("versao_parser", PARSER_VERSION)

    def _migrate(self) -> bool:
        """Migrações de catálogos criados por versões anteriores (``PRAGMA user_version``).
        Devolve True se o índice de busca precisa ser reconstruído."""
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE name = 'dispositivo'").fetchone()
        if not exists or version >= SCHEMA_VERSION:
            return False
        if version < 2:
            # v2: coluna "contexto" na busca. Recria o índice e força reimportação do recorte.
            cols = {r[1] for r in self.db.execute("PRAGMA table_info(dispositivo)")}
            if "contexto" not in cols:
                self.db.execute("ALTER TABLE dispositivo ADD COLUMN contexto TEXT NOT NULL DEFAULT ''")
            self.db.executescript(
                "DROP TRIGGER IF EXISTS dispositivo_ai; DROP TRIGGER IF EXISTS dispositivo_ad;"
                "DROP TABLE IF EXISTS dispositivo_fts;"
            )
            self.db.execute("UPDATE norma SET content_hash = ''")
            # sem último commit, a próxima atualização lista o recorte inteiro (e não só o diff)
            if self.db.execute("SELECT 1 FROM sqlite_master WHERE name = 'kv'").fetchone():
                self.db.execute("DELETE FROM kv WHERE chave IN ('ultimo_commit', 'recorte_adicionar', 'recorte_remover')")
        self.db.commit()
        return True

    def close(self) -> None:
        self.db.close()

    # ------------------------------------------------------------ estado
    def get(self, key: str) -> str | None:
        row = self.db.execute("SELECT valor FROM kv WHERE chave = ?", (key,)).fetchone()
        return row[0] if row else None

    def set(self, key: str, value: str) -> None:
        self.db.execute("INSERT INTO kv VALUES (?, ?) ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor", (key, value))

    def hashes(self) -> dict[str, str]:
        return dict(self.db.execute("SELECT id, content_hash FROM norma"))

    # ------------------------------------------------------------ escrita
    def delete(self, norma_id: str) -> bool:
        return self.db.execute("DELETE FROM norma WHERE id = ?", (norma_id,)).rowcount > 0

    def upsert(self, doc: document.NormDocument) -> None:
        self.delete(doc.id)  # cascata remove dispositivos, notas e entradas de busca
        c = doc.classification
        self.db.execute(
            """INSERT INTO norma (id, content_hash, esfera, tipo, titulo, numero, data, ano, ementa, uf,
                 municipio, orgao, tribunal, situacao, revogada, versao_texto, urn, fonte, nome_popular,
                 sigla, areas, relevancia, qualidade, faixa_qualidade, n_artigos, meta, importado_em)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (doc.id, doc.content_hash, doc.esfera, doc.tipo, doc.titulo, doc.numero,
             doc.data.isoformat() if doc.data else None, doc.ano, doc.ementa, doc.uf, doc.municipio,
             doc.orgao, doc.tribunal, doc.situacao, None if doc.revogada is None else int(doc.revogada),
             doc.versao_texto, doc.urn, doc.fonte, c.nome_popular, c.sigla,
             json.dumps(c.areas, ensure_ascii=False), c.relevancia, doc.quality.score, doc.quality.tier,
             len(doc.body.articles()), json.dumps(doc.meta, ensure_ascii=False, default=str), _now()),
        )
        ordem = 0
        notes: list[tuple] = []

        base_ctx = " ".join(x for x in (c.sigla, c.nome_popular) if x)

        def insert(unit, parent_id, rubrica_artigo):
            nonlocal ordem
            for child in unit.children:
                ordem += 1
                rub = child.rubrica if child.kind == "artigo" else rubrica_artigo
                # parágrafos e incisos herdam a rubrica do artigo: "roubo arma de fogo" acha o §2º-A, I
                contexto = " ".join(x for x in (base_ctx, rub if child.kind != "artigo" else None) if x)
                cur = self.db.execute(
                    """INSERT INTO dispositivo (norma_id, chave, caminho, pai_id, tipo, tipo_divisao, rotulo,
                         rubrica, texto, contexto, revogado, vetado, ordem, linha)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (doc.id, f"{doc.id}#{child.path}", child.path, parent_id, child.kind, child.div_type,
                     child.label, child.rubrica, child.text, contexto, int(child.revoked), int(child.vetoed),
                     ordem, child.line),
                )
                notes.extend((cur.lastrowid, n.kind, n.text, n.ref) for n in child.notes)
                insert(child, cur.lastrowid, rub)

        insert(doc.body.root, None, None)
        self.db.executemany("INSERT INTO nota_alteracao VALUES (?,?,?,?)", notes)
        if doc.precedent:
            self.db.executemany(
                "INSERT INTO referencia_legal VALUES (?,?,?,?,?,NULL)",
                [(doc.id, r.tipo, r.numero, r.ano, r.caminho) for r in doc.precedent.referencias],
            )

    def resolve_references(self) -> int:
        """Liga referências à norma-alvo do catálogo (federal por tipo+número+ano; CF pelo caminho)."""
        cur = self.db.execute(
            """UPDATE referencia_legal SET alvo_norma_id = CASE
                 WHEN alvo_tipo = 'Constituição' AND alvo_ano = 1988 THEN 'constituicao'
                 ELSE (SELECT n.id FROM norma n
                        WHERE n.esfera = 'federal' AND n.tipo = referencia_legal.alvo_tipo
                          AND n.numero = referencia_legal.alvo_numero AND n.ano = referencia_legal.alvo_ano
                        LIMIT 1)
               END
               WHERE alvo_norma_id IS NULL"""
        )
        return cur.rowcount

    # ------------------------------------------------------------ importação
    def import_entries(self, source, entries: list[Entry], report: ImportReport, batch: int = 500,
                       on_progress=None) -> None:
        known = self.hashes()
        todo = [e for e in entries if known.get(e.path[:-3]) != e.oid]
        report.seen += len(entries)
        report.unchanged += len(entries) - len(todo)
        if on_progress:
            on_progress("baixando", 0, len(todo))
        source.prefetch(todo)
        n = 0
        for entry, text in source.read(todo):
            try:
                if text is None:
                    raise LookupError(f"conteúdo do blob {entry.oid} indisponível (rede ou clone parcial)")
                doc = document.build(entry.path, text, entry.oid)
                existed = doc.id in known
                self.upsert(doc)
                self.db.execute("DELETE FROM falha_importacao WHERE caminho = ?", (entry.path,))
                if existed:
                    report.updated += 1
                    report.note(doc.id, doc.titulo, "alterada")
                else:
                    report.inserted += 1
                    report.note(doc.id, doc.titulo, "nova")
            except Exception as exc:  # uma norma ruim não derruba o lote
                report.failed += 1
                report.failures.append((entry.path, repr(exc)))
                self.db.execute(
                    "INSERT OR REPLACE INTO falha_importacao VALUES (?,?,?)", (entry.path, repr(exc)[:2000], _now())
                )
            n += 1
            if n % batch == 0:
                self.db.commit()
            if on_progress and (n % 25 == 0 or n == len(todo)):
                on_progress("importando", n, len(todo))
        self.db.commit()

    def _delete_noting(self, norma_id: str, report: ImportReport) -> None:
        row = self.db.execute("SELECT titulo FROM norma WHERE id = ?", (norma_id,)).fetchone()
        if row and self.delete(norma_id):
            report.deleted += 1
            report.note(norma_id, row[0], "removida")

    def sync(self, source, prefixes: list[str] | None = None, full: bool = False, on_progress=None,
             add_prefixes: list[str] | None = None, remove_prefixes: list[str] | None = None) -> ImportReport:
        """Importa tudo na primeira vez; depois, só o diff desde o último commit importado.

        Com ``prefixes`` (subconjunto do acervo), o diff é filtrado pelos mesmos prefixos.
        ``add_prefixes``/``remove_prefixes``: mudanças de recorte desde a última execução (pastas
        recém-adicionadas não aparecem no diff, porque não mudaram no remoto).
        Cada execução fica registrada em ``historico_sync``.
        """
        report = ImportReport()
        prefixes = prefixes or []
        last = self.get("ultimo_commit")
        started = _now()
        if isinstance(source, GitSource):
            report.commit = source.commit()
        if isinstance(source, GitSource) and last and not full:
            if on_progress:
                on_progress("comparando", 0, 0)
            upserts, deletes = source.changes(last)
            upserts = [e for e in upserts if in_scope(e.path, prefixes)]
            # falhas anteriores não aparecem mais no diff: tenta de novo no commit atual
            retry = {p for (p,) in self.db.execute("SELECT caminho FROM falha_importacao")} - {e.path for e in upserts}
            if retry:
                current = {e.path: e for e in source.list(sorted(retry))}
                upserts += [current[p] for p in retry if p in current and in_scope(p, prefixes)]
                for p in retry - current.keys():  # sumiu do acervo
                    self.db.execute("DELETE FROM falha_importacao WHERE caminho = ?", (p,))
            for p in deletes:
                if in_scope(p, prefixes):
                    self._delete_noting(p[:-3], report)
            self.import_entries(source, upserts, report, on_progress=on_progress)
        else:
            if on_progress:
                on_progress("listando", 0, 0)
            entries = source.list(prefixes)
            self.import_entries(source, entries, report, on_progress=on_progress)
            if full or not last:
                # remove normas que sumiram do acervo (dentro do recorte importado)
                present = {e.path[:-3] for e in entries}
                for norma_id in list(self.hashes()):
                    if in_scope(norma_id + ".md", prefixes) and norma_id not in present:
                        self._delete_noting(norma_id, report)
        if remove_prefixes:
            for norma_id in [i for i in self.hashes() if in_scope(i + ".md", remove_prefixes)]:
                self._delete_noting(norma_id, report)
        if add_prefixes and last and not full:  # em importação completa já entraram pelo list()
            self.import_entries(source, source.list(add_prefixes), report, on_progress=on_progress)
        self.resolve_references()
        if report.commit:
            self.set("ultimo_commit", report.commit)
        self.db.execute(
            """INSERT INTO historico_sync (de_commit, para_commit, iniciado_em, concluido_em, inseridas,
                 atualizadas, removidas, falhas, mudancas) VALUES (?,?,?,?,?,?,?,?,?)""",
            (last, report.commit, started, _now(), report.inserted, report.updated, report.deleted,
             report.failed, json.dumps(report.changed, ensure_ascii=False)),
        )
        self.db.commit()
        return report

    def history(self, limit: int = 20) -> list[dict]:
        rows = self.db.execute("SELECT * FROM historico_sync ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{**dict(r), "mudancas": json.loads(r["mudancas"])} for r in rows]

    def counts(self) -> dict[str, int]:
        return {
            "normas": self.db.execute("SELECT count(*) FROM norma").fetchone()[0],
            "dispositivos": self.db.execute("SELECT count(*) FROM dispositivo").fetchone()[0],
            "falhas": self.db.execute("SELECT count(*) FROM falha_importacao").fetchone()[0],
        }

    # ------------------------------------------------------------ leitura integral
    def norma_leitura(self, norma_id: str, inicio: int = 0, limite: int = 400, alvo: str | None = None) -> dict | None:
        """Norma para leitura: metadados, índice de divisões (com a posição de cada uma na ordem de leitura)
        e uma janela de dispositivos [inicio, fim). Com ``alvo`` (caminho), a janela é posicionada para
        conter esse dispositivo. Normas grandes (Código Civil) são lidas por janelas, não de uma vez."""
        n = self.db.execute(
            "SELECT id, titulo, tipo, numero, data, ementa, sigla, nome_popular, situacao, revogada, fonte, n_artigos "
            "FROM norma WHERE id = ?", (norma_id,)).fetchone()
        if n is None:
            return None
        limite = max(1, min(int(limite), 2000))
        total = self.db.execute("SELECT count(*) FROM dispositivo WHERE norma_id = ?", (norma_id,)).fetchone()[0]
        indice = [dict(r) for r in self.db.execute(
            """SELECT caminho, rotulo, texto AS titulo, tipo_divisao, pos FROM (
                 SELECT caminho, rotulo, texto, tipo, tipo_divisao, row_number() OVER (ORDER BY ordem) - 1 AS pos
                   FROM dispositivo WHERE norma_id = ?) WHERE tipo = 'divisao' ORDER BY pos""", (norma_id,))]
        alvo_pos = None
        if alvo:
            row = self.db.execute(
                "SELECT count(*) FROM dispositivo WHERE norma_id = ? AND ordem < "
                "(SELECT ordem FROM dispositivo WHERE norma_id = ? AND caminho = ?)", (norma_id, norma_id, alvo)).fetchone()
            if self.db.execute("SELECT 1 FROM dispositivo WHERE norma_id = ? AND caminho = ?", (norma_id, alvo)).fetchone():
                alvo_pos = row[0]
                inicio = max(0, alvo_pos - limite // 4)
        inicio = max(0, min(int(inicio), max(0, total - 1)))
        disp = [dict(r) for r in self.db.execute(
            """SELECT caminho, tipo, tipo_divisao, rotulo, rubrica, texto, revogado, vetado, ordem
                 FROM dispositivo WHERE norma_id = ? ORDER BY ordem LIMIT ? OFFSET ?""", (norma_id, limite, inicio))]
        fim = inicio + len(disp)
        return {
            "norma": dict(n), "total": total, "indice": indice, "dispositivos": disp,
            "inicio": inicio, "fim": fim, "alvo_pos": alvo_pos,
            "proximo": fim if fim < total else None,
            "anterior": max(0, inicio - limite) if inicio > 0 else None,
        }

    # ------------------------------------------------------------ consulta
    def search(self, query: str, limit: int = 10) -> list[sqlite3.Row]:
        """Busca em dispositivos, ordenada por BM25 e priorizando normas relevantes."""
        return self.db.execute(
            """SELECT n.id AS norma_id, COALESCE(n.sigla, n.titulo) AS norma, d.caminho, d.rotulo,
                      d.rubrica, snippet(dispositivo_fts, 2, '[', ']', '…', 18) AS trecho
                 FROM dispositivo_fts f
                 JOIN dispositivo d ON d.id = f.rowid
                 JOIN norma n ON n.id = d.norma_id
                WHERE dispositivo_fts MATCH ? AND d.revogado = 0
                ORDER BY bm25(dispositivo_fts, 2.0, 4.0, 1.0, 1.5)
                         + CASE n.relevancia WHEN 'alta' THEN -5 WHEN 'baixa' THEN 5 ELSE 0 END
                LIMIT ?""",
            (query, limit),
        ).fetchall()
