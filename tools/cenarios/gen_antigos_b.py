"""Gera gabinete, delegacia, custodia, escritorio, promotoria, corredor. Os retângulos de pontos clicáveis (em % do palco) são
convertidos em unidades do SVG por X=1.6*x, Y=y (viewBox 160x100). Uso: python gen_antigos_b.py"""
from pathlib import Path

from lib_cen import *

AQUI = Path(__file__).resolve().parent


def cadeira_giratoria(s, x, y, w, h, col='#2a2d38'):
    return (rect(x, y, w, h, col, rx=w * .3) + rect(x + w * .1, y + h * .08, w * .8, h * .84, '#fff', .06, rx=w * .25)
            + line(x + w * .5, y + h * .1, x + w * .5, y + h * .9, '#000', .25, .35))


def ceiling_panels(r, s, ts, u0=.3, u1=.7, col='#fffbe8'):
    for t0, t1 in ts:
        s.add(poly(r.cq(t0, t1, u0, u1), col, .95))
        s.glow(*r.C((t0 + t1) / 2, .5), 14, 3, '#fff4d0', .25)


def gabinete():
    s = Scene('gb', 21)
    r = Room(s, 6, 8, 154, 74)
    r.shell('#6b4a30', ('#4a3220', '#3a2616'), ('#3a2616', '#4a3220'), ('#2a1a10', '#3a2616'), '#7a4a28', '#34200f', grid=.16)
    # lambri e friso
    s.add(rect(6, 8, 148, 3, '#c9955c', .8), rect(6, 11, 148, 1, '#000', .25))
    s.add(rect(6, 54, 148, 20, s.lin([(0, '#4a2e1a'), (1, '#2e1c0e')])), rect(6, 53, 148, 1.6, '#c9955c'), rect(6, 54.6, 148, .6, '#000', .3))
    for i in range(9):
        s.add(rect(9 + i * 16.4, 57, 12, 14, '#000', .22, rx=.5), rect(10 + i * 16.4, 58, 10, 12, '#5a3a22', .8, rx=.4))
    # estante embutida (ponto 6..44% => 10..70)
    s.add(rect(9, 11, 62, 61, '#2e1c0e'), shelf_unit(s, 11, 13, 58, 44, 5, wood='#4a2e1a', back='#1c110a', plank='#9a6a3a'))
    s.add(rect(9.5, 57, 61, 15, '#4a2e1a'), rect(9.5, 57, 61, 1.2, '#9a6a3a'))
    for i in range(3):
        s.add(rect(11 + i * 19.6, 60, 17.4, 10.5, '#2e1c0e', rx=.5), rect(12 + i * 19.6, 61, 15.4, 8.5, '#5a3a22', rx=.4), rect(17 + i * 19.6, 64, 5.4, .8, '#d8b45a', rx=.4))
    s.add(globe(54, 41))
    # janela (96..136, 12..42)
    s.add(sq_window(s, 97, 13, 38, 29, sky=('#3a3f7a', '#e8a070'), frame='#c9955c', cols=2, rows=1, city=skyline(97, 38, 42, seed=5, hmax=16)))
    s.add(curtain(s, 90, 8, 10, 56, '#7a1f2a'), curtain(s, 134, 8, 10, 56, '#7a1f2a', side='l'))
    # bandeira (144..157, 20..50)
    s.add(banner(147, 22, 62, 10, '#2a4a8a', stripe='#f0e8d0'))
    s.add(rect(145.2, 61, 3.2, 1.6, '#3a2010'))
    # cadeira do juiz e mesa (48..112)
    s.add(rect(68, 36, 24, 26, '#2a1a22', rx=6), rect(70, 38, 20, 22, '#4a2a34', rx=5), rect(79.7, 39, .5, 20, '#000', .3), rect(74.5, 39, .5, 20, '#000', .3), rect(85, 39, .5, 20, '#000', .3))
    s.add(rug(r))
    s.add(desk(s, 48, 58, 64, 22, top='#b07a48', body='#6a3e22', dark='#2e1a0e', drawers=4))
    s.add(monitor(s, 74.6, 46.5, 14, 8.6, scr='#bfe0ff'))
    s.add(papers(52, 55.5, 9, 5), folder(63, 55.5, 5, 3.4, '#8a2a2a'), papers(98, 55.8, 10, 4), folder(94, 55.8, 5, 3.4, '#2a4a8a'))
    s.add(lamp_verde(104, 55.8))
    s.add(rect(54.5, 62.8, 5, 4, '#000', .0))
    ceiling_panels(r, s, [(.25, .45), (.62, .82)], col='#ffe9b0')
    return s


def globe(x, y):
    return (rect(x - .4, y + 7, .8, 5, '#c9a04a') + rect(x - 3, y + 11.6, 6, 1.2, '#c9a04a', rx=.5) + circ(x, y + 3, 5, '#3a6a8a')
            + path(f'M{f(x-3)} {f(y+2)}Q{f(x)} {f(y-.5)} {f(x+3)} {f(y+2)}Q{f(x+2)} {f(y+5)} {f(x-1)} {f(y+5.5)}Z', fill='#5a9a5a')
            + path(f'M{f(x-5)} {f(y+3)}A5 5 0 0 0 {f(x+5)} {f(y+3)}', stroke='#c9a04a', sw=.4) + circ(x - 1.8, y + 1, 1.2, '#fff', .25))


def lamp_verde(x, y):
    return (rect(x - 2.4, y - 1, 4.8, 1, '#c9a04a', rx=.3) + rect(x - .3, y - 6, .6, 5, '#c9a04a') + path(f'M{f(x-3)} {f(y-6)}Q{f(x)} {f(y-9.4)} {f(x+3)} {f(y-6)}Z', fill='#1f6a4a')
            + ell(x, y - 6, 3, .6, '#ffe9a0', .8))


def rug(r):
    s = r.s
    return (poly(r.fq(-.02, .55, .18, .82), '#5a1f26') + poly(r.fq(0, .5, .22, .78), 'none', stroke='#d8b45a', sw=.3)
            + poly(r.fq(.04, .46, .27, .73), '#7a2a32', .8))


def delegacia():
    s = Scene('dl', 22)
    r = Room(s, 8, 10, 152, 72)
    r.shell('#7fa28e', ('#6a8c78', '#5a7a68'), ('#5a7a68', '#6a8c78'), ('#d8ddd6', '#b8c0b8'), '#9aa89e', '#4a5a52', grid=.22, nlines=14)
    # faixa baixa escura (rodapé alto) + rodapé
    s.add(rect(8, 52, 144, 20, '#4a6a58'), rect(8, 51, 144, 1.5, '#d8dfd4'), rect(8, 52.5, 144, .6, '#000', .25), rect(8, 70.5, 144, 1.5, '#2a3a32'))
    for i in range(12):
        s.add(line(8 + i * 12, 53, 8 + i * 12, 70, '#000', .25, .2))
    # janela com persiana (esq)
    s.add(sq_window(s, 16, 14, 28, 24, sky=('#cfe0ee', '#f4f6f8'), frame='#e8e4da', cols=2, rows=1, blinds=True))
    # plaquinha, relógio, cartaz em branco
    s.add(rect(66, 13, 28, 7, '#1f3a2c', rx=.8, stroke='#d8b45a', sw=.5), rect(72, 15, 16, 1.2, '#d8b45a', .8, rx=.5), rect(75, 17.4, 10, .8, '#d8b45a', .5, rx=.4))
    s.add(clock(100, 17, 3.4))
    s.add(frame_art(50, 24, 9, 12, 2, frame='#3a2a1a'))
    # mural de cortiça (115..144, 14..38)
    s.add(cork(115, 14, 29, 24, s))
    # arquivo 4 gavetas + pastas (16..42, 47..61)
    s.add(arquivo(s, 18, 62, 22, 18))
    s.add(folder(19.5, 62, 5.5, 13, '#c9a04a'), folder(25.5, 62, 5.5, 11, '#3a6a9a'), folder(31.5, 62, 5.5, 12.5, '#a04a3a'))
    # balcão central (63..93, 44..58)
    s.add(desk(s, 54, 62, 52, 18, top='#9a9aa2', body='#5a5e66', dark='#2a2d33', drawers=3))
    s.add(open_book(65, 57, 27, 4.6), rect(61, 59.4, 3, .9, '#222'), pen_holder(97, 62))
    s.add(laptop(70, 56.2, 0) if False else '')
    # banco à direita e cesto
    s.add(rect(118, 66, 32, 2.4, '#8a6a42', rx=.6), rect(120, 68.2, 1.6, 9, '#3a2a1a'), rect(146, 68.2, 1.6, 9, '#3a2a1a'), ell(134, 78, 18, 1.4, '#000', .25))
    # luminárias
    ceiling_panels(r, s, [(.22, .38), (.52, .68), (.8, .94)], u0=.25, u1=.75, col='#f6fbf0')
    return s


def cork(x, y, w, h, s):
    o = [rect(x - 1.2, y - 1.2, w + 2.4, h + 2.4, '#7a5232', rx=.6), rect(x, y, w, h, '#b88a5a')]
    rng = random.Random(9)
    for i in range(70):
        o.append(circ(x + rng.uniform(0, w), y + rng.uniform(0, h), .25, '#8a6038', .6))
    sheets = [(2, 2, 8, 10, '#f4efe0'), (12, 3, 7, 8, '#ece6d2'), (20, 2, 7, 11, '#f4efe0'), (3, 14, 9, 8, '#fff2b8'), (14, 13, 6, 9, '#f4efe0'), (21, 14, 6, 8, '#cfe8f0')]
    for sx, sy, sw_, sh, c in sheets:
        o.append(rect(x + sx, y + sy, sw_, sh, c, stroke='#000', sw=.08))
        for k in range(3):
            o.append(rect(x + sx + 1, y + sy + 1.5 + k * 1.8, sw_ - 2, .4, '#6a6a6a', .5))
        o.append(circ(x + sx + sw_ / 2, y + sy + .6, .5, '#c33'))
    o.append(path(f'M{f(x+6)} {f(y+2.6)}L{f(x+15.5)} {f(y+3.6)}L{f(x+23.5)} {f(y+2.6)}L{f(x+16)} {f(y+14)}L{f(x+7)} {f(y+14.6)}', stroke='#c33', sw=.25, o=.9))
    return ''.join(o)


def arquivo(s, x, y, w, h):
    o = [ell(x + w / 2, y + h + .4, w * .6, 1.4, '#000', .3), rect(x, y, w, h, '#8a9098', rx=.5), rect(x, y, w, 1.2, '#b8bec4'), rect(x, y, w, h, s.lin([(0, '#fff', .12), (1, '#000', .18)]))]
    for i in range(4):
        gy = y + 2 + i * 4
        o += [rect(x + 1.2, gy, w - 2.4, 3.4, '#6a7078', rx=.3), rect(x + w / 2 - 2.4, gy + 1, 4.8, .9, '#d8dde0', rx=.4), rect(x + w / 2 - 3, gy + .3, 6, .5, '#000', .2)]
    return ''.join(o)


def pen_holder(x, y):
    return rect(x, y - 3.4, 2.6, 3.4, '#3a3d44', rx=.4) + line(x + .6, y - 3.4, x + .2, y - 5.6, '#c33', .35) + line(x + 1.6, y - 3.4, x + 2, y - 5.8, '#235', .35)


def custodia():
    s = Scene('cu', 23)
    r = Room(s, 8, 8, 152, 72)
    r.shell('#a3b4c4', ('#8a9cae', '#7a8c9e'), ('#7a8c9e', '#8a9cae'), ('#e4e8ec', '#c4ccd4'), '#aeb6bc', '#5c666e', grid=.22, nlines=14)
    s.add(rect(8, 54, 144, 18, '#6a7e92'), rect(8, 53, 144, 1.6, '#e8ecf0'), rect(8, 54.6, 144, .6, '#000', .25), rect(8, 70.6, 144, 1.4, '#2a3844'))
    for i in range(13):
        s.add(line(8 + i * 11.2, 55, 8 + i * 11.2, 70.5, '#000', .25, .2))
    # telão de videoconferência
    s.add(rect(44, 9.5, 72, 30, '#14181e', rx=1.4, stroke='#8a929a', sw=.5))
    tiles = [(46, 11.5), (82, 11.5), (46, 25.5), (82, 25.5)]
    cols = [('#2a4a6a', '#1a3050'), ('#3a4a5a', '#222e3c'), ('#2a5a5a', '#1a3a40'), ('#4a4a6a', '#2a2a44')]
    for (tx, ty), (c1, c2) in zip(tiles, cols):
        s.add(rect(tx, ty, 32, 12.4, s.lin([(0, c1), (1, c2)]), rx=.6))
        s.add(rect(tx + 1.2, ty + 9.6, 9, 1.8, '#000', .5, rx=.5), rect(tx + 2, ty + 10.2, 6, .6, '#cfe0ee', .9, rx=.3))
        s.add(circ(tx + 26.5, ty + 10.6, .9, '#4ac27a'))
        s.add(path(f'M{f(tx+11)} {f(ty+3)}h10v6h-10z', stroke='#fff', sw=.3, o=.25), rect(tx + 15.5, ty + 5, 1, 1.4, '#fff', .35))
    s.add(rect(74, 6.2, 12, 3.2, '#2a2d33', rx=.8), circ(80, 7.8, 1, '#4a90c8'))
    s.add(poly([(44, 9.5), (70, 9.5), (52, 39.5), (44, 39.5)], '#fff', .05))
    # brasão e relógio
    s.add(emblem(s, 26, 24, 6, bg='#243a54', gold='#d8b45a'), clock(134, 22, 5))
    # cadeiras de espera
    for cx in (16, 28):
        s.add(ell(cx + 4, 80, 6, 1, '#000', .3), rect(cx, 63, 8, 6, '#2a3a5a', rx=1), rect(cx + .8, 69, 6.4, 3, '#1c2840', rx=.6), rect(cx + 3.6, 72, .8, 7, '#555'), rect(cx + 1, 79, 6, .8, '#555', rx=.4))
    # armário/arquivo à direita
    s.add(arquivo(s, 126, 60, 20, 20), arquivo(s, 126 - 20.5, 60, 20, 20) if False else '')
    # bancada central com computador (48..112, 50..80)
    s.add(desk(s, 48, 58, 64, 22, top='#b08a5a', body='#6a4a30', dark='#2e1e12', drawers=4))
    s.add(emblem_small(80, 70))
    s.add(monitor(s, 74.6, 46.5, 14, 8.6, scr='#d8ecff'))
    s.add(papers(52, 55.5, 10, 5, '#f4f0e0'), folder(65, 55.5, 5, 3.4, '#2a4a8a'), rect(98, 54.2, 5, 1.4, '#3a2a1a', rx=.4), martelo(106, 55.8))
    ceiling_panels(r, s, [(.22, .38), (.52, .68), (.8, .94)], u0=.25, u1=.75, col='#f6fbff')
    return s


def emblem_small(cx, cy):
    return circ(cx, cy, 3.4, '#2e1e12', stroke='#d8b45a', sw=.35) + line(cx, cy - 1.8, cx, cy + 1.6, '#d8b45a', .35) + line(cx - 2.2, cy - 1, cx + 2.2, cy - 1, '#d8b45a', .35)


def martelo(x, y):
    return rect(x - 3, y - .6, 6, 1.2, '#3a2a1a', rx=.4) + rect(x - 1.8, y - 4.2, 3.6, 2.2, '#6a4228', rx=.4) + rect(x - .2, y - 2, .5, 1.8, '#6a4228')


def escritorio():
    s = Scene('es', 24)
    r = Room(s, 18, 10, 142, 66)
    r.shell('#8ea6bf', ('#7088a6', '#5e7694'), ('#6a82a0', '#5a7290'), ('#e0e4ea', '#c0c8d2'), '#a8703e', '#5a361c', grid=.1, nlines=10)
    s.add(rect(18, 52, 124, 14, '#6a84a2'), rect(18, 51, 124, 1.4, '#e8eef4'), rect(18, 64.6, 124, 1.4, '#e8eef4', .8))
    # parede esquerda: janela com pôr do sol
    s.add(poly(r.lq(.12, .8, .12, .62), '#e8e4da'))
    sky = s.lin([(0, '#3a3a7a'), (.55, '#d8688a'), (1, '#f6b070')])
    s.add(poly(r.lq(.16, .76, .17, .57), sky))
    for k in range(7):
        t0 = .16 + k * .09
        hh = [.42, .36, .46, .32, .4, .34, .44][k]
        s.add(poly(r.lq(t0, t0 + .07, .57 - hh * .5 - .0, .57), '#2a2f4a'))
    s.add(poly(r.lq(.46, .48, .17, .57), '#e8e4da'))
    s.add(poly(r.lq(.16, .76, .36, .38), '#e8e4da'))
    s.add(poly(r.lq(.1, .82, .62, .67), '#c8c4ba'))
    s.add(poly(r.lq(.06, .16, .08, .72), '#6a2a3a'), poly(r.lq(.76, .86, .08, .72), '#6a2a3a'))
    # parede direita: estante em perspectiva
    s.add(poly(r.rq(.1, .85, .08, .85), '#3a2616'))
    for k in range(4):
        v0 = .12 + k * .18
        s.add(poly(r.rq(.12, .83, v0 + .13, v0 + .15), '#8a6038'))
        t = .13
        while t < .8:
            tw = random.Random(int(t * 100) + k).choice([.025, .03, .04])
            col = random.Random(int(t * 1000) + k * 7).choice(BOOK_PAL)
            hh = random.Random(int(t * 777) + k).choice([.1, .11, .12, .13])
            s.add(poly(r.rq(t, t + tw, v0 + .13 - hh, v0 + .13), col))
            t += tw + .004
    s.add(poly(r.rq(.1, .85, .08, .85), s.lin([(0, '#000', .0), (1, '#000', .25)], horiz=True)))
    # quadros na parede do fundo (frame cluster)
    s.add(frame_art(21, 22, 8, 18, 0, frame='#2a2a2a'))
    s.add(rect(29.5, 22, 0, 0, '#000'))
    s.add(frame_art(32, 24, 7, 14, 1, frame='#2a2a2a'))
    s.add(frame_art(62, 31, 30, 18, 2, frame='#3a2414', mat='#f4efe0'))
    s.add(rect(96, 21, 44, 22, '#e8ecf0', rx=.8, stroke='#8a929a', sw=.6))
    for i, (sx, sy, c) in enumerate([(98, 23, '#fff2b8'), (108, 23, '#f4efe0'), (118, 23, '#cfe8f0'), (128, 23, '#f4efe0'), (100, 33, '#f4efe0'), (112, 32, '#fff2b8'), (124, 33, '#f4efe0')]):
        s.add(rect(sx, sy, 8, 7, c, stroke='#000', sw=.08), rect(sx + 1, sy + 1.6, 6, .4, '#7a7a7a', .6), rect(sx + 1, sy + 3, 5, .4, '#7a7a7a', .6), circ(sx + 4, sy + .6, .45, '#c33'))
    s.add(rect(141.5, 22, 15, 18, '#c05a3a', rx=.6), rect(143, 24, 12, 8, '#f4e8d0', .9), rect(143, 34, 12, 1.2, '#f4e8d0', .8), rect(143, 36.4, 8, 1, '#f4e8d0', .6))
    # credenza + impressora (esq)
    s.add(ell(35, 82, 17, 1.6, '#000', .3), rect(20, 66, 30, 15, '#6a4228'), rect(19, 65, 32, 1.8, '#b07a48'))
    for i in range(3):
        s.add(rect(21.2 + i * 9.6, 68, 8.8, 11.4, '#4a2e1a', rx=.4), rect(24.6 + i * 9.6, 70, 2, .8, '#d8b45a', rx=.4))
    s.add(rect(23, 58, 22, 7.2, '#cfd2d6', rx=1), rect(25, 56, 18, 2.4, '#e8eaee'), rect(26, 61, 16, 1.6, '#555', rx=.6), circ(42.4, 59.6, .6, '#4ac27a'))
    # caixas de arquivo
    s.add(rect(50, 64, 15, 11, '#c9a46a', rx=.3, stroke='#000', sw=.1), rect(52.5, 67, 10, 3, '#f0e2c0', rx=.3), rect(51.5, 55, 13, 9, '#d8b47a', rx=.3, stroke='#000', sw=.1), rect(53.5, 57.5, 9, 2.6, '#f0e2c0', rx=.3))
    # lixeira
    s.add(ell(91, 85, 8, 1.4, '#000', .3), poly([(84.6, 70.5), (97.4, 70.5), (95.6, 84.6), (86.4, 84.6)], '#5a6a7a'), rect(84, 69.6, 14, 1.6, '#7a8a9a', rx=.6), line(87.5, 73, 87.9, 82.5, '#fff', .3, .2))
    # mesa direita com computador
    s.add(desk(s, 108, 62, 46, 18, top='#c08a54', body='#7a4a28', dark='#3a2010', drawers=2))
    s.add(monitor(s, 128, 47, 16, 10, scr='#d8ecff'), rect(131, 59.4, 10, 1.2, '#2a2d33', rx=.4), papers(111, 59.5, 9, 4), plant(151, 52, .8))
    s.add(poly(r.fq(.08, .55, .3, .7), '#fff', .0))
    ceiling_panels(r, s, [(.2, .4), (.55, .75)], u0=.28, u1=.72, col='#fffbe8')
    return s


def promotoria():
    s = Scene('pr', 25)
    r = Room(s, 10, 10, 150, 70)
    r.shell('#3c4a66', ('#2c3850', '#222c40'), ('#222c40', '#2c3850'), ('#1a2030', '#2a3248'), '#3a4254', '#171b26', grid=.16, nlines=14)
    s.add(rect(10, 56, 140, 14, '#2c3854'), rect(10, 55, 140, 1.4, '#6a7a9a'), rect(10, 68.8, 140, 1.2, '#161b28'))
    # quadro de evidências (big board)
    s.add(rect(11, 9, 54, 38, '#6a4a2a', rx=1), rect(12.4, 10.4, 51.2, 35.2, '#b88a5a'))
    pins = [(16, 14), (30, 13), (46, 15), (22, 28), (38, 27), (54, 29)]
    for i, (px, py) in enumerate(pins):
        s.add(rect(px, py, 8, 9, '#f4efe0', stroke='#000', sw=.1), rect(px + 1, py + 1, 6, 5, '#7a8290'), rect(px + 1, py + 6.6, 5, .5, '#555'), circ(px + 4, py + .5, .5, '#c33'))
    s.add(path('M20 15L34 14L50 16L26 29L42 28L58 30', stroke='#d8423a', sw=.3, o=.9))
    s.add(rect(26, 36, 9, 7, '#fff2b8', stroke='#000', sw=.08), rect(46, 37, 9, 6, '#cfe8f0', stroke='#000', sw=.08))
    # mural (66..94, 8..22)
    s.add(rect(66, 8.4, 29, 13, '#e8e4d8', rx=.8, stroke='#6a4a2a', sw=.8), rect(69, 11, 23, 1.6, '#2a3a5a', rx=.5), rect(69, 14.4, 17, .8, '#6a6a6a', .6), rect(69, 16.6, 20, .8, '#6a6a6a', .6), rect(69, 18.6, 12, .8, '#6a6a6a', .6))
    # janela noturna (direita)
    s.add(sq_window(s, 102, 14, 36, 25, sky=('#10163a', '#2a3a6a'), frame='#aab4c8', cols=3, rows=1, blinds=True, city=skyline(102, 36, 39, cols=('#1a2040', '#222a50'), seed=8, hmax=14)))
    s.add(circ(131, 19, 2.2, '#f4f0d0'), circ(130.2, 18.4, 2, '#10163a', .0))
    # balcão comprido de evidências com três grupos
    s.add(rect(10, 58.5, 140, 2.2, '#c0c8d6'), rect(10, 58.5, 140, .6, '#fff', .5), rect(10, 60.7, 140, 17, '#48566e'), rect(10, 60.7, 140, 17, s.lin([(0, '#000', .25), (1, '#000', 0)])))
    for i in range(7):
        s.add(rect(12 + i * 20, 63, 17, 12.5, '#34425a', rx=.5), rect(18 + i * 20, 66, 5, .9, '#c0c8d6', rx=.4))
    s.add(ell(80, 79, 70, 1.6, '#000', .3))
    # grupo 1 (x 13..48): notebook + pasta
    s.add(laptop(16, 58.5, 16), folder(34, 58.5, 11, 8, '#a78a52'), rect(35, 52.6, 8, 1.4, '#f4efe0'))
    # grupo 2 (x 61..96): pastas + saco de evidência
    s.add(folder(64, 58.5, 12, 9, '#7a8aa6'), folder(66, 58.5, 12, 7, '#a78a52'), evid_bag(82, 58.5))
    # grupo 3 (109..144): pendrive em saco + relatório + caixa
    s.add(rect(112, 52.5, 14, 6, '#c9a46a', stroke='#000', sw=.1), rect(114, 54.4, 10, 1.8, '#f0e2c0'), evid_bag(128, 58.5), papers(138, 58.5, 8, 5))
    # caixas no chão
    for bx, by, n in ((16, 80, 3), (30, 80, 2)):
        for k in range(n):
            s.add(rect(bx, by + 6 - (k + 1) * 6, 12, 6, '#c9a46a', stroke='#000', sw=.1), rect(bx + 3, by - (k + 1) * 6 + 7.4, 6, 1.8, '#f0e2c0'))
    s.add(plant(150, 82, .9) if False else '')
    ceiling_panels(r, s, [(.2, .4), (.55, .75)], u0=.28, u1=.72, col='#e8f0ff')
    return s


def evid_bag(x, y):
    return (rect(x, y - 7, 9, 7, '#dfeaf2', .5, rx=.5, stroke='#aab8c8', sw=.2) + rect(x, y - 7, 9, 1.3, '#d8423a', .85)
            + rect(x + 2, y - 4.6, 5, 2.4, '#3a3d44', rx=.4) + rect(x + 2.6, y - 3.8, 1.4, .8, '#c9a04a'))


def corredor():
    s = Scene('co', 26)
    r = Room(s, 46, 24, 114, 70)
    r.shell('#d8cfb2', ('#cfc6a8', '#a89e82'), ('#a89e82', '#cfc6a8'), ('#f0eee4', '#d8d6c8'), '#c8bfa8', '#7a7466', grid=.18, nlines=8)
    for side in ('l', 'r'):
        q = r.lq if side == 'l' else r.rq
        s.add(poly(q(0, 1, .66, .92), '#6a8a82'), poly(q(0, 1, .64, .67), '#ece8dc'))
        s.add(poly(q(0, 1, .92, 1), '#4a4a42', .6))
        for k, (t0, t1) in enumerate([(.06, .24), (.34, .48), (.58, .68), (.78, .85)]):
            col = '#5a3a24' if (k + (side == 'l')) % 2 else '#6a4a2e'
            s.add(poly(q(t0, t1, .1, .94), '#2a1a10'), poly(q(t0 + .008, t1 - .008, .13, .94), col))
            s.add(poly(q(t0 + .02, t1 - .02, .2, .42), '#a8c4d0', .85))
            s.add(poly(q(t0 + .02, t1 - .02, .2, .42), '#fff', .0))
            s.add(poly(q((t0 + t1) / 2 - .02, (t0 + t1) / 2 + .02, .58, .6), '#d8b45a'))
            s.add(poly(q(t0 + .02, t1 - .02, .05, .09), '#2a3a5a'))
        for t0, t1, vv in [(.28, .32, .2), (.5, .54, .2)]:
            s.add(poly(q(t0, t1, .22, .46), '#8a6038'), poly(q(t0 + .004, t1 - .004, .24, .44), '#e8e4d8'), poly(q(t0 + .008, t1 - .008, .26, .3), '#d8423a', .7))
        for t0, t1 in [(.26, .35), (.51, .56)]:
            s.add(poly(q(t0, t1, .72, .74), '#3a3d44'), poly(q(t0 + .01, t1 - .01, .74, .86), '#2a4a7a', .0))
    # banco encostado (direita)
    s.add(poly(r.rq(.36, .5, .68, .72), '#2a3a5a'), poly(r.rq(.36, .5, .8, .84), '#2a3a5a'))
    # fundo: porta dupla e luz
    s.add(rect(66, 31, 28, 39, '#e8f0f4'), rect(66, 31, 28, 39, s.lin([(0, '#fff'), (1, '#cfe0ea')])))
    s.add(rect(68.5, 33.5, 11, 36.5, '#5a3a24'), rect(80.5, 33.5, 11, 36.5, '#5a3a24'), rect(70, 36, 8, 14, '#a8c4d0', .9), rect(82, 36, 8, 14, '#a8c4d0', .9), rect(78.6, 52, .8, 5, '#d8b45a'), rect(80.6, 52, .8, 5, '#d8b45a'))
    s.add(rect(66, 26, 28, 3.4, '#1f3a5a', rx=.5, stroke='#d8b45a', sw=.3), rect(72, 27.2, 16, .9, '#d8b45a', .8, rx=.4))
    s.add(poly(r.cq(.1, .3, .3, .7), '#fffbe8'), poly(r.cq(.4, .6, .3, .7), '#fffbe8'), poly(r.cq(.7, .86, .3, .7), '#fffbe8'))
    for t in (.2, .5, .78):
        s.glow(*r.C(t, .5), 18, 4, '#fff4d0', .35)
    s.add(ell(80, 90, 40, 5, '#fff', .08))
    return s


GERADORES = {'gabinete': gabinete, 'delegacia': delegacia, 'custodia': custodia, 'escritorio': escritorio, 'promotoria': promotoria, 'corredor': corredor}

if __name__ == '__main__':
    import sys
    for n, g in GERADORES.items():
        if len(sys.argv) > 1 and n not in sys.argv[1:]:
            continue
        (AQUI / f'{n}.svg').write_text(g().render(), encoding='utf-8')
        print(n)
