"""Gera os SVGs do lote 1: python tools/cenarios/gen_lote1.py [id ...]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
SC = {}
import lote1a
SC.update(lote1a.SCENES)
try:
    import lote1b
    SC.update(lote1b.SCENES)
except ImportError:
    pass
ids = sys.argv[1:] or list(SC)
for i in ids:
    (Path(__file__).resolve().parent / f"{i}.svg").write_text(SC[i](), encoding="utf-8")
    print("svg", i)
