"""Gera os SVGs dos 13 cenários repaginados: python tools/cenarios/src/build.py [nomes]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import cenas1, cenas2, cenas3  # noqa

MAPA = {}
for m in (cenas1, cenas2, cenas3):
    for n in ("bar", "mercado", "ponto", "apartamento", "obra", "rua", "loja", "clinica", "garagem", "carro", "casa", "cafe", "cemiterio"):
        if hasattr(m, n):
            MAPA[n] = getattr(m, n)

if __name__ == "__main__":
    alvo = Path(__file__).resolve().parents[1]
    nomes = sys.argv[1:] or list(MAPA)
    for n in nomes:
        (alvo / f"{n}.svg").write_text(MAPA[n](), encoding="utf-8")
        print("ok", n)
