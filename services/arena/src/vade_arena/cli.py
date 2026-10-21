"""Linha de comando da Arena.

    python jogar.py --repo ACERVO --db catalogo.sqlite                  (atalho na raiz do repositório)
    python -m vade_arena jogar   --repo ACERVO --db catalogo.sqlite [--jogador jogador.sqlite] [--porta 8765]
    python -m vade_arena validar --db catalogo.sqlite                   (confere o conteúdo contra a lei vigente)
"""

from __future__ import annotations

import argparse
import sys
import webbrowser

from . import bank


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="vade_arena")
    sub = ap.add_subparsers(dest="cmd", required=True)

    j = sub.add_parser("jogar", help="abre a Arena e o painel do acervo")
    j.add_argument("--repo", required=True, help="clone parcial do ctresb/leis")
    j.add_argument("--db", required=True, help="catálogo SQLite")
    j.add_argument("--jogador", default="jogador.sqlite", help="progresso do jogador (XP, sequência, histórico)")
    j.add_argument("--porta", type=int, default=8765)
    j.add_argument("--nao-abrir", action="store_true", help="não abrir o navegador")

    v = sub.add_parser("validar", help="valida estrutura do conteúdo e, com --db, o texto contra a lei vigente")
    v.add_argument("--db")

    a = ap.parse_args(argv)
    if a.cmd == "validar":
        b = bank.load()
        from . import tribunal

        errs = bank.validate_structure(b) + tribunal.validate(tribunal.load(), b.normas)
        n_ep = len(tribunal.load()["episodios"])
        print(f"Estrutura: {len(b.questoes)} questões, {len(b.casos)} casos, {n_ep} julgamentos, {len(errs)} erro(s)")
        for e in errs:
            print("  -", e)
        if a.db:
            problems, checked, absent = bank.validate_against_catalog(b, a.db)
            print(f"Lei vigente: {checked} fundamento(s) conferido(s), {absent} de normas fora do recorte, "
                  f"{len(problems)} problema(s)")
            for p in problems:
                print("  -", p)
            errs += problems
        return 1 if errs else 0

    from vade_ingest.updater import Updater

    from .server import Arena, make_server

    arena = Arena(a.db, a.jogador)
    srv = make_server(Updater(a.repo, a.db), arena, a.porta)
    url = f"http://127.0.0.1:{a.porta}"
    print(f"Arena em {url}  ·  painel do acervo em {url}/acervo  (Ctrl+C para sair)")
    if not a.nao_abrir:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
