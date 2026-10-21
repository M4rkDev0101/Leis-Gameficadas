"""Gera instalador/vade.ico (balança dourada) só com a biblioteca padrão: PNG feito à mão dentro de um ICO."""

import math
import struct
import sys
import zlib
from pathlib import Path

N = 256
BG, GOLD, GOLD2 = (20, 16, 12), (245, 183, 0), (201, 160, 74)


def render() -> list[list[tuple[int, int, int, int]]]:
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]
    r = 46  # cantos arredondados

    def inside_rounded(x, y):
        cx = min(max(x, r), N - 1 - r)
        cy = min(max(y, r), N - 1 - r)
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r

    def seg(x, y, x1, y1, x2, y2, w):
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) <= w

    def tri(x, y, ax, ay, bx, by, cx, cy):
        d1 = (x - bx) * (ay - by) - (ax - bx) * (y - by)
        d2 = (x - cx) * (by - cy) - (bx - cx) * (y - cy)
        d3 = (x - ax) * (cy - ay) - (cx - ax) * (y - ay)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))

    for y in range(N):
        for x in range(N):
            if not inside_rounded(x, y):
                continue
            c = BG
            if seg(x, y, 128, 52, 128, 200, 7) or seg(x, y, 84, 204, 172, 204, 9):
                c = GOLD
            if seg(x, y, 52, 78, 204, 78, 6) or math.hypot(x - 128, y - 50) <= 12:
                c = GOLD
            for px0 in (52, 204):
                if seg(x, y, px0, 78, px0 - 30, 140, 3) or seg(x, y, px0, 78, px0 + 30, 140, 3):
                    c = GOLD2
                if tri(x, y, px0 - 38, 140, px0 + 38, 140, px0, 162) and y >= 140:
                    c = GOLD
            px[y][x] = (*c, 255)
    return px


def png(px) -> bytes:
    raw = b"".join(b"\x00" + bytes(v for p in row for v in p) for row in px)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", N, N, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def ico(png_bytes: bytes) -> bytes:
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png_bytes), 6 + 16)  # 0 = 256 px
    return header + entry + png_bytes


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("vade.ico")
    out.write_bytes(ico(png(render())))
    print("ícone gerado:", out)
