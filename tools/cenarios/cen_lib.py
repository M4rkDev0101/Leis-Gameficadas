"""Pecas comuns para gerar cenarios SVG (viewBox 160x100)."""
import random


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def R(x, y, w, h, fill, o=None, rx=None, st=None, sw=.3):
    a = f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}"'
    if o is not None: a += f' opacity="{o}"'
    if rx is not None: a += f' rx="{rx}"'
    if st: a += f' stroke="{st}" stroke-width="{sw}"'
    return a + '/>'


def C(cx, cy, r, fill, o=None):
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}"' + (f' opacity="{o}"' if o is not None else "") + '/>'


def E(cx, cy, rx, ry, fill, o=None):
    return f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{fill}"' + (f' opacity="{o}"' if o is not None else "") + '/>'


def PG(pts, fill, o=None, st=None, sw=.3):
    p = " ".join(f"{f(x)},{f(y)}" for x, y in pts)
    a = f'<polygon points="{p}" fill="{fill}"'
    if o is not None: a += f' opacity="{o}"'
    if st: a += f' stroke="{st}" stroke-width="{sw}"'
    return a + '/>'


def L(x1, y1, x2, y2, col, w=.3, o=None):
    return (f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{col}" stroke-width="{w}"'
            + (f' opacity="{o}"' if o is not None else "") + '/>')


def PATH(d, fill="none", st=None, sw=.3, o=None):
    return (f'<path d="{d}" fill="{fill}"' + (f' stroke="{st}" stroke-width="{sw}"' if st else "")
            + (f' opacity="{o}"' if o is not None else "") + '/>')


def LG(i, stops, x2=0, y2=1):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{i}" x1="0" y1="0" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def RG(i, stops, r=.5):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<radialGradient id="{i}" cx="0.5" cy="0.5" r="{r}">{s}</radialGradient>'


def P(x, y, w, h):
    """% da imagem 16:10 -> unidades do viewBox."""
    return (x * 1.6, y, w * 1.6, h)


def wrap(sid, defs, body, vig=.5, warm=None):
    v = f'vg_{sid}'
    d = RG(v, [(0.55, "#000", 0), (1, "#000", vig)], .78)
    tint = f'<rect width="160" height="100" fill="{warm[0]}" opacity="{warm[1]}"/>' if warm else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" preserveAspectRatio="xMidYMid slice" width="1920" height="1200">'
            f'<defs>{d}{defs}</defs>{body}{tint}<rect width="160" height="100" fill="url(#{v})"/></svg>')


BOOKPAL = ["#7a2630", "#23406e", "#2f5d4a", "#c9a04a", "#4a3a6a", "#a8602a", "#d8d2c0", "#1f2a3a", "#5a1f2a", "#3a6a8a"]


def books(x, y, w, h, seed, pal=BOOKPAL, gap=.15):
    r = random.Random(seed)
    out = []
    cx = x
    while cx < x + w - 1:
        bw = min(r.uniform(1.1, 2.4), x + w - cx)
        bh = h * r.uniform(.68, .97)
        c = r.choice(pal)
        out.append(R(cx, y + h - bh, bw - gap, bh, c))
        out.append(R(cx, y + h - bh, bw - gap, .35, "#fff", .12))
        if r.random() < .5: out.append(R(cx + .15, y + h - bh * .55, bw - gap - .3, .35, "#e8c46a", .6))
        cx += bw
        if r.random() < .06: cx += r.uniform(1.5, 3.5)
    return "".join(out)


def shelf_unit(x, y, w, h, rows, frame, back, seed, pal=BOOKPAL, plank=None, sparse=0.0):
    plank = plank or frame
    o = [R(x, y, w, h, back), R(x - .8, y - .8, w + 1.6, .9, frame), R(x - .8, y, .9, h, frame), R(x + w - .1, y, .9, h, frame)]
    rh = h / rows
    for i in range(rows):
        yy = y + i * rh
        rr = random.Random(seed + i)
        if sparse and rr.random() < sparse:
            if rr.random() < .5:
                o.append(books(x + .6, yy + .8, w * .45, rh - 1.4, seed + i * 3, pal))
            else:
                o.append(R(x + w * .2, yy + rh - 4.6, w * .3, 3.8, "#cdbf9a"))
                o.append(R(x + w * .2, yy + rh - 4.6, w * .3, .5, "#fff", .2))
        else:
            o.append(books(x + .6, yy + .8, w - 1.2, rh - 1.4, seed + i * 3, pal))
        o.append(R(x - .4, yy + rh - .6, w + .8, .7, plank))
        o.append(R(x - .4, yy + rh - .6, w + .8, .15, "#fff", .25))
        o.append(R(x, yy + rh + .1, w, .9, "#000", .18))
    return "".join(o)


def monitor(x, y, w, h, body="#1c2128", screen="#2a5a8a", bars="#bcd8f0", stand="#2a2d33"):
    o = [R(x + w / 2 - 1.2, y + h, 2.4, 1.6, stand), R(x + w / 2 - 3.2, y + h + 1.4, 6.4, .8, stand, rx=.3),
         R(x, y, w, h, body, rx=.6), R(x + .6, y + .6, w - 1.2, h - 1.2, screen)]
    for i in range(3):
        o.append(R(x + 1.4, y + 1.2 + i * (h - 2.4) / 3.4, (w - 2.8) * (.85 - .2 * i), .5, bars, .8))
    o.append(R(x + .6, y + .6, w - 1.2, (h - 1.2) * .4, "#fff", .08))
    return "".join(o)


def folder(x, y, w, h, col, tab=None):
    return (R(x, y, w, h, col, rx=.25) + R(x, y - .5, w * .38, .6, tab or col, rx=.2) +
            R(x, y, w, .3, "#fff", .18) + R(x, y + h - .35, w, .35, "#000", .18))


def papers(x, y, w, h, n=3, col="#efe9d8", seed=1):
    r = random.Random(seed)
    o = []
    for i in range(n):
        dx, dy = r.uniform(-.8, .8), -i * .5
        o.append(R(x + dx, y + dy, w, h, col, st="#b8ae92", sw=.15))
        for k in range(3): o.append(R(x + dx + .8, y + dy + 1 + k * (h / 4.5), w * .6 - k * w * .1, .3, "#8a8470", .7))
    return "".join(o)


def window(x, y, w, h, grad, frame="#2a2218", mull=(1, 1), extra=""):
    o = [R(x - 1, y - 1, w + 2, h + 2, frame, rx=.4), R(x, y, w, h, f"url(#{grad})"), extra]
    for k in range(1, mull[0] + 1):
        o.append(R(x + w * k / (mull[0] + 1) - .35, y, .7, h, frame))
    for k in range(1, mull[1] + 1):
        o.append(R(x, y + h * k / (mull[1] + 1) - .35, w, .7, frame))
    o.append(PG([(x, y), (x + w * .35, y), (x + w * .1, y + h), (x, y + h)], "#fff", .07))
    return "".join(o)


def banner_flag(x, y, w, h, c1, c2, gold="#d8b04a", pole="#c9a04a"):
    """bandeira generica (emblema losango/circulo ficticio), pendurada em haste horizontal."""
    o = [R(x - .6, y - 1.2, w + 1.2, 1.1, pole, rx=.5), C(x - .6, y - .65, .9, "#e8c46a"), C(x + w + .6, y - .65, .9, "#e8c46a"),
         R(x, y, w, h, c1), R(x, y + h * .66, w, h * .09, gold, .8), R(x, y + h * .8, w, h * .05, gold, .6),
         PG([(x + w / 2, y + h * .1), (x + w * .88, y + h * .33), (x + w / 2, y + h * .56), (x + w * .12, y + h * .33)], c2, st=gold, sw=.3),
         C(x + w / 2, y + h * .33, w * .14, gold), R(x, y, w, h, "#000", .1), R(x + w * .66, y, w * .34, h, "#000", .08)]
    return "".join(o)


def pfloor(y0, vx, vy, color, op=.4, nx=16, ny=6, w=.3, span=330):
    o = []
    for i in range(nx + 1):
        xb = vx - span / 2 + span * i / nx
        o.append(L(vx + (xb - vx) * (y0 - vy) / (100 - vy), y0, xb, 100, color, w))
    for j in range(1, ny + 1):
        t = (j / ny) ** 1.9
        o.append(L(0, y0 + (100 - y0) * t, 160, y0 + (100 - y0) * t, color, w))
    return f'<g opacity="{op}">' + "".join(o) + '</g>'


def armchair(x, y, w, h, col, hi):
    o = [E(x + w / 2, y + h + .6, w * .55, 1.3, "#000", .3),
         R(x, y + h * .28, w * .2, h * .6, col, rx=1.2), R(x + w * .8, y + h * .28, w * .2, h * .6, col, rx=1.2),
         R(x + w * .12, y, w * .76, h * .62, col, rx=2.2), R(x + w * .2, y + h * .06, w * .6, h * .5, hi, .3, rx=1.6),
         R(x + w * .1, y + h * .58, w * .8, h * .3, col, rx=1.4), R(x + w * .12, y + h * .6, w * .76, .6, hi, .4),
         R(x + w * .06, y + h * .86, 1.2, h * .14, "#1a1208"), R(x + w * .86, y + h * .86, 1.2, h * .14, "#1a1208")]
    for k in range(5):
        o.append(C(x + w * (.22 + k * .14), y + h * .12, .28, "#d8b04a", .8))
    return "".join(o)


def lamp(x, y, col="#c9a04a", shade="#2a6a4a"):
    return (R(x - .3, y, .6, 4, col) + E(x, y + 4, 1.6, .5, col) +
            PG([(x - 2.6, y), (x + 2.6, y), (x + 1.6, y - 2.6), (x - 1.6, y - 2.6)], shade) + R(x - 2.6, y - .2, 5.2, .3, "#fff", .25))


def cup(x, y, s=1, col="#efe8d8", coffee="#3a2210"):
    return (E(x, y + .5 * s, 2.4 * s, .7 * s, "#000", .25) + E(x, y + .3 * s, 2.2 * s, .6 * s, "#d8d0bc") +
            R(x - 1.2 * s, y - 1.6 * s, 2.4 * s, 1.9 * s, col, rx=.3) + E(x, y - 1.6 * s, 1.2 * s, .4 * s, coffee) +
            PATH(f"M{f(x+1.2*s)} {f(y-1.2*s)}q1.1 .1 1.1 .9t-1.1 .9", st=col, sw=.35))


def car_side(cx, cy, s, body, glass="#5a7a96", wheel="#06080a", hub="#6a7480", wet=False):
    """carro de lado, centro-base (cx,cy), largura ~ 16*s"""
    o = [E(cx, cy + 1.9 * s, 8.8 * s, 1.0 * s, "#000", .35)]
    o.append(PATH(f"M{f(cx-8*s)} {f(cy+1*s)} L{f(cx-7*s)} {f(cy-1.4*s)} Q{f(cx-5*s)} {f(cy-3.4*s)} {f(cx-1*s)} {f(cy-3.4*s)} "
                  f"L{f(cx+3.5*s)} {f(cy-3.4*s)} Q{f(cx+6*s)} {f(cy-3*s)} {f(cx+7*s)} {f(cy-1.2*s)} L{f(cx+8.2*s)} {f(cy+1*s)} Z", fill=body))
    o.append(PG([(cx - 4.5 * s, cy - 1.4 * s), (cx - 3.6 * s, cy - 2.9 * s), (cx + 2.6 * s, cy - 2.9 * s), (cx + 4.8 * s, cy - 1.4 * s)], glass, .85))
    o.append(R(cx - 8 * s, cy - .2 * s, 16.2 * s, .4 * s, "#fff", .22))
    o.append(R(cx - 8 * s, cy + .6 * s, 16.2 * s, .5 * s, "#000", .25))
    for wx in (cx - 4.6 * s, cx + 4.8 * s):
        o += [C(wx, cy + 1.3 * s, 1.7 * s, wheel), C(wx, cy + 1.3 * s, .65 * s, hub)]
    return "".join(o)
