"""Gera parlatorio, juri, stf, praca (composições frontais). Pontos clicáveis: X=1.6*x%, Y=y%. Uso: python gen_antigos_c.py"""
from pathlib import Path

from lib_cen import *

AQUI = Path(__file__).resolve().parent


def checker(s, y0, c1, c2, vpy, n=10, rows=7, gloss=.1):
    out = [rect(0, y0, 160, 100 - y0, c1)]
    ys = [y0 + (100 - y0) * ((k / rows) ** 1.8) for k in range(rows + 1)]

    def xat(xb, y):
        return 80 + (xb - 80) * (y - vpy) / (100 - vpy)
    step = 38
    for ri in range(rows):
        ya, yb = ys[ri], ys[ri + 1]
        for ci in range(-n, n):
            if (ri + ci) % 2:
                xa0, xa1 = xat(80 + ci * step, ya), xat(80 + (ci + 1) * step, ya)
                xb0, xb1 = xat(80 + ci * step, yb), xat(80 + (ci + 1) * step, yb)
                out.append(poly([(xa0, ya), (xa1, ya), (xb1, yb), (xb0, yb)], c2))
    out.append(ell(80, y0 + (100 - y0) * .45, 70, (100 - y0) * .32, s.rad([(0, '#fff', gloss), (1, '#fff', 0)])))
    out.append(rect(0, y0, 160, 1.6, s.lin([(0, '#000', .35), (1, '#000', 0)])))
    return ''.join(out)


def telefone_parede(x, y):
    return (rect(x, y, 8, 13, '#1c1e22', rx=1.2) + rect(x + 1, y + 1, 6, 3.6, '#2a2d33', rx=.6) + rect(x + 1.4, y + 5.6, 5.2, 4.4, '#33363c', rx=.5)
            + ''.join(circ(x + 2.4 + (i % 3) * 1.6, y + 6.6 + (i // 3) * 1.4, .35, '#8a8f98') for i in range(6))
            + path(f'M{f(x-.4)} {f(y+2)}Q{f(x-3)} {f(y+8)} {f(x+1)} {f(y+13.6)}', stroke='#2a2d33', sw=.5))


def parlatorio():
    s = Scene('pa', 31)
    s.add(rect(0, 0, 160, 100, s.lin([(0, '#8a9098'), (1, '#6c727a')])))
    # tijolos aparentes cinza
    for ry in range(0, 66, 4):
        s.add(line(0, ry + 4, 160, ry + 4, '#000', .2, .16))
        for rx in range((ry // 4 % 2) * 4, 160, 8):
            s.add(line(rx, ry, rx, ry + 4, '#000', .2, .12))
    s.add(rect(0, 0, 160, 5, '#3a3e44'), rect(0, 5, 160, .6, '#d8dde2', .45))
    for x in (6, 58, 100):
        s.add(rect(x, 0, 10, 3, '#fffbe8', .9, rx=.6))
    s.glow(80, 4, 40, 9, '#fff4d0', .3)
    # placa genérica central
    s.add(rect(54, 5.5, 52, 5, '#1f3a5a', rx=.8, stroke='#d8b45a', sw=.5))
    for i in range(7):
        s.add(circ(60 + i * 6.7, 8, .7, '#d8b45a', .8))
    # cabines (x 8,48,88,128; w 32; y 12..50)
    for k, cx in enumerate((8, 48, 88, 128)):
        s.add(rect(cx - 2, 11, 36, 44, '#2a2d33', rx=1))
        s.add(rect(cx, 13, 32, 37, s.lin([(0, '#1c2c40'), (1, '#0e1824')])))
        # interior: parede de fundo + cadeira escura
        s.add(rect(cx + 1, 14, 30, 35, s.lin([(0, '#2a3e56'), (1, '#16222f')])))
        s.add(rect(cx + 20, 34, 9, 10, '#10161e', rx=1.5), rect(cx + 21, 44, 7, 4, '#10161e', rx=.8))
        # vidro: reflexos
        s.add(poly([(cx + 3, 13), (cx + 11, 13), (cx + 3, 40)], '#fff', .1), poly([(cx + 14, 13), (cx + 17, 13), (cx + 7, 50), (cx + 4, 50)], '#fff', .06))
        s.add(rect(cx, 13, 32, 37, 'none', stroke='#6a8aa8', sw=.4))
        s.add(rect(cx - 2, 50, 36, 5, '#3a3e44'), rect(cx - 2, 50, 36, 1.2, '#b8bec6'), rect(cx + 6, 52, 20, .6, '#000', .3))
        # fone no vidro, ao lado
        s.add(telefone_parede(cx + 9.6, 35.5) if k in (0, 1, 2, 3) and False else '')
        s.add(rect(cx + 10, 36, 8, 12, '#1c1e22', rx=1.2), rect(cx + 11, 37, 6, 3.6, '#2a2d33', rx=.6), rect(cx + 11.4, 41.6, 5.2, 4.4, '#33363c', rx=.5))
        for i in range(6):
            s.add(circ(cx + 12.4 + (i % 3) * 1.6, 42.6 + (i // 3) * 1.4, .35, '#8a8f98'))
        s.add(path(f'M{f(cx+10)} {f(40)}Q{f(cx+6)} {f(45)} {f(cx+11)} {f(49)}', stroke='#2a2d33', sw=.5))
        s.add(rect(cx + 8, 49.4, 8, 1.2, '#1c1e22', rx=.5))
    # papel colado na cabine 2 (57.6..72, 41..50)
    s.add(poly([(58.6, 41.4), (71, 41), (71.6, 49.4), (58.2, 49.8)], '#f4efe0', stroke='#000', sw=.1), rect(60, 43.4, 9, .5, '#6a6a6a', .6), rect(60, 45, 8, .5, '#6a6a6a', .6), rect(60, 46.6, 5, .5, '#c33', .8))
    s.add(rect(63, 40.6, 2.4, 1, '#d8b45a', .8))
    # pilar central
    s.add(rect(80.6, 11, 6.8, 44, '#5a6068'), rect(81.6, 11, 1.2, 44, '#fff', .12))
    # piso + faixa amarela
    s.add(rect(0, 55, 160, 45, s.lin([(0, '#3a3e44'), (1, '#24272b')])))
    s.add(floor_persp(s, 62, '#50555c', '#2a2d31', vpy=40, n=14, m=6, gloss=.14))
    s.add(rect(0, 60, 160, 2, '#c9a82a'), rect(0, 60, 160, .5, '#fff', .3))
    # balcão do livro de visitas (10..20% => x 16..32, y 56..64)
    s.add(rect(12, 55.6, 30, 5, '#5a3a24'), rect(11, 54.6, 32, 1.4, '#a87848'))
    s.add(ell(27, 82, 17, 1.6, '#000', .3), rect(14, 60.6, 26, 21, '#3a2616'), rect(15.5, 62.6, 23, 17, '#5a3a24', rx=.6), rect(25, 66, 4, .9, '#d8b45a', rx=.4))
    s.add(poly([(15, 55), (21, 52), (27, 53.5), (33, 52), (39, 55)], '#fff', .0))
    s.add(open_book(16, 56.6, 16, 3), rect(34, 55.6, 2, 1, '#2a2d33'), line(34.4, 55.6, 34.8, 53, '#c33', .35))
    # banquinhos
    for bx in (60, 100, 138):
        s.add(ell(bx, 88, 6.4, 1.2, '#000', .3), ell(bx, 76, 5.2, 1.5, '#8a8f98'), rect(bx - 5.2, 76, 10.4, 2.4, '#5a6068'), rect(bx - .6, 78.4, 1.2, 9, '#4a4f56'), ell(bx, 88, 4, .8, '#4a4f56'))
    return s


def juri():
    s = Scene('jr', 32)
    # parede de madeira escura com almofadas
    s.add(rect(0, 0, 160, 100, s.lin([(0, '#6a4630'), (1, '#4a2e1c')])))
    for i in range(0, 160, 10):
        s.add(rect(i + 1, 5, 8, 50, '#000', .1, rx=.4), rect(i + 1.6, 5.6, 6.8, 48.8, 'none', stroke='#c9955c', sw=.18, o=.35))
    s.add(rect(0, 0, 160, 4, '#2a1a10'), rect(0, 4, 160, .7, '#d8b45a', .6), rect(0, 4.7, 160, 6, s.lin([(0, '#000', .3), (1, '#000', 0)])))
    # colunas de mármore
    for x in (2, 150):
        s.add(rect(x, 4, 8, 52, s.lin([(0, '#d8d4c8'), (.5, '#f4f0e6'), (1, '#b8b4a8')], horiz=True)), rect(x - 1, 4, 10, 2.4, '#e8e4d8'), rect(x - 1, 53.6, 10, 2.4, '#e8e4d8'))
        for k in range(1, 4):
            s.add(line(x + k * 2, 6, x + k * 2, 54, '#000', .2, .1))
    s.add(emblem(s, 80, 17, 9, bg='#2a1a12'))
    # monitor grande (esq): 13..64 x 20..48
    s.add(rect(12, 19, 53, 30, '#16181c', rx=1.4, stroke='#8a8f98', sw=.5), rect(13.6, 20.6, 49.8, 26.8, s.lin([(0, '#243a54'), (1, '#10202e')])))
    s.add(circ(38.5, 33, 5, 'none', stroke='#cfe0ee', sw=.5, o=.7), poly([(37, 30.5), (37, 35.5), (41.4, 33)], '#cfe0ee', .8))
    s.add(rect(16, 42.6, 44, 1.2, '#cfe0ee', .5, rx=.5), rect(16, 42.6, 18, 1.2, '#4a90c8', .9, rx=.5), rect(16, 22.4, 12, 1.6, '#cfe0ee', .4, rx=.4))
    # armário/estante do oficial (118..154 x 22..44)
    s.add(shelf_unit(s, 120, 24, 30, 19, 2, wood='#2a1a10', back='#1a100a', plank='#8a6038', pal=['#2a3a5a', '#5a2a2a', '#2a4a3a', '#6a5a3a']))
    s.add(rect(118, 43.6, 34, 2, '#8a6038'))
    # balaustrada do júri + cadeiras
    for i in range(5):
        cx = 67 + i * 10.4
        s.add(rect(cx, 40, 8, 13, '#7a1f26', rx=2), rect(cx + 1, 41, 6, 11, '#9a2a32', rx=1.6), rect(cx + 3.6, 41.6, .5, 10, '#000', .25), rect(cx - 1, 50.4, 10, 3, '#5a161c', rx=1))
    s.add(rect(62, 53.2, 56, 2.4, '#8a6038', rx=.5), rect(62, 53.2, 56, .6, '#fff', .3))
    for i in range(20):
        s.add(rect(63 + i * 2.8, 55.6, .9, 4.4, '#5a3a22'))
    s.add(rect(62, 60, 56, 1.4, '#3a2616'))
    # piso xadrez
    s.add(checker(s, 66, '#d9d4c6', '#4a4a50', vpy=40))
    s.add(rect(0, 64.4, 160, 2.6, '#2a1a10'), rect(0, 64.4, 160, .6, '#c9955c', .6))
    # mesa do centro-direita (envelope) 80..128 x 56..80
    s.add(desk(s, 80, 66, 48, 14, top='#8a6038', body='#5a3a22', dark='#2a1a10', drawers=3))
    s.add(rect(92, 61, 14, 5, '#f4efe0', stroke='#000', sw=.1), poly([(92, 61), (99, 64.2), (106, 61)], 'none', stroke='#aaa', sw=.2), circ(99, 64, 1.2, '#c33'))
    s.add(papers(112, 65.6, 8, 3))
    # mesinha esquerda (celular lacrado) 19..58 x 62..82
    s.add(desk(s, 20, 72, 36, 12, top='#8a6038', body='#5a3a22', dark='#2a1a10', drawers=2))
    s.add(evid_bag2(34, 71))
    s.add(pendant(s, 40, 4, 12, 58, glow='#ffe9b0'), pendant(s, 130, 4, 12, 58, glow='#ffe9b0'))
    return s


def evid_bag2(x, y):
    return (rect(x, y - 7, 10, 7, '#dfeaf2', .5, rx=.5, stroke='#aab8c8', sw=.2) + rect(x, y - 7, 10, 1.3, '#d8423a', .85)
            + rect(x + 3, y - 5.2, 4, 3.8, '#2a2d33', rx=.6) + rect(x + 3.6, y - 4.6, 2.8, 2.2, '#4a90c8'))


def stf():
    s = Scene('sf', 33)
    s.add(rect(0, 0, 160, 100, s.lin([(0, '#e6d8b4'), (1, '#c8b88e')])))
    for i in range(0, 160, 5):
        s.add(rect(i, 6, 2.2, 54, '#000', .035))
    # painel central creme com rodapé dourado
    s.add(rect(0, 0, 160, 5, '#3a2616'), rect(0, 5, 160, .8, '#d8b45a', .8), rect(0, 5.8, 160, 8, s.lin([(0, '#000', .3), (1, '#000', 0)])))
    # colunas laterais em madeira
    for x0, x1 in ((0, 38), (122, 160)):
        s.add(rect(x0, 5, x1 - x0, 55, s.lin([(0, '#9a7048'), (1, '#6a4a2c')])))
        for i in range(int((x1 - x0) / 4)):
            s.add(rect(x0 + i * 4, 5, 2, 55, '#000', .1))
    s.add(rect(38, 5, 1.4, 55, '#d8b45a', .8), rect(120.6, 5, 1.4, 55, '#d8b45a', .8))
    # janela para a praça (13..45 x 16..50)
    s.add(sq_window(s, 13, 17, 30, 32, sky=('#7ab4e8', '#f2f6fa'), frame='#d8b45a', cols=2, rows=2))
    s.add(rect(14, 40, 28, 9, '#7a9a5a', .8), rect(14, 44, 28, 5, '#5a7a42'))
    s.add(curtain(s, 3, 9, 8, 54, '#7a1f2a'), curtain(s, 44, 7, 8, 54, '#7a1f2a', side='l'))
    # estante do código (106..131 x 42..62)
    s.add(shelf_unit(s, 126, 24, 0, 0, 1) if False else '')
    s.add(emblem(s, 80, 17, 9.5, bg='#243a6a', gold='#d8b45a', ring='#f0d27a'))
    for x in (56, 104):
        s.add(pendant(s, x, 5, 14, 50, glow='#ffe9b0'))
    # cadeiras (7) atrás da bancada
    xs = [46 + i * 8.7 for i in range(7)]
    for i, cx in enumerate(xs):
        hh = 17 if i == 3 else 14
        top = 53 - hh - (3 if i == 3 else 0)
        s.add(rect(cx - 1, top, 8, hh + 3, '#1e2230', rx=2.6), rect(cx, top + 1, 6, hh + 1, '#2c3348', rx=2), rect(cx + 3.2, top + 1.6, .4, hh - 1, '#000', .35))
    # bancada curva
    s.add(ell(75, 64, 38, 2.4, '#000', .3))
    s.add(path('M42 53Q75 47 108 53V68Q75 62 42 68Z', fill=s.lin([(0, '#7a4a28'), (1, '#4a2a16')])))
    s.add(path('M42 53Q75 47 108 53V55.4Q75 49.4 42 55.4Z', fill='#c9955c'))
    for i in range(7):
        cx = 46 + i * 8.7 + 3
        s.add(rect(cx - 2.6, 58.4, 5.2, 4.8, '#4a2a16', rx=.4, stroke='#d8b45a', sw=.25), rect(cx - 1.4, 60, 2.8, .8, '#d8b45a', rx=.4))
        s.add(rect(cx - .3, 48.6, .6, 3, '#222'), circ(cx, 48.4, 1, '#333'))
    # estante à direita (108..132 x 42..62)
    s.add(shelf_unit(s, 110, 42, 22, 20, 3, wood='#4a2e1a', back='#1c110a', plank='#9a6a3a'))
    # carpete vinho
    s.add(rect(0, 68, 160, 32, s.lin([(0, '#5a1a26'), (1, '#3a0f18')])))
    s.add(floor_persp(s, 68, '#6a1e2c', '#3a0f18', vpy=44, n=14, m=6, gloss=.1, grid=.2))
    s.add(rect(0, 66.6, 160, 1.6, '#d8b45a', .8), rect(0, 68.2, 160, 1, '#000', .25))
    # mesa de apoio (48..70 x 52..66) com notebook
    s.add(desk(s, 50, 66, 22, 12, top='#b08a5a', body='#6a4a30', dark='#2e1e12', drawers=1))
    s.add(laptop(55, 63, 10), papers(66, 63, 5, 3))
    # pódio esquerdo e direito baixo
    return s


def praca():
    s = Scene('pz', 34)
    s.add(rect(0, 0, 160, 70, s.lin([(0, '#6a76b0'), (.55, '#e89aa0'), (1, '#f6c48a')])))
    s.glow(110, 52, 60, 20, '#ffd8a0', .35)
    # nuvens
    for cx, cy, w in ((20, 12, 20), (128, 18, 26), (84, 8, 16)):
        s.add(ell(cx, cy, w / 2, 2.4, '#fff', .35), ell(cx + w * .2, cy - 1.2, w * .3, 2, '#fff', .35))
    # skyline distante
    s.add(skyline(0, 160, 62, cols=('#6a6a98', '#7a78a4', '#5a5a88'), lit='#ffe0a0', seed=4, hmax=26, hmin=10))
    s.add(rect(0, 56, 160, 14, '#6a6a98', .0))
    # árvores
    for tx in (146, 12):
        s.add(rect(tx - 1, 50, 2, 20, '#5a3a22'), circ(tx, 44, 9, '#3a6a4a'), circ(tx - 5, 49, 6, '#2f5a3e'), circ(tx + 5, 48, 6.6, '#3f7a52'))
    # Fórum: degraus, colunas, frontão
    s.add(poly([(48, 68), (112, 68), (108, 63), (52, 63)], '#d6cfc0'), poly([(52, 63), (108, 63), (105, 59), (55, 59)], '#e4ded0'))
    s.add(rect(54, 24, 52, 35, '#e8e2d4'), rect(54, 24, 52, 35, '#000', .06))
    s.add(rect(56, 29, 48, 28, '#3a3a58'), rect(72, 37, 16, 20, '#2a1a10'), rect(73, 38, 7, 19, '#5a3a24'), rect(80, 38, 7, 19, '#5a3a24'), rect(78, 46, 1, 4, '#d8b45a'), rect(81, 46, 1, 4, '#d8b45a'))
    for i in range(8):
        cx = 56 + i * 6.3
        if 70 < cx < 88:
            continue
        s.add(rect(cx, 25, 3.4, 33.5, s.lin([(0, '#f2eee2'), (1, '#c8c2b2')], horiz=True)), rect(cx - .4, 24.4, 4.2, 1.6, '#fff'), rect(cx - .4, 56.6, 4.2, 2, '#fff'))
    s.add(rect(52, 21, 56, 4, '#f2eee2'), rect(52, 24, 56, 1, '#000', .15))
    s.add(poly([(50, 21), (110, 21), (80, 7)], '#ece6d8'), poly([(54, 20), (106, 20), (80, 9.2)], '#d8d2c2'))
    s.add(emblem(s, 80, 16, 4.2, bg='#243a6a'))
    # faixa na fachada (58..106 x 14..36 → pendurada)
    s.add(rect(58, 26, 48, 9, '#f6f0dc', rx=.4, stroke='#a8a090', sw=.2), rect(61, 28.4, 24, 1.8, '#d8423a', .9, rx=.6), rect(61, 31.6, 38, 1.2, '#2a4a8a', .8, rx=.5))
    s.add(line(58, 26, 56, 23.6, '#7a6a52', .3), line(106, 26, 108, 23.6, '#7a6a52', .3))
    # bandeira no mastro (22..54 x 8..30)
    s.add(rect(23, 10, .9, 58, '#c9a04a'), circ(23.45, 9.4, 1.3, '#e8c46a'))
    s.add(path('M24 11.4Q34 9 44 12Q52 15 52 15V28Q44 25 34 27Q28 28.4 24 27Z', fill='#2f6a4a'))
    s.add(path('M24 19.4Q34 17 52 21V24Q34 21 24 23Z', fill='#f0e8d0', o=.9), circ(38, 21, 3, '#d8b45a', .9))
    # praça: piso em perspectiva
    s.add(rect(0, 68, 160, 32, '#9a9488'))
    s.add(floor_persp(s, 68, '#b4ad9e', '#7a7468', vpy=56, n=14, m=7, gloss=.16, grid=.16))
    s.add(rect(0, 67.6, 160, 1.6, '#6a6458'))
    # carro de som (10..52 x 30..60) com grade na frente (y 54..80)
    s.add(ell(30, 64, 23, 2, '#000', .3))
    s.add(rect(10, 40, 40, 20, '#d8d4cc', rx=1.6), rect(10, 40, 40, 20, s.lin([(0, '#fff', .2), (1, '#000', .15)])), rect(10, 55, 40, 2, '#2a4a8a'))
    s.add(poly([(34, 41), (49, 41), (50, 51), (34, 51)], '#9ac4e0'), rect(12, 42, 18, 12, '#3a3e44', rx=.6))
    for k in range(3):
        s.add(rect(14 + k * 5.4, 44, 4, 8, '#555', rx=.4), circ(16 + k * 5.4, 46.4, 1, '#222'), circ(16 + k * 5.4, 50, 1.4, '#222'))
    s.add(rect(11, 30.6, 26, 9.4, '#2a2d33', rx=.8), circ(18, 35.2, 3.2, '#444'), circ(18, 35.2, 1.4, '#222'), circ(30, 35.2, 3.2, '#444'), circ(30, 35.2, 1.4, '#222'))
    for wx in (20, 42):
        s.add(circ(wx, 60.4, 3.2, '#222'), circ(wx, 60.4, 1.4, '#888'))
    for gx in range(10, 52, 14):
        s.add(rect(gx, 64, 12, 12, 'none', stroke='#9aa0a8', sw=.6), rect(gx, 64, 12, 12, '#fff', .05))
        for k in range(1, 4):
            s.add(line(gx + k * 3, 64, gx + k * 3, 76, '#9aa0a8', .35))
        s.add(rect(gx - .4, 75.4, 1.2, 2, '#6a7078'), rect(gx + 11.2, 75.4, 1.2, 2, '#6a7078'))
    # mesa de distribuição (112..147 x 50..74) com tenda
    s.add(rect(112, 40, .8, 24, '#8a8f98'), rect(145.2, 40, .8, 24, '#8a8f98'))
    s.add(path('M108 41Q129 35 150 41L146 47H112Z', fill='#f2eee2'), path('M108 41Q129 35 150 41', stroke='#d8423a', sw=.8))
    for k in range(5):
        s.add(poly([(112 + k * 7, 47), (119 + k * 7, 47), (119 + k * 7 + 0, 47)], '#d8423a', .0))
    s.add(ell(130, 76, 20, 1.6, '#000', .3), rect(114, 62, 32, 2.2, '#c9a46a'), rect(116, 64, 28, 12, '#6a4a30'), rect(116, 64, 28, 12, '#000', .15))
    s.add(rect(118, 58, 10, 4, '#f4efe0'), rect(119, 56, 10, 2.4, '#e4dcc4'), rect(132, 57, 8, 5, '#c9a46a'), rect(134, 59, 4, 1.6, '#f0e2c0'))
    for lx in (123, 129, 135):
        s.add(rect(lx, 70, 3, 5, '#f4efe0', .0))
    # postes de luz
    for lx in (68, 96):
        s.add(rect(lx, 40, .8, 28, '#2a2d33'), rect(lx - 1.4, 38, 3.6, 2, '#2a2d33', rx=.6), circ(lx + .4, 38.6, 2.4, '#ffe9b0', .9))
        s.glow(lx + .4, 39, 8, 6, '#ffe9b0', .35)
    return s


GERADORES = {'parlatorio': parlatorio, 'juri': juri, 'stf': stf, 'praca': praca}

if __name__ == '__main__':
    import sys
    for n, g in GERADORES.items():
        if len(sys.argv) > 1 and n not in sys.argv[1:]:
            continue
        (AQUI / f'{n}.svg').write_text(g().render(), encoding='utf-8')
        print(n)
