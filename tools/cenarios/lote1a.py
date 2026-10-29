import random
from cen_lib import *


def gabinete_instrutor_stf():
    s = "gi"
    d = (LG("wl" + s, [(0, "#34495a"), (1, "#26343f")]) + LG("fl" + s, [(0, "#3a2a22"), (1, "#1c1410")]) +
         LG("sk" + s, [(0, "#8aa6bc"), (1, "#d3dfe8")]) + LG("dk" + s, [(0, "#4a3326"), (1, "#2a1c14")]) +
         RG("lw" + s, [(0, "#dcecff", .3), (1, "#dcecff", 0)]) + LG("rg" + s, [(0, "#5a1a22"), (1, "#3a1016")]))
    b = [R(0, 0, 160, 100, f"url(#wl{s})")]
    for i in range(8): b.append(R(i * 20 + 1, 3, 18, 64, "#000", .09, rx=.5))
    b += [R(0, 0, 160, 3, "#1c2832"), R(0, 3, 160, .5, "#9ab0c4", .5), R(0, 68, 160, 6, "#1c2832"), R(0, 68, 160, .6, "#9ab0c4", .5),
          R(0, 74, 160, 26, f"url(#fl{s})"), pfloor(74, 80, 55, "#000", .4, 18, 5),
          PG([(96, 74), (136, 74), (150, 100), (84, 100)], "#cfe4ff", .07)]
    # estante de aco (ponto 6,10,38,60)
    x, y, w, h = P(6, 10, 38, 60)
    b.append(R(x - 1.6, y - 1.6, w + 3.2, h + 2.4, "#14202a"))
    b.append(shelf_unit(x, y, w, h, 5, "#6a7a88", "#1a242e", 11,
                        ["#7a2630", "#23406e", "#2f5d4a", "#8a8a96", "#c8c0a8", "#4a3a6a", "#1f2a3a", "#a8602a"], plank="#8a9aa8"))
    for k in range(4): b.append(R(x + w * (k + 1) / 5 - .25, y, .5, h, "#8a9aa8", .55))
    b.append(R(x - 1.6, y + h + .8, w + 3.2, 1.2, "#0e161e"))
    # janela com carro preto (60,12,25,30)
    wx, wy, ww, wh = P(60, 12, 25, 30)
    ex = (R(wx, wy + wh * .62, ww, wh * .38, "#4a5560") + R(wx, wy + wh * .62, ww, .5, "#9aa8b4") +
          R(wx + 2, wy + wh * .3, 7, wh * .32, "#586878") + R(wx + 11, wy + wh * .18, 8, wh * .44, "#667688") + R(wx + 30, wy + wh * .35, 8, wh * .27, "#586878"))
    for k in range(5): ex += R(wx + 12.5, wy + wh * .22 + k * 2.4, 1.6, 1.1, "#e8f0f8", .35)
    ex += PATH(f"M{f(wx+ww*.45)} {f(wy+wh*.62)} Q{f(wx+ww*.6)} {f(wy+wh*.42)} {f(wx+ww*.75)} {f(wy+wh*.62)}Z", fill="#6a7a8c") + R(wx + ww * .42, wy + wh * .62, ww * .36, wh * .05, "#7a8a9a")
    b.append(R(wx - 2.4, wy - 3, ww + 4.8, 1.8, "#1c2832"))
    b.append(R(wx - 2, wy + wh + 1, ww + 4, 1.4, "#9ab0c4", .8))
    b.append(window(wx, wy, ww, wh, "sk" + s, frame="#16202a", mull=(1, 1), extra=ex))
    for k in range(7): b.append(R(wx - 4.6, wy + k * 4.3, 3, 3.4, "#9aa8b4", .55))
    # bandeira (90,20,8,30)
    fx, fy, fw, fh = P(90, 20, 8, 30)
    b += [R(fx + fw / 2 - .4, fy - 3, .8, 57, "#c9a04a"), C(fx + fw / 2, fy - 3.4, 1.1, "#e8c46a"),
          banner_flag(fx, fy, fw, fh - 2, "#233a6a", "#d8b04a"), E(fx + fw / 2, 74.4, 3.6, 1, "#1a1208")]
    # tapete
    b += [PG([(36, 80), (124, 80), (140, 98), (20, 98)], f"url(#rg{s})"), PG([(40, 82), (120, 82), (134, 96), (26, 96)], "none", st="#c9a04a", sw=.3)]
    # mesa (30,56,40,24)
    mx, my, mw, mh = P(30, 56, 40, 24)
    b += [E(80, 82, 38, 2.4, "#000", .35),
          PG([(mx + 2, my), (mx + mw - 2, my), (mx + mw + 1, my + 12), (mx - 1, my + 12)], "#6a4a34"),
          PG([(mx + 2, my), (mx + mw - 2, my), (mx + mw - 3, my + 1.2), (mx + 3, my + 1.2)], "#8a6648"),
          R(mx - 1, my + 12, mw + 2, 12, f"url(#dk{s})"), R(mx - 1, my + 12, mw + 2, .8, "#9a7a58")]
    for k in range(3):
        b += [R(mx + 3 + k * 20.3, my + 14.2, 18.4, 8.6, "#000", .2, rx=.4, st="#7a5a3c", sw=.25), R(mx + 10.5 + k * 20.3, my + 17.8, 3.4, .7, "#d8b04a", rx=.3)]
    fcols = ["#c9a860", "#8a3a3a", "#d8d0b8", "#4a6a8a", "#a89868", "#6a4a32"]

    def pilha(px, py, n, seed):
        r = random.Random(seed)
        return "".join(folder(px + r.uniform(-.7, .7), py - (i + 1) * 1.15, 11, 1.1, r.choice(fcols)) for i in range(n))
    b += [pilha(mx + 4, my + 10, 7, 3), pilha(mx + 16, my + 10.5, 4, 5), pilha(mx + 43, my + 9.6, 5, 8), pilha(mx + 52, my + 10.4, 3, 2)]
    # computador (46,46,10,10)
    cx2, cy2, cw, ch = P(46, 46, 10, 10)
    b += [monitor(cx2 + 1.2, cy2 + .6, cw - 2.4, 6.4, screen="#2a587a"), R(cx2 + 3, cy2 + 8.4, 9, 1.0, "#aab4be", rx=.2)]
    b.append(lamp(mx + 60, my + 4))
    b += [armchair(10, 74, 20, 19, "#5a2a20", "#a8644a"), armchair(132, 74, 20, 19, "#5a2a20", "#a8644a"), E(116, 28, 30, 22, f"url(#lw{s})")]
    return wrap(s, d, "".join(b), .55, ("#a0c8ff", .05))


def sala_das_partes_stf():
    s = "sp"
    d = (LG("wl" + s, [(0, "#cfe0cf"), (1, "#b6cdb8")]) + LG("fl" + s, [(0, "#b8a888"), (1, "#8f8062")]) +
         LG("sk" + s, [(0, "#8ec2ec"), (1, "#dcecf6")]))
    b = [R(0, 0, 160, 100, f"url(#wl{s})"), R(0, 0, 160, 3, "#eef2ea"), R(0, 64, 160, 10, "#eef2ea"), R(0, 64, 160, .5, "#8aa090", .6),
         R(0, 74, 160, 26, f"url(#fl{s})"), pfloor(74, 80, 52, "#6a5a40", .45, 18, 5),
         R(145, 3, 15, 61, "#f2f2ee", .85), R(144.6, 3, .7, 61, "#e8d890")]
    b += [PG([(0, 100), (22, 100), (30, 90), (6, 88)], "#d8e0e8", .9), PG([(0, 100), (10, 90), (6, 88), (0, 90)], "#fff", .5),
          R(2, 78, 14, 5, "#e8e8e0"), R(2, 76.6, 14, 1.6, "#d8a840"), E(9, 77, 5.6, .8, "#b8483a")]
    x, y, w, h = P(6, 10, 38, 60)
    b += [R(x - 1, y - 1, w + 2, h + 1.4, "#e8e4d8"),
          shelf_unit(x, y, w, h, 5, "#f4f1e6", "#d6d2c2", 21, ["#7a2630", "#23406e", "#2f5d4a", "#c9a04a", "#4a3a6a", "#1f2a3a"], plank="#f4f1e6", sparse=.4)]
    wx, wy, ww, wh = P(60, 12, 25, 30)
    ex = R(wx, wy + wh * .66, ww, wh * .34, "#c8c4b4") + R(wx, wy + wh * .66, ww, .4, "#fff", .5)
    ex += R(wx + 3, wy + wh * .36, 9, wh * .3, "#e8e8e4") + R(wx + 3, wy + wh * .36, 9, .5, "#9aa8b4", .6)
    ex += PG([(wx + 14, wy + wh * .66), (wx + 14, wy + wh * .4), (wx + 18, wy + wh * .3), (wx + 22, wy + wh * .4), (wx + 22, wy + wh * .66)], "#dcdcd4")
    ex += R(wx + 26, wy + wh * .4, 11, wh * .26, "#e4e4dc") + R(wx + 26, wy + wh * .4, 11, .5, "#a8b4bc", .6)
    for k in range(5): ex += R(wx + 4 + k * 1.7, wy + wh * .42, .5, wh * .22, "#8a98a4", .5)
    ex += R(wx, wy + wh * .8, ww, wh * .2, "#d4c8aa", .9)
    b += [R(wx - 2, wy + wh + 1, ww + 4, 1.6, "#f4f1e6"), window(wx, wy, ww, wh, "sk" + s, frame="#f4f1e6", mull=(1, 0), extra=ex),
          PG([(wx - 1, wy - 1), (wx + 5, wy - 1), (wx + 3, wy + wh + 1), (wx - 1, wy + wh + 1)], "#fff", .5)]
    fx, fy, fw, fh = P(90, 20, 8, 30)
    b += [R(fx + fw / 2 - .4, fy - 3, .8, 57, "#b8b0a0"), C(fx + fw / 2, fy - 3.4, 1, "#d8c88a"),
          banner_flag(fx, fy, fw, fh - 2, "#2a5a8a", "#e8e0b8", gold="#e0c868", pole="#b8b0a0"), E(fx + fw / 2, 74.4, 3.2, .9, "#4a4a48")]
    mx, my, mw, mh = P(30, 56, 40, 24)
    b.append(E(80, 82, 36, 2.2, "#000", .25))
    for lx in (mx + 1, mx + mw - 3): b.append(R(lx, my + 11, 1.6, 13, "#7a7a78"))
    b += [PG([(mx + 1, my), (mx + mw - 1, my), (mx + mw + 1, my + 12), (mx - 1, my + 12)], "#d6bd8a"),
          PG([(mx + 1, my), (mx + mw - 1, my), (mx + mw - 1.6, my + 1), (mx + 1.6, my + 1)], "#ead2a0"),
          R(mx - 1, my + 12, mw + 2, 2.2, "#a88c5a"), R(mx - 1, my + 12, mw + 2, .4, "#fff", .3)]
    r = random.Random(77)
    for i in range(26):
        px = mx + 2 + r.uniform(0, mw - 12); py = my + 2 + r.uniform(0, 8)
        b.append(PG([(px, py), (px + 7, py + r.uniform(-.8, .8)), (px + 7.4, py + 3.2), (px + .4, py + 3.4)], r.choice(["#f2eedd", "#e8e4cf", "#f6f2e4", "#dfe6e2"]), st="#b8b098", sw=.12))
        if r.random() < .6: b.append(R(px + 1, py + 1, 4, .3, "#8a8470", .6))
    for px, py, n, sd in ((mx + 5, my + 10, 5, 1), (mx + 50, my + 10.8, 4, 2)):
        rr = random.Random(sd)
        for i in range(n): b.append(folder(px + rr.uniform(-.6, .6), py - (i + 1) * 1.05, 10, 1, rr.choice(["#c8b078", "#8a4a4a", "#5a7a9a", "#e8e0c8"])))
    cx2, cy2, cw, ch = P(46, 46, 10, 10)
    b.append(monitor(cx2 + 1.2, cy2 + .6, cw - 2.4, 6.4, body="#e4e4e0", screen="#3a7aa8", stand="#b8b8b4"))
    for cx in (12, 130):
        b += [E(cx + 9, 96, 9, 1.2, "#000", .2), R(cx, 78, 18, 9, "#d8d4c4", rx=2), R(cx - 1, 85, 20, 3.4, "#c8c4b0", rx=1.4)]
        for lx in (cx + 1, cx + 15): b.append(R(lx, 88, 1.2, 8, "#6a6a68"))
    return wrap(s, d, "".join(b), .3, ("#fff8e0", .05))


def sala_reunioes_ministra():
    s = "sr"
    d = (LG("wl" + s, [(0, "#d9d6cc"), (1, "#c2beb2")]) + LG("fl" + s, [(0, "#9a948a"), (1, "#c8c2b6")]) +
         LG("sk" + s, [(0, "#9cc0e0"), (1, "#e8eef4")]) + LG("tb" + s, [(0, "#8a5a36"), (1, "#5a3820")]) +
         LG("tt" + s, [(0, "#a87a4c"), (1, "#7a4e2c")]))
    b = [R(0, 0, 160, 100, f"url(#wl{s})"), R(0, 0, 160, 3, "#8a8678"), R(0, 3, 160, .5, "#fff", .5), R(0, 70, 160, 4, "#8a8678"),
         R(0, 74, 160, 26, f"url(#fl{s})")]
    # marmore polido: veios + reflexos
    r = random.Random(5)
    for i in range(14):
        x0 = r.uniform(0, 160); y0 = 76 + r.uniform(0, 22)
        b.append(PATH(f"M{f(x0)} {f(y0)}q{f(r.uniform(6, 14))} {f(r.uniform(-2, 2))} {f(r.uniform(12, 24))} {f(r.uniform(-1, 1))}", st="#7a746a", sw=.12, o=.3))
    b.append(pfloor(74, 80, 52, "#6a655a", .35, 16, 5))
    b.append(PG([(60, 74), (130, 74), (150, 100), (50, 100)], "#fff", .1))
    # parede de janelas (janela 60,12,25,30 + faixa)
    for k, (xx, ww2) in enumerate(((84, 20), (108, 24), (136, 22))):
        pass
    wx, wy, ww, wh = P(60, 12, 25, 30)
    skyline = ""
    for k, (bx, bw, bh) in enumerate(((0, 6, 10), (7, 8, 16), (16, 5, 8), (22, 9, 13), (32, 6, 18))):
        skyline += R(wx + bx, wy + wh - bh - 4, bw, bh + 4, "#7f93a8", .85) + R(wx + bx, wy + wh - bh - 4, bw, .4, "#fff", .4)
    skyline += R(wx, wy + wh - 4, ww, 4, "#a9b4b0")
    for i in range(4):
        b.append(window(40 * 1.6 + 0, 8, 1, 1, "sk" + s) if False else "")
    big = window(wx - 18, 8, ww + 36, 44, "sk" + s, frame="#5a5a58", mull=(5, 1), extra=R(wx - 18, 8, ww + 36, 44, "none")
                 + skyline.replace("", ""))
    b += [R(wx - 20, 6, ww + 40, 2, "#7a7a78"), big, skyline, R(wx - 20, 52, ww + 40, 1.8, "#e8e6de"),
          R(wx - 20, 53.6, ww + 40, .8, "#000", .15)]
    for k in range(6):  # persiana vertical recolhida
        b.append(R(wx - 18 + k * (ww + 36) / 6 + 1, 8, .5, 44, "#fff", .3))
    # estante embutida clara (6,10,38,60)
    x, y, w, h = P(6, 10, 38, 60)
    b += [R(x - 1.4, y - 1.4, w + 2.8, h + 2.2, "#e8e4d8"),
          shelf_unit(x, y, w, h, 5, "#f2ede0", "#b9b4a6", 31, ["#3a4a5a", "#7a2630", "#d8d2c0", "#2f4a5a", "#8a8070"], plank="#f2ede0", sparse=.45)]
    # bandeira (90,20,8,30)
    fx, fy, fw, fh = P(90, 20, 8, 30)
    b += [R(fx + fw / 2 - .4, fy - 3, .8, 57, "#c9a04a"), C(fx + fw / 2, fy - 3.4, 1.1, "#e8c46a"),
          banner_flag(fx, fy, fw, fh - 2, "#2a3a5a", "#d8b04a"), E(fx + fw / 2, 74.4, 3.4, .9, "#2a2218")]
    # mesa longa (30,56,40,24): tampo em perspectiva
    mx, my, mw, mh = P(30, 56, 40, 24)
    b += [E(80, 83, 40, 2.4, "#000", .3),
          PG([(mx + 8, my), (mx + mw - 8, my), (mx + mw + 4, my + 13), (mx - 4, my + 13)], f"url(#tt{s})"),
          PG([(mx + 8, my), (mx + mw - 8, my), (mx + mw - 10, my + 1.4), (mx + 10, my + 1.4)], "#c89a68"),
          R(mx - 4, my + 13, mw + 8, 8, f"url(#tb{s})"), R(mx - 4, my + 13, mw + 8, .7, "#c89a68"),
          PG([(mx + 14, my + 3), (mx + mw - 14, my + 3), (mx + mw - 6, my + 11), (mx + 6, my + 11)], "#fff", .07)]
    # cadeiras de couro dos dois lados
    for cx in (mx - 18, mx - 12, mx + mw + 4, mx + mw + 10):
        b += [E(cx + 5, 91, 6.5, 1, "#000", .25), R(cx, 70, 10, 14, "#2a2a2e", rx=2.4), R(cx + 1.2, 71.2, 7.6, 10, "#4a4a52", .6, rx=1.6),
              R(cx - 1, 82, 12, 4, "#2a2a2e", rx=1.4), R(cx + 4.4, 86, 1.2, 6, "#6a6a70"), R(cx + 1, 91.4, 8, .8, "#6a6a70", rx=.4)]
    # computador (46,46,10,10): notebook com grade de cameras
    cx2, cy2, cw, ch = P(46, 46, 10, 10)
    b.append(R(cx2 + 1, cy2 + 8.4, cw - 2, 1.4, "#9a9a98", rx=.4))
    b.append(R(cx2 + 1.4, cy2 + 1.2, cw - 2.8, 7.4, "#15191e", rx=.6))
    for i in range(2):
        for j in range(2):
            b.append(R(cx2 + 2.1 + i * 6.1, cy2 + 2 + j * 3.4, 5.6, 3, "#2a6a86"))
            b.append(R(cx2 + 2.1 + i * 6.1, cy2 + 2 + j * 3.4, 5.6, 1, "#fff", .15))
    # relatorio da varredura + saco de evidencia + fita
    b += [papers(mx + 18, my + 7.4, 9, 6, 3, seed=3), R(mx + 20, my + 8, 5, .4, "#8a8470"), R(mx + 20, my + 9, 4, .4, "#8a8470")]
    b += [PG([(mx + 52, my + 6), (mx + 60, my + 6.4), (mx + 59.4, my + 11), (mx + 51.6, my + 10.6)], "#dfe8ea", .85, st="#9ab0b8", sw=.2),
          R(mx + 53, my + 7.4, 5, 1.6, "#c8b890"), R(mx + 53, my + 6.6, 5.4, .5, "#d83a2a")]
    for k in range(7):  # fita zebrada no canto da mesa
        b.append(PG([(mx + 62 + k * 1.1, my + 12.8), (mx + 63 + k * 1.1, my + 12.8), (mx + 64.4 + k * 1.1, my + 13.6), (mx + 63.4 + k * 1.1, my + 13.6)], "#111" if k % 2 else "#e8c428"))
    b += [PATH(f"M{f(mx+62)} {f(my+13)} L{f(mx+74)} {f(my+22)}", st="#e8c428", sw=.7), PATH(f"M{f(mx+62)} {f(my+13)} L{f(mx+74)} {f(my+22)}", st="#111", sw=.7, o=.0)]
    for k in range(9):
        t = k / 9
        b.append(PG([(mx + 62 + t * 12, my + 13 + t * 9), (mx + 63.2 + t * 12, my + 13.4 + t * 9), (mx + 64.4 + t * 12 - .6, my + 14.8 + t * 9), (mx + 63.2 + t * 12 - .8, my + 14.4 + t * 9)], "#111" if k % 2 else "#e8c428"))
    return wrap(s, d, "".join(b), .4, ("#cfe4ff", .05))


def gabinete_presidencia_stf():
    s = "gp"
    d = (LG("wl" + s, [(0, "#5a3a26"), (1, "#3a2416")]) + LG("fl" + s, [(0, "#d8d0bc"), (1, "#a89e88")]) +
         LG("sk" + s, [(0, "#3a3a7a"), (.55, "#c4608a"), (1, "#f4a860")]) + LG("dk" + s, [(0, "#4a2c1c"), (1, "#2a180e")]) +
         LG("dt" + s, [(0, "#6a3e28"), (1, "#4a2a1a")]) + RG("lg" + s, [(0, "#ffd6a0", .4), (1, "#ffd6a0", 0)]) + LG("gr" + s, [(0, "#1c3a2a"), (1, "#12281c")]))
    b = [R(0, 0, 160, 100, f"url(#wl{s})")]
    for i in range(10): b.append(R(i * 16 + 1.5, 4, 13, 58, "#000", .1, rx=.5)); b.append(R(i * 16 + 2.5, 5, 11, 56, "none", st="#c9a04a", sw=.15, o=.3))
    b += [R(0, 0, 160, 4, "#24140a"), R(0, 4, 160, .6, "#c9a04a", .6)]
    # rodape de marmore
    b += [R(0, 62, 160, 14, "#e2dccb"), R(0, 62, 160, .7, "#c9a04a"), R(0, 76, 160, 24, f"url(#fl{s})")]
    r = random.Random(9)
    for i in range(16): b.append(PATH(f"M{f(r.uniform(0,160))} {f(r.uniform(63,75))}q{f(r.uniform(6,12))} {f(r.uniform(-2,2))} {f(r.uniform(10,22))} {f(r.uniform(-1,1))}", st="#a8a08a", sw=.14, o=.4))
    for i in range(0, 160, 20):
        b.append(R(i + 2, 62, 16, 14, "#000", .05, rx=.4))
    # piso xadrez de marmore
    for j in range(6):
        for i in range(-4, 24):
            if (i + j) % 2:
                y0 = 76 + (24 * (j / 6) ** 1.6); y1 = 76 + (24 * ((j + 1) / 6) ** 1.6)
                xs0 = 80 + (i * 8 - 80) * (1 + (y0 - 76) / 24 * 1.6); xs1 = 80 + ((i + 1) * 8 - 80) * (1 + (y0 - 76) / 24 * 1.6)
                xs2 = 80 + ((i + 1) * 8 - 80) * (1 + (y1 - 76) / 24 * 1.6); xs3 = 80 + (i * 8 - 80) * (1 + (y1 - 76) / 24 * 1.6)
                b.append(PG([(xs0, y0), (xs1, y0), (xs2, y1), (xs3, y1)], "#2a2a2c", .22))
    # brasao generico central + janela ao entardecer
    b += [C(80, 11.5, 4.6, "#c9a04a"), C(80, 11.5, 3.6, "#2a180e"), PG([(80, 8.4), (82.8, 11.5), (80, 14.6), (77.2, 11.5)], "#c9a04a"), C(80, 11.5, 1.1, "#2a180e")]
    wx, wy, ww, wh = 132, 7, 22, 49
    ex = R(wx, wy + wh * .66, ww, wh * .34, "#2a2a3a")
    for k, (bx, bw, bh) in enumerate(((0, 5, 12), (6, 4, 8), (11, 6, 15), (18, 4, 9))):
        ex += R(wx + bx, wy + wh * .66 - bh, bw, bh + 1, "#3a3258") + R(wx + bx + .8, wy + wh * .66 - bh + 1.4, .8, .8, "#ffd070", .8) + R(wx + bx + 2.4, wy + wh * .66 - bh + 3, .8, .8, "#ffd070", .6)
    ex += R(wx, wy + wh * .66, ww, wh * .34, "#2a2a3a", .0)
    for k in range(4): ex += R(wx + 2 + k * 5.6, wy + wh * .7, .4, 6, "#555a70") + C(wx + 2.2 + k * 5.6, wy + wh * .7, .9, "#ffe0a0", .9)
    b += [R(wx - 3.4, wy - 3, ww + 6.8, 2, "#24140a"), PATH(f"M{wx} {wy+wh} V{wy+6} Q{wx+ww/2} {wy-5} {wx+ww} {wy+6} V{wy+wh} Z", fill=f"url(#sk{s})"),
          ex.replace("", ""), R(wx - 1, wy + wh, ww + 2, 1.8, "#e2dccb")]
    b += [PATH(f"M{wx-1} {wy+wh+1.8} V{wy+6} Q{wx+ww/2} {wy-6.4} {wx+ww+1} {wy+6} V{wy+wh+1.8}", st="#24140a", sw=1.2),
          R(wx + ww / 2 - .35, wy - 1, .7, wh + 1, "#24140a"), R(wx, wy + 22, ww, .7, "#24140a")]
    # cortinas
    b += [PATH(f"M{wx-4} {wy-2} q3 22 .5 {wh+2} h5 q-1 -{wh/2} 2 -{wh+2}z", fill="#6a1a24"), PATH(f"M{wx+ww+4} {wy-2} q-3 22 -.5 {wh+2} h-5 q1 -{wh/2} -2 -{wh+2}z", fill="#6a1a24")]
    # quadro de presencas (4,18,12,26) e molduras de documentos
    qx, qy, qw, qh = P(4, 18, 12, 26)
    b += [R(qx - .8, qy - .8, qw + 1.6, qh + 1.6, "#c9a04a", rx=.5), R(qx, qy, qw, qh, f"url(#gr{s})"), R(qx, qy, qw, 2.6, "#0e1c14")]
    for j in range(7):
        for i in range(4):
            cc = ["#58d878", "#58d878", "#d85858", "#58d878", "#e8c040"][(i * 3 + j * 2) % 5]
            b += [R(qx + 1.4 + i * 3.8, qy + 4 + j * 3.1, 3, 1.8, "#0a140e", rx=.3), C(qx + 2.9 + i * 3.8, qy + 4.9 + j * 3.1, .55, cc)]
    for (px, py, pw, ph, sd) in ((20, 18, 24, 22, 1), (56, 18, 24, 22, 2)):
        fx, fy, fw, fh = P(px, py, pw, ph)
        b += [R(fx - 1.2, fy - 1.2, fw + 2.4, fh + 2.4, "#c9a04a", st="#6a5224", sw=.3), R(fx, fy, fw, fh, "#efe6cf"), R(fx, fy, fw, fh, "#000", .07),
              R(fx + 2, fy + 2, fw * .6, .9, "#5a5240", .9)]
        for k in range(8): b.append(R(fx + 2, fy + 4.4 + k * 1.7, fw - 4 - (k % 3) * 3, .4, "#8a8470", .8))
        b += [C(fx + fw - 4, fy + fh - 3.6, 2, "#8a2a2a"), PG([(fx + fw - 5.4, fy + fh - 2), (fx + fw - 4, fy + fh + .4), (fx + fw - 2.6, fy + fh - 2)], "#8a2a2a")]
    # mesa enorme: tampo fundo + frente
    b += [E(80, 85, 70, 2.4, "#000", .3),
          PG([(6, 56), (144, 56), (150, 72), (2, 72)], f"url(#dt{s})"), PG([(6, 56), (144, 56), (143, 57.4), (7, 57.4)], "#8a5a3a"),
          R(2, 72, 148, 12, f"url(#dk{s})"), R(2, 72, 148, .8, "#c9a04a"), R(2, 83, 148, .8, "#c9a04a", .6)]
    for k in range(5):
        b += [R(8 + k * 29, 74.4, 25, 7.4, "#000", .2, rx=.4, st="#c9a04a", sw=.2), R(18 + k * 29, 77.4, 5, .7, "#d8b04a", rx=.3)]
    b.append(PG([(8, 58), (80, 58), (82, 70), (6, 70)], "#1a3a2a", .45))
    # documentos nos pontos
    def doc(ax, ay, aw, ah, tint, sd, stk=3):
        r2 = random.Random(sd)
        o = [PG([(ax + 3, ay + 2), (ax + aw - 3, ay + 2), (ax + aw - 1.5, ay + ah - 5), (ax + 1.5, ay + ah - 5)], tint, st="#000", sw=.15),
             PG([(ax + 3, ay + 2), (ax + aw * .4, ay + 2), (ax + aw * .4 - 1, ay + 1), (ax + 5, ay + 1)], tint)]
        for i in range(stk):
            o.append(PG([(ax + 5 + i * .9, ay + 4 - i * .5), (ax + aw - 5 + i * .9, ay + 4 - i * .5), (ax + aw - 4 + i * .9, ay + ah - 8 - i * .5), (ax + 4 + i * .9, ay + ah - 8 - i * .5)], "#f2ecd8", st="#b8ae92", sw=.12))
        for k in range(5): o.append(R(ax + 6.4, ay + 5.4 + k * 1.5, aw * .5 - (k % 2) * 3, .35, "#7a7460", .8))
        o.append(C(ax + aw - 7.4, ay + ah - 11, 1.3, "#8a2a2a", .9))
        return "".join(o)
    b += [doc(*P(8, 54, 24, 24), "#8a3a3a", 1), doc(*P(36, 56, 22, 24), "#2a4a7a", 2), doc(*P(62, 56, 22, 24), "#c9b070", 3)]
    b += [cup(138, 66, 1.1), PATH("M0 0", st="none")]
    b += [R(124, 60.4, 8, 2.6, "#d8d2c0"), R(124, 62.4, 8, .6, "#2a1c14"), R(124, 59.4, 8, 1.2, "#7a1f2a")]  # livro de regras encadernado
    for fxp in (97, 101):
        b += [R(fxp, 55.6, .4, 5.6, "#c9a04a"), R(fxp + .4, 55.8, 3.2, 2.2, "#233a6a" if fxp == 97 else "#2a5a3a")]
    b += [armchair(14, 78, 22, 19, "#6a2a22", "#b8704c"), armchair(124, 78, 22, 19, "#6a2a22", "#b8704c")]
    b.append(E(138, 44, 22, 26, f"url(#lg{s})"))
    return wrap(s, d, "".join(b), .6, ("#ff9a50", .05))


def corredor_stf():
    s = "cs"
    d = (LG("cl" + s, [(0, "#8e8a82"), (1, "#bdb8ae")]) + LG("wl" + s, [(0, "#cfc8b8"), (1, "#e6e0d0")]) + LG("wr" + s, [(0, "#e6e0d0"), (1, "#cfc8b8")]) +
         LG("fl" + s, [(0, "#a8a296"), (.4, "#d8d2c4"), (1, "#8a8478")]) + LG("dr" + s, [(0, "#4a2c1c"), (1, "#2a180e")]) +
         LG("bk" + s, [(0, "#fffbe8"), (1, "#dce8f4")]) + RG("lg" + s, [(0, "#fff4d0", .6), (1, "#fff4d0", 0)]) + LG("lp" + s, [(0, "#fffbe6"), (1, "#f6e8b8")]))
    VX0, VX1, TY, BY = 62, 98, 34, 60  # fundo do corredor
    b = [R(0, 0, 160, 100, "#2a2418"),
         PG([(0, 0), (160, 0), (VX1, TY), (VX0, TY)], f"url(#cl{s})"),
         PG([(0, 0), (VX0, TY), (VX0, BY), (0, 86)], f"url(#wl{s})"), PG([(160, 0), (VX1, TY), (VX1, BY), (160, 86)], f"url(#wr{s})"),
         PG([(0, 86), (VX0, BY), (VX1, BY), (160, 86), (160, 100), (0, 100)], f"url(#fl{s})")]

    def lw(xa, xb, v0, v1, side=0):
        """quad na parede esquerda (side 0) ou direita (1); x em coords da esquerda; v: 0 piso .. 1 teto."""
        def top(x): return TY * x / VX0
        def bot(x): return 86 - (86 - BY) * x / VX0
        pts = []
        for x, v in ((xa, v0), (xa, v1), (xb, v1), (xb, v0)):
            y = bot(x) + v * (top(x) - bot(x))
            pts.append((160 - x if side else x, y))
        return pts
    # fundo luminoso
    b += [R(VX0, TY, VX1 - VX0, BY - TY, "#bfb6a0"), R(VX0 + 3, TY + 2.4, VX1 - VX0 - 6, BY - TY - 2.4, f"url(#bk{s})"), R(79.5, TY + 2.4, 1, BY - TY - 2.4, "#8a8270"),
          E(80, 47, 22, 15, f"url(#lg{s})")]
    # lampadas no teto
    for yy in (4, 14, 21.6, 26.6, 30, 32.2):
        t = (TY - yy) / TY
        hw = 80 - (62 * yy / TY) - 4 if False else (80 - 62 * yy / TY)
        wdt = max(3, hw * .55 * (1 - t * .0))
        b += [R(80 - wdt / 2, yy, wdt, 1 + (TY - yy) * .05, f"url(#lp{s})"), E(80, yy + .8, wdt * .8, 1.2, "#fff4d0", .25)]
    # portas altas de madeira escura + pilastras
    marks = [(2, 10), (14, 22), (27, 34), (40, 45.5), (50, 54.5)]
    for side in (0, 1):
        for (xa, xb) in marks:
            fr = lw(xa, xb, 0, .9, side)
            b.append(PG(fr, "#1a0e06"))
            inn = lw(xa + (xb - xa) * .1, xb - (xb - xa) * .1, 0, .88, side)
            b.append(PG(inn, f"url(#dr{s})"))
            pn = lw(xa + (xb - xa) * .25, xb - (xb - xa) * .25, .4, .82, side)
            b.append(PG(pn, "#000", .22, st="#8a5a38", sw=.12))
            kn = lw(xb - (xb - xa) * .22, xb - (xb - xa) * .17, .38, .42, side)
            b.append(PG(kn, "#d9b86a"))
            tp = lw(xa, xb, .9, .94, side)
            b.append(PG(tp, "#c9a04a", .5))
        # rodape + friso em marmore escuro
        b.append(PG(lw(0, VX0, 0, .06, side), "#5a5650", .7)); b.append(PG(lw(0, VX0, .06, .07, side), "#e8e0c4"))
        for xa in (12, 25, 38, 48, 56):
            b.append(PG(lw(xa - .5, xa + .5, .1, .86, side), "#000", .14))
        # arandela
        for xa in (12.5, 38.5):
            sc = lw(xa, xa + 2, .62, .72, side)
            b.append(PG(sc, "#fff0c0"));
    # banco e carrinho de cafe ao fundo
    b += [R(66.5, 53, 9, .8, "#5a3a22"), R(67, 53.8, .6, 2.4, "#2a1a10"), R(74.4, 53.8, .6, 2.4, "#2a1a10"), R(66.5, 50.6, 9, 1.6, "#6a4a30", .9),
          R(84.5, 50.5, 7, 4.8, "#d8d0bc"), R(84.5, 50.5, 7, .7, "#fff", .5), R(85.4, 47.6, 2.2, 2.9, "#8a8a90"), R(88, 48.6, 2.8, 1.9, "#b8312a"),
          C(85.5, 55.6, .7, "#222"), C(90.4, 55.6, .7, "#222")]
    # chao: reflexos
    for xx, yy, ww in ((80, 62, 9), (80, 67, 12), (80, 75, 18), (80, 88, 30)):
        b.append(E(xx, yy, ww, 1.1 + (yy - 60) * .05, "#fff4d0", .24))
    b.append(PG([(70, 60), (90, 60), (118, 100), (42, 100)], "#fff", .07))
    b.append(pfloor(BY, 80, 38, "#6a6252", .45, 12, 6, span=420))
    r = random.Random(3)
    for i in range(10):
        x0 = r.uniform(0, 160); y0 = 64 + r.uniform(0, 34)
        b.append(PATH(f"M{f(x0)} {f(y0)}q{f(r.uniform(5,10))} {f(r.uniform(-1.4,1.4))} {f(r.uniform(10,20))} {f(r.uniform(-.8,.8))}", st="#7a7466", sw=.12, o=.4))
    return wrap(s, d, "".join(b), .5, None)


def cafe_stf():
    s = "cf"
    d = (LG("wl" + s, [(0, "#8a5a38"), (1, "#6a4228")]) + LG("fl" + s, [(0, "#c8b898"), (1, "#a8977a")]) +
         LG("sk" + s, [(0, "#bcd8ee"), (1, "#f4f0dc")]) + LG("cn" + s, [(0, "#5a3a22"), (1, "#3a2414")]) + LG("tp" + s, [(0, "#7a4a2a"), (1, "#5a3418")]) +
         RG("lg" + s, [(0, "#ffe9b0", .5), (1, "#ffe9b0", 0)]))
    b = [R(0, 0, 160, 100, f"url(#wl{s})")]
    for i in range(32): b.append(R(i * 5, 0, .35, 68, "#000", .22)); b.append(R(i * 5 + .35, 0, .25, 68, "#fff", .06))
    b += [R(0, 0, 160, 3, "#2a170c"), R(0, 44, 160, 1, "#2a170c", .7), R(0, 44, 160, .35, "#d8a870", .7),
          R(0, 68, 160, 6, "#3a2414"), R(0, 68, 160, .6, "#d8a870", .6), R(0, 74, 160, 26, f"url(#fl{s})")]
    # piso xadrez
    for j in range(6):
        for i in range(-6, 26):
            if (i + j) % 2:
                y0 = 74 + 26 * (j / 6) ** 1.5; y1 = 74 + 26 * ((j + 1) / 6) ** 1.5
                k0 = 1 + (y0 - 74) / 26 * 1.5; k1 = 1 + (y1 - 74) / 26 * 1.5
                b.append(PG([(80 + (i * 8 - 80) * k0, y0), (80 + ((i + 1) * 8 - 80) * k0, y0), (80 + ((i + 1) * 8 - 80) * k1, y1), (80 + (i * 8 - 80) * k1, y1)], "#6a4a2e", .45))
    # janela no canto direito alto, com toldo
    wx, wy, ww, wh = 122, 8, 30, 27
    ex = R(wx, wy + wh * .55, ww, wh * .45, "#8a9aa0", .8) + R(wx + 3, wy + wh * .2, 7, wh * .5, "#a8b4b8") + R(wx + 14, wy + wh * .3, 9, wh * .4, "#9eaab0") + R(wx, wy + wh * .8, ww, wh * .2, "#c8c4b0")
    b += [window(wx, wy, ww, wh, "sk" + s, frame="#2a170c", mull=(2, 0), extra=ex),
          PG([(wx - 2, wy - 1), (wx + ww + 2, wy - 1), (wx + ww + 3, wy + 4), (wx - 3, wy + 4)], "#a8362a")]
    for k in range(8): b.append(PG([(wx - 2 + k * (ww + 4) / 8, wy - 1), (wx - 2 + (k + .5) * (ww + 4) / 8, wy - 1), (wx - 3 + (k + .5) * (ww + 6) / 8, wy + 4), (wx - 3 + k * (ww + 6) / 8, wy + 4)], "#f0e6d2"))
    b.append(E(138, 40, 26, 14, f"url(#lg{s})"))
    # PDF original (8,24,16,18): quadro de cortica com folha
    qx, qy, qw, qh = P(8, 24, 16, 18)
    b += [R(qx - 1, qy - 1, qw + 2, qh + 2, "#4a2c18", rx=.4), R(qx, qy, qw, qh, "#b8885a"), R(qx, qy, qw, qh, "#000", .06)]
    rr = random.Random(2)
    for i in range(30): b.append(C(qx + rr.uniform(.5, qw - .5), qy + rr.uniform(.5, qh - .5), .25, "#8a5a32", .6))
    b += [R(qx + 2.4, qy + 1.4, qw * .5, qh * .72, "#f4efe0", st="#b8ae92", sw=.12), R(qx + 3.2, qy + 2.4, qw * .3, .5, "#7a2a2a"), C(qx + 2.8 + qw * .24, qy + 1.4, .55, "#d83a3a")]
    for k in range(6): b.append(R(qx + 3.2, qy + 4 + k * 1.3, qw * .38 - (k % 2), .35, "#8a8470"))
    b += [R(qx + qw * .52, qy + qh * .45, qw * .4, qh * .4, "#e8d878", .95), R(qx + qw * .56, qy + qh * .55, qw * .28, .35, "#8a7a30")]
    # caderno de notas (54,26,16,16) numa prateleira alta com suporte
    nx, ny, nw, nh = P(54, 26, 16, 16)
    b += [R(nx - 3, ny + nh, nw + 6, 1.4, "#2a170c"), R(nx - 3, ny + nh, nw + 6, .35, "#d8a870", .7),
          PG([(nx + 1, ny + nh), (nx + nw / 2, ny + 2), (nx + nw - 1, ny + nh)], "#000", .12),
          R(nx + 1, ny + 2, nw / 2 - .6, nh - 2, "#f4efe0", st="#b8ae92", sw=.12), R(nx + nw / 2 + .6, ny + 2, nw / 2 - 1.6, nh - 2, "#f0ead8", st="#b8ae92", sw=.12),
          R(nx + nw / 2 - .6, ny + 1.6, 1.2, nh - 1.2, "#2a2a30")]
    for k in range(6):
        b += [R(nx + 2, ny + 4 + k * 1.6, nw / 2 - 3.4, .3, "#6a86a8", .8), R(nx + nw / 2 + 1.6, ny + 4 + k * 1.6, nw / 2 - 3.4 - (k % 2), .3, "#6a86a8", .8)]
    for k in range(6): b.append(C(nx + nw / 2, ny + 2.4 + k * 2, .35, "#cfcfcf"))
    # balcao ao fundo a direita
    b += [R(96, 52, 64, 4, f"url(#tp{s})"), R(96, 52, 64, .6, "#d8a870", .7), R(96, 56, 64, 18, f"url(#cn{s})")]
    for k in range(8): b += [R(98 + k * 7.6, 58, 6.4, 14, "#000", .2, rx=.3, st="#8a5a38", sw=.2)]
    b += [E(150, 50, 4.4, 1.2, "#000", .0), R(144, 40, 9, 12, "#cfcfd2", rx=1.2), R(145, 41, 7, 3, "#2a2a30", rx=.4), C(148.5, 47, 1.7, "#7a1f1a"), R(144, 51, 9, 1, "#2a2a30"),
          E(108, 51, 5, 1.6, "#d8d0bc", .0), R(104, 46.4, 9, 5, "#e8e2d0", rx=2.6), R(104, 49.6, 9, 2.4, "#e8e2d0"), R(103.6, 51.4, 9.8, .8, "#c8c0a8")]
    # lustres
    for lx in (30, 76, 122):
        b += [L(lx, 3, lx, 17, "#1a100a", .3), PATH(f"M{lx-4} 21 Q{lx-4} 16.4 {lx} 16.4 Q{lx+4} 16.4 {lx+4} 21Z", fill="#2a1c12"), E(lx, 21, 4.2, .8, "#fff2c0"), E(lx, 22.4, 12, 3.4, "#ffe9b0", .18)]
    def mesa(cx, cy, rw, col="#7a4a2a"):
        o = [E(cx, cy + rw * .4 + 6, rw * 1.1, rw * .22, "#000", .3), R(cx - .8, cy + 1, 1.6, 7 + rw * .3, "#2a2a30"), E(cx, cy + 8 + rw * .3, rw * .5, .9, "#2a2a30"),
             E(cx, cy, rw, rw * .3, "#5a3418"), E(cx, cy - .6, rw, rw * .3, "#8a5a36"), E(cx, cy - .6, rw * .88, rw * .24, "#a8764a", .6)]
        return "".join(o)
    def cadeira(cx, cy, flip=1):
        return "".join([R(cx - 3, cy - 10, 6, 1.2, "#3a2414", rx=.5), R(cx - 2.4, cy - 10, .7, 10, "#3a2414"), R(cx + 1.7, cy - 10, .7, 10, "#3a2414"),
                        R(cx - 3.4, cy - 1.4, 6.8, 1.4, "#4a2c18", rx=.5), R(cx - 2.6, cy, .7, 5, "#2a1a10"), R(cx + 1.9, cy, .7, 5, "#2a1a10")])
    # mesa de fundo (e-mail anonimo) 30,50,16,14 ; Saulo 76,48,14,14 ; xicara 18,70,14,14
    ax, ay, aw, ah = P(30, 50, 16, 14)
    b += [cadeira(ax + 3, ay + 4), cadeira(ax + aw - 3, ay + 4), mesa(ax + aw / 2, ay + ah * .55, aw * .5),
          PG([(ax + 7, ay + 5.6), (ax + aw - 7, ay + 5), (ax + aw - 6, ay + 10), (ax + 6, ay + 10.6)], "#f6f1e2", st="#b8ae92", sw=.15)]
    for k in range(5): b.append(R(ax + 9, ay + 6.8 + k * .7, aw - 18 - (k % 2) * 3, .3, "#8a8470"))
    b.append(R(ax + 9, ay + 6, aw - 20, .5, "#4a4a58"))
    sx, sy, sw_, sh = P(76, 48, 14, 14)
    b += [cadeira(sx + 2.4, sy + 3), cadeira(sx + sw_ - 2.4, sy + 3), mesa(sx + sw_ / 2, sy + sh * .55, sw_ * .5),
          PG([(sx + 8, sy + 4.4), (sx + 12.8, sy + 4.6), (sx + 12.4, sy + 11), (sx + 7.6, sy + 10.8)], "#15181e", st="#3a3e48", sw=.2),
          PG([(sx + 8.5, sy + 5.2), (sx + 12.2, sy + 5.3), (sx + 11.9, sy + 10.2), (sx + 8.2, sy + 10)], "#3a76a6"), R(sx + 9, sy + 6, 2.6, .5, "#cfe6f8"), R(sx + 9, sy + 7.2, 2, .5, "#cfe6f8"), R(sx + 9, sy + 8.4, 2.4, .5, "#cfe6f8")]
    cx0, cy0, cw0, ch0 = P(18, 70, 14, 14)
    b += [mesa(cx0 + cw0 / 2, cy0 + 6, cw0 * .5), E(cx0 + cw0 / 2 + .6, cy0 + 5.2, 3.6, 1.1, "#e8e0cc"), R(cx0 + cw0 / 2 - 1.6, cy0 + 1.4, 4.4, 3.8, "#f4efe4", rx=.7),
          E(cx0 + cw0 / 2 + .6, cy0 + 1.5, 2.2, .7, "#4a3320"), PATH(f"M{f(cx0+cw0/2+2.8)} {f(cy0+2.4)}q2 .2 1.8 1.4t-1.8 1.2", st="#f4efe4", sw=.5),
          R(cx0 + cw0 / 2 - 5.6, cy0 + 3.6, 3.4, .5, "#c8c0a8", .9)]
    return wrap(s, d, "".join(b), .45, ("#ffcf90", .04))


def praca_tres_poderes():
    s = "pr"
    d = (LG("sk" + s, [(0, "#4f9ad8"), (.7, "#9cd0f0"), (1, "#f4f0d8")]) + LG("gr" + s, [(0, "#bfb8a8"), (1, "#9a9384")]) +
         LG("bl" + s, [(0, "#f2eee2"), (1, "#d6d0c0")]) + LG("tl" + s, [(0, "#2a3a5a"), (1, "#1a2540")]))
    b = [R(0, 0, 160, 100, f"url(#sk{s})")]
    # nuvens
    for (cx, cy, rx) in ((10, 8, 12), (40, 20, 8), (130, 10, 10), (150, 24, 7)):
        b += [E(cx, cy, rx, 2, "#fff", .5), E(cx + 3, cy - 1.2, rx * .6, 1.6, "#fff", .6)]
    # predios modernistas: duas torres gemeas, cupula e tigela (genericos)
    b += [R(0, 40, 160, 5, "#e6e2d4"), R(0, 44.4, 160, .6, "#9a9384", .5)]
    b += [R(18, 36, 40, 4.4, f"url(#bl{s})"), R(20, 38, 36, 1.4, "#8aa0b4", .5)]
    for k in range(18): b.append(R(21 + k * 1.95, 38, .5, 1.6, "#6a7a8a", .6))
    b += [PATH("M100 40 Q108 28 116 40Z", fill="#e8e4d6"), PATH("M120 40 Q128 46 136 40Z", fill="#c8c2b0"), R(98, 40, 40, 1.4, "#e6e2d4")]
    b += [R(76, 24, 5.4, 17, f"url(#bl{s})"), R(83, 24, 5.4, 17, f"url(#bl{s})")]
    for k in range(10): b += [R(77, 25.4 + k * 1.5, 3.4, .6, "#7a8fa4", .8), R(84, 25.4 + k * 1.5, 3.4, .6, "#7a8fa4", .8)]
    b += [R(76, 24, 12.4, .5, "#fff", .6), R(76, 40, 12.4, 1.6, "#d6d0c0")]
    # praca de concreto
    b += [R(0, 45, 160, 55, f"url(#gr{s})")]
    b.append(pfloor(45, 80, 40, "#6a6558", .5, 22, 7, span=520))
    b.append(PG([(0, 100), (160, 100), (160, 90), (0, 96)], "#fff", .08))
    # telao dos canais de noticias (46,10,28,24) em estrutura
    tx, ty, tw, th = P(46, 10, 28, 24)
    b += [R(tx + 2, ty + th, 1.6, 46 - th + 8, "#3a3e46"), R(tx + tw - 3.6, ty + th, 1.6, 46 - th + 8, "#3a3e46"),
          L(tx + 2.8, ty + th, tx + tw - 2.8, 52, "#4a4e56", .4), L(tx + tw - 2.8, ty + th, tx + 2.8, 52, "#4a4e56", .4),
          R(tx - .8, ty - .8, tw + 1.6, th + 1.6, "#15181e", rx=.5), R(tx, ty, tw, th, f"url(#tl{s})")]
    for i in range(3):
        for j in range(2):
            b += [R(tx + .8 + i * (tw - 1.6) / 3, ty + .8 + j * (th - 1.6) / 2, (tw - 1.6) / 3 - .5, (th - 1.6) / 2 - .5, ["#2f6a9a", "#9a3a3a", "#3a8a6a", "#c8a03a", "#5a4a9a", "#2a8aa0"][i + j * 3], .9)]
            b += [R(tx + 1.6 + i * (tw - 1.6) / 3, ty + 2 + j * (th - 1.6) / 2, 6, .5, "#fff", .8), R(tx + 1.6 + i * (tw - 1.6) / 3, ty + 3.4 + j * (th - 1.6) / 2, 4, .4, "#fff", .6)]
    b.append(R(tx, ty, tw, th * .35, "#fff", .06))
    # mastro e bandeira (14,8,20,22) - bandeira generica
    fx, fy, fw, fh = P(14, 8, 20, 22)
    b += [R(fx - .8, fy - 2, 1.4, 56, "#d8d4c8"), C(fx - .1, fy - 2.4, 1.2, "#e8c46a"), E(fx - .1, 54.4, 3, 1, "#7a7568")]
    b += [PATH(f"M{f(fx+.6)} {f(fy)} Q{f(fx+fw*.35)} {f(fy-2)} {f(fx+fw*.7)} {f(fy+.6)} T{f(fx+fw)} {f(fy+.2)} V{f(fy+fh*.58)} Q{f(fx+fw*.75)} {f(fy+fh*.58+2)} {f(fx+fw*.5)} {f(fy+fh*.58)} T{f(fx+.6)} {f(fy+fh*.58+.4)}Z", fill="#2a5a9a")]
    b += [PATH(f"M{f(fx+.6)} {f(fy+fh*.38)} Q{f(fx+fw*.3)} {f(fy+fh*.38-1.4)} {f(fx+fw*.6)} {f(fy+fh*.38)} T{f(fx+fw)} {f(fy+fh*.4)} V{f(fy+fh*.5)} Q{f(fx+fw*.7)} {f(fy+fh*.5+1)} {f(fx+fw*.4)} {f(fy+fh*.5)} T{f(fx+.6)} {f(fy+fh*.52)}Z", fill="#e8c840", o=.95)]
    b += [PG([(fx + fw * .5, fy + 1.6), (fx + fw * .62, fy + fh * .3), (fx + fw * .5, fy + fh * .44), (fx + fw * .38, fy + fh * .3)], "#f4f0e0"), C(fx + fw * .5, fy + fh * .3, 1.1, "#2a5a9a")]
    # carro de som (38,40,22,22): caminhao com caixas
    cx, cy, cw, ch = P(38, 40, 22, 22)
    b += [E(cx + cw / 2, cy + ch - .6, cw * .55, 1.4, "#000", .3), R(cx + 1, cy + 6, cw * .68, ch - 11, "#e8e4d6", rx=.8), R(cx + 1, cy + ch - 9, cw * .68, 2.4, "#2a5a8a"),
          PATH(f"M{f(cx+cw*.7)} {f(cy+ch-5)} V{f(cy+10)} H{f(cx+cw*.88)} L{f(cx+cw-1)} {f(cy+ch-9)} V{f(cy+ch-5)}Z", fill="#d8d4c4"),
          PG([(cx + cw * .72, cy + 11), (cx + cw * .87, cy + 11), (cx + cw * .96, cy + ch - 9.4), (cx + cw * .72, cy + ch - 9.4)], "#4a6a88", .9)]
    for wxp in (cx + cw * .2, cx + cw * .5, cx + cw * .82): b += [C(wxp, cy + ch - 3.2, 2.1, "#15181e"), C(wxp, cy + ch - 3.2, .9, "#7a8088")]
    b += [R(cx + 2, cy + 1, 3.4, 5.4, "#2a2e36", rx=.5), R(cx + 5.8, cy + 2.4, 3.4, 4, "#2a2e36", rx=.5), R(cx + 10, cy + 1, 3.4, 5.4, "#2a2e36", rx=.5), R(cx + 13.4, cy + 4.2, 4, .5, "#2a2e36")]
    for k in range(3): b.append(C(cx + 3.7 + k * 4.2, cy + 3.6, .9 if k != 1 else .6, "#8a8e96"))
    b += [R(cx + 1, cy + 6, cw * .68, 1, "#fff", .5), L(cx + 6, cy + 7, cx + 6, cy + ch - 9, "#9a9684", .3)]
    # vigilia da Obra Segura (66,52,24,26): faixas sem texto, velas, tenda
    vx, vy, vw, vh = P(66, 52, 24, 26)
    b += [PG([(vx + 1, vy + 8), (vx + vw * .55, vy + 1), (vx + vw - 1, vy + 8)], "#d8d0b0"), R(vx + 1, vy + 8, vw - 2, 1, "#a8a088"),
          R(vx + 1.6, vy + 9, .8, vh - 9, "#6a6a68"), R(vx + vw - 2.4, vy + 9, .8, vh - 9, "#6a6a68"), R(vx + 3, vy + 9, vw - 6, vh - 12, "#000", .12)]
    for k, c in enumerate(("#e8c428", "#2a8a58", "#e8c428")):
        b += [R(vx + 2 + k * 11.4, vy + 11 + k % 2 * 1.4, 10, 5, c), R(vx + 2.6 + k * 11.4, vy + 12.6 + k % 2 * 1.4, 7, .6, "#15181e", .6), R(vx + 2.6 + k * 11.4, vy + 13.8 + k % 2 * 1.4, 5, .6, "#15181e", .5)]
    b.append(PATH(f"M{f(vx+1)} {f(vy+vh-3)} h{f(vw-2)}", st="#7a7468", sw=.5))
    for k in range(9):
        px = vx + 3 + k * 4.2
        b += [R(px, vy + vh - 3.4, 1.4, 2.4, "#efe6cf"), PATH(f"M{f(px+.7)} {f(vy+vh-5.8)} q-.9 1.2 0 2 q.9 -.8 0 -2", fill="#ffd060"), C(px + .7, vy + vh - 4.4, 1.9, "#ffd060", .22)]
    b += [R(vx + 2, vy + vh - 7.4, 3.2, 4, "#8a5a3a"), R(vx + 2, vy + vh - 7.4, 3.2, .6, "#d8a870")]
    # grade do lado leste (6,54,26,26)
    gx, gy, gw, gh = P(6, 54, 26, 26)
    b += [R(gx, gy + 1.4, gw, 1.2, "#2a2e34"), R(gx, gy + gh - 2, gw, 1.4, "#2a2e34"), R(gx - .6, gy, 1.8, gh + 1.4, "#3a3e46"), R(gx + gw - 1.2, gy, 1.8, gh + 1.4, "#3a3e46")]
    n = int(gw / 2.2)
    for k in range(n + 1):
        xx = gx + 1.2 + k * (gw - 2.4) / n
        b += [R(xx - .3, gy + 2.6, .7, gh - 4.6, "#2a2e34"), PG([(xx - .5, gy + 2.6), (xx, gy + .8), (xx + .5, gy + 2.6)], "#2a2e34"), R(xx - .3, gy + 2.6, .2, gh - 4.6, "#fff", .25)]
    b.append(R(gx - 2, gy + gh + 1.4, gw + 4, .8, "#000", .2))
    # tripes de camera no piso (sem pessoas)
    for (tx2, ty2, sc, col) in ((72, 82, 1.0, "#1a1d22"), (122, 90, 1.2, "#1a1d22"), (30, 90, 1.1, "#1a1d22")):
        b += [L(tx2, ty2 - 9 * sc, tx2 - 4 * sc, ty2, col, .6), L(tx2, ty2 - 9 * sc, tx2 + 4 * sc, ty2, col, .6), L(tx2, ty2 - 9 * sc, tx2 + .4, ty2 + .6, col, .5),
              R(tx2 - 2.6 * sc, ty2 - 13 * sc, 5.2 * sc, 3.6 * sc, "#262a32", rx=.6), R(tx2 + 1.8 * sc, ty2 - 12.6 * sc, 2.6 * sc, 2.4 * sc, "#15181e", rx=.4), C(tx2 + 3.2 * sc, ty2 - 11.4 * sc, .9 * sc, "#3a5a8a")]
    return wrap(s, d, "".join(b), .3, ("#fff0c0", .06))


SCENES = dict(gabinete_instrutor_stf=gabinete_instrutor_stf, sala_das_partes_stf=sala_das_partes_stf, sala_reunioes_ministra=sala_reunioes_ministra,
              gabinete_presidencia_stf=gabinete_presidencia_stf, corredor_stf=corredor_stf, cafe_stf=cafe_stf, praca_tres_poderes=praca_tres_poderes)
