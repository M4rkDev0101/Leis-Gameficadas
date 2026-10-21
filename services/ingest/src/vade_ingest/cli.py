"""Linha de comando do importador.

    python -m vade_ingest serve     --repo ACERVO --db catalogo.sqlite [--verificar-a-cada 30] [--atualizar-auto]
    python -m vade_ingest recorte   --repo ACERVO --db catalogo.sqlite constituicao.md federal/decretos-lei
    python -m vade_ingest verificar --repo ACERVO --db catalogo.sqlite
    python -m vade_ingest atualizar --repo ACERVO --db catalogo.sqlite [--completo]
    python -m vade_ingest sync   --repo CAMINHO_DO_CLONE --db catalogo.sqlite [--prefix federal/leis-complementares] [--full]
    python -m vade_ingest parse  ARQUIVO.md [--path federal/...] [--json]
    python -m vade_ingest search --db catalogo.sqlite "legítima defesa"
    python -m vade_ingest stats  --db catalogo.sqlite
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import document
from .loader import Catalog
from .sources import FsSource, GitSource


def _unit_json(u) -> dict:
    d = {"tipo": u.kind, "caminho": u.path, "rotulo": u.label, "texto": u.text}
    if u.rubrica:
        d["rubrica"] = u.rubrica
    if u.revoked:
        d["revogado"] = True
    if u.vetoed:
        d["vetado"] = True
    if u.notes:
        d["notas"] = [{"tipo": n.kind, "ref": n.ref, "texto": n.text} for n in u.notes]
    if u.children:
        d["filhos"] = [_unit_json(c) for c in u.children]
    return d


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="vade_ingest")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sync", help="importa (completo ou incremental) para o catálogo")
    s.add_argument("--repo", required=True)
    s.add_argument("--db", required=True)
    s.add_argument("--prefix", action="append", default=[])
    s.add_argument("--full", action="store_true", help="ignora o último commit e reconcilia tudo")
    s.add_argument("--fs", action="store_true", help="lê arquivos do disco em vez do object store do git")

    p = sub.add_parser("parse", help="mostra a estrutura extraída de um arquivo")
    p.add_argument("file")
    p.add_argument("--path", help="caminho no acervo (define esfera e classificação)")
    p.add_argument("--json", action="store_true")

    q = sub.add_parser("search")
    q.add_argument("--db", required=True)
    q.add_argument("query")
    q.add_argument("--limit", type=int, default=10)

    st = sub.add_parser("stats")
    st.add_argument("--db", required=True)

    sv = sub.add_parser("serve", help="painel local com o botão Verificar atualização")
    sv.add_argument("--repo", required=True)
    sv.add_argument("--db", required=True)
    sv.add_argument("--porta", type=int, default=8765)
    sv.add_argument("--verificar-a-cada", type=float, default=0, metavar="MIN",
                    help="verifica sozinho a cada N minutos (0 = só pelo botão)")
    sv.add_argument("--atualizar-auto", action="store_true", help="aplica sozinho quando houver mudança no recorte")

    vc = sub.add_parser("verificar", help="mostra se há atualização no GitHub (não baixa conteúdo)")
    vc.add_argument("--repo", required=True)
    vc.add_argument("--db", required=True)

    up = sub.add_parser("atualizar", help="aplica as atualizações pendentes do recorte")
    up.add_argument("--repo", required=True)
    up.add_argument("--db", required=True)
    up.add_argument("--completo", action="store_true")
    up.add_argument("--tudo", action="store_true", help="permite importar o acervo inteiro se o recorte estiver vazio")

    rc = sub.add_parser("recorte", help="define as pastas/arquivos importados")
    rc.add_argument("--repo", required=True)
    rc.add_argument("--db", required=True)
    rc.add_argument("prefixos", nargs="*")

    a = ap.parse_args(argv)

    if a.cmd in ("serve", "verificar", "atualizar", "recorte"):
        from dataclasses import asdict

        from .updater import Updater

        upd = Updater(a.repo, a.db)
        if a.cmd == "recorte":
            if a.prefixos:
                upd.set_recorte(a.prefixos)
            print(json.dumps(upd.recorte(), ensure_ascii=False, indent=2))
            return 0
        if a.cmd == "verificar":
            print(json.dumps(asdict(upd.check()), ensure_ascii=False, indent=2))
            return 0
        if a.cmd == "atualizar":
            job = upd.run_update_blocking(full=a.completo, allow_all=a.tudo)
            print(json.dumps(job, ensure_ascii=False, indent=2, default=str))
            return 0 if job["estado"] == "concluido" else 1
        from .server import make_server, start_auto_check

        if a.verificar_a_cada > 0:
            start_auto_check(upd, a.verificar_a_cada, a.atualizar_auto)
        srv = make_server(upd, a.porta)
        print(f"Painel em http://127.0.0.1:{a.porta}  (Ctrl+C para sair)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0

    if a.cmd == "sync":
        cat = Catalog(a.db)
        source = FsSource(a.repo) if a.fs else GitSource(a.repo)
        r = cat.sync(source, a.prefix, full=a.full)
        print(json.dumps({k: v for k, v in r.__dict__.items() if k != "failures"}, ensure_ascii=False))
        for path, err in r.failures[:20]:
            print(f"FALHA {path}: {err}", file=sys.stderr)
        return 1 if r.failed and not (r.inserted or r.updated) else 0

    if a.cmd == "parse":
        f = Path(a.file)
        doc = document.build(a.path or f.name, f.read_text(encoding="utf-8"))
        if a.json:
            out = {
                "id": doc.id, "titulo": doc.titulo, "tipo": doc.tipo, "esfera": doc.esfera,
                "qualidade": doc.quality.__dict__, "classificacao": doc.classification.__dict__,
                "avisos": doc.warnings, "estrutura": [_unit_json(u) for u in doc.body.root.children],
            }
            print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        else:
            arts = doc.body.articles()
            print(f"{doc.titulo} [{doc.tipo}] esfera={doc.esfera} artigos={len(arts)} "
                  f"qualidade={doc.quality.score} ({doc.quality.tier}) áreas={doc.classification.areas}")
            for w in doc.warnings:
                print("  aviso:", w)
        return 0

    if a.cmd == "search":
        cat = Catalog(a.db)
        for row in cat.search(a.query, a.limit):
            rub = f" — {row['rubrica']}" if row["rubrica"] else ""
            print(f"{row['norma']} {row['caminho']}{rub}\n    {row['trecho']}")
        return 0

    if a.cmd == "stats":
        cat = Catalog(a.db)
        db = cat.db
        print("normas:", db.execute("SELECT count(*) FROM norma").fetchone()[0])
        print("dispositivos:", db.execute("SELECT count(*) FROM dispositivo").fetchone()[0])
        for row in db.execute("SELECT esfera, faixa_qualidade, relevancia, count(*) c FROM norma GROUP BY 1,2,3 ORDER BY 1,2,3"):
            print(f"  {row['esfera']:<15} qualidade={row['faixa_qualidade']:<6} relevância={row['relevancia']:<7} {row['c']}")
        print("falhas:", db.execute("SELECT count(*) FROM falha_importacao").fetchone()[0])
        print("último commit:", cat.get("ultimo_commit"))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
