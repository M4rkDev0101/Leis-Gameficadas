"""Mini biblioteca para gerar cenários SVG (viewBox 160x100) no padrão novo: composição simétrica,
perspectiva de um ponto, paleta coesa, luz suave, sem texto e sem pessoas."""
import math

W, H = 160, 100


def f(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


class Sc:
    def __init__(s, p):
        s.pre, s.d, s.b, s.n = p, [], [], 0

    def _id(s):
        s.n += 1
        return f"{s.pre}{s.n}"

    # ---- gradientes -> devolvem url(#id)
    def lg(s, c1, c2, o1=1, o2=1, horiz=False):
        i = s._id()
        x2, y2 = (1, 0) if horiz else (0, 1)
        s.d.append(f'<linearGradient id="{i}" x1="0" y1="0" x2="{x2}" y2="{y2}"><stop offset="0" stop-color="{c1}" stop-opacity="{o1}"/><stop offset="1" stop-color="{c2}" stop-opacity="{o2}"/></linearGradient>')
        return f"url(#{i})"

    def lg3(s, stops, horiz=False):
        i = s._id()
        x2, y2 = (1, 0) if horiz else (0, 1)
        st = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
        s.d.append(f'<linearGradient id="{i}" x1="0" y1="0" x2="{x2}" y2="{y2}">{st}</linearGradient>')
        return f"url(#{i})"

    def rg(s, c, o=0.5, o2=0):
        i = s._id()
        s.d.append(f'<radialGradient id="{i}" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{c}" stop-opacity="{o}"/><stop offset="1" stop-color="{c}" stop-opacity="{o2}"/></radialGradient>')
        return f"url(#{i})"

    def pat(s, w, h, inner):
        i = s._id()
        s.d.append(f'<pattern id="{i}" width="{w}" height="{h}" patternUnits="userSpaceOnUse">{inner}</pattern>')
        return f"url(#{i})"

    # ---- primitivas
    def add(s, x):
        s.b.append(x)

    @staticmethod
    def _a(fill, o=None, st=None, sw=None, rx=None, extra=""):
        a = f' fill="{fill}"' if fill else ' fill="none"'
        if o is not None: a += f' opacity="{o}"'
        if st: a += f' stroke="{st}" stroke-width="{sw or .4}"'
        if rx is not None: a += f' rx="{rx}"'
        return a + (" " + extra if extra else "")

    def r(s, x, y, w, h, fill, o=None, st=None, sw=None, rx=None, extra=""):
        s.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"{s._a(fill,o,st,sw,rx,extra)}/>')

    def e(s, cx, cy, rx, ry, fill, o=None, st=None, sw=None):
        s.add(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}"{s._a(fill,o,st,sw)}/>')

    def c(s, cx, cy, r_, fill, o=None, st=None, sw=None):
        s.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r_)}"{s._a(fill,o,st,sw)}/>')

    def p(s, d, fill=None, o=None, st=None, sw=None, extra=""):
        s.add(f'<path d="{d}"{s._a(fill,o,st,sw,None,extra)}/>')

    def poly(s, pts, fill, o=None, st=None, sw=None):
        s.add('<path d="M' + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + f'Z"{s._a(fill,o,st,sw)}/>')

    def l(s, x1, y1, x2, y2, st, sw=.4, o=None):
        oo = f' opacity="{o}"' if o is not None else ""
        s.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{st}" stroke-width="{sw}"{oo}/>')

    def g(s, tr, fn):
        s.add(f'<g transform="{tr}">')
        fn()
        s.add('</g>')

    def glow(s, cx, cy, rx, ry, color="#fff", o=.5):
        s.e(cx, cy, rx, ry, s.rg(color, o))

    def cone(s, x, y, w_top, w_bot, y2, color="#fff", o=.12):
        s.poly([(x - w_top / 2, y), (x + w_top / 2, y), (x + w_bot / 2, y2), (x - w_bot / 2, y2)],
               s.lg(color, color, o, 0))

    def floor(s, y0, c1, c2, line="#000", lo=.18, vpx=80, nlines=18, spread=14, rows=5, tile=None):
        """chão em perspectiva de um ponto: gradiente + linhas que convergem ao ponto de fuga."""
        s.r(0, y0, W, H - y0, s.lg(c1, c2))
        vy = y0 - 16
        g = [f'<g stroke="{line}" stroke-width=".3" opacity="{lo}">']
        for i in range(-nlines, nlines + 1):
            x0 = vpx + i * spread * .4
            k = (H - vy) / (y0 - vy)
            x1 = vpx + (x0 - vpx) * k
            g.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{H}"/>')
        for t in range(1, rows + 1):
            y = y0 + (H - y0) * (t / (rows + 1)) ** 1.8
            g.append(f'<line x1="0" y1="{f(y)}" x2="{W}" y2="{f(y)}"/>')
        g.append('</g>')
        s.add("".join(g))

    def vig(s, tint=None, ot=.04, strong=.55):
        if tint:
            s.r(0, 0, W, H, tint, ot)
        i = s._id()
        s.d.append(f'<radialGradient id="{i}" cx="0.5" cy="0.5" r="0.78"><stop offset="0.5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="{strong}"/></radialGradient>')
        s.add(f'<rect width="160" height="100" fill="url(#{i})"/>')

    def out(s):
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" preserveAspectRatio="xMidYMid slice" width="1920" height="1200">'
                f'<defs>{"".join(s.d)}</defs>\n' + "\n".join(s.b) + "</svg>")


def mirror_x(v):
    return W - v


def frange(a, b, st):
    out = []
    while a < b:
        out.append(a)
        a += st
    return out
