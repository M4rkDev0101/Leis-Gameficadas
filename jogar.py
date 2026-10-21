"""Atalho para abrir a Arena sem instalar nada:

    python jogar.py --repo acervo --db catalogo.sqlite

Equivale a ``python -m vade_arena jogar ...`` com os três pacotes no caminho de importação.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for pkg in ("ingest", "learning", "arena"):
    sys.path.insert(0, str(ROOT / "services" / pkg / "src"))

from vade_arena.cli import main  # noqa: E402

if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(main(args if args and args[0] in ("jogar", "validar") else ["jogar", *args]))
