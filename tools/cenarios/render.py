"""Renderiza tools/cenarios/*.svg (ou os nomes passados) para web/cenarios/<nome>.webp (1920x1080) via Edge headless + Pillow.

Uso: python tools/cenarios/render.py [nome ...] [--qualidade 88]
O SVG é mostrado em 100vw x 100vh com preserveAspectRatio="xMidYMid slice" (igual ao jogo, que usa object-fit: cover).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

EDGE = r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
AQUI = Path(__file__).resolve().parent
SAIDA = AQUI.parents[1] / "services/arena/src/vade_arena/web/cenarios"
L, A = 1920, 1080


def renderizar(svg: Path, qualidade: int) -> Path:
    texto = svg.read_text(encoding="utf-8")
    if "preserveAspectRatio" not in texto:
        texto = texto.replace("<svg ", '<svg preserveAspectRatio="xMidYMid slice" ', 1)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        html = tmp / "c.html"
        png = tmp / "c.png"
        html.write_text(
            '<!doctype html><meta charset="utf-8"><style>html,body{margin:0;width:100vw;height:100vh;overflow:hidden;background:#000}'
            'svg{display:block;width:100vw;height:100vh}</style>' + texto, encoding="utf-8")
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={L},{A}",
                        f"--screenshot={png}", html.as_uri()], check=True, capture_output=True, timeout=120)
        im = Image.open(png).convert("RGB")
        if im.size != (L, A):
            im = im.crop((0, 0, L, A))
        SAIDA.mkdir(parents=True, exist_ok=True)
        saida = SAIDA / (svg.stem + ".webp")
        im.save(saida, "WEBP", quality=qualidade, method=6)
    return saida


def main(args: list[str]) -> None:
    q = 88
    if "--qualidade" in args:
        i = args.index("--qualidade")
        q = int(args[i + 1])
        del args[i:i + 2]
    arqs = [AQUI / (a.removesuffix(".svg") + ".svg") for a in args] or sorted(AQUI.glob("*.svg"))
    for s in arqs:
        out = renderizar(s, q)
        print(f"{s.stem}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1:])
