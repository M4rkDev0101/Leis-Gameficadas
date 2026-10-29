import random
from cen_lib import *


def garagem_stf():
    s = "ga"
    d = (LG("cl" + s, [(0, "#1c1214"), (1, "#3a2428")]) + LG("wl" + s, [(0, "#3a2a2c"), (1, "#5a3a3a")]) + LG("fl" + s, [(0, "#3a2c2e"), (1, "#1a1012")]) +
         RG("rd" + s, [(0, "#ff4a3a", .6), (1, "#ff4a3a", 0)]) + LG("rp" + s, [(0, "#6a4a46"), (1, "#3a2828")]) + RG("dl" + s, [(0, "#d8c0a0", .35), (1, "#d8c0a0", 0)]))
    VX0, VX1, TY, BY = 56, 104, 38, 62
    b = [R(0, 0, 160, 100, "#120a0c"),
         PG([(0, 0), (160, 0), (VX1, TY), (VX0, TY)], f"url(#cl{s})"),
         PG([(0, 0), (VX0, TY), (VX0, BY), (0, 90)], f"url(#wl{s})"), PG([(160, 0), (VX1, TY), (VX1, BY), (160, 90)], f"url(#wl{s})"),
         PG([(0, 90), (VX0, BY), (VX1, BY), (160, 90), (160, 100), (0, 100)], f"url(#fl{s})")]
    # rampa rachada ao fundo, subindo
    b += [R(VX0, TY, VX1 - VX0, BY - TY, "#2a1c1e"),
          PG([(VX0 + 6, BY), (VX1 - 6, BY), (VX1 - 12, TY + 3), (VX0 + 12, TY + 3)], f"url(#rp{s})"),
          PG([(VX0 + 12, TY + 3), (VX1 - 12, TY + 3), (VX1 - 14, TY - 1), (VX0 + 14, TY - 1)], "#d8b890", .8), R(VX0 + 14, TY - 1.8, VX1 - VX0 - 28, 1.2, "#f0e0c0", .6)]
    for (x1, y1, x2, y2) in ((74, 58, 80, 52), (80, 52, 78, 47), (78, 47, 84, 43), (84, 43, 83, 41), (90, 60, 88, 55), (88, 55, 92, 50)):
        b.append(L(x1, y1, x2, y2, "#0a0506", .5)); b.append(L(x1 + .5, y1, x2 + .5, y2, "#c8a888", .12, .5))
    for k in range(4): b.append(L(VX0 + 6 + k * 3, BY, VX0 + 12 + k * 2, TY + 3, "#1a1012", .2, .5))
    # pilares em perspectiva, base zebrada
    def pil(xl, yt, yb, w, side):
        x = xl if not side else 160 - xl - w
        return [R(x, yt, w, yb - yt, "#4a3638"), R(x + w * .72, yt, w * .28, yb - yt, "#000", .25), R(x, yt, w * .12, yb - yt, "#fff", .06),
                R(x - .2, yb - w * .9, w + .4, w * .9, "#d8b030"), R(x - .2, yb - w * .9, w + .4, w * .9, "#000", .1)]
    for (xl, w, ytop, ybot) in ((0, 15, 0, 100), (22, 9, 8, 80), (38, 5.5, 19, 69), (48, 3.2, 28.4, 64.2)):
        for side in (0, 1):
            o = pil(xl, ytop, ybot, w, side)
            b += o
            x = xl if not side else 160 - xl - w
            for k in range(3):
                b.append(PG([(x - .2 + k * w * .35, ybot - w * .9), (x - .2 + k * w * .35 + w * .17, ybot - w * .9), (x - .2 + k * w * .35 + w * .17 - w * .15, ybot), (x - .2 + k * w * .35 - w * .15, ybot)], "#18100c", .8))
    # canos e dutos no teto
    b += [L(0, 6, 160, 6, "#5a4448", 1.6), L(14, 14, 146, 14, "#4a3a3c", 1.2)]
    for x0 in (30, 60, 100, 130): b.append(R(x0, 5, 1.2, 3.6, "#2a1c1e"))
    for k in range(6):
        b.append(PG([(80 - 18 + k * 7, TY), (80 - 18 + k * 7 + .5, TY), (60 + k * 8, 0), (59 + k * 8, 0)], "#000", .1))
    # luzes de emergencia (vermelhas) e luz de teto quebrada
    for (lx, ly, sc) in ((22, 12, 1.3), (138, 12, 1.3), (62, 31, .7), (98, 31, .7), (80, 26, .5)):
        b += [C(lx, ly, 6 * sc, f"url(#rd{s})"), R(lx - 2.2 * sc, ly - .8 * sc, 4.4 * sc, 1.6 * sc, "#ff7a6a", rx=.4), C(lx, ly, 1 * sc, "#fff2ee")]
    b.append(PG([(70, 0), (90, 0), (86, 40), (74, 40)], f"url(#dl{s})"))
    # chao: faixas de vaga e rachadura
    b.append(pfloor(BY, 80, 38, "#000", .45, 14, 6, span=380))
    for k in range(4):
        y0 = 70 + k * 7; b.append(PG([(14 + k * 4, y0 + 1), (16 + k * 4, y0 + 1), (6 + k * 7 * 0, y0 + 9), (0, y0 + 9)], "#c8a040", .5))
    b += [PATH("M62 100 L66 92 L63 86 L70 80 L68 74", st="#080406", sw=.5), PATH("M120 100 L114 92 L118 85 L112 78", st="#080406", sw=.4)]
    b += [PG([(0, 100), (160, 100), (160, 96), (0, 96)], "#ff5040", .06), E(80, 74, 36, 4, "#ff4a3a", .08)]
    # carros parados (silhuetas escuras) e entulho
    b += [car_side(34, 62, 1.5, "#241a1c", glass="#3a2e34", wheel="#08050a", hub="#4a3a3c"), car_side(130, 66, 1.4, "#1c1618", glass="#3a2e34", wheel="#08050a", hub="#4a3a3c")]
    # poeira caindo
    r = random.Random(11)
    for i in range(70):
        px = r.uniform(0, 160); py = r.uniform(4, 96)
        b.append(R(px, py, .25, r.uniform(1.4, 4), "#e8d0b0", r.uniform(.15, .5)))
    for i in range(36):
        b.append(C(r.uniform(66, 96), r.uniform(6, 80), r.uniform(.2, .5), "#f0dcc0", r.uniform(.2, .55)))
    b += [PG([(92, 0), (100, 0), (104, 28), (94, 28)], "#d8c0a0", .1), E(60, 98, 4, 1, "#3a2a2c"), E(66, 98.4, 2.6, .8, "#4a3434")]
    for i in range(9): b.append(PG([(120 + i * 2.6, 99), (121 + i * 2.6, 96 - (i % 3)), (123 + i * 2.6, 99)], "#4a3434", .9))
    return wrap(s, d, "".join(b), .75, ("#ff3a20", .05))


def esplanada_ministerios():
    s = "es"
    d = (LG("sk" + s, [(0, "#78b0dc"), (.6, "#d4e4ec"), (1, "#f6eed0")]) + LG("gr" + s, [(0, "#c0b078"), (1, "#a89a60")]) +
         LG("rd" + s, [(0, "#6a6a6e"), (1, "#4a4a50")]) + LG("bl" + s, [(0, "#eceadc"), (1, "#cfcbb8")]) + RG("sn" + s, [(0, "#fff8d8", .8), (1, "#fff8d8", 0)]))
    b = [R(0, 0, 160, 100, f"url(#sk{s})"), C(130, 12, 22, f"url(#sn{s})"), C(130, 12, 5, "#fffbe8")]
    b += [E(40, 14, 14, 1.4, "#fff", .5), E(90, 24, 10, 1.2, "#fff", .4)]
    # fileira de ministerios identicos
    for k in range(6):
        x0 = -4 + k * 28
        b += [R(x0, 29, 25, 16, f"url(#bl{s})"), R(x0, 29, 25, 1.2, "#fff"), R(x0, 44, 25, 1, "#8a8672", .5), R(x0 + 19, 29, 6, 16, "#000", .08)]
        for r_ in range(6):
            for c_ in range(8):
                b.append(R(x0 + 1 + c_ * 3, 31.4 + r_ * 2.1, 2.2, 1.1, "#5a7a96", .85))
    b.append(R(0, 44, 160, 2, "#d8d2bc"))
    # gramado seco
    b += [R(0, 46, 160, 22, f"url(#gr{s})")]
    r = random.Random(4)
    for i in range(140): b.append(R(r.uniform(0, 160), r.uniform(47, 66), r.uniform(.6, 2), .22, "#8a7a40", .5))
    # calcada e pista
    b += [R(0, 66, 160, 6, "#d4d0c0"), R(0, 66, 160, .5, "#a8a490"), R(0, 72, 160, 28, f"url(#rd{s})"), R(0, 72, 160, 1.4, "#9a9a9a")]
    for k in range(7): b.append(R(k * 26 + 4, 88, 14, 1.2, "#e8e0b0", .85))
    b += [R(0, 98.6, 160, 1.4, "#fff", .15), E(80, 84, 70, 4, "#fff", .06)]
    # vulto de transito esparso ao fundo
    b += [car_side(26, 64.4, .5, "#c8c4b8", glass="#6a7a8a"), car_side(118, 68, .45, "#7a3a2a", glass="#6a7a8a")]
    # muro com cartaz antigo (4,45,30,27)
    mx, my, mw, mh = P(4, 45, 30, 27)
    b += [R(mx, my, mw, mh, "#b8b09a"), R(mx - .6, my - 1.2, mw + 1.2, 1.4, "#cfc8b2"), R(mx, my + mh - 1, mw, 1, "#8a8470", .6)]
    for k in range(5): b.append(L(mx, my + 4 + k * 4.6, mx + mw, my + 4 + k * 4.6, "#8a8470", .15, .5))
    for k in range(7): b.append(L(mx + k * mw / 7, my, mx + k * mw / 7, my + mh, "#8a8470", .12, .4))
    b += [PG([(mx + 8, my + 4), (mx + 30, my + 3), (mx + 31, my + 20), (mx + 9, my + 21)], "#d8c890"), PG([(mx + 8, my + 4), (mx + 30, my + 3), (mx + 30, my + 5.4), (mx + 8, my + 6.2)], "#c0392b", .85),
          PG([(mx + 25, my + 3.2), (mx + 30, my + 3), (mx + 31, my + 20), (mx + 28, my + 20), (mx + 27, my + 10)], "#e6dcb0")]
    for k in range(4): b.append(R(mx + 11, my + 8 + k * 2.4, 12 - (k % 2) * 3, .5, "#7a6a48", .7))
    b += [PG([(mx + 9, my + 20.4), (mx + 16, my + 17), (mx + 14, my + 21)], "#b8a468"), R(mx + 1, my + 2, 4, 3, "#cfc08a", .8), R(mx + 3, my + 13, 4, 2, "#a89c70", .6)]
    for k in range(5): b.append(PATH(f"M{f(mx+3+k*5.4)} {f(my+mh)} q-.4 -2 .4 -3", st="#8a8a50", sw=.4))
    # guiche de protocolo do anexo (39,29,29,28)
    gx, gy, gw, gh = P(39, 29, 29, 28)
    b += [R(gx - 1, gy + gh - 1, gw + 2, 2, "#b8b4a0"), R(gx, gy + 5, gw, gh - 5, f"url(#bl{s})"), R(gx - 1.6, gy + 2.6, gw + 3.2, 3, "#9a9686"), R(gx - 1.6, gy + 2.2, gw + 3.2, .6, "#fff"),
          R(gx + 3, gy + 8, gw * .6, gh - 15, "#2a3a46"), R(gx + 3, gy + 8, gw * .6, gh - 15, "#9ec4dc", .55), R(gx + 3, gy + 16, gw * .6, 1.3, "#6a6a66"),
          R(gx + 2.2, gy + 8, 6, gh - 14, "#000", .0)]
    for k in range(6): b.append(R(gx + 4 + k * 5, gy + 8, .45, 8, "#3a3e44"))
    b += [R(gx + gw * .72, gy + 8, gw * .22, gh - 13, "#6a4a30", rx=.4), R(gx + gw * .74, gy + 10, gw * .18, 7, "#2a2a28", .5), C(gx + gw * .74 + 1, gy + 21, .5, "#d9b86a"),
          R(gx + 3, gy + 6.4, gw * .6, 1.2, "#c9a04a", .0), R(gx + gw * .3, gy - 1.6, gw * .4, 3, "#2a5a8a", rx=.3), R(gx + gw * .34, gy - .8, gw * .32, .5, "#e8e0c8", .8), PG([(gx, gy + 5), (gx + gw, gy + 5), (gx + gw - 2, gy + 2.6), (gx + 2, gy + 2.6)], "#fff", .3)]
    # carro estacionado (62,61,29,19)
    cx, cy, cw, ch = P(62, 61, 29, 19)
    b += [car_side(cx + cw / 2, cy + ch - 3.4, 2.5, "#5a6a76", glass="#b8cfdc"), R(cx + cw / 2 - 18, cy + ch - 5.4, 36, .4, "#fff", .12)]
    b += [R(cx + 5, cy + 2, 40, 1.2, "#fff", .0)]
    # ondulacao de calor sobre a pista/gramado
    for k in range(5):
        y0 = 47 + k * 5
        b.append(PATH(f"M0 {y0} q10 -1.2 20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0", st="#fff", sw=.35, o=.12))
    b.append(R(0, 44, 160, 6, "#fff8d8", .22))
    for xx in (50, 108, 150): b += [PATH(f"M{xx} 66 q-2 -3 -1 -5", st="#8a8a50", sw=.5), PATH(f"M{xx} 66 q2 -3 1 -5", st="#8a8a50", sw=.5)]
    return wrap(s, d, "".join(b), .25, ("#fff0b0", .07))


def secretaria_turma():
    s = "st"
    d = (LG("wl" + s, [(0, "#d6d2c0"), (1, "#c2bea8")]) + LG("fl" + s, [(0, "#8a8a82"), (1, "#6a6a66")]) + LG("ck" + s, [(0, "#c8935a"), (1, "#a8733a")]) +
         RG("mn" + s, [(0, "#fff0c0", .35), (1, "#fff0c0", 0)]) + LG("pn" + s, [(0, "#1a2a3a"), (1, "#0e1824")]))
    b = [R(0, 0, 160, 100, f"url(#wl{s})"), R(0, 0, 160, 3, "#8a8672"), R(0, 66, 160, 8, "#5a6a62"), R(0, 66, 160, .6, "#e8e2cc"),
         R(0, 74, 160, 26, f"url(#fl{s})"), pfloor(74, 80, 52, "#4a4a46", .45, 18, 5)]
    for i in range(0, 160, 20): b.append(R(i, 3, .5, 63, "#000", .1))
    # prateleira de arquivo no alto (caixas)
    b += [R(0, 5, 160, 1, "#6a6652")]
    for k in range(40):
        rr = random.Random(k)
        b += [R(k * 4 + .3, 7 + rr.uniform(0, 1), 3.2, 4.6, rr.choice(["#c8b078", "#b8a468", "#d6c288", "#a89868"]), st="#6a5a38", sw=.12), R(k * 4 + 1, 9.4, 1.6, 1.2, "#efe6cf", .8)]
    b.append(R(0, 12.8, 160, .8, "#6a6652"))
    # quadro eletronico de escala (52,22,20,16)
    qx, qy, qw, qh = P(52, 22, 20, 16)
    b += [R(qx - 1, qy - 1, qw + 2, qh + 2, "#15181e", rx=.6), R(qx, qy, qw, qh, f"url(#pn{s})")]
    for j in range(5):
        b.append(R(qx + 1, qy + 1.2 + j * 2.7, qw - 2, 1.9, "#2a3e54" if j % 2 else "#223448"))
        b.append(R(qx + 1.6, qy + 1.8 + j * 2.7, 6, .7, "#9ac8e8", .9))
        for c_ in range(4):
            b.append(R(qx + 10 + c_ * 5.4, qy + 1.8 + j * 2.7, 4.2, .7, ["#58d878", "#e8c040", "#58d878", "#d85858"][(j + c_) % 4], .85))
    b.append(R(qx, qy, qw, 1, "#2a6a9a"))
    # mural de avisos (10,22,16,18): cortica
    mx, my, mw, mh = P(10, 22, 16, 18)
    b += [R(mx - 1, my - 1, mw + 2, mh + 2, "#6a4a2a", rx=.4), R(mx, my, mw, mh, f"url(#ck{s})"), R(mx, my, mw, mh, "#000", .05)]
    for i, (px, py, pw, ph, c) in enumerate(((1.5, 1.4, 7, 8, "#f4efe0"), (10, 2, 7, 5.4, "#9ac8e8"), (14, 3.6, 5, 5, "#e8d878"), (3.4, 10.4, 6, 6, "#f0c8c8"), (10.6, 9.6, 8, 5.6, "#f4efe0"), (18, 11, 4, 4.6, "#c8e8b8"))):
        b += [R(mx + px * 1.0, my + py * 1.0, pw, ph, c, st="#8a7a58", sw=.1), C(mx + px + pw / 2, my + py + .5, .4, "#c0392b")]
        for k in range(int(ph / 1.5) - 1): b.append(R(mx + px + .8, my + py + 1.6 + k * 1.4, pw - 2 - (k % 2) * 1.4, .28, "#6a6450", .7))
    # arquivos baixos a esquerda
    for k in range(3):
        x0 = 4 + k * 10
        b += [R(x0, 46, 9, 28, "#8a96a0"), R(x0, 46, 9, .8, "#c8d0d8"), R(x0, 46, 1.2, 28, "#fff", .15)]
        for j in range(3): b += [R(x0 + 1.2, 48 + j * 8.6, 6.6, 7, "#76828c", st="#5a6670", sw=.15), R(x0 + 3, 50.6 + j * 8.6, 3, .8, "#d8d0b0")]
    # armario com impressora (80,18,12,14) em cima de arquivo, lado direito
    px, py, pw, ph = P(80, 18, 12, 14)
    b += [R(px - 4, 32, pw + 16, 34, "#8a96a0"), R(px - 4, 32, pw + 16, 1, "#c8d0d8"), R(px - 4, 32, 1, 34, "#fff", .15)]
    for j in range(4): b += [R(px - 2.6, 34 + j * 7.6, pw + 13.2, 6.4, "#76828c", st="#5a6670", sw=.15), R(px + pw / 2 - .8, 36.4 + j * 7.6, 4.4, .9, "#d8d0b0")]
    b += [R(px + 1, py + 4, pw - 2, ph - 6, "#e8e6e0", rx=.8), R(px + 1, py + 4, pw - 2, 1.4, "#fff"), R(px + 2, py + 6.6, pw - 4, 2.2, "#3a3e46"),
          R(px + 3, py + 7.2, 6, .6, "#9ac8e8"), C(px + pw - 3, py + 7.9, .5, "#58d878"), R(px - .4, py + ph - 2.4, pw + .8, 2.6, "#cfcdc4", rx=.5), R(px + 2.4, py + 1.6, pw - 4.8, 3, "#f4efe0", st="#b8ae92", sw=.12)]
    # mesa vazia de Valmir (30,56,16,14)
    vx, vy, vw, vh = P(30, 56, 16, 14)
    b += [E(vx + vw / 2, vy + vh + 6, vw * .7, 2, "#000", .25), R(vx + 1, vy + 2, vw - 2, 2.2, "#b89c6a"), R(vx + 1, vy + 2, vw - 2, .5, "#e8cfa0"),
          R(vx + 2, vy + 4.2, 1.8, vh + 3, "#6a6a68"), R(vx + vw - 3.8, vy + 4.2, 1.8, vh + 3, "#6a6a68"), R(vx + 1, vy + 4.2, vw - 2, 1.4, "#8a7248")]
    b += [monitor(vx + vw - 12, vy - 8, 9, 6.2, body="#2a2d33", screen="#15181e", bars="#15181e"), R(vx + 3, vy + .6, 8, 1.6, "#d8d4c4", st="#9a967c", sw=.15), R(vx + 2.4, vy - .6, 2.6, 2.6, "#efe8d8", rx=.3)]
    b += [E(vx + 4.6, vy + 2.6, 1.4, .4, "#6a4a30"), R(vx + 2.6, vy - .4, 2.2, .4, "#6a4a30")]
    b += [R(vx - 8, vy + 6, 7.6, 2.8, "#2a2d33", rx=1.4), R(vx - 8.4, vy - 2.4, 2.4, 9, "#2a2d33", rx=1), R(vx - 4.4, vy + 8.6, .9, 8, "#4a4a50"), E(vx - 4, vy + 17, 3.6, .6, "#2a2d33")]
    # balcao da recepcao com livro de acesso (70,56,18,14)
    lx, ly, lw, lh = P(70, 56, 18, 14)
    b += [R(lx - 2, ly + 2, lw + 6, lh + 12, "#7a5a3a"), R(lx - 2, ly + 2, lw + 6, 1.8, "#a8804e"), R(lx - 2, ly + 3.8, lw + 6, .5, "#fff", .25),
          R(lx, ly + lh - 2, lw + 2, 8, "#000", .08)]
    for j in range(3): b.append(R(lx + 1 + j * 9.8, ly + lh + 1, 8.6, 8, "#000", .18, st="#5a3a22", sw=.2))
    b += [PG([(lx + 3, ly + 2), (lx + lw - 2, ly + 2), (lx + lw - 3, ly - 5), (lx + 4, ly - 5.6)], "#5a2a2a"), PG([(lx + 3.4, ly + 1.6), (lx + lw - 2.4, ly + 1.6), (lx + lw - 3.2, ly - 4.4), (lx + 4.2, ly - 4.8)], "#efe9d8")]
    for k in range(7): b.append(R(lx + 5, ly - 3.6 + k * .8, lw - 9, .3, "#7a7460", .8))
    b += [R(lx + lw - 7, ly - 9, 1.6, 8.6, "#2a2d33"), R(lx + lw - 8.4, ly - 9, 4.4, 1.2, "#2a2d33", rx=.5), PATH(f"M{f(lx+lw-6.2)} {f(ly-3)} q-2.6 -1 -1.6 -3", st="#2a2d33", sw=.3)]
    b += [C(lx + 3.4, ly - 2.4, .8, "#c0392b", .0)]
    # carpete mancha de luz da janela
    b.append(E(80, 90, 70, 6, "#fff", .06))
    b.append(E(120, 22, 46, 24, f"url(#mn{s})"))
    return wrap(s, d, "".join(b), .4, ("#ffe8b0", .05))


def corredor_senado_ccj():
    s = "cc"
    d = (LG("wl" + s, [(0, "#4a2c1c"), (1, "#2e1a10")]) + LG("fl" + s, [(0, "#2a3a6a"), (1, "#1a2548")]) + LG("dr" + s, [(0, "#2a160c"), (1, "#1a0e06")]) +
         LG("cl" + s, [(0, "#d8d2c0"), (1, "#c2bca8")]) + RG("lg" + s, [(0, "#ffe9b0", .35), (1, "#ffe9b0", 0)]) + LG("gl" + s, [(0, "#a8c8e0"), (1, "#7a9ab4")]) + LG("mb" + s, [(0, "#e8dcc4"), (1, "#c8b898")]))
    b = [R(0, 0, 160, 100, f"url(#wl{s})")]
    # painel de madeira escura em almofadas
    for k in range(14): b += [R(k * 11.6 + 3, 6, 9, 56, "#000", .14, rx=.4), R(k * 11.6 + 3.8, 6.8, 7.4, 54.4, "none", st="#a8804e", sw=.18, o=.4)]
    b += [R(0, 0, 160, 4, f"url(#cl{s})"), R(0, 4, 160, .7, "#c9a04a", .7), R(0, 62, 160, 6, "#1e1008"), R(0, 62, 160, .8, "#c9a04a", .6), R(0, 68, 160, 32, f"url(#fl{s})")]
    # carpete azul com guarda
    b.append(pfloor(68, 80, 52, "#0e1630", .5, 18, 5, span=420))
    b += [PG([(52, 68), (108, 68), (136, 100), (24, 100)], "#4a1a24", .85), PG([(56, 68), (104, 68), (130, 100), (30, 100)], "#6a2a34", .5)]
    b += [PG([(58, 68), (102, 68), (122, 100), (38, 100)], "none", st="#c9a04a", sw=.3)]
    # luz tensa da manha (feixes)
    b += [PG([(0, 4), (40, 4), (70, 68), (20, 68)], "#fff", .05), PG([(120, 4), (160, 4), (150, 68), (110, 68)], "#fff", .05)]
    # sala vazia da Comissao (8,40,26,30): porta aberta, luz fria
    dx, dy, dw, dh = P(8, 40, 26, 30)
    b += [R(dx - 1.4, dy - 1.4, dw + 2.8, dh + 1.4, "#1a0e06"), R(dx, dy, dw, dh, "#0e1218"), R(dx, dy, dw, dh, "#7a98b4", .22)]
    for k in range(3): b.append(R(dx + 2 + k * 11, dy + 14, 9, 7, "#3a2418", rx=1.2)); b.append(R(dx + 3 + k * 11, dy + 8, 7, 7, "#4a3020", rx=1.4))
    b += [R(dx + 1, dy + 20, dw - 2, 1.6, "#5a3a22"), PG([(dx + dw, dy), (dx + dw + 6, dy + 2), (dx + dw + 6, dy + dh - 1), (dx + dw, dy + dh)], "#3a2214"), R(dx + dw + 1.4, dy + 14, .8, 2, "#d9b86a"),
          PG([(dx, dy), (dx + 6, dy + 3), (dx + 6, dy + dh), (dx, dy + dh)], "#000", .2)]
    b += [R(dx + 4, dy - 6, dw - 8, 3.4, "#c9a04a", st="#6a5224", sw=.2), R(dx + 6, dy - 5, dw - 12, .7, "#3a2410", .6), R(dx + 6, dy - 3.8, dw - 15, .5, "#3a2410", .5)]
    # mural de ex-ministros (20,8,30,20): fileira de molduras (retratos abstratos)
    mx, my, mw, mh = P(20, 8, 30, 20)
    b += [R(mx - 1, my - 1, mw + 2, mh + 2, "#1a0e06", rx=.4), R(mx, my, mw, mh, "#3a2418")]
    for j in range(2):
        for i in range(6):
            fx = mx + 1.6 + i * (mw - 3) / 6; fy = my + 1.4 + j * (mh - 2) / 2
            b += [R(fx, fy, (mw - 3) / 6 - 1, (mh - 2) / 2 - 1.2, "#c9a04a", st="#6a5224", sw=.15), R(fx + .8, fy + .8, (mw - 3) / 6 - 2.6, (mh - 2) / 2 - 2.8, ["#6a7a8a", "#8a7a6a", "#5a6a7a"][(i + j) % 3]),
                  C(fx + ((mw - 3) / 6 - 1) / 2, fy + 3.4, 1.5, "#d8c0a0", .8), PATH(f"M{f(fx+1.6)} {f(fy+(mh-2)/2-1.2-.8)} q{f(((mw-3)/6-1)/2-1.6)} -5.4 {f(((mw-3)/6-1)-3.2)} 0z", fill="#2a2a34", o=.8)]
    # painel de votacao apagado (40,12,24,18)
    px, py, pw, ph = P(40, 12, 24, 18)
    b += [R(px - 1.2, py - 1.2, pw + 2.4, ph + 2.4, "#c9a04a"), R(px, py, pw, ph, "#0a0d12"), R(px, py, pw, ph * .3, "#fff", .04)]
    for j in range(4):
        for i in range(10): b.append(R(px + 2 + i * (pw - 4) / 10, py + 2.4 + j * 3.5, (pw - 4) / 10 - .8, 2, "#161c24"))
    b += [R(px + 2, py + ph - 2.4, pw * .4, .8, "#1c2430"), R(px + pw * .6, py + ph - 2.4, pw * .3, .8, "#1c2430"), PG([(px, py + ph), (px + pw * .4, py), (px + pw * .55, py), (px + pw * .15, py + ph)], "#fff", .05)]
    # balcao da assessoria (62,20,24,22): guiche na parede
    gx, gy, gw, gh = P(62, 20, 24, 22)
    b += [R(gx - 1.4, gy - 1.4, gw + 2.8, gh + 6, "#1a0e06"), R(gx, gy, gw, gh, f"url(#gl{s})"), R(gx, gy, gw, gh, "#000", .35), R(gx + 3, gy + 3, gw - 6, gh - 9, "#2a3a4a", .5),
          R(gx - 2.4, gy + gh, gw + 4.8, 2.4, f"url(#mb{s})"), R(gx - 2.4, gy + gh + 2.4, gw + 4.8, 3.4, "#2a1a10")]
    for k in range(7): b.append(R(gx + 1.6 + k * (gw - 3) / 7, gy, .4, gh, "#1a2430", .6))
    b += [papers(gx + 4, gy + gh - 1.4, 7, 1.2, 2, seed=2), R(gx + gw - 8, gy + gh - 3.6, 4, 3.6, "#2a2d33", rx=.4), R(gx + gw - 7.4, gy + gh - 3, 2.8, 1.6, "#3a76a6")]
    b += [R(gx + 3, gy - 4.4, gw - 6, 2.4, "#c9a04a", st="#6a5224", sw=.2), R(gx + 5, gy - 3.6, gw - 10, .6, "#3a2410", .6)]
    # copa dos senadores (70,50,20,28): porta/bancada com cafeteira
    cx, cy, cw, ch = P(70, 50, 20, 28)
    b += [R(cx - 1.2, cy - 1.2, cw + 2.4, ch + 1.2, "#1a0e06"), R(cx, cy, cw, ch, "#d8d0bc"), R(cx, cy + ch * .52, cw, ch * .48, "#5a3a22"), R(cx, cy + ch * .5, cw, 1.6, f"url(#mb{s})"),
          R(cx + 2, cy + 3, cw - 4, 9, "#e8e4d4", st="#8a7a58", sw=.2), R(cx + 3, cy + 4, cw - 6, 3.4, "#a8c4d8", .7)]
    b += [R(cx + 3, cy + ch * .5 - 9, 9, 9, "#2a2d33", rx=1), R(cx + 4, cy + ch * .5 - 7.6, 7, 3, "#9a9aa0"), C(cx + 7.5, cy + ch * .5 - 2, .8, "#c0392b"), R(cx + 14, cy + ch * .5 - 5, 3.4, 5, "#d8d4c4", rx=.5),
          R(cx + 15, cy + ch * .5 - 6.4, 1.4, 1.4, "#6a3a22")]
    for k in range(2): b.append(R(cx + 2 + k * 8, cy + ch * .56, 7, ch * .38, "#000", .2, rx=.3, st="#8a5a38", sw=.2))
    # cadeiras enfileiradas ao longo do corredor + tripes
    for k, x0 in enumerate((2, 14.4, 26.8, 112, 125, 138, 150)):
        pass
    for (x0, y0, sc) in ((42, 70, 1.0), (96, 70, 1.0)):
        pass
    for x0 in (4, 26, 118, 140):
        b += [E(x0 + 7, 88, 8, 1.1, "#000", .3), R(x0, 71, 14, 4.2, "#c9a04a", .0), R(x0, 71, 14, 12, "#141a3a", rx=1.6), R(x0 + 1.2, 72.2, 11.6, 6, "#2a3a6a", .6, rx=1.2),
              R(x0 - .6, 80, 15.2, 3.4, "#141a3a", rx=1.2), R(x0 + 1, 83.4, 1, 5, "#6a6a70"), R(x0 + 12, 83.4, 1, 5, "#6a6a70")]
    for (tx, ty, sc) in ((46, 90, 1.1), (112, 94, 1.3), (10, 96, 1.4)):
        b += [L(tx, ty - 9 * sc, tx - 4 * sc, ty, "#0e1014", .6), L(tx, ty - 9 * sc, tx + 4 * sc, ty, "#0e1014", .6), L(tx, ty - 9 * sc, tx + .4, ty + .6, "#0e1014", .5),
              R(tx - 2.6 * sc, ty - 13 * sc, 5.2 * sc, 3.6 * sc, "#262a32", rx=.6), R(tx + 1.8 * sc, ty - 12.6 * sc, 2.6 * sc, 2.4 * sc, "#15181e", rx=.4), C(tx + 3.2 * sc, ty - 11.4 * sc, .9 * sc, "#3a5a8a")]
    # lustres/arandelas
    for x0 in (6, 38, 66, 94, 122, 154):
        b += [R(x0 - .6, 24, 1.2, 4, "#c9a04a"), PG([(x0 - 1.8, 24), (x0 + 1.8, 24), (x0 + 1.2, 20), (x0 - 1.2, 20)], "#f4e4b0"), E(x0, 22, 5, 7, f"url(#lg{s})")]
    b.append(E(80, 70, 50, 3, "#ffe9b0", .06))
    return wrap(s, d, "".join(b), .55, ("#ffd890", .04))


def saida_lateral_senado():
    s = "sl"
    d = (LG("sk" + s, [(0, "#f2a050"), (.45, "#f8c878"), (1, "#fce8b8")]) + LG("wl" + s, [(0, "#d4b890"), (1, "#a88868")]) + LG("rp" + s, [(0, "#c8a880"), (1, "#a08460")]) +
         LG("st" + s, [(0, "#6a5a58"), (1, "#3a2c2a")]) + RG("sn" + s, [(0, "#fff4c8", .9), (1, "#fff4c8", 0)]) + LG("gr" + s, [(0, "#8a7a52"), (1, "#6a5a3a")]))
    b = [R(0, 0, 160, 100, f"url(#sk{s})"), C(112, 50, 30, f"url(#sn{s})"), C(112, 50, 6, "#fffbe0")]
    b += [E(130, 22, 18, 1.6, "#fff", .35), E(70, 12, 14, 1.2, "#fff", .3), R(0, 46, 160, 8, "#a8825a", .3)]
    # skyline distante (cupula e predios baixos) contra o sol
    b += [R(60, 46, 100, 4, "#a8785a", .6), PATH("M96 46 Q108 34 120 46Z", fill="#9a6a50", o=.8), R(130, 40, 5, 10, "#a8785a", .7), R(138, 41, 5, 9, "#a8785a", .7)]
    # gramado e rua vazia
    b += [R(0, 50, 160, 8, f"url(#gr{s})"), R(0, 58, 160, 42, f"url(#st{s})"), R(0, 58, 160, 1.2, "#e8d0a8", .7)]
    for k in range(5): b.append(PG([(70 + k * 6, 66), (73 + k * 6, 66), (66 + k * 22 - 22, 100), (56 + k * 22 - 22, 100)], "#d8b078", .0))
    for k in range(6): b.append(R(0 + k * 28 - 6 + (k * 3), 76 + (k % 2) * 0, 12, .9, "#e8d098", .5))
    b += [E(120, 80, 36, 3, "#ffd890", .18), E(112, 64, 24, 1.6, "#ffe0a0", .2)]
    # edificio lateral do Senado: parede de concreto com brises (esquerda)
    b += [PG([(0, 0), (66, 6), (66, 70), (0, 90)], f"url(#wl{s})")]
    for k in range(7): b.append(PG([(k * 9.4, 0 + k * .9), (k * 9.4 + 1.4, k * .9 + .1), (k * 9.4 + 1.4, 90 - k * 2.9 - 0), (k * 9.4, 90 - k * 3.0)], "#6a4a38", .0))
    for k in range(8):
        x0 = 4 + k * 8; ytop = 0.09 * x0 + 0; ybot = 90 - 0.30 * x0
        b.append(PG([(x0, ytop), (x0 + 1.8, ytop + .16), (x0 + 1.8, ybot - .5), (x0, ybot)], "#7a5a42", .5))
    b += [PG([(0, 84), (66, 70), (66, 72.4), (0, 87)], "#7a5a42"), PG([(0, 0), (66, 6), (66, 7.6), (0, 1.6)], "#e8d0a8")]
    # porta de saida de aco com marquise
    b += [PG([(14, 72), (14, 20), (46, 23), (46, 65.6)], "#2a2220"), PG([(16.6, 70.6), (16.6, 24), (43.4, 26.4), (43.4, 65)], "#7a8896"), PG([(16.6, 24), (30, 25.2), (30, 67.8), (16.6, 70.6)], "#fff", .08)]
    b += [PG([(30, 25.2), (31, 25.3), (31, 67.4), (30, 67.6)], "#2a2220"), PG([(40.4, 43), (41.4, 43), (41.4, 49), (40.4, 49.2)], "#d9b86a"),
          PG([(12, 19), (48, 22.4), (48, 17), (12, 14)], "#e8c488"), PG([(12, 14), (48, 17), (48, 15.6), (12, 12.6)], "#fff4d0", .8), PG([(18, 19.4), (44, 21.6), (44, 28), (18, 26)], "#000", .1)]
    b += [PG([(20.6, 28.6), (39, 30), (39, 33.4), (20.6, 32)], "#2a8a58"), PG([(22, 29.6), (30, 30.2), (30, 31.4), (22, 31)], "#e8f4e8", .85)]
    # rampa de concreto descendo da porta (em perspectiva)
    b += [PG([(8, 74.4), (50, 69), (96, 92), (30, 100), (0, 100), (0, 86)], f"url(#rp{s})"), PG([(8, 74.4), (50, 69), (52, 70.4), (10, 76)], "#e8d0a8"),
          PG([(30, 100), (96, 92), (98, 93), (34, 100)], "#6a5238", .5)]
    for k in range(6):
        t = k / 6
        b.append(L(14 + t * 70, 77 + t * 17, 40 + t * 70, 70 + t * 24, "#8a6a48", .25, .45))
    b += [PATH("M20 92 L24 88 L22 85 L28 82", st="#4a3a28", sw=.3, o=.8), PATH("M70 90 L66 94 L69 97", st="#4a3a28", sw=.3, o=.8)]
    # corrimao metalico da rampa
    for k in range(5):
        x0 = 56 + k * 8.2; y0 = 72 + k * 4.2
        b.append(R(x0, y0 - 6, .7, 6, "#3a3e46"))
    b += [L(56, 66, 94, 86, "#3a3e46", .6), L(56, 69, 94, 89, "#3a3e46", .3, .5)]
    # cerca de metal (grade) a direita, estende ate o fundo
    for k in range(34):
        xx = 74 + k * 2.6 + (k * k) * .0
        b.append(R(xx, 54 - (k * .1), .5, 20 - (k * .05), "#2a2a30"))
    b += [R(74, 55, 90, .8, "#2a2a30"), R(74, 71, 90, .8, "#2a2a30"), R(74, 62, 90, .5, "#2a2a30", .7)]
    for k in range(8): b.append(R(74 + k * 12, 52, 1.4, 22, "#1c1c22"))
    b += [R(74, 74, 90, 2, "#c8a878"), R(74, 74, 90, .6, "#f4dcb0"), R(74, 76, 90, 1, "#000", .15)]
    # sombras longas da grade e do sol baixo
    for k in range(8): b.append(PG([(74 + k * 12, 75), (75.4 + k * 12, 75), (60 + k * 12 - 22, 98), (58.4 + k * 12 - 22, 98)], "#2a1a14", .22))
    b += [PG([(0, 90), (66, 72), (86, 98), (0, 100)], "#000", .0)]
    # lixeira e hidrante
    b += [R(150, 62, 5, 9, "#4a4a4e"), R(149.6, 61, 5.8, 1.2, "#6a6a70"), R(60, 66, 2.6, 4, "#b8392a"), R(59.6, 65.4, 3.4, .8, "#8a2a20")]
    return wrap(s, d, "".join(b), .5, ("#ff9a30", .08))


def sala_negociacao_delacao():
    s = "sn"
    d = (LG("wl" + s, [(0, "#f2f2ee"), (1, "#dcdcd6")]) + LG("fl" + s, [(0, "#c6c6c0"), (1, "#a6a6a0")]) + LG("tb" + s, [(0, "#e8e8e4"), (1, "#c8c8c2")]) +
         RG("lg" + s, [(0, "#ffffff", .85), (1, "#ffffff", 0)]) + LG("pn" + s, [(0, "#c8b078"), (1, "#a89058")]))
    b = [R(0, 0, 160, 100, f"url(#wl{s})"), R(0, 0, 160, 5, "#fff"), R(0, 5, 160, .7, "#a8a8a2", .6), R(0, 70, 160, 4, "#b8b8b2"), R(0, 74, 160, 26, f"url(#fl{s})")]
    for k in range(10): b.append(R(k * 16.6, 5, .3, 65, "#000", .06))
    b.append(pfloor(74, 80, 52, "#7a7a74", .4, 16, 5))
    # luz forte: paineis de teto
    for (x0, w) in ((10, 38), (61, 38), (112, 38)):
        b += [R(x0, 0, w, 4, "#fff"), R(x0 + 1, .5, w - 2, 2.6, "#fffff4"), E(x0 + w / 2, 22, w * .75, 28, f"url(#lg{s})")]
    b += [PG([(40, 5), (120, 5), (150, 74), (10, 74)], "#fff", .08)]
    # camera de teto (domo)
    b += [R(78, 4, 4, 2.4, "#3a3e46"), PATH("M76.4 6.4 Q80 .8 83.6 6.4Z", fill="#15181e"), C(80, 5.4, 1, "#2a6a9a"), C(81.4, 4.4, .35, "#ff3a3a")]
    # porta de aco a esquerda
    b += [R(2, 18, 11, 54, "#8a949c"), R(3, 19, 9, 52, "#a8b2ba"), R(4.4, 24, 6.2, 9, "#6a7a86"), R(4.4, 24, 6.2, 9, "#cfe6f4", .4), R(10.4, 46, .8, 3.6, "#2a2d33"), R(2, 18, 11, .8, "#fff", .5)]
    # ventilacao
    b += [R(26, 12, 20, 5, "#c8c8c2", st="#a8a8a2", sw=.2)]
    for k in range(8): b.append(R(27.4 + k * 2.3, 13, 1.2, 3, "#8a8a84", .8))
    # pasta sobre o arquivo (10,46,16,16): mesinha lateral a esquerda com pasta em pe
    px, py, pw, ph = P(10, 46, 16, 16)
    b += [R(px - 2, py + ph, pw + 4, 1.6, "#9a9a94"), R(px - 1, py + ph + 1.6, 1.4, 11, "#7a7a76"), R(px + pw - .4, py + ph + 1.6, 1.4, 11, "#7a7a76"), E(px + pw / 2, py + ph + 12, pw * .6, 1, "#000", .15)]
    b += [R(px + 1.4, py + 1, pw - 3, ph - 1, "#c8a85a", rx=.4), R(px + 1.4, py + 1, (pw - 3) * .4, 1.2, "#d8bc72"), R(px + 1.4, py + ph - 1.4, pw - 3, .6, "#000", .2),
          R(px + 3.6, py + 5, pw - 7.4, .5, "#fff", .6), R(px + 3.6, py + 6.6, pw - 9, .5, "#fff", .5), R(px + pw * .5, py + 9, 4, 4, "#fff", .35, rx=.4),
          R(px + 3, py + 2.6, pw - 6.4, 1.4, "#efe9d8", .0), PG([(px + 3, py - .6), (px + 4, py - 2.6), (px + 12, py - 2.6), (px + 13, py - .6)], "#efe9d8", .0)]
    b += [R(px - .6, py + ph - 3.4, pw + 1, 3.4, "#b8984a", .0), R(px + 1.4, py - .8, pw - 3.6, 1.4, "#efe9d8"), R(px + 2.4, py - 1.6, pw - 5.6, .9, "#e4dcc4")]
    # mural de avisos (72,14,18,24)
    mx, my, mw, mh = P(72, 14, 18, 24)
    b += [R(mx - 1, my - 1, mw + 2, mh + 2, "#8a8a84", rx=.4), R(mx, my, mw, mh, f"url(#pn{s})")]
    for i, (px_, py_, pw_, ph_, c) in enumerate(((1.6, 1.6, 8, 10, "#fff"), (11, 2, 8, 6, "#9ac8e8"), (20.6, 2.6, 6, 8, "#f4efe0"), (3, 14, 7, 7, "#e8d878"), (11.6, 11, 9, 10, "#fff"), (22, 13, 6, 8, "#f0c8c8"), (2, 22.6, 9, 8, "#f4efe0"), (14, 22.6, 9, 8, "#c8e8b8"))):
        if py_ + ph_ > mh - .6 or px_ + pw_ > mw - .6: continue
        b += [R(mx + px_, my + py_, pw_, ph_, c, st="#8a7a58", sw=.1), C(mx + px_ + pw_ / 2, my + py_ + .6, .4, "#c0392b")]
        for k in range(int(ph_ / 1.5) - 1): b.append(R(mx + px_ + .8, my + py_ + 1.8 + k * 1.4, pw_ - 2 - (k % 2) * 1.4, .28, "#6a6450", .7))
    # balcao com livro de acesso (40,44,18,14): livro em pe sobre o balcao no fundo
    lx, ly, lw, lh = P(40, 44, 18, 14)
    b += [R(lx - 12, ly + lh, lw + 24, 3, "#b8b8b2"), R(lx - 12, ly + lh, lw + 24, .6, "#fff"), R(lx - 11, ly + lh + 3, lw + 22, 11, f"url(#tb{s})"), R(lx - 11, ly + lh + 3, lw + 22, .5, "#a8a8a2"),
          R(lx - 11, ly + lh + 3, 1.2, 11, "#000", .1), R(lx + lw + 9, ly + lh + 3, 1.2, 11, "#000", .1)]
    b += [PG([(lx + 1.6, ly + lh), (lx + 3, ly + 1.4), (lx + lw - 3, ly + 1.4), (lx + lw - 1.6, ly + lh)], "#2a2d33"), PG([(lx + 2.8, ly + lh - .8), (lx + 4, ly + 2.4), (lx + lw - 4, ly + 2.4), (lx + lw - 2.8, ly + lh - .8)], "#efe9d8")]
    for k in range(6): b.append(R(lx + 4.4, ly + 4 + k * 1.4, lw - 8.8 - (k % 2) * 2.6, .3, "#7a7460", .8))
    b += [R(lx + lw / 2 - .3, ly + 2.4, .6, lh - 3, "#c8c0a8", .7), R(lx + lw - 6.4, ly + lh - 1.6, .7, 1.6, "#2a2d33"), R(lx + lw - 6.4, ly + lh - 3, .5, 1.6, "#2a2d33", .0)]
    b += [R(lx + lw + 2, ly + lh - 2.4, 1, 2.4, "#2a2d33"), R(lx + lw + 1.6, ly + lh - 3, 1.8, .7, "#c0392b"), PATH(f"M{f(lx+lw+2.5)} {f(ly+lh-3)} q-1.4 -3 -5 -3", st="#2a2d33", sw=.25)]
    # mesa redonda e quatro cadeiras (em primeiro plano, baixas)
    b += [E(80, 94, 34, 4, "#000", .2), E(80, 82.4, 30, 7.6, "#a8a8a2"), E(80, 80.6, 30, 7.6, f"url(#tb{s})"), E(80, 80.2, 27, 6.6, "#f4f4f0", .5), R(78.6, 85, 2.8, 8.4, "#7a7a76"), E(80, 93.4, 8, 1.4, "#7a7a76")]
    for (cx, cy, c) in ((44, 80, 1), (116, 80, 1), (62, 71.5, .8), (98, 71.5, .8)):
        sc = c
        b += [E(cx, cy + 9 * sc, 6 * sc, 1, "#000", .2), R(cx - 4.6 * sc, cy - 4 * sc, 9.2 * sc, 8 * sc, "#4a5560", rx=1.4 * sc), R(cx - 4 * sc, cy - 3.4 * sc, 8 * sc, 4.6 * sc, "#6a7886", .6, rx=1 * sc),
              R(cx - 5 * sc, cy + 3.2 * sc, 10 * sc, 2.2 * sc, "#4a5560", rx=1 * sc), R(cx - 4 * sc, cy + 5.4 * sc, .8 * sc, 4 * sc, "#2a2d33"), R(cx + 3.2 * sc, cy + 5.4 * sc, .8 * sc, 4 * sc, "#2a2d33")]
    return wrap(s, d, "".join(b), .25, ("#ffffff", .06))


def fachada_tre():
    s = "ft"
    d = (LG("sk" + s, [(0, "#2a3a6a"), (.5, "#6a82b4"), (1, "#e8a890")]) + LG("gl" + s, [(0, "#4a5e8a"), (.7, "#94a8cc"), (1, "#e4b4a8")]) +
         LG("pv" + s, [(0, "#4a5260"), (1, "#2a303c")]) + LG("sw" + s, [(0, "#8a92a0"), (1, "#6a727e")]) + RG("lg" + s, [(0, "#ffe8a8", .55), (1, "#ffe8a8", 0)]))
    b = [R(0, 0, 160, 100, f"url(#sk{s})")]
    for k in range(30):
        rr = random.Random(k); b.append(C(rr.uniform(0, 160), rr.uniform(0, 12), .22, "#fff", rr.uniform(.2, .6)))
    # predio de vidro
    b += [R(16, 8, 144, 54, "#3a4258"), R(16, 8, 144, 1.6, "#a8b4cc")]
    for j in range(7):
        for i in range(24):
            b.append(R(17 + i * 5.97, 10 + j * 7.4, 5.5, 7, f"url(#gl{s})" if (i + j) % 5 else "#e4c898", .96))
    b += [R(16, 8, 144, 54, "#000", .1)]
    for i in range(25): b.append(R(16.6 + i * 5.97 - .4, 9.6, .5, 52, "#2a3248"))
    for j in range(8): b.append(R(16, 9.6 + j * 7.4 - .3, 144, .5, "#2a3248"))
    b += [PG([(30, 10), (50, 10), (24, 62), (16, 62)], "#fff", .08), PG([(90, 10), (100, 10), (74, 62), (64, 62)], "#fff", .06)]
    b += [R(16, 60, 144, 3, "#6a7280"), R(16, 62.4, 144, 1.4, "#2a303c")]
    # portaria / entrada (39,29,28,28)
    gx, gy, gw, gh = P(39, 29, 28, 28)
    b += [R(gx - 1.4, gy + 4, gw + 2.8, gh - 2, "#2a303c"), R(gx - 2, gy + 2.4, gw + 4, 3, "#aab2c0"), R(gx - 2, gy + 2.4, gw + 4, .6, "#fff", .6),
          R(gx, gy + 5.4, gw, gh - 5.4, "#a8c8e0"), R(gx, gy + 5.4, gw, gh - 5.4, "#ffe0a0", .22), R(gx + gw / 2 - .4, gy + 5.4, .8, gh - 5.4, "#2a303c")]
    for k in range(4): b.append(R(gx + 1 + k * (gw - 2) / 4, gy + 5.4, .35, gh - 5.4, "#2a303c", .5))
    b += [R(gx + 2.4, gy + 11, 1, 10, "#d8d8e0"), R(gx + gw - 3.4, gy + 11, 1, 10, "#d8d8e0"), R(gx - 2, gy + gh, gw + 4, 1.6, "#9aa2b0"), R(gx + 3, gy + 15, gw - 6, 6, "#ffe8a8", .18),
          E(gx + gw / 2, gy + gh - 3, gw * .5, 1.4, "#ffe8a8", .3)]
    # camera da portaria (grande, bem visivel)
    b += [R(gx + gw * .5 - .5, gy - 1.6, 1, 4.4, "#3a3e46"), R(gx + gw * .5 - 5, gy - 6.4, 10, 5, "#d8dce4", rx=1.2), R(gx + gw * .5 - 5, gy - 6.4, 10, 1.2, "#fff", .7, rx=.6), R(gx + gw * .5 - 4, gy - 5, 6, 2.8, "#15181e", rx=.6),
          C(gx + gw * .5 - 1.2, gy - 3.6, 1.1, "#3a5a8a"), C(gx + gw * .5 + 3.4, gy - 5.4, .55, "#ff3a3a"), C(gx + gw * .5 + 3.4, gy - 5.4, 1.8, "#ff3a3a", .2),
          R(gx + gw * .5 + 4.4, gy - 6, 2.4, .6, "#8a8e96", .0)]
    # faixa de placa sem texto
    b += [R(gx + 4, gy - .4, gw - 8, 2, "#1a2a4a", rx=.3), R(gx + 6, gy + .2, gw - 12, .6, "#e8e0c8", .85)]
    # mastro com bandeira generica
    b += [R(148.6, 4, 1, 60, "#c8ccd4"), C(149.1, 3.6, 1.1, "#e8c46a")]
    b += [PATH("M149.6 6 Q153 4.6 156 6.2 T159.4 6 V15 Q156 16.4 153 15 T149.6 16Z", fill="#f2f2ee"), PATH("M149.6 9 Q153 7.6 156 9.2 T159.4 9 V12 Q156 13.4 153 12 T149.6 13Z", fill="#2a5a9a", o=.95),
          C(154.4, 10.8, 1.2, "#e8c840")]
    # calcada molhada, rua escura
    b += [R(0, 63, 160, 12, f"url(#sw{s})"), R(0, 63, 160, .8, "#c8ccd8", .6), R(0, 75, 160, 25, f"url(#pv{s})"), R(0, 75, 160, 1.4, "#aab0bc")]
    for k in range(9): b.append(L(k * 22 - 8, 63, k * 22 - 14, 75, "#5a626e", .25, .55))
    for k in range(6): b.append(R(k * 30 + 8, 90, 16, 1, "#e8e0b8", .5))
    # reflexos de poca / molhado
    for (x0, y0, w) in ((84, 70, 18), (30, 68, 14), (110, 90, 24), (50, 95, 20)):
        b.append(E(x0, y0, w, 1.2, "#fff", .14))
    b += [R(76, 64, 22, 10, f"url(#lg{s})", .0), E(87, 68, 24, 4, "#ffe8a8", .22), E(87, 80, 14, 7, "#ffe8a8", .1), R(84, 63, 4, 30, "#ffe8a8", .06)]
    # muro (4,45,30,27) com papeis jogados fora
    mx, my, mw, mh = P(4, 45, 30, 27)
    b += [R(mx, my, mw, mh, "#8a8e98"), R(mx - .6, my - 1.2, mw + 1.2, 1.4, "#aab0bc"), R(mx, my + mh - 1.2, mw, 1.2, "#5a6070", .6)]
    for k in range(5): b.append(L(mx, my + 4.4 + k * 4.4, mx + mw, my + 4.4 + k * 4.4, "#5a6070", .14, .5))
    b += [R(mx + 2, my + 6, 6.4, 8, "#3a4250", rx=.4), R(mx + 2, my + 6, 6.4, 1.2, "#5a6272"), PG([(mx + 2.4, my + 6), (mx + 4, my + 3), (mx + 7, my + 3.4), (mx + 8, my + 6)], "#efe9d8"),
          PG([(mx + 4, my + 3.4), (mx + 6, my + 1.4), (mx + 8.4, my + 3.8), (mx + 6, my + 5)], "#f4efe0")]
    rr = random.Random(8)
    for i in range(16):
        px = mx + 3 + rr.uniform(-1, mw - 9); py = my + mh - 2.4 + rr.uniform(-2.6, 2.4)
        if i % 3 == 0:
            b.append(C(px, py, rr.uniform(.9, 1.4), "#f2eee0", .95)); b.append(C(px + .3, py + .2, .5, "#b8b4a4", .5))
        else:
            b.append(PG([(px, py), (px + 2.6, py - .3), (px + 2.8, py + 1.6), (px + .2, py + 1.8)], "#f4efe0", st="#a8a490", sw=.1))
            b.append(R(px + .5, py + .5, 1.6, .2, "#7a7460", .6))
    b += [PATH(f"M{f(mx+10)} {f(my+mh)} q3 -2.6 6 -1 t5 .4", st="#e8e4d0", sw=.5, o=.9)]
    # carro estacionado com rastreador (62,61,29,19)
    cx, cy, cw, ch = P(62, 61, 29, 19)
    b += [E(cx + cw / 2, cy + ch + .6, 22, 1.4, "#fff", .08), car_side(cx + cw / 2, cy + ch - 3.4, 2.5, "#2a2e3c", glass="#8aa0bc", wheel="#06080c", hub="#7a8290"),
          R(cx + cw / 2 - 18, cy + ch - 5.6, 36, .5, "#fff", .15), E(cx + cw / 2, cy + ch + 1.8, 18, 1.4, "#8aa0bc", .2)]
    b += [R(cx + cw / 2 + 11, cy + ch - 1.2, 3.2, 1.4, "#15181e", rx=.3), C(cx + cw / 2 + 12.6, cy + ch - .5, .4, "#58d878"), C(cx + cw / 2 + 12.6, cy + ch - .5, 1.2, "#58d878", .25)]
    return wrap(s, d, "".join(b), .5, ("#6a8ad0", .07))


SCENES = dict(garagem_stf=garagem_stf, esplanada_ministerios=esplanada_ministerios, secretaria_turma=secretaria_turma, corredor_senado_ccj=corredor_senado_ccj,
              saida_lateral_senado=saida_lateral_senado, sala_negociacao_delacao=sala_negociacao_delacao, fachada_tre=fachada_tre)
