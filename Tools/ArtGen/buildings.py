"""Building library: 10 categories x 6 eras. Anchor = (x, base): left of footprint, bottom facade row.
Every drawer returns a list of FX hooks for the fine pass: ('smoke'|'fire'|'glow'|'steam'|'holo', x, y[, color])."""
import math, random
import numpy as np
from lib import *

ERAS = ['STONE AGE', 'ANCIENT', 'MEDIEVAL', 'INDUSTRIAL', 'MODERN', 'FUTURE']
CATS = ['poor', 'rich', 'seat', 'commerce', 'industry', 'mine', 'research', 'energy', 'military', 'defense']
CAT_NAMES = {'poor': 'HOMES', 'rich': 'RICH HOMES', 'seat': 'SEAT OF RULE', 'commerce': 'TRADE',
             'industry': 'CRAFT/INDUSTRY', 'mine': 'MINES', 'research': 'KNOWLEDGE', 'energy': 'ENERGY',
             'military': 'MILITARY', 'defense': 'DEFENSE'}
MORTAR = hx('#b9a48e')


# ---------------- walls ----------------
def wall(a, x, y, w, h, mat, seed=0, beams=True):
    rp = W[mat]; r = random.Random(seed)
    rect(a, x, y, w, h, rp[1])
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            dy, dx = yy - y, xx - x
            c = None
            if mat == 'hide':
                if dx % 4 == 0 and dy % 2 == 0: c = rp[0]
            elif mat in ('mud', 'mudw'):
                v = r.random()
                c = rp[0] if v < .05 else (rp[2] if v < .1 else None)
            elif mat in ('stone', 'fort'):
                row = dy // 2
                if dy % 2 == 1: c = rp[0]
                elif (dx + row * 2) % (4 if mat == 'stone' else 5) == 0: c = rp[0]
                elif ((dx + row * 2) // 4 + row) % 3 == 0: c = rp[2]
            elif mat == 'brick':
                if dy % 2 == 1: c = MORTAR if (dx + dy) % 7 else rp[0]
                elif (dx + (dy // 2) * 2) % 4 == 0: c = rp[0]
            elif mat == 'concrete':
                if dy % 4 == 3 or dx % 6 == 5: c = rp[0]
            elif mat == 'glass':
                if dx % 3 == 2 or dy % 3 == 2: c = rp[0]
                elif (dx - dy) % 9 in (0, 1): c = rp[2]
            elif mat == 'metal':
                c = rp[0] if dx % 2 == 0 else None
            elif mat == 'marble':
                c = rp[2] if dx % 3 else rp[1]
            elif mat == 'white':
                c = rp[2] if dy % 5 else rp[1]
            elif mat == 'plaster':
                c = rp[2] if r.random() < .08 else None
            if c is not None: put(a, xx, yy, c)
    if mat == 'plaster' and beams:
        for bx in range(x, x + w, 5): vline(a, bx, y, h, C['beam'])
        vline(a, x + w - 1, y, h, C['beam']); hline(a, x, y, w, C['beam'])
        if h >= 6: hline(a, x, y + h // 2, w, C['beam'])
    vline(a, x, y, h, lit(rp[1], .2))
    vline(a, x + w - 1, y, h, rp[0])
    hline(a, x, y + h - 1, w, lit(rp[0], -.15))


def windows(a, x, y, w, h, spec, lit_p, seed, skip=None, kind='sq'):
    if not spec: return
    ww, wh, sx, sy = spec
    r = random.Random(seed)
    n = max(1, (w - 2 + (sx - ww)) // sx)
    x0 = x + (w - (n * sx - (sx - ww))) // 2
    yy = y + 1
    while yy + wh <= y + h - 1:
        for i in range(n):
            xx = x0 + i * sx
            if skip and xx + ww > skip[0] and xx < skip[0] + skip[1] and yy + wh > skip[2]: continue
            if r.random() < lit_p:
                rect(a, xx, yy, ww, wh, C['lit2']); put(a, xx, yy, C['lit'])
            else:
                rect(a, xx, yy, ww, wh, C['win']); put(a, xx, yy, lit(C['win'], .3))
            if kind == 'arch' and wh >= 3:
                put(a, xx, yy, a[yy - 1, xx] if yy > 0 else C['win'])
                put(a, xx + ww - 1, yy, a[yy - 1, xx + ww - 1] if yy > 0 else C['win'])
        yy += sy


def door(a, x, y, w, h, col=None, arch=False):
    rect(a, x, y, w, h, col or C['door'])
    hline(a, x - (1 if w > 2 else 0), y - 1, w + (2 if w > 2 else 0), lit(col or C['door'], -.3))
    if arch and w >= 3:
        put(a, x, y, lit(col or C['door'], .1)); put(a, x + w - 1, y, lit(col or C['door'], .1))


# ---------------- roofs ----------------
def roof_gable(a, x, top, w, rh, rp, over=1, tiles=True):
    X0, WW = x - over, w + 2 * over
    back = max(1, rh // 3)
    rect(a, X0, top, WW, back, rp[1])
    hline(a, X0, top + back, WW, rp[4])
    for ry in range(top + back + 1, top + rh):
        for rx in range(X0, X0 + WW):
            c = rp[2]
            if tiles and (rx + ry) % 3 == 0: c = rp[3] if rx < X0 + WW // 2 else rp[1]
            put(a, rx, ry, c)
    vline(a, X0, top + back, rh - back, rp[3]); vline(a, X0 + WW - 1, top + back, rh - back, rp[1])
    hline(a, X0, top + rh, WW, rp[0])


def roof_hip(a, x, top, w, rh, rp, over=1):
    roof_gable(a, x, top, w, rh, rp, over)
    back = max(1, rh // 3)
    X0, WW = x - over, w + 2 * over
    for i in range(rh):
        e = min(3, 1 + i // 2)
        for j in range(e):
            put(a, X0 + j, top + i, rp[3]); put(a, X0 + WW - 1 - j, top + i, rp[1])
    put(a, X0, top, a[top - 1, X0] if top > 0 else rp[3]); put(a, X0 + WW - 1, top, a[top - 1, X0 + WW - 1] if top > 0 else rp[1])


def roof_flat(a, x, top, w, rh, rp, seed=0, clutter=True):
    rect(a, x, top, w, rh, rp[2])
    hline(a, x, top, w, rp[3]); vline(a, x, top, rh, rp[3]); vline(a, x + w - 1, top, rh, rp[1])
    hline(a, x, top + rh - 1, w, rp[0])
    if clutter and w > 7 and rh > 3:
        r = random.Random(seed)
        for _ in range(max(1, w // 8)):
            bx, by = x + r.randint(2, w - 4), top + r.randint(1, max(1, rh - 3))
            rect(a, bx, by, 2, 1, rp[1]); put(a, bx, by - 1 if by > top + 1 else by, rp[4])


def roof_thatch(a, x, top, w, rh, rp=None, seed=0):
    rp = rp or R['straw']
    dome(a, x + w / 2, top + rh * .62, w / 2 + 1, rh * .7, rp, seed)
    for yy in range(int(top), int(top + rh), 2):
        for xx in range(x - 1, x + w + 1):
            if (xx * 7 + yy * 3) % 5 == 0 and tuple(a[yy, xx]) in [tuple(c) for c in rp] if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] else False:
                put(a, xx, yy, rp[1])


def roof_tent(a, x, top, w, rh, rp, stripes=None):
    cx = x + w / 2
    for i in range(rh):
        half = (i + 1) / rh * (w / 2 + .5)
        y = top + i
        for xx in range(int(cx - half), int(math.ceil(cx + half))):
            c = rp[3] if xx < cx - .5 else (rp[4] if abs(xx + .5 - cx) < 1 else rp[1])
            if i % 3 == 2: c = lit(c, -.12)
            if stripes and i in stripes: c = stripes[i]
            put(a, xx, y, c)
    put(a, int(cx) - 1, top - 1, C['wood'][1]); put(a, int(cx) + 1, top - 1, C['wood'][1]); put(a, int(cx) - 2, top - 2, C['wood'][2]); put(a, int(cx) + 2, top - 2, C['wood'][0])


def roof_cone(a, x, top, w, rh, rp):
    cx = x + w / 2
    for i in range(rh):
        half = (i + 1) / rh * (w / 2 + 1)
        for xx in range(int(cx - half), int(math.ceil(cx + half))):
            c = rp[3] if xx < cx - .5 else rp[1]
            if (i + xx) % 3 == 0: c = rp[2]
            if abs(xx + .5 - cx) < .8: c = rp[4]
            put(a, xx, top + i, c)
    put(a, int(cx), top - 1, rp[4])


def roof_crenel(a, x, top, w, rh, rp=None):
    rp = rp or R['stone']
    rect(a, x, top, w, rh, rp[2]); hline(a, x, top + rh - 1, w, rp[0])
    for xx in range(x, x + w):
        if ((xx - x) // 2) % 2 == 0:
            put(a, xx, top, rp[4]); put(a, xx, top + 1, rp[3])
        else:
            put(a, xx, top, rp[0])
    vline(a, x, top, rh, rp[3]); vline(a, x + w - 1, top, rh, rp[1])


def roof_sawtooth(a, x, top, w, rh):
    for i in range(0, w, 6):
        for k in range(6):
            col = x + i + k
            if col >= x + w: break
            if k < 2:
                vline(a, col, top, rh, W['glass'][2] if k == 0 else R['glass'][3])
            else:
                vline(a, col, top + (k - 2), rh - (k - 2), R['metal'][2] if k < 4 else R['metal'][1])
    hline(a, x, top + rh - 1, w, R['metal'][0])


def roof_solar(a, x, top, w, rh):
    roof_flat(a, x, top, w, rh, R['white'], clutter=False)
    for yy in range(top + 1, top + rh - 1, 2):
        for xx in range(x + 1, x + w - 1, 3):
            rect(a, xx, yy, 2, 1, hx('#2a4f8a')); put(a, xx, yy, hx('#6f9bd8'))


# ---------------- generic building ----------------
def bld(a, x, base, w, wh, rh, mat, roof, rp=None, seed=0, win=(2, 2, 3, 3), lit_p=.3, dr=(2, 3), shadow=True,
        winkind='sq', door_col=None):
    top = base - wh - rh + 1
    fy = base - wh + 1
    if shadow: shadow_rect(a, x + 3, top + 3, w + (1 if roof in ('gable', 'hip') else 0), wh + rh - 1)
    wall(a, x, fy, w, wh, mat, seed)
    sk = None
    if dr:
        dx = x + (w - dr[0]) // 2
        sk = (dx - 1, dr[0] + 2, base - dr[1] - 1)
    windows(a, x, fy, w, wh, win, lit_p, seed, sk, winkind)
    if dr: door(a, x + (w - dr[0]) // 2, base - dr[1] + 1, dr[0], dr[1], door_col, arch=winkind == 'arch')
    if roof == 'gable': roof_gable(a, x, top, w, rh, rp)
    elif roof == 'hip': roof_hip(a, x, top, w, rh, rp)
    elif roof == 'flat': roof_flat(a, x, top, w, rh, rp, seed)
    elif roof == 'thatch': roof_thatch(a, x, top, w, rh, rp, seed)
    elif roof == 'crenel': roof_crenel(a, x, top, w, rh, rp)
    elif roof == 'sawtooth': roof_sawtooth(a, x, top, w, rh)
    elif roof == 'solar': roof_solar(a, x, top, w, rh)
    elif roof == 'cone': roof_cone(a, x, top, w, rh, rp)
    return top


# ---------------- props ----------------
def chimney(a, x, y, h=4, mat='stone'):
    rp = W[mat]
    rect(a, x, y, 2, h, rp[1]); vline(a, x, y, h, rp[2]); hline(a, x, y, 2, R['stone'][3])
    return ('smoke', x + 1, y - 1)


def flag(a, x, y, rp=None, h=7):
    rp = rp or R['K']
    vline(a, x, y - h, h + 1, W['marble'][1]); put(a, x, y - h - 1, C['gold'])
    rect(a, x + 1, y - h, 4, 2, rp[2]); put(a, x + 1, y - h, rp[4]); put(a, x + 4, y - h + 1, rp[1]); put(a, x + 2, y - h + 2, rp[1])


def banner(a, x, y, h=3, rp=None):
    rp = rp or R['K']
    rect(a, x, y, 2, h, rp[2]); vline(a, x, y, h, rp[3]); put(a, x, y + h, rp[1]); put(a, x + 1, y + h, rp[1])
    put(a, x, y + 1, C['gold'])


def columns(a, x, y, w, h, n=None):
    rp = W['marble']
    for cx in range(x, x + w - 1, 3):
        vline(a, cx, y, h, rp[2]); vline(a, cx + 1, y, h, rp[1])
        if cx + 2 < x + w: vline(a, cx + 2, y, h, lit(W['marble'][0], -.35))
    hline(a, x - 1, y - 1, w + 2, rp[2]); hline(a, x - 1, y + h, w + 2, rp[0])


def pediment(a, x, y, w, rp=None):
    rp = rp or W['marble']
    for i in range(w // 2 + 1):
        hline(a, x + w // 2 - i, y + i // 2, 2 * i + 1 if x + w // 2 + i < x + w else w - (w // 2 - i), rp[2] if i < w // 4 else rp[1])
    hline(a, x, y + w // 4 + 1, w, rp[0])


def fence(a, x, y, w, col=None):
    col = col or C['wood'][1]
    for xx in range(x, x + w):
        put(a, xx, y, lit(col, .1) if xx % 2 == 0 else col)
        if xx % 3 == 0: put(a, xx, y - 1, col)


def iron_fence(a, x, y, w):
    for xx in range(x, x + w):
        put(a, xx, y, hx('#2b2c30'))
        if xx % 2 == 0: put(a, xx, y - 1, hx('#3d3e44'))


def campfire(a, x, y, big=False):
    shadow_ell(a, x + 2, y + 2, 5 if big else 4, 2, .2)
    pts = [(-3, 0), (3, 0), (-2, -2), (2, -2), (-2, 2), (2, 2), (0, 3), (0, -3)]
    if big: pts += [(-4, 1), (4, 1), (-4, -1), (4, -1), (1, 3), (-1, 3)]
    for (dx, dy) in pts:
        put(a, x + dx, y + dy, R['stone'][2]); put(a, x + dx + 1, y + dy, R['stone'][1])
    for d in range(-2, 3): put(a, x + d, y + d // 2, C['wood'][1]); put(a, x + d, y - d // 2, C['wood'][0])
    return ('fire', x, y)


def pot(a, x, y, col=None):
    col = col or R['mud']
    dome(a, x, y, 1.6, 1.6, col); put(a, x, y - 2, col[0])


def crates(a, x, y, n=2):
    for i in range(n):
        rect(a, x + i * 3, y, 3, 2, C['wood'][2]); put(a, x + i * 3, y, lit(C['wood'][2], .2)); put(a, x + i * 3 + 2, y + 1, C['wood'][0])


def stall(a, x, y, rpA, rpB, w=6):
    vline(a, x, y - 3, 4, C['wood'][0]); vline(a, x + w - 1, y - 3, 4, C['wood'][0])
    for i in range(w + 2):
        c = rpA if (i // 2) % 2 == 0 else rpB
        put(a, x - 1 + i, y - 5, lit(c, .15)); put(a, x - 1 + i, y - 4, c)
    hline(a, x - 1, y - 3, w + 2, lit(rpA, -.35))
    hline(a, x, y, w, C['wood'][2])
    r = random.Random(x * 3 + y)
    for i in range(1, w - 1):
        put(a, x + i, y - 1, [hx('#d6b04b'), hx('#c4563d'), hx('#6c9e4c'), hx('#e8eef6')][r.randint(0, 3)])


def cart(a, x, y, load=None):
    rect(a, x, y, 5, 2, C['wood'][1]); hline(a, x, y, 5, C['wood'][2])
    if load: rect(a, x + 1, y - 1, 3, 1, load)
    put(a, x, y + 2, hx('#2b2c30')); put(a, x + 4, y + 2, hx('#2b2c30'))


def rails(a, x, y, w):
    for xx in range(x, x + w):
        put(a, xx, y, R['metal'][3]); put(a, xx, y + 2, R['metal'][3])
        if xx % 2 == 0: put(a, xx, y + 1, C['wood'][0])


def pit(a, cx, cy, rx, ry, rp, ore=None, seed=0):
    shadow_ell(a, cx + 1, cy + 1, rx + 1, ry + 1, .15)
    for k, c in enumerate([rp[3], rp[2], rp[1], rp[0]]):
        m = ellipse_mask(a.shape[:2], cx, cy + k * .6, rx * (1 - k * .22), ry * (1 - k * .22))
        a[m] = c
        if k < 3:
            m2 = ellipse_mask(a.shape[:2], cx, cy + k * .6 - .6, rx * (1 - k * .22) - .5, ry * (1 - k * .22) - .2)
            edge = m & ~m2
            a[edge] = lit(c, .18)
    if ore:
        r = random.Random(seed)
        for _ in range(int(rx * ry / 3)):
            dx, dy = r.uniform(-rx * .8, rx * .8), r.uniform(-ry * .7, ry * .7)
            if (dx / rx) ** 2 + (dy / ry) ** 2 < .7: put(a, int(cx + dx), int(cy + dy), ore)


def headframe(a, x, base, h=12, mat='wood'):
    c1 = C['wood'][2] if mat == 'wood' else R['metal'][3]
    c0 = C['wood'][0] if mat == 'wood' else R['metal'][1]
    for i in range(h):
        put(a, x + i // 4, base - i, c1); put(a, x + 6 - i // 4, base - i, c0)
        if i % 3 == 0: hline(a, x + i // 4, base - i, 7 - 2 * (i // 4), c0)
    dome(a, x + 3.5, base - h, 2.2, 2.2, R['metal'] if mat != 'wood' else [C['wood'][0], C['wood'][1], C['wood'][2], C['wood'][2], lit(C['wood'][2], .2)])
    put(a, x + 3, base - h, hx('#1c1d20'))


def heap(a, x, y, rx, ry, rp, seed=0):
    shadow_ell(a, x + 1, y + 1, rx, ry * .6, .2)
    dome(a, x, y, rx, ry, rp, seed, top=int(y + ry * .45))


def tank(a, x, base, w=5, h=5, rp=None):
    rp = rp or W['white']
    shadow_ell(a, x + w / 2 + 2, base + 1, w / 2 + 1, 1.5)
    rect(a, x, base - h + 1, w, h, rp[1]); vline(a, x, base - h + 1, h, rp[2]); vline(a, x + w - 1, base - h + 1, h, rp[0])
    dome(a, x + w / 2, base - h + 1, w / 2, 1.6, R['white'])


def dish(a, x, y, r=3):
    vline(a, x, y, 4, R['metal'][2])
    m = ellipse_mask(a.shape[:2], x, y - 1, r, r * .7)
    a[m] = W['white'][2]
    m2 = ellipse_mask(a.shape[:2], x + .5, y - .6, r * .6, r * .4)
    a[m2] = W['white'][1]
    put(a, x, y - 1, hx('#2b2c30'))


def antenna(a, x, y, h=8):
    vline(a, x, y - h, h, R['metal'][3]); put(a, x, y - h - 1, hx('#e06a55'))
    for i in range(2, h, 3): put(a, x - 1, y - h + i, R['metal'][2]); put(a, x + 1, y - h + i, R['metal'][1])


def pool(a, x, y, w, h):
    rect(a, x - 1, y - 1, w + 2, h + 2, W['white'][2])
    rect(a, x, y, w, h, C['water'][3]); hline(a, x, y, w, C['water'][2])
    for i in range(1, w - 1, 3): put(a, x + i, y + h // 2, C['water'][4])


def cooling_tower(a, x, base, w=10, h=13):
    rp = R['concrete']
    shadow_rect(a, x + 4, base - h + 4, w, h - 2, .3)
    for i in range(h):
        t = i / (h - 1)
        k = .78 + .22 * (2 * t - 1) ** 2 if t < .7 else .78 + .22 * ((t - .7) / .3) ** 1.2 + .0
        half = w / 2 * min(1, k)
        y = base - h + 1 + i
        cx = x + w / 2
        for xx in range(int(cx - half), int(math.ceil(cx + half))):
            f = (xx + .5 - (cx - half)) / (2 * half)
            c = rp[4] if f < .2 else rp[3] if f < .45 else rp[2] if f < .75 else rp[1]
            put(a, xx, y, c)
    m = ellipse_mask(a.shape[:2], x + w / 2, base - h + 1, w * .39, 1.4)
    a[m] = rp[0]
    return ('steam', int(x + w / 2), base - h - 1)


def windmill_sails(a, cx, cy, L=7):
    for t in range(-L, L + 1):
        put(a, cx + t, cy + t, C['wood'][0]); put(a, cx + t, cy - t, C['wood'][0])
    for t in range(2, L):
        for s in (1, -1):
            put(a, cx + t * s + (1 if s > 0 else -1) * 0, cy + t * s - 1, W['plaster'][2])
            put(a, cx - t * s, cy + t * s + 1 - 2 * (s < 0), W['plaster'][2])
    put(a, cx, cy, W['stone'][2])


def palisade(a, x, base, w, h=6):
    for i in range(w):
        c = C['wood'][2] if i % 2 == 0 else C['wood'][1]
        vline(a, x + i, base - h + 1, h, c)
        put(a, x + i, base - h, lit(c, .2) if i % 2 == 0 else c)
        if i % 2 == 1: put(a, x + i, base - h, a[base - h - 1, x + i] if base - h - 1 >= 0 else c)
    hline(a, x, base - 2, w, C['wood'][0])


def cannon(a, x, y):
    rect(a, x, y, 4, 1, hx('#2b2c30')); put(a, x, y, hx('#55575e'))
    put(a, x + 1, y + 1, C['wood'][0]); put(a, x + 3, y + 1, C['wood'][0])


def drone(a, x, y):
    put(a, x, y, hx('#2b2c30')); put(a, x - 1, y - 1, hx('#55575e')); put(a, x + 1, y - 1, hx('#55575e'))
    put(a, x - 1, y + 1, hx('#55575e')); put(a, x + 1, y + 1, hx('#55575e')); put(a, x, y - 1, C['cyan'])


# ============================== ERA 0: STONE AGE ==============================
def s_poor(a, x, b, s=0):
    shadow_ell(a, x + 7, b + 1, 6, 2)
    roof_tent(a, x, b - 8, 10, 9, R['hide'])
    for i in range(4):
        hline(a, x + 5 - i // 2, b - 3 + i, 1 + i, hx('#2a1d14'))
    return []


def s_rich(a, x, b, s=0):
    shadow_ell(a, x + 9, b + 1, 8, 3)
    wall(a, x, b - 2, 13, 3, 'mud', s)
    roof_thatch(a, x, b - 10, 13, 9, R['straw'], s)
    rect(a, x + 5, b - 3, 3, 4, hx('#2a1d14'))
    vline(a, x + 15, b - 6, 7, C['wood'][0]); vline(a, x + 20, b - 6, 7, C['wood'][0]); hline(a, x + 15, b - 6, 6, C['wood'][1])
    rect(a, x + 16, b - 5, 4, 4, hx('#b98e5e')); put(a, x + 16, b - 5, hx('#d6b585'))
    return [('smoke', x + 6, b - 11)]


def s_seat(a, x, b, s=0):
    bld(a, x, b, 22, 5, 9, 'hide', 'gable', R['straw'], s, win=None, dr=(3, 4))
    # bone/antler trophy over door, K war paint band
    hline(a, x, b - 4, 22, R['K'][2]); hline(a, x, b - 3, 22, R['K'][1])
    put(a, x + 9, b - 5, W['marble'][2]); put(a, x + 12, b - 5, W['marble'][2])
    # totem
    tx = x + 24
    shadow_rect(a, tx + 2, b - 10, 2, 11, .25)
    cols = [R['K'][2], C['gold'], R['K'][3], hx('#3277b0'), R['K'][1]]
    for i in range(12):
        c = cols[(i // 2) % len(cols)]
        put(a, tx, b - i, lit(c, .15)); put(a, tx + 1, b - i, c)
        if i % 2 == 0: put(a, tx + 1, b - i, hx('#1c1d20'))
    hline(a, tx - 2, b - 11, 6, C['wood'][2]); put(a, tx - 2, b - 12, C['wood'][2]); put(a, tx + 3, b - 12, C['wood'][2])
    flag(a, x - 2, b - 4, h=9)
    return [('smoke', x + 11, b - 15)]


def s_commerce(a, x, b, s=0):
    shadow_rect(a, x + 2, b - 4, 13, 4, .25)
    for px in (x, x + 11): vline(a, px, b - 6, 7, C['wood'][0])
    for i in range(13):
        put(a, x - 1 + i, b - 7, R['hide'][3] if i % 4 else R['hide'][1]); put(a, x - 1 + i, b - 6, R['hide'][2])
    rect(a, x + 1, b - 1, 10, 2, hx('#b98e5e'))
    pot(a, x + 3, b - 2); pot(a, x + 6, b - 2, R['K']); rect(a, x + 8, b - 3, 2, 2, hx('#e8e2d0'))
    for i in range(3): put(a, x + 1 + i, b - 2, hx('#d6b04b'))
    return []


def s_industry(a, x, b, s=0):
    shadow_rect(a, x + 2, b - 5, 10, 5, .25)
    vline(a, x, b - 5, 6, C['wood'][0]); vline(a, x + 9, b - 3, 4, C['wood'][0])
    for i in range(11): put(a, x - 1 + i, b - 6 + i // 4, R['straw'][2 + (i % 2)])
    for i in range(11): put(a, x - 1 + i, b - 5 + i // 4, R['straw'][1])
    rock(a, x + 3, b - 1, 2, 3); rock(a, x + 12, b - 1, 2.4, 4); rock(a, x + 15, b, 1.6, 5)
    rect(a, x + 5, b - 1, 4, 1, C['wood'][1])
    for i in range(5): put(a, x + 2 + i * 2, b + 1, R['stone'][3])
    return []


def s_mine(a, x, b, s=0):
    pit(a, x + 8, b - 3, 8, 4.5, R['stone'], seed=s)
    rock(a, x + 18, b - 1, 2.2, 1); rock(a, x + 16, b + 1, 1.6, 2)
    for i in range(5): put(a, x + 3 + i, b - 5 + i, C['wood'][2]); put(a, x + 4 + i, b - 5 + i, C['wood'][1])
    return []


def s_research(a, x, b, s=0):
    shadow_ell(a, x + 7, b + 1, 6, 2)
    stripes = {3: R['K'][2], 6: hx('#3277b0'), 9: R['K'][3]}
    roof_tent(a, x, b - 12, 10, 13, R['hide'], stripes)
    for i in range(4): hline(a, x + 5 - i // 2, b - 3 + i, 1 + i, hx('#2a1d14'))
    for ang in range(0, 360, 40):
        rx = x + 5 + int(9 * math.cos(math.radians(ang))); ry = b - 4 + int(5 * math.sin(math.radians(ang)))
        if ry > b - 2 or rx < x - 1 or rx > x + 11: put(a, rx, ry, R['stone'][3])
    put(a, x + 4, b - 14, hx('#e8e2d0')); put(a, x + 6, b - 14, R['K'][3])
    return [('smoke', x + 5, b - 14)]


def s_energy(a, x, b, s=0):
    fx = campfire(a, x + 7, b - 3, big=True)
    for i in range(3): rect(a, x + 14, b - 2 + i - 1, 5, 1, C['wood'][1 + (i % 2)])
    for i in range(3): rect(a, x - 1, b - 1 + i - 2, 4, 1, C['wood'][1 + (i % 2)])
    return [fx, ('fire', x + 7, b - 3)]


def s_military(a, x, b, s=0):
    s_poor(a, x, b, s)
    rx = x + 13
    hline(a, rx, b - 6, 6, C['wood'][1]); vline(a, rx, b - 6, 7, C['wood'][0]); vline(a, rx + 5, b - 6, 7, C['wood'][0])
    for i in range(4):
        vline(a, rx + 1 + i, b - 9, 9, C['wood'][2]); put(a, rx + 1 + i, b - 10, R['stone'][3])
    dome(a, x + 22, b - 5, 2.4, 2.4, [R['K'][1], W['plaster'][2], R['K'][2], W['plaster'][2], R['K'][3]])
    vline(a, x + 22, b - 3, 4, C['wood'][0])
    return []


def s_defense(a, x, b, s=0):
    shadow_rect(a, x + 2, b - 4, 22, 4, .3)
    palisade(a, x, b, 22, 7)
    # watch platform
    px = x + 7
    shadow_rect(a, px + 3, b - 12, 8, 12, .25)
    for dx in (0, 7): vline(a, px + dx, b - 12, 13, C['wood'][0])
    rect(a, px - 1, b - 13, 10, 2, C['wood'][2]); hline(a, px - 1, b - 13, 10, lit(C['wood'][2], .2))
    roof_tent(a, px - 1, b - 19, 10, 6, R['straw'])
    return []


# ============================== ERA 1: ANCIENT ==============================
def a_poor(a, x, b, s=0):
    bld(a, x, b, 9, 5, 4, 'mudw', 'flat', R['mud'], s, win=(1, 2, 5, 3), lit_p=.4, dr=(2, 3))
    pot(a, x + 2, b - 7, R['K']); pot(a, x + 6, b - 7)
    return []


def a_rich(a, x, b, s=0):
    top = bld(a, x, b, 18, 5, 8, 'mudw', 'flat', R['mud'], s, win=(1, 2, 4, 3), lit_p=.5, dr=(3, 3))
    rect(a, x + 4, top + 2, 10, 4, C['grass'][2]); rect(a, x + 4, top + 2, 10, 1, lit(C['grass'][0], -.2))
    rect(a, x + 8, top + 3, 3, 2, C['water'][3])
    palm(a, x + 5, top - 2, s)
    for i in range(5): put(a, x + 6 + i, b - 4, R['K'][2] if i % 2 else R['K'][3])
    hline(a, x + 6, b - 3, 5, R['K'][1])
    return []


def a_seat(a, x, b, s=0):
    bld(a, x, b, 28, 3, 3, 'stone', 'flat', R['stone'], s, win=None, dr=None)
    bld(a, x + 4, b - 6, 20, 3, 3, 'stone', 'flat', R['stone'], s + 1, win=None, dr=None, shadow=False)
    top = bld(a, x + 8, b - 12, 12, 5, 6, 'marble', 'gable', R['K'], s + 2, win=None, dr=(2, 3), shadow=False)
    columns(a, x + 9, b - 16, 10, 4)
    rect(a, x + 12, b - 11, 4, 12, R['stone'][3])
    for yy in range(b - 11, b + 1, 2): hline(a, x + 12, yy, 4, R['stone'][1])
    banner(a, x + 2, b - 2); banner(a, x + 24, b - 2); banner(a, x + 6, b - 8); banner(a, x + 20, b - 8)
    flag(a, x + 13, top, h=6)
    return [('fire', x + 3, b - 7), ('fire', x + 25, b - 7)]


def a_commerce(a, x, b, s=0):
    shadow_rect(a, x + 2, b - 4, 21, 4, .25)
    stall(a, x, b, R['K'][2], W['plaster'][2])
    stall(a, x + 8, b, hx('#3277b0'), W['plaster'][2])
    stall(a, x + 16, b, hx('#d6b04b'), W['plaster'][2])
    pot(a, x + 7, b + 1); pot(a, x + 15, b + 1, R['K'])
    return []


def a_industry(a, x, b, s=0):
    bld(a, x, b, 12, 5, 4, 'mud', 'flat', R['mud'], s, win=None, dr=(3, 3))
    shadow_ell(a, x + 17, b, 4, 2)
    dome(a, x + 15, b - 3, 4, 3.5, R['mud'], s)
    rect(a, x + 14, b - 2, 3, 2, C['fire'][1]); put(a, x + 15, b - 2, C['fire'][2])
    fx = chimney(a, x + 3, b - 13, 5, 'mud')
    for i in range(3): rect(a, x + 1 + i * 3, b + 1, 2, 1, hx('#c98a3a')); put(a, x + 1 + i * 3, b + 1, hx('#ecc25c'))
    return [fx, ('glow', x + 15, b - 2, C['fire'][1])]


def a_mine(a, x, b, s=0):
    pit(a, x + 9, b - 3, 9, 4.5, R['mud'], ore=C['ore_cu'], seed=s)
    # hoist A-frame
    for i in range(8): put(a, x + 15 + i // 3, b - 4 - i, C['wood'][2]); put(a, x + 20 - i // 3, b - 4 - i, C['wood'][0])
    hline(a, x + 16, b - 11, 5, C['wood'][1]); vline(a, x + 18, b - 10, 5, hx('#c4bfb3'))
    rect(a, x + 1, b - 1, 3, 2, hx('#b48c48')); put(a, x + 2, b - 2, C['ore_cu'])
    return []


def a_research(a, x, b, s=0):
    top = bld(a, x, b, 16, 6, 4, 'marble', 'flat', R['stone'], s, win=None, dr=(2, 3))
    columns(a, x + 1, b - 5, 14, 5)
    hline(a, x, b - 6, 16, W['marble'][2]); banner(a, x + 7, top + 1, 2)
    rect(a, x + 7, b - 3, 2, 4, C['door'])
    return []


def a_energy(a, x, b, s=0):
    rect(a, x - 2, b - 1, 24, 3, C['water'][3]); hline(a, x - 2, b - 1, 24, C['water'][2])
    for i in range(0, 24, 4): put(a, x - 2 + i, b, C['water'][4])
    bld(a, x, b - 3, 11, 5, 4, 'mudw', 'flat', R['mud'], s, win=(1, 2, 4, 3), dr=(2, 3))
    cx, cy = x + 15, b - 4
    for ang in range(0, 360, 45):
        for r_ in range(1, 5): put(a, cx + round(r_ * math.cos(math.radians(ang))), cy + round(r_ * math.sin(math.radians(ang))), C['wood'][1])
    m = ellipse_mask(a.shape[:2], cx + .5, cy + .5, 5, 5) & ~ellipse_mask(a.shape[:2], cx + .5, cy + .5, 4, 4)
    a[m] = C['wood'][2]
    return []


def a_military(a, x, b, s=0):
    bld(a, x, b, 16, 5, 5, 'mud', 'crenel', R['mud'], s, win=(1, 1, 3, 3), dr=(3, 3))
    banner(a, x + 2, b - 4); banner(a, x + 12, b - 4)
    for i in range(3): vline(a, x + 18 + i, b - 6, 7, C['wood'][2]); put(a, x + 18 + i, b - 7, hx('#c98a3a'))
    rect(a, x + 22, b - 2, 4, 2, C['wood'][1]); put(a, x + 22, b, hx('#2b2c30')); put(a, x + 25, b, hx('#2b2c30'))
    return []


def a_defense(a, x, b, s=0):
    bld(a, x, b, 24, 6, 3, 'mud', 'crenel', R['mud'], s, win=None, dr=None)
    top = bld(a, x + 8, b, 8, 11, 3, 'mud', 'crenel', R['mud'], s + 1, win=(1, 1, 3, 4), dr=(4, 4), shadow=False, winkind='sq')
    banner(a, x + 11, b - 10, 3)
    return []


# ============================== ERA 2: MEDIEVAL ==============================
def m_poor(a, x, b, s=0):
    bld(a, x, b, 10, 5, 6, 'plaster', 'gable', R['straw'], s, win=(2, 2, 6, 3), lit_p=.5, dr=(2, 3))
    return [('smoke', x + 2, b - 12)]


def m_rich(a, x, b, s=0):
    top = bld(a, x, b, 18, 7, 7, 'stone', 'gable', R['K'], s, win=(2, 2, 4, 3), lit_p=.55, dr=(2, 3), winkind='arch')
    f1 = chimney(a, x + 2, top - 3, 4); f2 = chimney(a, x + 14, top - 3, 4)
    for i in range(4): bush(a, x + 20 + (i % 2) * 3, b - 6 + i * 2, s + i)
    hline(a, x - 1, b + 2, 22, R['leaf'][1])
    return [f1, f2]


def m_seat(a, x, b, s=0):
    # side round towers
    for tx in (x, x + 20):
        bld(a, tx, b, 7, 13, 0, 'fort', 'flat', R['stone'], s + tx, win=(1, 2, 3, 4), lit_p=.6, dr=None)
        roof_cone(a, tx - 1, b - 19, 9, 7, R['K'])
    top = bld(a, x + 6, b, 15, 10, 4, 'fort', 'crenel', R['stone'], s, win=(1, 2, 3, 3), lit_p=.6, dr=(3, 4), winkind='arch', shadow=False)
    # keep tower
    bld(a, x + 10, b - 13, 7, 6, 3, 'fort', 'crenel', R['stone'], s + 3, win=(1, 2, 3, 3), lit_p=.7, dr=None, shadow=False)
    flag(a, x + 13, b - 22, h=8)
    banner(a, x + 8, b - 8); banner(a, x + 17, b - 8)
    return []


def m_commerce(a, x, b, s=0):
    top = bld(a, x, b, 18, 9, 6, 'plaster', 'gable', R['K'], s, win=(2, 2, 4, 3), lit_p=.6, dr=None)
    rect(a, x, b - 3, 18, 4, W['stone'][1])
    for i in range(1, 18, 4): rect(a, x + i, b - 2, 3, 3, hx('#1e1a16')); put(a, x + i, b - 2, W['stone'][1]); put(a, x + i + 2, b - 2, W['stone'][1])
    stall(a, x + 20, b + 1, R['K'][2], W['plaster'][2], 5)
    crates(a, x - 4, b, 1)
    return []


def m_industry(a, x, b, s=0):
    top = bld(a, x, b, 13, 5, 5, 'stone', 'gable', R['slate'], s, win=None, dr=None)
    rect(a, x + 2, b - 3, 6, 4, hx('#1e1a16')); rect(a, x + 3, b - 2, 4, 2, C['fire'][1]); put(a, x + 4, b - 2, C['fire'][2])
    fx = chimney(a, x + 9, top - 5, 7)
    rect(a, x + 14, b - 1, 3, 1, hx('#3d3e44')); put(a, x + 15, b, hx('#3d3e44')); put(a, x + 14, b - 1, hx('#8b939a'))
    crates(a, x + 14, b + 2, 1)
    return [fx, ('glow', x + 5, b - 2, C['fire'][1])]


def m_mine(a, x, b, s=0):
    heap(a, x + 7, b - 2, 8, 6, R['stone'], s)
    rect(a, x + 5, b - 4, 4, 5, hx('#14110e')); hline(a, x + 4, b - 5, 6, C['wood'][2]); vline(a, x + 4, b - 4, 5, C['wood'][1]); vline(a, x + 9, b - 4, 5, C['wood'][1])
    headframe(a, x + 13, b, 11, 'wood')
    rails(a, x + 6, b + 1, 14); cart(a, x + 15, b - 1, C['ore_fe'])
    heap(a, x + 22, b, 3, 2, [lit(C['ore_fe'], -.4), lit(C['ore_fe'], -.2), C['ore_fe'], lit(C['ore_fe'], .2), lit(C['ore_fe'], .35)], s + 1)
    return []


def m_research(a, x, b, s=0):
    top = bld(a, x, b, 18, 7, 6, 'stone', 'gable', R['slate'], s, win=(2, 3, 4, 4), lit_p=.6, dr=(2, 3), winkind='arch')
    bld(a, x + 13, b - 7, 6, 10, 0, 'stone', 'flat', R['stone'], s + 2, win=(2, 3, 3, 4), lit_p=.6, dr=None, shadow=False, winkind='arch')
    roof_cone(a, x + 12, b - 23, 8, 7, R['slate'])
    put(a, x + 16, b - 24, C['gold'])
    return []


def m_energy(a, x, b, s=0):
    bld(a, x + 4, b, 7, 11, 0, 'plaster', 'flat', R['stone'], s, win=(2, 2, 3, 4), lit_p=.3, dr=(2, 3))
    roof_cone(a, x + 3, b - 16, 9, 6, R['K'])
    windmill_sails(a, x + 7, b - 12, 7)
    rect(a, x + 13, b - 1, 4, 2, hx('#e8e2d0')); put(a, x + 13, b - 1, hx('#f6f1e2'))
    return []


def m_military(a, x, b, s=0):
    bld(a, x, b, 17, 6, 5, 'stone', 'gable', R['slate'], s, win=(1, 2, 3, 3), lit_p=.5, dr=(3, 3))
    banner(a, x + 2, b - 5); banner(a, x + 13, b - 5)
    fence(a, x + 19, b - 6, 8); fence(a, x + 19, b, 8); vline(a, x + 19, b - 6, 7, C['wood'][1]); vline(a, x + 26, b - 6, 7, C['wood'][1])
    vline(a, x + 22, b - 4, 4, C['wood'][1]); hline(a, x + 21, b - 3, 3, hx('#b98e5e')); put(a, x + 22, b - 5, hx('#d6b585'))
    return []


def m_defense(a, x, b, s=0):
    bld(a, x, b, 22, 7, 3, 'fort', 'crenel', R['stone'], s, win=None, dr=None)
    bld(a, x + 14, b + 1, 8, 13, 0, 'fort', 'flat', R['stone'], s + 1, win=(1, 2, 3, 4), lit_p=.4, dr=None, shadow=False)
    roof_cone(a, x + 13, b - 18, 10, 7, R['K'])
    rect(a, x + 4, b - 4, 4, 5, hx('#14110e')); hline(a, x + 4, b - 4, 4, W['fort'][2])
    return []


# ============================== ERA 3: INDUSTRIAL ==============================
def i_poor(a, x, b, s=0):
    fx = []
    for i in range(3):
        top = bld(a, x + i * 8, b, 8, 6, 5, 'brick', 'gable', R['K'], s + i, win=(2, 2, 4, 3), lit_p=.5, dr=(2, 3), shadow=(i == 0))
        fx.append(chimney(a, x + i * 8 + 5, top - 2, 3, 'brick'))
    shadow_rect(a, x + 4, b - 8, 22, 9, .18)
    return fx


def i_rich(a, x, b, s=0):
    top = bld(a, x, b, 16, 8, 6, 'stone', 'hip', R['slate'], s, win=(2, 3, 4, 4), lit_p=.6, dr=(2, 3))
    iron_fence(a, x - 2, b + 3, 22)
    for i in range(3): bush(a, x + 18, b - 6 + i * 3, s + i)
    vline(a, x - 3, b - 4, 7, hx('#2b2c30')); put(a, x - 3, b - 5, C['lit'])
    fx = chimney(a, x + 12, top - 2, 3)
    return [fx, ('glow', x - 3, b - 5, C['lit'])]


def i_seat(a, x, b, s=0):
    top = bld(a, x, b, 26, 8, 5, 'marble', 'flat', R['concrete'], s, win=(2, 3, 4, 4), lit_p=.6, dr=None)
    columns(a, x + 8, b - 7, 10, 7)
    pediment(a, x + 7, b - 12, 12)
    rect(a, x + 12, b - 3, 2, 4, C['door'])
    # clock tower
    tx = x + 10
    bld(a, tx, b - 13, 6, 9, 0, 'marble', 'flat', R['concrete'], s + 1, win=None, dr=None, shadow=False)
    m = ellipse_mask(a.shape[:2], tx + 3, b - 18, 2.2, 2.2); a[m] = hx('#f6f1e2')
    put(a, tx + 3, b - 19, hx('#1c1d20')); put(a, tx + 3, b - 18, hx('#1c1d20')); put(a, tx + 4, b - 18, hx('#1c1d20'))
    dome(a, tx + 3, b - 23, 3.4, 3, R['copper'], s)
    flag(a, tx + 3, b - 26, h=5)
    flag(a, x + 1, b - 8, h=6); flag(a, x + 24, b - 8, h=6)
    return []


def i_commerce(a, x, b, s=0):
    top = bld(a, x, b, 18, 11, 4, 'brick', 'flat', R['concrete'], s, win=(3, 2, 4, 3), lit_p=.75, dr=(4, 3))
    rect(a, x + 2, top + 4, 14, 2, R['K'][2]); hline(a, x + 2, top + 4, 14, R['K'][3])
    for i in range(3): put(a, x + 5 + i * 4, top + 5, C['gold'])
    for i in range(18): put(a, x + i, b - 4, R['K'][2] if (i // 2) % 2 else W['plaster'][2])
    hline(a, x, b - 3, 18, lit(R['K'][1], -.2))
    return []


def i_industry(a, x, b, s=0):
    top = bld(a, x, b, 26, 8, 6, 'brick', 'sawtooth', None, s, win=(3, 4, 5, 6), lit_p=.8, dr=None)
    rect(a, x + 19, b - 4, 5, 5, R['metal'][1])
    for yy in range(b - 4, b + 1, 2): hline(a, x + 19, yy, 5, R['metal'][0])
    hline(a, x, b - 7, 26, R['K'][2])
    cx = x + 3
    rect(a, cx, top - 10, 4, 12, W['brick'][1]); vline(a, cx, top - 10, 12, W['brick'][2]); vline(a, cx + 3, top - 10, 12, W['brick'][0])
    hline(a, cx - 1, top - 10, 6, R['stone'][3])
    return [('smoke', cx + 2, top - 12)]


def i_mine(a, x, b, s=0):
    bld(a, x, b, 10, 6, 4, 'brick', 'gable', R['slate'], s, win=(2, 2, 4, 3), lit_p=.6, dr=(2, 3))
    fx = chimney(a, x + 7, b - 14, 5, 'brick')
    headframe(a, x + 12, b, 16, 'steel')
    heap(a, x + 24, b - 1, 4, 3, C['coal'] + [C['coal'][2], hx('#55575e')], s)
    rails(a, x + 10, b + 2, 18); cart(a, x + 19, b, C['coal'][1])
    return [fx]


def i_research(a, x, b, s=0):
    top = bld(a, x, b, 24, 8, 5, 'stone', 'flat', R['slate'], s, win=(2, 3, 4, 4), lit_p=.6, dr=None, winkind='arch')
    columns(a, x + 8, b - 7, 8, 7)
    rect(a, x + 11, b - 3, 2, 4, C['door'])
    dome(a, x + 12, top - 1, 5, 4.4, R['copper'], s)
    put(a, x + 12, top - 6, C['gold'])
    return []


def i_energy(a, x, b, s=0):
    top = bld(a, x, b, 22, 9, 5, 'brick', 'flat', R['metal'], s, win=(2, 4, 4, 6), lit_p=.7, dr=(4, 4))
    fx = []
    for cx in (x + 4, x + 14):
        rect(a, cx, top - 14, 4, 16, W['brick'][1]); vline(a, cx, top - 14, 16, W['brick'][2]); vline(a, cx + 3, top - 14, 16, W['brick'][0])
        hline(a, cx - 1, top - 14, 6, R['stone'][3]); hline(a, cx, top - 9, 4, MORTAR)
        fx.append(('smoke', cx + 2, top - 16))
    heap(a, x + 26, b - 1, 4, 3, C['coal'] + [C['coal'][2], hx('#55575e')], s)
    return fx


def i_military(a, x, b, s=0):
    bld(a, x, b, 18, 6, 4, 'brick', 'flat', R['concrete'], s, win=(1, 2, 3, 3), lit_p=.5, dr=(3, 3))
    flag(a, x + 21, b, h=12)
    cannon(a, x + 1, b + 3); cannon(a, x + 8, b + 3)
    hline(a, x, b - 4, 18, R['K'][2])
    return []


def i_defense(a, x, b, s=0):
    from PIL import Image as _I, ImageDraw as _D
    def poly_mask(pts):
        im = _I.new('L', (a.shape[1], a.shape[0]), 0); _D.Draw(im).polygon(pts, fill=1)
        return np.asarray(im).astype(bool)
    outer = [(x, b - 9), (x + 26, b - 9), (x + 26, b - 3), (x + 13, b + 3), (x, b - 3)]
    face = poly_mask([(px, py + 3) for px, py in outer]) & ~poly_mask(outer)
    shadow_rect(a, x + 3, b - 6, 27, 11, .25)
    a[face] = W['fort'][0]
    for yy in range(b - 9, b + 7):
        for xx in range(x, x + 27):
            if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and face[yy, xx] and (xx + yy) % 4 == 0: a[yy, xx] = W['fort'][1]
    m = poly_mask(outer); a[m] = W['fort'][2]
    inner = poly_mask([(x + 2, b - 7), (x + 24, b - 7), (x + 24, b - 4), (x + 13, b + 1), (x + 2, b - 4)])
    a[inner] = C['grass'][0]
    hline(a, x, b - 9, 27, R['stone'][4])
    cannon(a, x + 5, b - 5); cannon(a, x + 17, b - 5); cannon(a, x + 11, b - 2)
    flag(a, x + 13, b - 7, h=7)
    return []


# ============================== ERA 4: MODERN ==============================
def o_poor(a, x, b, s=0):
    top = bld(a, x, b, 20, 15, 4, 'concrete', 'flat', R['concrete'], s, win=(2, 2, 4, 4), lit_p=.4, dr=(3, 3))
    for yy in range(b - 13, b - 3, 4): hline(a, x + 1, yy + 2, 18, W['concrete'][0])
    rect(a, x, b - 5, 20, 2, R['K'][2]); hline(a, x, b - 5, 20, R['K'][3])
    return []


def o_rich(a, x, b, s=0):
    top = bld(a, x, b, 16, 6, 6, 'white', 'flat', R['white'], s, win=(3, 2, 4, 3), lit_p=.5, dr=(3, 3))
    hline(a, x + 1, b - 4, 14, W['glass'][2]); hline(a, x + 1, b - 3, 14, W['glass'][1])
    rect(a, x + 4, top + 1, 6, 2, W['glass'][2])
    pool(a, x + 19, b - 6, 7, 4)
    palm(a, x + 18, b - 9, s); bush(a, x + 26, b + 1, s)
    hline(a, x - 1, b + 3, 30, R['leaf'][2])
    return []


def o_seat(a, x, b, s=0):
    top = bld(a, x, b, 30, 8, 6, 'marble', 'flat', R['concrete'], s, win=(2, 3, 4, 4), lit_p=.6, dr=None)
    columns(a, x + 9, b - 7, 13, 7)
    pediment(a, x + 8, b - 13, 15)
    rect(a, x + 14, b - 3, 3, 4, C['door'])
    dome(a, x + 15, top - 3, 7, 6, R['copper'], s)
    rect(a, x + 13, top - 10, 5, 2, W['marble'][2]); put(a, x + 15, top - 11, C['gold'])
    flag(a, x + 2, b - 8, h=8); flag(a, x + 27, b - 8, h=8, rp=K2['blue'])
    for i in range(4): hline(a, x + 10, b + 1 + i, 12, R['concrete'][3 - (i % 2)])
    return []


def o_commerce(a, x, b, s=0):
    r = random.Random(s)
    shadow_rect(a, x + 6, b - 26, 15, 27, .34)
    rect(a, x, b - 30, 15, 4, R['concrete'][3]); hline(a, x, b - 27, 15, R['concrete'][0])
    rect(a, x + 2, b - 29, 3, 2, R['metal'][2]); antenna(a, x + 11, b - 30, 6)
    wall(a, x, b - 26, 15, 27, 'glass', s)
    for yy in range(b - 24, b - 4, 3):
        for xx in range(x + 1, x + 14, 3):
            if r.random() < .3: rect(a, xx, yy, 2, 2, C['lit'])
    hline(a, x, b - 26, 15, R['K'][2]); hline(a, x, b - 25, 15, R['K'][3])
    rect(a, x, b - 3, 15, 4, W['concrete'][1]); rect(a, x + 5, b - 2, 5, 3, C['lit'])
    return []


def o_industry(a, x, b, s=0):
    top = bld(a, x, b, 20, 6, 6, 'metal', 'flat', R['white'], s, win=None, dr=(5, 4), door_col=W['metal'][0])
    for i in range(0, 20, 2): hline(a, x, top + 1 + (i // 2) % 2, 1, R['white'][2])
    hline(a, x, b - 5, 20, R['K'][2])
    for i in range(3): tank(a, x + 22 + i * 6, b, 5, 7)
    vline(a, x + 21, b - 6, 7, R['metal'][3]); hline(a, x + 21, b - 6, 18, R['metal'][3])
    return [('steam', x + 25, b - 9)]


def o_mine(a, x, b, s=0):
    pit(a, x + 10, b - 3, 11, 5.5, R['mud'], ore=hx('#55575e'), seed=s)
    # pumpjack
    px = x + 22
    rect(a, px, b - 1, 7, 2, R['metal'][1])
    for i in range(6): put(a, px + 2 + i // 3, b - 2 - i, R['metal'][3]); put(a, px + 5 - i // 3, b - 2 - i, R['metal'][1])
    hline(a, px - 1, b - 8, 10, hx('#2b2c30')); rect(a, px - 2, b - 9, 2, 3, hx('#e8b46a'))
    rect(a, px + 8, b - 3, 2, 3, hx('#2b2c30'))
    return []


def o_research(a, x, b, s=0):
    top = bld(a, x, b, 16, 6, 5, 'white', 'flat', R['white'], s, win=(3, 2, 4, 3), lit_p=.6, dr=(3, 3))
    hline(a, x, b - 5, 16, C['cyan'])
    dish(a, x + 20, b - 4, 4)
    antenna(a, x + 13, top, 7)
    return []


def o_energy(a, x, b, s=0):
    f1 = cooling_tower(a, x, b, 11, 15)
    f2 = cooling_tower(a, x + 12, b + 2, 11, 15)
    shadow_rect(a, x + 26, b - 6, 9, 8, .3)
    rect(a, x + 24, b - 4, 9, 5, W['white'][1]); vline(a, x + 24, b - 4, 5, W['white'][2])
    dome(a, x + 28.5, b - 5, 4.5, 3.6, R['white'], s)
    hline(a, x + 24, b - 1, 9, hx('#e8b46a'))
    return [f1, f2]


def o_military(a, x, b, s=0):
    shadow_rect(a, x + 3, b - 6, 18, 8, .3)
    rect(a, x, b - 4, 18, 5, W['metal'][1])
    for i in range(7):
        t = 1 - ((i - 3) / 3.5) ** 2
        hline(a, x, b - 5 - i // 2, 18, R['metal'][2 + (i < 3)])
    dome(a, x + 9, b - 6, 9.5, 3.5, R['metal'], s, top=b - 4)
    rect(a, x + 6, b - 3, 6, 4, hx('#1c1d20'))
    hp = x + 21
    rect(a, hp, b - 6, 8, 7, hx('#3c3f45')); m = ellipse_mask(a.shape[:2], hp + 4, b - 2.5, 3.4, 3.2) & ~ellipse_mask(a.shape[:2], hp + 4, b - 2.5, 2.6, 2.4); a[m] = W['white'][2]
    vline(a, hp + 3, b - 4, 4, W['white'][2]); vline(a, hp + 5, b - 4, 4, W['white'][2]); hline(a, hp + 3, b - 2, 3, W['white'][2])
    rect(a, x + 1, b + 3, 4, 2, hx('#4f5a3a')); put(a, x + 1, b + 3, hx('#6b7a4f'))
    return []


def o_defense(a, x, b, s=0):
    shadow_rect(a, x + 2, b - 3, 15, 5, .3)
    rect(a, x, b - 3, 14, 4, W['concrete'][1]); hline(a, x, b - 4, 14, R['concrete'][3]); hline(a, x + 1, b - 5, 12, R['concrete'][2])
    for i in range(2, 13, 4): hline(a, x + i, b - 2, 2, hx('#14110e'))
    dish(a, x + 18, b - 3, 3)
    rect(a, x + 22, b - 2, 4, 3, W['metal'][1]); hline(a, x + 23, b - 5, 1, R['metal'][3]); vline(a, x + 24, b - 6, 4, R['metal'][3]); vline(a, x + 25, b - 6, 4, R['metal'][3])
    return []


# ============================== ERA 5: FUTURE ==============================
def f_poor(a, x, b, s=0):
    for i, (dx, dy) in enumerate([(0, 0), (7, 0), (3, -6), (14, 0)]):
        shadow_ell(a, x + dx + 5, b + dy + 1, 4, 1.5)
        dome(a, x + dx + 3, b + dy - 2, 3.4, 3, R['white'], s + i)
        hline(a, x + dx + 1, b + dy - 2, 4, C['cyan']); put(a, x + dx + 1, b + dy - 2, C['cyan2'])
    return [('glow', x + 9, b - 4, C['cyan'])]


def f_rich(a, x, b, s=0):
    shadow_ell(a, x + 11, b + 1, 11, 3)
    rect(a, x, b - 2, 20, 3, W['white'][1]); hline(a, x, b - 2, 20, W['white'][2]); hline(a, x, b, 20, C['cyan'])
    m = ellipse_mask(a.shape[:2], x + 10, b - 4, 9, 7)
    gr = grass_ground(a.shape[1], a.shape[0], 9)
    a[m] = gr[m]
    for (tx, ty) in [(6, -6), (12, -8), (14, -4)]: bush(a, x + tx, b + ty, s + tx)
    pool(a, x + 4, b - 5, 4, 2)
    blend_mask(a, m, R['glass'][4], .35)
    m2 = ellipse_mask(a.shape[:2], x + 10, b - 4, 9, 7) & ~ellipse_mask(a.shape[:2], x + 10, b - 4, 8.2, 6.2)
    a[m2] = R['glass'][3]
    put(a, x + 6, b - 9, (255, 255, 255)); put(a, x + 5, b - 8, (255, 255, 255))
    return []


def f_seat(a, x, b, s=0):
    shadow_rect(a, x + 9, b - 30, 14, 31, .32)
    m = ellipse_mask(a.shape[:2], x + 12, b + 1, 13, 3.5); a[m] = W['white'][2]
    hline(a, x, b + 1, 25, C['cyan'])
    for i in range(34):
        hw = 7 - i * 6.2 / 34
        y = b - i
        for xx in range(int(x + 12 - hw), int(math.ceil(x + 12 + hw))):
            f = (xx - (x + 12 - hw)) / (2 * hw)
            c = R['glass'][4] if f < .18 else R['glass'][3] if f < .45 else R['glass'][2] if f < .8 else R['glass'][1]
            if i % 4 == 0: c = C['cyan'] if f < .5 else lit(C['cyan'], -.3)
            put(a, xx, y, c)
    for i in range(3): put(a, x + 12, b - 34 - i, C['gold'])
    rect(a, x + 10, b - 35, 5, 1, R['K'][2]); put(a, x + 12, b - 36, R['K'][3])
    flag(a, x + 1, b, h=8); flag(a, x + 23, b, h=8)
    return [('glow', x + 12, b - 34, C['cyan'])]


def f_commerce(a, x, b, s=0):
    shadow_ell(a, x + 13, b, 12, 4)
    for i in range(10):
        hw = 11 - abs(i - 2) * .4
        hline(a, int(x + 11 - hw), b - i, int(2 * hw), W['white'][2] if i % 3 else W['white'][1])
    hline(a, x + 1, b - 3, 20, C['cyan'])
    rect(a, x + 3, b - 14, 6, 3, C['magenta']); hline(a, x + 3, b - 14, 6, lit(C['magenta'], .4))
    rect(a, x + 13, b - 16, 7, 3, C['cyan']); hline(a, x + 13, b - 16, 7, C['cyan2'])
    vline(a, x + 6, b - 11, 2, R['metal'][3]); vline(a, x + 16, b - 13, 4, R['metal'][3])
    rect(a, x + 9, b - 2, 4, 3, C['lit'])
    return [('holo', x + 6, b - 13, C['magenta']), ('holo', x + 16, b - 15, C['cyan'])]


def f_industry(a, x, b, s=0):
    bld(a, x, b, 20, 7, 5, 'white', 'solar', None, s, win=None, dr=(6, 4), door_col=W['dark'][1])
    hline(a, x, b - 6, 20, C['cyan'])
    for k, ax in enumerate((x + 23, x + 29)):
        vline(a, ax, b - 4, 5, R['metal'][2]); put(a, ax, b - 5, hx('#e8b46a'))
        for t in range(4): put(a, ax + 1 + t // 2, b - 5 - t, R['metal'][3])
        put(a, ax + 3, b - 9, C['cyan'])
    hline(a, x + 21, b + 1, 12, hx('#3c3f45')); hline(a, x + 21, b + 2, 12, hx('#2b2c30'))
    drone(a, x + 26, b - 14); drone(a, x + 32, b - 11)
    return [('glow', x + 26, b - 9, C['cyan'])]


def f_mine(a, x, b, s=0):
    m = ellipse_mask(a.shape[:2], x + 9, b - 1, 5, 2.4); a[m] = hx('#1c1d20')
    blend_mask(a, ellipse_mask(a.shape[:2], x + 9, b - 1, 3, 1.4), hx('#ff8a3c'), .8)
    for i in range(18):
        put(a, x + 6 + (i % 2), b - 3 - i, W['dark'][2]); put(a, x + 12 - (i % 2), b - 3 - i, W['dark'][0])
        if i % 3 == 0: hline(a, x + 6, b - 3 - i, 7, W['dark'][1])
    rect(a, x + 5, b - 22, 9, 3, W['white'][2]); hline(a, x + 5, b - 20, 9, C['cyan'])
    vline(a, x + 9, b - 19, 18, hx('#8b939a'))
    for i in range(2): rect(a, x + 16 + i * 6, b - 3, 5, 4, R['K'][2] if i == 0 else W['white'][1]); hline(a, x + 16 + i * 6, b - 3, 5, lit(R['K'][2] if i == 0 else W['white'][1], .25))
    return [('glow', x + 9, b - 1, hx('#ff8a3c'))]


def f_research(a, x, b, s=0):
    bld(a, x, b, 18, 5, 5, 'white', 'flat', R['white'], s, win=(3, 1, 4, 3), lit_p=.8, dr=(3, 3))
    for rr, c in ((8, W['dark'][1]), (7, C['cyan']), (6, W['dark'][0])):
        m = ellipse_mask(a.shape[:2], x + 9, b - 13, rr + 2, rr * .45 + 1) & ~ellipse_mask(a.shape[:2], x + 9, b - 13, rr + 1, rr * .45)
        a[m] = c
    vline(a, x + 3, b - 12, 3, R['metal'][3]); vline(a, x + 15, b - 12, 3, R['metal'][3])
    return [('glow', x + 9, b - 13, C['cyan'])]


def f_energy(a, x, b, s=0):
    shadow_ell(a, x + 10, b, 10, 4)
    m = ellipse_mask(a.shape[:2], x + 9, b - 4, 9, 4.6) & ~ellipse_mask(a.shape[:2], x + 9, b - 4, 4.5, 2)
    a[m] = W['dark'][1]
    blend_mask(a, ellipse_mask(a.shape[:2], x + 9, b - 4, 9, 4.6) & ~ellipse_mask(a.shape[:2], x + 9, b - 4.6, 8.5, 4.1), W['dark'][2], 1)
    m3 = ellipse_mask(a.shape[:2], x + 9, b - 4, 6.8, 3.2) & ~ellipse_mask(a.shape[:2], x + 9, b - 4, 5.6, 2.5)
    a[m3] = C['cyan']
    a[ellipse_mask(a.shape[:2], x + 9, b - 4, 3.6, 1.5)] = C['cyan2']
    for yy in range(b - 6, b + 3, 3):
        for xx in range(x + 21, x + 33, 3):
            rect(a, xx, yy, 2, 2, hx('#2a4f8a')); put(a, xx, yy, hx('#6f9bd8'))
    return [('glow', x + 9, b - 4, C['cyan'])]


def f_military(a, x, b, s=0):
    shadow_rect(a, x + 3, b - 6, 20, 8, .32)
    for i in range(7):
        hline(a, x + max(0, 3 - i), b - 6 + i, 20 - 2 * max(0, 3 - i), W['dark'][2 if i < 2 else 1])
    hline(a, x, b - 3, 20, R['K'][2])
    rect(a, x + 6, b - 2, 8, 3, hx('#0e1116')); hline(a, x + 6, b - 2, 8, C['cyan'])
    for (dx, dy) in [(4, -12), (12, -14), (19, -11), (25, -6)]: drone(a, x + dx, b + dy)
    return []


def f_defense(a, x, b, s=0):
    shadow_rect(a, x + 13, b - 14, 4, 15, .3)
    for i in range(16):
        put(a, x + 12, b - i, W['white'][2]); put(a, x + 13, b - i, W['white'][1]); put(a, x + 14, b - i, W['white'][0])
    dome(a, x + 13, b - 17, 2.4, 2.2, R['white'], s); put(a, x + 13, b - 17, C['cyan'])
    m = ellipse_mask(a.shape[:2], x + 13, b - 2, 14, 13)
    m = m & (np.mgrid[0:a.shape[0], 0:a.shape[1]][0] <= b + 1)
    blend_mask(a, m, C['cyan'], .14)
    edge = m & ~ellipse_mask(a.shape[:2], x + 13, b - 2, 13, 12)
    blend_mask(a, edge, C['cyan2'], .55)
    return [('glow', x + 13, b - 17, C['cyan'])]


BUILD = [
    dict(poor=s_poor, rich=s_rich, seat=s_seat, commerce=s_commerce, industry=s_industry, mine=s_mine,
         research=s_research, energy=s_energy, military=s_military, defense=s_defense),
    dict(poor=a_poor, rich=a_rich, seat=a_seat, commerce=a_commerce, industry=a_industry, mine=a_mine,
         research=a_research, energy=a_energy, military=a_military, defense=a_defense),
    dict(poor=m_poor, rich=m_rich, seat=m_seat, commerce=m_commerce, industry=m_industry, mine=m_mine,
         research=m_research, energy=m_energy, military=m_military, defense=m_defense),
    dict(poor=i_poor, rich=i_rich, seat=i_seat, commerce=i_commerce, industry=i_industry, mine=i_mine,
         research=i_research, energy=i_energy, military=i_military, defense=i_defense),
    dict(poor=o_poor, rich=o_rich, seat=o_seat, commerce=o_commerce, industry=o_industry, mine=o_mine,
         research=o_research, energy=o_energy, military=o_military, defense=o_defense),
    dict(poor=f_poor, rich=f_rich, seat=f_seat, commerce=f_commerce, industry=f_industry, mine=f_mine,
         research=f_research, energy=f_energy, military=f_military, defense=f_defense),
]

SUBTITLE = [
    dict(poor='HIDE TENT', rich='BIG HUT', seat="CHIEF'S HALL", commerce='BARTER POST', industry='FLINT CAMP',
         mine='QUARRY', research="SHAMAN'S TENT", energy='GREAT FIRE', military='HUNT LODGE', defense='PALISADE'),
    dict(poor='MUD HOUSE', rich='COURT VILLA', seat='STEP PALACE', commerce='BAZAAR', industry='BRONZE FOUNDRY',
         mine='COPPER PIT', research='SCRIBE HALL', energy='WATER WHEEL', military='BARRACKS', defense='MUD WALL'),
    dict(poor='COTTAGE', rich='MANOR', seat='CASTLE', commerce='MARKET HALL', industry='FORGE',
         mine='IRON SHAFT', research='MONASTERY', energy='WINDMILL', military='GARRISON', defense='STONE WALL'),
    dict(poor='TERRACES', rich='TOWNHOUSE', seat='CITY HALL', commerce='DEPT STORE', industry='FACTORY',
         mine='COAL MINE', research='UNIVERSITY', energy='COAL PLANT', military='ARMORY', defense='BASTION'),
    dict(poor='APARTMENTS', rich='POOL VILLA', seat='PARLIAMENT', commerce='OFFICE TOWER', industry='PLANT',
         mine='OPEN PIT+OIL', research='LAB', energy='NUCLEAR', military='AIR BASE', defense='RADAR BUNKER'),
    dict(poor='HAB PODS', rich='DOME VILLA', seat='CRYSTAL SPIRE', commerce='HOLO MALL', industry='FABRICATOR',
         mine='CORE DRILL', research='QUANTUM RING', energy='FUSION', military='DRONE HANGAR', defense='SHIELD TOWER'),
]
