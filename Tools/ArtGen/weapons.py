"""Army weapons through the 6 eras: soldiers, war machines and attack FX (2x fine grid)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from people import person2, T

PW_, PH_ = 72, 40
INKC = hx('#14110e'); STEEL = [hx('#5a6068'), hx('#8b939a'), hx('#c8ced4')]; BRONZE = [hx('#7a4a1e'), hx('#b0742e'), hx('#e0a85a')]
TEAM = R['K']
SMOKE = hx('#d8d4cc')


def outfit(kind):
    tk = [TEAM[1], TEAM[2], TEAM[3]]
    base = dict(shoes=hx('#3a2a1e'), head=None, hcol=None, item=None, cape=None)
    o = {
        'club': dict(top=T('#6e5034', '#93714b', '#b79262'), bot='wrap', brp=T('#6e5034', '#93714b', '#b79262'), ex=['bone'], shoes=None),
        'sling': dict(top=T('#5d4229', '#7d5c3a', '#9e7a50'), bot='wrap', brp=T('#5d4229', '#7d5c3a', '#9e7a50'), ex=[], shoes=None),
        'hoplite': dict(top=tk, bot='kilt', brp=T('#b9ad95', '#d8ccb2', '#ece3cf'), ex=['trim_gold']),
        'archer': dict(top=T('#4a5a3a', '#5e7048', '#76885c'), bot='pants', brp=T('#5a4632', '#7a6044', '#9a7c5a'), ex=['legwrap']),
        'knight': dict(top=[STEEL[0], STEEL[1], STEEL[2]], bot='pants', brp=[STEEL[0], STEEL[1], STEEL[2]], ex=[]),
        'xbow': dict(top=tk, bot='pants', brp=T('#3a3a40', '#4e4e56', '#64646c'), ex=['belt_brass']),
        'musket': dict(top=tk, bot='pants', brp=T('#d8d2c4', '#ece8de', '#ffffff'), ex=['white_shirt']),
        'gunner': dict(top=T('#2e3a52', '#3c4a68', '#52628a'), bot='pants', brp=T('#2e3a52', '#3c4a68', '#52628a'), ex=[]),
        'rifle': dict(top=T('#4a5236', '#5f6a45', '#78845a'), bot='pants', brp=T('#4a5236', '#5f6a45', '#78845a'), ex=[]),
        'flame': dict(top=T('#3a3a34', '#4e4e46', '#66665c'), bot='pants', brp=T('#3a3a34', '#4e4e46', '#66665c'), ex=[]),
        'laser': dict(top=T('#262b33', '#343a44', '#474f5b'), bot='pants', brp=T('#262b33', '#343a44', '#474f5b'), ex=['cyanline']),
        'pilot': dict(top=T('#c9cdd2', '#e6e9ec', '#ffffff'), bot='pants', brp=T('#b0b6bc', '#ccd2d8', '#e4e8ec'), ex=['cyanline']),
    }[kind]
    base.update(o); return base


def helmet(a, x, y, kind):
    hx0, ht = x + 4, y + 4
    if kind == 'bronze':
        hline(a, hx0 - 1, ht - 1, 8, BRONZE[1]); hline(a, hx0, ht - 2, 6, BRONZE[2]); vline(a, hx0 - 1, ht, 4, BRONZE[0])
        for i in range(5): put(a, hx0 + i, ht - 3 - (i in (1, 2, 3)), TEAM[2])
    elif kind == 'knight':
        rect(a, hx0 - 1, ht - 2, 8, 6, STEEL[1]); hline(a, hx0 - 1, ht - 2, 8, STEEL[2]); hline(a, hx0 + 2, ht + 1, 5, INKC); put(a, hx0 + 4, ht + 3, INKC)
        vline(a, hx0 + 6, ht - 2, 6, STEEL[0]); put(a, hx0 + 2, ht - 3, TEAM[2]); put(a, hx0 + 3, ht - 4, TEAM[3])
    elif kind == 'kettle':
        hline(a, hx0 - 2, ht - 1, 10, STEEL[1]); hline(a, hx0, ht - 2, 6, STEEL[2])
    elif kind == 'tricorn':
        hline(a, hx0 - 2, ht - 1, 10, INKC); hline(a, hx0, ht - 2, 6, hx('#2a2c32')); put(a, hx0 + 6, ht - 2, C['gold'])
    elif kind == 'shako':
        rect(a, hx0, ht - 5, 6, 5, hx('#1e2024')); hline(a, hx0 - 1, ht - 1, 8, INKC); put(a, hx0 + 2, ht - 4, C['gold']); put(a, hx0 + 2, ht - 6, TEAM[3])
    elif kind == 'modern':
        hline(a, hx0 - 1, ht - 1, 8, hx('#4a5236')); hline(a, hx0, ht - 2, 6, hx('#5f6a45')); hline(a, hx0 + 1, ht - 3, 4, hx('#78845a'))
    elif kind == 'mask':
        hline(a, hx0 - 1, ht - 1, 8, hx('#3a3a34')); rect(a, hx0 + 3, ht + 2, 4, 3, hx('#2a2a26')); put(a, hx0 + 3, ht + 2, hx('#8ad0e0')); put(a, hx0 + 5, ht + 2, hx('#8ad0e0'))
    elif kind == 'visor':
        rect(a, hx0 - 1, ht - 2, 8, 5, hx('#262b33')); hline(a, hx0 + 1, ht + 1, 6, C['cyan']); hline(a, hx0 - 1, ht - 2, 8, hx('#474f5b'))


def soldier(a, x, y, kind, frame=0, seed=1, culture='highland'):
    person2(a, x, y, culture, 'middle', 'adult', 'm', frame, seed=seed, o_over=outfit(kind), shadow=True)
    hx_, hy_ = x + 11, y + 19     # right hand
    if kind == 'club':
        line(a, hx_, hy_, hx_ + 5, hy_ - 9, C['wood'][1]); line(a, hx_ + 1, hy_, hx_ + 6, hy_ - 9, C['wood'][2])
        rect(a, hx_ + 4, hy_ - 13, 4, 5, R['stone'][2]); hline(a, hx_ + 4, hy_ - 13, 4, R['stone'][3]); put(a, hx_ + 7, hy_ - 9, R['stone'][1])
    elif kind == 'sling':
        for i in range(6): put(a, hx_ + 1 + i, hy_ - 4 - int(2 * math.sin(i)), hx('#a89878'))
    elif kind == 'hoplite':
        helmet(a, x, y, 'bronze')
        line(a, hx_ + 1, hy_ + 4, hx_ + 1, hy_ - 18, C['wood'][2]); put(a, hx_ + 1, hy_ - 19, BRONZE[2]); put(a, hx_ + 1, hy_ - 20, BRONZE[2])
        dome(a, x + 3, y + 16, 4.2, 5, [BRONZE[0], BRONZE[0], BRONZE[1], BRONZE[2], hx('#f0c880')], 3); rect(a, x + 2, y + 15, 3, 3, TEAM[2])
    elif kind == 'archer':
        for i in range(-6, 7): put(a, hx_ + 3 + int(2.5 * math.cos(i / 6 * 1.4)), hy_ - 6 + i, C['wood'][2])
        vline(a, hx_ + 1, hy_ - 12, 13, hx('#e8e2d4'))
        helmet(a, x, y, 'kettle')
    elif kind == 'knight':
        helmet(a, x, y, 'knight')
        line(a, hx_ + 1, hy_, hx_ + 1, hy_ - 11, STEEL[2]); hline(a, hx_, hy_ + 1, 3, C['gold'])
        rect(a, x + 1, y + 13, 5, 7, TEAM[2]); hline(a, x + 1, y + 13, 5, TEAM[3]); put(a, x + 3, y + 15, C['gold']); hline(a, x + 2, y + 20, 3, TEAM[1])
    elif kind == 'xbow':
        helmet(a, x, y, 'kettle')
        hline(a, hx_ - 2, hy_ - 3, 9, C['wood'][1]); vline(a, hx_ + 5, hy_ - 7, 9, STEEL[1])
    elif kind == 'musket':
        helmet(a, x, y, 'tricorn')
        line(a, hx_ - 4, hy_ - 2, hx_ + 9, hy_ - 5, C['wood'][1]); line(a, hx_ + 4, hy_ - 4, hx_ + 11, hy_ - 6, STEEL[1])
        hline(a, x + 4, y + 12, 6, hx('#ece6da'))
    elif kind == 'rifle':
        helmet(a, x, y, 'modern')
        line(a, hx_ - 4, hy_ - 2, hx_ + 8, hy_ - 4, hx('#2a2c30')); rect(a, hx_, hy_ - 3, 3, 2, hx('#4a3a2a')); put(a, hx_ + 2, hy_ - 1, hx('#2a2c30'))
    elif kind == 'flame':
        helmet(a, x, y, 'mask')
        rect(a, x + 1, y + 12, 3, 8, hx('#8a3a2a')); rect(a, x + 1, y + 12, 1, 8, hx('#b05a42')); put(a, x + 2, y + 11, STEEL[1])
        line(a, hx_ - 3, hy_ - 1, hx_ + 7, hy_ - 3, hx('#2a2c30')); put(a, hx_ + 8, hy_ - 3, STEEL[2]); put(a, hx_ + 6, hy_ - 2, hx('#ffb84a'))
    elif kind == 'laser':
        helmet(a, x, y, 'visor')
        line(a, hx_ - 3, hy_ - 2, hx_ + 8, hy_ - 4, hx('#d8e2ea')); put(a, hx_ + 8, hy_ - 4, C['cyan']); put(a, hx_ + 3, hy_ - 3, C['cyan'])


def line(a, x0, y0, x1, y1, col):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n):
        put(a, int(round(x0 + (x1 - x0) * i / max(1, n - 1))), int(round(y0 + (y1 - y0) * i / max(1, n - 1))), col)


# ---------------- machines
def catapult(a, x, b, frame=0):
    shadow_ell(a, x + 9, b + 1, 9, 1.4)
    rect(a, x, b - 3, 18, 3, C['wood'][1]); hline(a, x, b - 3, 18, C['wood'][2])
    for wx in (x + 3, x + 14): dome(a, wx, b, 2, 2, [C['wood'][0]] * 2 + [C['wood'][1], C['wood'][2], C['wood'][2]], wx)
    vline(a, x + 7, b - 9, 6, C['wood'][1]); vline(a, x + 11, b - 9, 6, C['wood'][1]); hline(a, x + 7, b - 9, 5, C['wood'][2])
    if frame == 0: line(a, x + 9, b - 8, x + 2, b - 12, C['wood'][2]); rect(a, x + 1, b - 14, 3, 3, R['stone'][2])
    else: line(a, x + 9, b - 8, x + 14, b - 17, C['wood'][2]); put(a, x + 14, b - 18, C['wood'][1])


def cannon(a, x, b):
    shadow_ell(a, x + 8, b + 1, 9, 1.4)
    line(a, x + 2, b - 5, x + 16, b - 8, INKC); line(a, x + 2, b - 4, x + 16, b - 7, hx('#2a2c30')); line(a, x + 2, b - 6, x + 15, b - 9, hx('#4a4e56'))
    rect(a, x + 2, b - 6, 3, 3, hx('#1e2024'))
    dome(a, x + 6, b - 1, 3, 3, [C['wood'][0], C['wood'][0], C['wood'][1], C['wood'][2], C['wood'][2]], 3); put(a, x + 6, b - 1, INKC)


def tank(a, x, b):
    shadow_ell(a, x + 13, b + 1, 14, 1.8, .35)
    rect(a, x, b - 4, 26, 5, hx('#2a2c26'))
    for i in range(0, 26, 3): put(a, x + i, b - 4, hx('#4a4e44')); dome(a, x + 2 + i, b - 1, 1.3, 1.3, [hx('#1e2018')] * 2 + [hx('#3a3e34')] * 3, i) if i % 6 == 0 else None
    rect(a, x + 1, b - 9, 24, 5, hx('#5f6a45')); hline(a, x + 1, b - 9, 24, hx('#78845a')); hline(a, x + 1, b - 5, 24, hx('#4a5236'))
    rect(a, x + 7, b - 13, 11, 4, hx('#5f6a45')); hline(a, x + 7, b - 13, 11, hx('#8a9668')); hline(a, x + 18, b - 12, 11, hx('#3a4228'))
    put(a, x + 9, b - 12, TEAM[2]); put(a, x + 10, b - 12, TEAM[3])


def drone(a, x, y, frame=0):
    shadow_ell(a, x + 7, y + 16, 5, 1.2, .25)
    rect(a, x + 3, y + 3, 9, 3, hx('#3c4352')); hline(a, x + 3, y + 3, 9, hx('#6a7488')); put(a, x + 10, y + 4, C['cyan'])
    for (rx, s) in ((x, 1), (x + 11, -1)):
        hline(a, rx, y + 2, 4, hx('#c8ced4') if frame % 2 else hx('#6a7488')); vline(a, rx + 2, y + 2, 2, hx('#3c4352'))
    rect(a, x + 6, y + 6, 3, 2, hx('#262b33')); put(a, x + 7, y + 7, hx('#e05a5a'))


def mech(a, x, b):
    shadow_ell(a, x + 8, b + 1, 8, 1.6, .35)
    for lx in (x + 3, x + 10):
        rect(a, lx, b - 8, 3, 8, hx('#474f5b')); vline(a, lx, b - 8, 8, hx('#6a7488')); rect(a, lx - 1, b, 5, 1, hx('#262b33'))
    rect(a, x + 1, b - 18, 15, 10, hx('#d8dee4')); hline(a, x + 1, b - 18, 15, hx('#ffffff')); hline(a, x + 1, b - 9, 15, hx('#9aa4ae'))
    rect(a, x + 9, b - 16, 6, 3, hx('#262b33')); hline(a, x + 10, b - 15, 4, C['cyan']); put(a, x + 4, b - 14, TEAM[2]); put(a, x + 5, b - 14, TEAM[3])
    rect(a, x + 15, b - 13, 6, 2, hx('#474f5b')); put(a, x + 20, b - 13, C['cyan'])


# ---------------- FX
def fx_arrow(a, x, y, bolt=False):
    hline(a, x, y, 7 if not bolt else 5, C['wood'][2]); put(a, x + (7 if not bolt else 5), y, STEEL[2])
    if not bolt: put(a, x, y - 1, hx('#e8e2d4')); put(a, x, y + 1, hx('#e8e2d4'))


def fx_smoke(a, x, y, n=3, big=1.0):
    for i in range(n):
        blend_mask(a, ellipse_mask(a.shape[:2], x + i * 3, y - i, (2 + i) * big, (1.7 + i * .8) * big), SMOKE, .65 - i * .15)


def fx_flash(a, x, y):
    for (dx, dy, c) in [(0, 0, hx('#fff2b0')), (1, 0, hx('#ffd34a')), (2, 0, hx('#f49a3c')), (1, -1, hx('#ffd34a')), (1, 1, hx('#ffd34a'))]: put(a, x + dx, y + dy, c)


def fx_flame(a, x, y, L=30, seed=1):
    r = random.Random(seed)
    for i in range(L):
        u = i / L
        w = 1 + u * 5
        cy = y - u * u * 4
        for j in range(int(-w), int(w) + 1):
            if r.random() < .85 - u * .3:
                c = hx('#fff2b0') if u < .15 else hx('#ffd34a') if u < .35 else hx('#f49a3c') if u < .6 else hx('#d5452d') if u < .85 else hx('#7a3a2a')
                put(a, x + i, int(cy + j * .7 + r.uniform(-1, 1)), c)
    blend_mask(a, ellipse_mask(a.shape[:2], x + L * .5, y, L * .6, 8), hx('#ffb35a'), .18)
    fx_smoke(a, x + L - 2, y - 6, 3, 1.2)


def fx_laser(a, x, y, x2):
    hline(a, x, y, x2 - x, C['cyan2']); hline(a, x, y - 1, x2 - x, C['cyan']); hline(a, x, y + 1, x2 - x, C['cyan'])
    blend_rect(a, x, y - 3, x2 - x, 7, C['cyan'], .18)
    blend_mask(a, ellipse_mask(a.shape[:2], x2, y, 4, 4), C['cyan2'], .6)


def fx_boom(a, x, y, s=1.0):
    blend_mask(a, ellipse_mask(a.shape[:2], x, y, 7 * s, 6 * s), hx('#ffb35a'), .35)
    dome(a, x, y, 4 * s, 3.6 * s, [hx('#d5452d'), hx('#f49a3c'), hx('#ffd34a'), hx('#fff2b0'), hx('#ffffff')], 5, rough=.4)
    fx_smoke(a, x - 2, y - 5 * s, 3, s)


def dummy(a, x, b, hit=False):
    vline(a, x + 2, b - 12, 13, C['wood'][1]); hline(a, x, b - 9, 5, C['wood'][1])
    dome(a, x + 2, b - 13, 2.4, 2.4, R['straw'], 3)
    if hit:
        for (dx, dy) in [(-2, -14), (5, -15), (-3, -9), (6, -8)]: put(a, x + dx, b + dy, hx('#ffffff'))


def panel(seed, tint='#74a753'):
    return grass_ground(PW_, PH_, seed, tint=(hx(tint), .25))


def cell(era, k):
    f = panel(era * 7 + k, ['#8a9a5a', '#c8b480', '#74a753', '#8a8a70', '#7a8a6a', '#6a7a7a'][era])
    b = PH_ - 3
    if era == 0:
        if k == 0: soldier(f, 4, b - 27, 'club', 1); soldier(f, 20, b - 27, 'club', 3, seed=4); dummy(f, 50, b, True)
        elif k == 1:
            soldier(f, 4, b - 27, 'sling', 0); dummy(f, 56, b, True)
            for i in range(5): put(f, 26 + i * 6, b - 22 - int(6 * math.sin(i / 4 * math.pi)), R['stone'][2] if i == 4 else lit(f[0, 0], .05))
            dome(f, 52, b - 17, 1.4, 1.4, R['stone'], 1)
        else:
            soldier(f, 4, b - 27, 'club', 0, seed=8)
            for xx, h in ((32, 10), (44, 12), (56, 9)):
                vline(f, xx, b - h, h + 1, C['wood'][1]); put(f, xx, b - h - 1, hx('#ffd34a')); put(f, xx, b - h - 2, hx('#f49a3c'))
            hline(f, 28, b - 4, 34, C['wood'][1])
    elif era == 1:
        if k == 0:
            for i in range(3): soldier(f, 2 + i * 9, b - 27, 'hoplite', 0, seed=i)
            dummy(f, 58, b)
        elif k == 1: soldier(f, 4, b - 27, 'archer', 0); fx_arrow(f, 30, b - 21); fx_arrow(f, 44, b - 18); dummy(f, 58, b, True)
        else:
            # chariot
            shadow_ell(f, 30, b + 1, 18, 1.6)
            from animals import draw as adraw
            adraw(f, 34, b - 20, 'horse', 1, False, 3)
            rect(f, 14, b - 9, 12, 6, BRONZE[1]); hline(f, 14, b - 9, 12, BRONZE[2]); dome(f, 20, b - 2, 3, 3, [C['wood'][0]] * 2 + [C['wood'][1]] * 3, 2)
            put(f, 20, b - 2, INKC); line(f, 26, b - 6, 36, b - 8, C['wood'][1])
            soldier(f, 13, b - 33, 'hoplite', 0, seed=5)
    elif era == 2:
        if k == 0: soldier(f, 6, b - 27, 'knight', 0); soldier(f, 22, b - 27, 'knight', 2, seed=3); dummy(f, 56, b, True)
        elif k == 1: soldier(f, 4, b - 27, 'xbow', 0); fx_arrow(f, 32, b - 22, True); dummy(f, 58, b, True)
        else:
            catapult(f, 4, b, 1)
            for i in range(9): rect(f, 22 + i * 5, int(b - 22 - 10 * math.sin(i / 8 * math.pi)), 2, 1, hx('#e8e4da'))
            dome(f, 66, b - 14, 2.6, 2.6, R['stone'], 3); fx_boom(f, 66, b - 3, .6)
    elif era == 3:
        if k == 0:
            soldier(f, 4, b - 27, 'musket', 0); soldier(f, 16, b - 27, 'musket', 0, seed=5)
            fx_flash(f, 31, b - 26); fx_smoke(f, 33, b - 27, 3); dummy(f, 60, b, True)
        elif k == 1:
            cannon(f, 6, b); fx_flash(f, 23, b - 9); fx_smoke(f, 24, b - 11, 4, 1.3)
            dome(f, 46, b - 16, 1.6, 1.6, [INKC, INKC, hx('#2a2c30'), hx('#4a4e56'), hx('#6a6e76')], 1)
            for i in range(4): put(f, 38 - i * 3, b - 15 + i // 2, SMOKE)
        else:
            soldier(f, 4, b - 27, 'gunner', 0); helmet(f, 4, b - 27, 'shako')
            soldier(f, 20, b - 27, 'gunner', 2, seed=4); helmet(f, 20, b - 27, 'shako')
            vline(f, 38, b - 22, 22, C['wood'][2]); rect(f, 39, b - 22, 8, 5, TEAM[2]); hline(f, 39, b - 22, 8, TEAM[3]); put(f, 42, b - 20, C['gold'])
    elif era == 4:
        if k == 0:
            soldier(f, 4, b - 27, 'rifle', 0); fx_flash(f, 20, b - 23)
            for i in range(3): hline(f, 26 + i * 12, b - 23 - i // 2, 4, hx('#ffe27a'))
            dummy(f, 60, b, True)
        elif k == 1:
            soldier(f, 2, b - 27, 'flame', 0); fx_flame(f, 20, b - 22, 40, 3)
        else:
            tank(f, 2, b); fx_flash(f, 40, b - 12); fx_smoke(f, 41, b - 13, 3)
            fx_boom(f, 62, b - 6, .9)
    else:
        if k == 0: soldier(f, 4, b - 27, 'laser', 0); fx_laser(f, 20, b - 23, 60); dummy(f, 60, b, True)
        elif k == 1:
            drone(f, 10, 4, 1); drone(f, 30, 9, 0)
            for i in range(10): put(f, 18 + i * 3, 12 + i * 2, hx('#c8ced4') if i % 2 else SMOKE)
            rect(f, 46, 30, 3, 2, hx('#3c4352')); fx_boom(f, 54, b - 5, .8)
        else:
            soldier(f, 2, b - 27, 'pilot', 0); mech(f, 18, b); fx_laser(f, 40, b - 13, 64); dummy(f, 64, b, True)
    return f


ERAS_ = ['STONE', 'ANCIENT', 'MEDIEVAL', 'INDUSTRIAL', 'MODERN', 'FUTURE']
NAMES = [['CLUB WARBAND', 'SLINGER', 'TORCH STAKES (night guard)'], ['BRONZE PHALANX', 'ARCHER', 'WAR CHARIOT'],
         ['KNIGHTS', 'CROSSBOWMAN', 'CATAPULT'], ['MUSKET LINE', 'FIELD CANNON', 'DRUM & COLOURS'], ['RIFLEMAN', 'FLAMETHROWER', 'TANK'],
         ['LASER TROOPER', 'STRIKE DRONES', 'EXO-MECH']]

if __name__ == '__main__':
    S = 4; G = 12; TH = 92; LW = 170
    pw, ph = PW_ * S, PH_ * S
    W_ = LW + 3 * (pw + G) + G
    H_ = TH + 6 * (ph + 40 + G)
    out = Image.new('RGB', (W_, H_), (18, 22, 28)); d = ImageDraw.Draw(out)
    d.text((G, 30), 'ARMIES THROUGH THE AGES  -  WEAPONS, MACHINES & ATTACK FX', fill=(240, 228, 200), font=ImageFont.load_default(size=32), anchor='lm')
    d.text((G, 66), 'each nation fields what its era + resources allow. team colour on tabards, shields, flags & machines.', fill=(150, 160, 175), font=ImageFont.load_default(size=20), anchor='lm')
    for e in range(6):
        y = TH + e * (ph + 40 + G)
        d.text((G, y + 40 + ph // 2), ERAS_[e], fill=(232, 180, 106), font=ImageFont.load_default(size=24), anchor='lm')
        for k in range(3):
            x = LW + k * (pw + G)
            d.text((x, y + 18), NAMES[e][k], fill=(200, 205, 212), font=ImageFont.load_default(size=18), anchor='lm')
            out.paste(Image.fromarray(cell(e, k)).resize((pw, ph), Image.NEAREST), (x, y + 36))
    out.save('army_weapons.png'); print(out.size)
