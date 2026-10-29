"""Biblioteca de desenho para os geradores de cenários (SVG 160x100, estilo limpo/plano com perspectiva de um ponto)."""
import math
import random


def f(v):
    return ('%.2f' % v).rstrip('0').rstrip('.')


def lerp(a, b, t):
    return a + (b - a) * t


def rect(x, y, w, h, fill, o=None, rx=None, stroke=None, sw=.3):
    return (f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}"'
            + (f' opacity="{o}"' if o is not None else '') + (f' rx="{rx}"' if rx else '')
            + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + '/>')


def poly(pts, fill, o=None, stroke=None, sw=.3):
    p = ' '.join(f'{f(a)},{f(b)}' for a, b in pts)
    return (f'<polygon points="{p}" fill="{fill}"' + (f' opacity="{o}"' if o is not None else '')
            + (f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else '') + '/>')


def line(x1, y1, x2, y2, c, sw=.3, o=None, cap=None):
    return (f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{c}" stroke-width="{f(sw)}"'
            + (f' opacity="{o}"' if o is not None else '') + (f' stroke-linecap="{cap}"' if cap else '') + '/>')


def circ(cx, cy, r, fill, o=None, stroke=None, sw=.3):
    return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}"' + (f' opacity="{o}"' if o is not None else '')
            + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + '/>')


def ell(cx, cy, rx, ry, fill, o=None):
    return (f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{fill}"'
            + (f' opacity="{o}"' if o is not None else '') + '/>')


def path(d, fill='none', stroke=None, sw=.3, o=None, cap='round'):
    return (f'<path d="{d}" fill="{fill}"'
            + (f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}" stroke-linejoin="round"' if stroke else '')
            + (f' opacity="{o}"' if o is not None else '') + '/>')


class Scene:
    def __init__(s, name, seed=1):
        s.n = name
        s.defs = []
        s.b = []
        s.k = 0
        s.rng = random.Random(seed)

    def add(s, *parts):
        s.b.extend(p for p in parts if p)

    def _id(s):
        s.k += 1
        return f'{s.n}{s.k}'

    @staticmethod
    def _stops(stops):
        return ''.join(f'<stop offset="{st[0]}" stop-color="{st[1]}"' + (f' stop-opacity="{st[2]}"' if len(st) > 2 else '') + '/>' for st in stops)

    def lin(s, stops, horiz=False):
        i = s._id()
        d = 'x1="0" y1="0" x2="1" y2="0"' if horiz else 'x1="0" y1="0" x2="0" y2="1"'
        s.defs.append(f'<linearGradient id="{i}" {d}>{s._stops(stops)}</linearGradient>')
        return f'url(#{i})'

    def rad(s, stops, r=.5):
        i = s._id()
        s.defs.append(f'<radialGradient id="{i}" cx="0.5" cy="0.5" r="{r}">{s._stops(stops)}</radialGradient>')
        return f'url(#{i})'

    def clip(s, inner):
        i = s._id()
        s.defs.append(f'<clipPath id="{i}">{inner}</clipPath>')
        return f'url(#{i})'

    def glow(s, cx, cy, rx, ry, color='#fff4d0', o=.5):
        s.add(ell(cx, cy, rx, ry, s.rad([(0, color, o), (1, color, 0)])))

    def render(s, vig=.5):
        v = s.rad([(.5, '#000', 0), (1, '#000', vig)], r=.78)
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" preserveAspectRatio="xMidYMid slice" width="1920" height="1200">'
                '<defs>' + ''.join(s.defs) + '</defs>\n' + '\n'.join(s.b) + f'\n<rect width="160" height="100" fill="{v}"/></svg>')


BOOK_PAL = ['#7a2e2e', '#2e4a7a', '#2e6a4a', '#8a6a2e', '#5a3a6a', '#b0a088', '#3a5a6a', '#8a4a2e', '#a04a4a', '#4a4a5a']


def books_row(s, x, y, w, h, pal=BOOK_PAL):
    out = []
    cx = x + .5
    while cx < x + w - 1.2:
        bw = s.rng.choice([1.1, 1.4, 1.7, 2.0, 2.4])
        if cx + bw > x + w - .4:
            break
        bh = h * s.rng.choice([.72, .8, .88, .95, 1.0])
        col = s.rng.choice(pal)
        out.append(rect(cx, y - bh, bw, bh, col))
        out.append(rect(cx, y - bh, .35, bh, '#fff', .12))
        out.append(rect(cx + .15, y - bh * .7, bw - .3, .35, '#e8d08a', .5))
        cx += bw + s.rng.choice([0, 0, .1, .3])
        if s.rng.random() < .06:
            cx += 2.2
    return ''.join(out)


def shelf_unit(s, x, y, w, h, rows, wood='#5a3a22', back='#2a1a10', plank='#8a6038', pal=BOOK_PAL):
    out = [rect(x - 1, y - 1, w + 2, h + 2, wood, rx=.6), rect(x, y, w, h, back)]
    rh = h / rows
    for r in range(rows):
        by = y + rh * (r + 1) - .9
        out.append(books_row(s, x + .3, by, w - .6, rh - 2.2, pal))
        out.append(rect(x, by, w, .9, plank))
        out.append(rect(x, by + .9, w, .5, '#000', .25))
    out.append(rect(x, y, w, h, s.lin([(0, '#fff', .08), (1, '#000', .15)])))
    return ''.join(out)


def floor_persp(s, y0, ca, cb, vpy=40, n=16, m=9, gloss=.12, grid=.14):
    h = 100 - y0
    cl = s.clip(f'<rect x="0" y="{f(y0)}" width="160" height="{f(h)}"/>')
    out = [rect(0, y0, 160, h, s.lin([(0, ca), (1, cb)]))]
    inner = []
    for i in range(-n, n + 1):
        xb = 80 + i * 6.2
        inner.append(line(80, vpy, 80 + (xb - 80) * 3, 130, '#000', .35, grid))
    for k in range(1, m):
        y = y0 + h * ((k / m) ** 1.9)
        inner.append(line(0, y, 160, y, '#000', .3, grid * .9))
    out.append(f'<g clip-path="{cl}">' + ''.join(inner) + '</g>')
    out.append(ell(80, y0 + h * .45, 70, h * .32, s.rad([(0, '#fff', gloss), (1, '#fff', 0)])))
    out.append(rect(0, y0, 160, 1.6, s.lin([(0, '#000', .35), (1, '#000', 0)])))
    return ''.join(out)


def emblem(s, cx, cy, r, gold='#d8b45a', bg='#2a1a12', ring='#f0d27a', laurel='#4f8a58'):
    o = [circ(cx, cy, r * 1.35, s.rad([(0, gold, .35), (1, gold, 0)])),
         circ(cx, cy, r, bg, stroke=gold, sw=r * .1), circ(cx, cy, r * .82, 'none', stroke=ring, sw=r * .04, o=.6)]
    for sx in (-1, 1):
        o.append(path(f'M{f(cx+sx*r*1.02)} {f(cy-r*.2)}Q{f(cx+sx*r*1.18)} {f(cy+r*.6)} {f(cx+sx*r*.45)} {f(cy+r*1.02)}', stroke=laurel, sw=r * .13, o=.9))
    o.append(line(cx, cy - r * .55, cx, cy + r * .5, gold, r * .09))
    o.append(line(cx - r * .62, cy - r * .38, cx + r * .62, cy - r * .38, gold, r * .09))
    o.append(circ(cx, cy - r * .58, r * .09, gold))
    for sx in (-1, 1):
        px = cx + sx * r * .6
        o.append(line(px, cy - r * .38, px - r * .22, cy + r * .05, gold, r * .04))
        o.append(line(px, cy - r * .38, px + r * .22, cy + r * .05, gold, r * .04))
        o.append(path(f'M{f(px-r*.28)} {f(cy+r*.05)}H{f(px+r*.28)}Q{f(px)} {f(cy+r*.36)} {f(px-r*.28)} {f(cy+r*.05)}Z', fill=gold))
    o.append(rect(cx - r * .3, cy + r * .5, r * .6, r * .1, gold, rx=r * .04))
    return ''.join(o)


def pendant(s, x, ytop, ylamp, cone_to=54, col='#3a2414', glow='#ffe9b0', cone=.1):
    s.glow(x, ylamp + 1, 9, 5, glow, .45)
    o = [line(x, ytop, x, ylamp - 3, '#201008', .25),
         poly([(x - 1.2, ylamp - 3), (x + 1.2, ylamp - 3), (x + 4.5, ylamp), (x - 4.5, ylamp)], col, stroke='#c9a04a', sw=.2),
         ell(x, ylamp, 4.5, .9, glow),
         poly([(x - 4.5, ylamp), (x + 4.5, ylamp), (x + 18, cone_to), (x - 18, cone_to)], s.lin([(0, glow, cone), (1, glow, 0)]))]
    s.add(''.join(o))


def curtain(s, x, w, y0, y1, col, side='r', gold='#d8b45a'):
    hi = s.lin([(0, '#fff', .16), (.5, '#000', .12), (1, '#fff', .1)], horiz=True)
    o = [rect(x, y0, w, y1 - y0, col), rect(x, y0, w, y1 - y0, hi)]
    n = max(3, int(w / 2.2))
    for i in range(1, n):
        o.append(line(x + w * i / n, y0 + 2, x + w * i / n, y1, '#000', .25, .22))
    o.append(rect(x - .5, y0 - 1, w + 1, 3.2, col, rx=.8))
    o.append(rect(x - .5, y0 - 1, w + 1, 1, gold, .55))
    tb = y0 + (y1 - y0) * .55
    o.append(path(f'M{f(x)} {f(tb)}Q{f(x+w/2)} {f(tb+2.4)} {f(x+w)} {f(tb)}', stroke=gold, sw=.7))
    o.append(circ(x + (w if side == 'l' else 0), tb, .9, gold))
    return ''.join(o)


def arch_window(s, x, y, w, h, sky=('#9cc8ee', '#e8f2fa'), frame='#3a2414', sill='#5a3a22', city=None):
    o = []
    r = w / 2
    g = s.lin([(0, sky[0]), (1, sky[1])])
    arc = f'M{f(x)} {f(y+h)}V{f(y+r)}A{f(r)} {f(r)} 0 0 1 {f(x+w)} {f(y+r)}V{f(y+h)}Z'
    o.append(path(f'M{f(x-1)} {f(y+h+1)}V{f(y+r)}A{f(r+1)} {f(r+1)} 0 0 1 {f(x+w+1)} {f(y+r)}V{f(y+h+1)}Z', fill=frame))
    o.append(path(arc, fill=g))
    if city:
        cl = s.clip(f'<path d="{arc}"/>')
        o.append(f'<g clip-path="{cl}">' + city + '</g>')
    o.append(line(x + w / 2, y, x + w / 2, y + h, frame, .6))
    o.append(line(x, y + h * .5, x + w, y + h * .5, frame, .6))
    o.append(path(f'M{f(x+w*.12)} {f(y+r*.9)}A{f(r*.88)} {f(r*.88)} 0 0 1 {f(x+w*.88)} {f(y+r*.9)}', stroke='#fff', sw=.4, o=.3))
    o.append(rect(x - 2, y + h + .8, w + 4, 1.6, sill, rx=.4))
    return ''.join(o)


def sq_window(s, x, y, w, h, sky=('#9cc8ee', '#e8f2fa'), frame='#e8e4da', cols=2, rows=2, blinds=False, city=None):
    g = s.lin([(0, sky[0]), (1, sky[1])])
    o = [rect(x - 1.2, y - 1.2, w + 2.4, h + 2.4, frame, rx=.4, stroke='#000', sw=.15), rect(x, y, w, h, g)]
    if city:
        cl = s.clip(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"/>')
        o.append(f'<g clip-path="{cl}">' + city + '</g>')
    if blinds:
        yy = y + .6
        while yy < y + h - .5:
            o.append(rect(x, yy, w, 1.3, '#f4f2ea', .92))
            o.append(rect(x, yy + 1.3, w, .3, '#000', .15))
            yy += 1.9
    for i in range(1, cols):
        o.append(line(x + w * i / cols, y, x + w * i / cols, y + h, frame, .7))
    for i in range(1, rows):
        o.append(line(x, y + h * i / rows, x + w, y + h * i / rows, frame, .7))
    o.append(poly([(x, y), (x + w * .45, y), (x + w * .1, y + h), (x, y + h)], '#fff', .12))
    o.append(rect(x - 2, y + h + 1, w + 4, 1.5, frame, rx=.4))
    return ''.join(o)


def skyline(x, w, base, cols=('#2a2f4a', '#3a3f5e', '#232844'), lit='#ffd27a', seed=3, hmax=22, hmin=8):
    rng = random.Random(seed)
    o = []
    cx = x
    while cx < x + w:
        bw = rng.uniform(4, 8)
        bh = rng.uniform(hmin, hmax)
        o.append(rect(cx, base - bh, bw, bh + 2, rng.choice(cols)))
        for yy in range(int(base - bh + 2), int(base - 1), 3):
            for xx in range(int(cx + 1), int(cx + bw - 1), 2):
                if rng.random() < .35:
                    o.append(rect(xx, yy, .9, 1.2, lit, .85))
        cx += bw + rng.uniform(0, 1)
    return ''.join(o)


def clock(cx, cy, r, face='#f4f0e2', rim='#2a2d33'):
    o = [circ(cx, cy, r + .7, rim), circ(cx, cy, r, face)]
    for a in range(12):
        t = a * math.pi / 6
        o.append(line(cx + (r - .9) * math.sin(t), cy - (r - .9) * math.cos(t), cx + (r - .35) * math.sin(t), cy - (r - .35) * math.cos(t), '#333', .22))
    o += [line(cx, cy, cx, cy - r * .62, '#222', .35, cap='round'), line(cx, cy, cx + r * .42, cy + r * .2, '#222', .3, cap='round'), circ(cx, cy, .35, '#c33')]
    return ''.join(o)


def plant(x, y, sc=1.0, pot='#a05a34'):
    o = [poly([(x - 3 * sc, y - 5 * sc), (x + 3 * sc, y - 5 * sc), (x + 2.2 * sc, y), (x - 2.2 * sc, y)], pot),
         rect(x - 3.3 * sc, y - 5.8 * sc, 6.6 * sc, 1.3 * sc, '#c06a40', rx=.4)]
    for a, c in [(-38, '#2f7a4a'), (30, '#2f7a4a'), (-12, '#3a9058'), (14, '#3a9058'), (0, '#2a6a40')]:
        ang = math.radians(a - 90)
        L = (10 + abs(a) * .06) * sc
        ex, ey = x + math.cos(ang) * L, y - 5.5 * sc + math.sin(ang) * L
        mx, my = x + math.cos(ang) * L * .5, y - 5.5 * sc + math.sin(ang) * L * .5
        o.append(path(f'M{f(x)} {f(y-5.5*sc)}Q{f(mx+2*sc)} {f(my)} {f(ex)} {f(ey)}Q{f(mx-2*sc)} {f(my)} {f(x)} {f(y-5.5*sc)}Z', fill=c))
    return ''.join(o)


def desk(s, x, y, w, hb, top='#a87848', body='#6a4228', dark='#3a2010', drawers=3, shadow=True):
    """Mesa vista de frente: y = borda frontal do tampo; hb = altura do corpo."""
    o = []
    if shadow:
        o.append(ell(x + w / 2, y + hb + .6, w * .56, 1.8, '#000', .3))
    o.append(poly([(x + 2.5, y - 3), (x + w - 2.5, y - 3), (x + w + .6, y), (x - .6, y)], top, stroke='#000', sw=.1))
    o.append(poly([(x + 2.5, y - 3), (x + w - 2.5, y - 3), (x + w + .6, y), (x - .6, y)], '#fff', .12))
    o.append(rect(x - .6, y, w + 1.2, 1.8, top))
    o.append(rect(x - .6, y + 1.2, w + 1.2, .6, '#000', .25))
    o.append(rect(x, y + 1.8, w, hb - 1.8, body))
    o.append(rect(x, y + 1.8, w, hb - 1.8, s.lin([(0, '#000', .25), (1, '#000', 0)])))
    dw = (w - 4) / drawers
    for i in range(drawers):
        dx = x + 2 + i * dw
        o.append(rect(dx + .5, y + 3.4, dw - 1, hb - 5.8, dark, .55, rx=.4, stroke='#000', sw=.1))
        o.append(rect(dx + 1.3, y + 4.2, dw - 2.6, hb - 7.4, body, rx=.3))
        o.append(rect(dx + dw / 2 - 2, y + 5.2, 4, .8, '#d8b45a', rx=.4))
    o.append(rect(x + 1, y + hb, 1.8, 1.2, dark))
    o.append(rect(x + w - 2.8, y + hb, 1.8, 1.2, dark))
    return ''.join(o)


def monitor(s, x, y, w, h, scr='#cfe6ff', stand=True, bars=True, frame='#2a2d33'):
    o = [rect(x, y, w, h, frame, rx=.7), rect(x + .7, y + .7, w - 1.4, h - 1.4, s.lin([(0, scr), (1, '#7ab0e0')]), rx=.3)]
    if bars:
        for i in range(3):
            o.append(rect(x + 1.6, y + 1.6 + i * (h - 3) / 4, (w - 3.2) * (.85 - .2 * i), .7, '#2a4a7a', .55, rx=.3))
    if stand:
        o.append(rect(x + w / 2 - .6, y + h, 1.2, 1.6, '#555'))
        o.append(rect(x + w / 2 - 3, y + h + 1.4, 6, .9, '#444', rx=.4))
    return ''.join(o)


def laptop(x, y, w):
    h = w * .62
    return (rect(x + w * .08, y - h, w * .84, h, '#2a2d33', rx=.5) + rect(x + w * .12, y - h + .6, w * .76, h - 1.2, '#8ab8e8')
            + rect(x + w * .2, y - h + 1.6, w * .4, .5, '#2a4a7a', .6) + poly([(x, y), (x + w, y), (x + w - 1, y + 1.2), (x + 1, y + 1.2)], '#9a9ea6'))


def papers(x, y, w, n=4, col='#f1ecdc'):
    return ''.join(rect(x + (i % 2) * .6, y - (i + 1) * .9, w, .9, col if i % 2 == 0 else '#e4dcc4', stroke='#000', sw=.08) for i in range(n))


def folder(x, y, w, h, col='#c9a04a'):
    return (rect(x, y - h, w, h, col, rx=.3, stroke='#000', sw=.1) + rect(x + w * .1, y - h - 1, w * .3, 1.1, col, rx=.3)
            + rect(x + w * .1, y - h * .6, w * .8, .35, '#fff', .55) + rect(x, y - h, w, h * .3, '#fff', .12))


def open_book(x, y, w, h=3):
    o = [poly([(x, y), (x + w / 2, y - .8), (x + w, y), (x + w, y + h - .8), (x + w / 2, y + h - 1.6), (x, y + h - .8)], '#f4f0e0', stroke='#6a5a3a', sw=.15),
         line(x + w / 2, y - .8, x + w / 2, y + h - 1.6, '#6a5a3a', .2)]
    for i in range(3):
        o.append(line(x + 1.2, y + .5 + i * .6, x + w / 2 - .8, y + .2 + i * .6, '#8a8a8a', .15))
        o.append(line(x + w / 2 + .8, y + .2 + i * .6, x + w - 1.2, y + .5 + i * .6, '#8a8a8a', .15))
    return ''.join(o)


def frame_art(x, y, w, h, kind=0, frame='#3a2414', mat='#f0e8d4'):
    cols = [('#c98a4a', '#3a6a8a'), ('#6a8a4a', '#d8b45a'), ('#8a4a6a', '#e8c88a')][kind % 3]
    return (rect(x, y, w, h, frame, rx=.3) + rect(x + .8, y + .8, w - 1.6, h - 1.6, mat) + rect(x + 1.8, y + 1.8, w - 3.6, h - 3.6, cols[1])
            + path(f'M{f(x+1.8)} {f(y+h-1.8)}L{f(x+w*.4)} {f(y+h*.45)}L{f(x+w*.6)} {f(y+h*.7)}L{f(x+w*.75)} {f(y+h*.5)}L{f(x+w-1.8)} {f(y+h-1.8)}Z', fill=cols[0])
            + circ(x + w * .72, y + h * .32, w * .08, '#fff', .7))


def banner(x, ytop, ybot, w, col, accent='#d8b45a', pole='#c9a04a', stripe=None):
    o = [rect(x - .5, ytop - 2, .9, ybot - ytop + 2, pole), circ(x - .05, ytop - 2.2, 1.2, '#e8c46a'),
         rect(x + .4, ytop, w, w * 1.15, col), rect(x + .4, ytop, w, w * 1.15, '#000', .12),
         rect(x + .4, ytop + w * 1.15 - 2.2, w, 2.2, accent, .75), circ(x + .4 + w / 2, ytop + w * .55, w * .22, accent, .85)]
    if stripe:
        o.append(rect(x + .4, ytop + w * .2, w, 1.4, stripe, .8))
    return ''.join(o)


class Room:
    """Sala em perspectiva de um ponto. Fundo (bx0,by0,bx1,by1); t=0 frente (borda da tela), t=1 fundo."""

    def __init__(r, s, bx0, by0, bx1, by1):
        r.s, r.bx0, r.by0, r.bx1, r.by1 = s, bx0, by0, bx1, by1

    def L(r, t, v):
        yc, yf = lerp(0, r.by0, t), lerp(100, r.by1, t)
        return (lerp(0, r.bx0, t), yc + (yf - yc) * v)

    def R(r, t, v):
        yc, yf = lerp(0, r.by0, t), lerp(100, r.by1, t)
        return (lerp(160, r.bx1, t), yc + (yf - yc) * v)

    def F(r, t, u):
        return (lerp(lerp(0, r.bx0, t), lerp(160, r.bx1, t), u), lerp(100, r.by1, t))

    def C(r, t, u):
        return (lerp(lerp(0, r.bx0, t), lerp(160, r.bx1, t), u), lerp(0, r.by0, t))

    def lq(r, t0, t1, v0, v1):
        return [r.L(t0, v0), r.L(t1, v0), r.L(t1, v1), r.L(t0, v1)]

    def rq(r, t0, t1, v0, v1):
        return [r.R(t0, v0), r.R(t1, v0), r.R(t1, v1), r.R(t0, v1)]

    def fq(r, t0, t1, u0, u1):
        return [r.F(t0, u0), r.F(t1, u0), r.F(t1, u1), r.F(t0, u1)]

    def cq(r, t0, t1, u0, u1):
        return [r.C(t0, u0), r.C(t1, u0), r.C(t1, u1), r.C(t0, u1)]

    def shell(r, wall_back, wall_l, wall_r, ceil, floor_a, floor_b, grid=.12, nlines=12):
        s = r.s
        bw, bh = r.bx1 - r.bx0, r.by1 - r.by0
        o = [rect(0, 0, 160, 100, wall_back),
             poly([(0, 0), (r.bx0, r.by0), (r.bx0, r.by1), (0, 100)], s.lin([(0, wall_l[0]), (1, wall_l[1])], horiz=True)),
             poly([(160, 0), (r.bx1, r.by0), (r.bx1, r.by1), (160, 100)], s.lin([(0, wall_r[0]), (1, wall_r[1])], horiz=True)),
             rect(r.bx0, r.by0, bw, bh, wall_back),
             poly([(0, 0), (160, 0), (r.bx1, r.by0), (r.bx0, r.by0)], s.lin([(0, ceil[0]), (1, ceil[1])])),
             poly([(0, 100), (r.bx0, r.by1), (r.bx1, r.by1), (160, 100)], s.lin([(0, floor_b), (1, floor_a)]))]
        for i in range(nlines + 1):
            u = i / nlines
            a, b = r.F(1, u), r.F(-.35, u)
            o.append(line(a[0], a[1], b[0], b[1], '#000', .3, grid))
        for k in range(1, 15):
            t = 1 - 1 / (1 + .32 * k)
            a, b = r.F(t, 0), r.F(t, 1)
            o.append(line(a[0], a[1], b[0], b[1], '#000', .28, grid * .9))
        o.append(line(r.bx0, r.by0, r.bx0, r.by1, '#000', .5, .25))
        o.append(line(r.bx1, r.by0, r.bx1, r.by1, '#000', .5, .25))
        o.append(rect(r.bx0, r.by1 - 1.4, bw, 1.4, '#000', .18))
        o.append(ell(80, lerp(r.by1, 100, .5), 60, (100 - r.by1) * .4, s.rad([(0, '#fff', .12), (1, '#fff', 0)])))
        s.add(''.join(o))
