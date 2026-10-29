"""Gera os fundos do tribunal (acusacao, defesa, testemunha, juiz) + juri e stf. Uso: python gen_antigos_a.py"""
from pathlib import Path

from lib_cen import *

AQUI = Path(__file__).resolve().parent


def tribunal(name, seed, wall, wood, accent='#d8b45a'):
    s = Scene(name, seed)
    wg = s.lin([(0, wall[0]), (1, wall[1])])
    s.add(rect(0, 0, 160, 100, wg))
    for i in range(0, 160, 8):
        s.add(rect(i, 4, 4, 52, '#000', .035))
    # pilastras
    for x in (0, 56, 104):
        s.add(rect(x + 2, 5, 3.2, 50, '#fff', .07), rect(x + 5.2, 5, .6, 50, '#000', .1))
    # teto/sanca
    s.add(rect(0, 0, 160, 4.2, '#2a1a12'), rect(0, 4.2, 160, .7, accent, .65), rect(0, 4.9, 160, 6, s.lin([(0, '#000', .3), (1, '#000', 0)])))
    # lambri
    s.add(rect(0, 54, 160, 46, s.lin([(0, wood[0]), (1, wood[1])])))
    s.add(rect(0, 53, 160, 2.2, '#c9955c'), rect(0, 55.2, 160, .8, '#000', .3), rect(0, 53, 160, .5, '#fff', .3))
    for i in range(10):
        x = 3 + i * 16
        s.add(rect(x, 58.5, 11, 24, '#000', .2, rx=.6, stroke='#000', sw=.1), rect(x + 1, 59.5, 9, 22, wood[0], .55, rx=.4),
              rect(x + 1, 59.5, 9, 1, '#fff', .12), rect(x + 1, 80.6, 9, .9, '#000', .2))
    s.add(rect(0, 84.5, 160, 2, '#2a1a10'), rect(0, 84.5, 160, .5, '#c9955c', .6))
    s.add(floor_persp(s, 86.5, wood[1], '#2a1a10', vpy=60, n=14, m=5, gloss=.1))
    return s


def acusacao():
    s = tribunal('ac', 11, ('#dba99d', '#c28b7e'), ('#9a6a42', '#6e4828'))
    s.add(shelf_unit(s, 12, 14, 26, 36, 4, wood='#5a2e22', back='#2a1612', plank='#a56a44'))
    s.add(rect(10, 51.5, 30, 2, '#5a2e22', rx=.5), rect(10, 51.5, 30, .5, '#fff', .2))
    s.add(arch_window(s, 120, 14, 22, 36, frame='#5a3a22', sill='#7a5232'))
    s.add(curtain(s, 144, 16, 6, 54, '#9a2a2e'))
    s.add(curtain(s, 0, 7, 6, 54, '#7a1f24'))
    s.add(emblem(s, 80, 17, 7.5, bg='#4a2a24'))
    pendant(s, 52, 4, 15, 54, glow='#ffe2b0'); pendant(s, 108, 4, 15, 54, glow='#ffe2b0')
    s.add(frame_art(46, 32, 10, 7, 0, frame='#5a2e22'), frame_art(104, 32, 10, 7, 1, frame='#5a2e22'))
    s.add(poly([(116, 52), (140, 52), (152, 84), (108, 84)], '#fff', .06))
    return s


def defesa():
    s = tribunal('de', 12, ('#b4c5de', '#8fa6c8'), ('#8a6040', '#5e3e24'))
    s.add(arch_window(s, 20, 14, 22, 36, sky=('#8fc0ea', '#eaf3fb'), frame='#4a3220', sill='#6a4a2c'))
    s.add(shelf_unit(s, 122, 14, 26, 36, 4, wood='#2a3a5a', back='#12182a', plank='#6a7a9a', pal=['#2e4a7a', '#7a2e2e', '#3a5a6a', '#8a6a2e', '#b0a088', '#2e6a4a']))
    s.add(rect(120, 51.5, 30, 2, '#2a3a5a', rx=.5), rect(120, 51.5, 30, .5, '#fff', .2))
    s.add(curtain(s, 0, 16, 6, 54, '#2f4f94'))
    s.add(curtain(s, 150, 10, 6, 54, '#27427e'))
    s.add(emblem(s, 80, 17, 7.5, bg='#243556'))
    pendant(s, 52, 4, 15, 54, glow='#fff0cc'); pendant(s, 108, 4, 15, 54, glow='#fff0cc')
    s.add(frame_art(46, 32, 10, 7, 2, frame='#3a2a1a'), frame_art(104, 32, 10, 7, 0, frame='#3a2a1a'))
    s.add(poly([(20, 52), (44, 52), (56, 84), (8, 84)], '#fff', .07))
    return s


def testemunha():
    s = tribunal('te', 13, ('#e8d8ad', '#d2be8d'), ('#a07048', '#6e4a2a'))
    # galeria do público (bancos vazios) atrás de um gradil
    s.add(rect(0, 41, 160, 12, '#2a1a10', .22))
    for row, (y, c) in enumerate([(42, '#6a4228'), (46.5, '#7a5232'), (51, '#8a6038')]):
        for i in range(8):
            x = 6 + i * 19 + (row % 2) * 3
            s.add(rect(x, y, 16, 3.2, c, rx=.5), rect(x, y, 16, .7, '#fff', .18), rect(x, y + 2.6, 16, .6, '#000', .25))
    s.add(rect(0, 53.2, 160, 1, '#000', .25))
    for i in range(0, 160, 5):
        s.add(rect(i + .6, 55.6, 1.1, 5, '#6a4228'), circ(i + 1.15, 55.4, .9, '#8a6038'))
    s.add(rect(0, 60.4, 160, 1.3, '#8a6038'), rect(0, 60.4, 160, .4, '#fff', .25))
    s.add(arch_window(s, 12, 12, 22, 28, sky=('#9cc8ee', '#f2f6fa'), frame='#5a3a22', sill='#7a5232'))
    s.add(curtain(s, 0, 8, 6, 40, '#4a6a3a'))
    s.add(curtain(s, 36, 8, 6, 40, '#3e5a30', side='l'))
    s.add(curtain(s, 144, 16, 6, 40, '#4a6a3a'))
    s.add(emblem(s, 80, 17, 7.5, bg='#3a3a24'))
    pendant(s, 52, 4, 15, 42, glow='#fff0c8'); pendant(s, 108, 4, 15, 42, glow='#fff0c8')
    s.add(shelf_unit(s, 116, 14, 20, 24, 3, wood='#5a3a22', back='#2a1a10', plank='#8a6038'))
    return s


def juiz():
    s = tribunal('ju', 14, ('#cf9a6a', '#b07a4c'), ('#8a5a38', '#5a3822'))
    # cortinão de fundo atrás do brasão
    s.add(rect(54, 5, 52, 49, s.lin([(0, '#6a1e26'), (1, '#4a1219')])), rect(54, 5, 52, 49, s.lin([(0, '#000', .3), (.5, '#fff', .08), (1, '#000', .3)], horiz=True)))
    for i in range(1, 13):
        s.add(line(54 + i * 4, 5, 54 + i * 4, 54, '#000', .3, .25))
    s.add(rect(53, 4.5, 54, 3, '#c9a04a', .9, rx=.6), rect(53, 7.4, 54, .7, '#000', .3))
    s.add(emblem(s, 80, 22, 10.5, bg='#2a1a12'))
    for xx, col in ((22, '#2f6a4a'), (122, '#2a4a8a')):
        s.add(banner(xx, 16, 56, 15, col, stripe='#f0e8d0'))
    s.add(curtain(s, 0, 10, 6, 54, '#9a2a2e')); s.add(curtain(s, 150, 10, 6, 54, '#9a2a2e'))
    pendant(s, 40, 4, 14, 54); pendant(s, 120, 4, 14, 54)
    for x in (12, 140):
        s.add(rect(x, 6, 2, 48, '#000', .08))
    return s


GERADORES = {'acusacao': acusacao, 'defesa': defesa, 'testemunha': testemunha, 'juiz': juiz}

if __name__ == '__main__':
    for n, g in GERADORES.items():
        (AQUI / f'{n}.svg').write_text(g().render(), encoding='utf-8')
        print(n)
