"""Modular housing generator: culture x tier x archetype x seed -> unique house.
Tiers: 0 slum, 1 poor, 2 middle, 3 rich, 4 palace. Each tier has several structural archetypes per culture."""
import math, random
import numpy as np
from lib import *
from buildings import (wall, windows, door, roof_gable, roof_hip, roof_flat, roof_thatch, roof_cone, roof_crenel,
                       chimney, flag, banner, columns, fence, iron_fence, pot, crates, stall, pool, bld)

W.update({
    'logs': ramp('#4e3626', '#6b4b33', '#8a6544'),
    'planks': ramp('#3f2c20', '#57402e', '#74573f'),
    'reedw': ramp('#8d7a4e', '#a8935f', '#c2ad78'),
    'adobe': ramp('#9a6e45', '#b8875a', '#d1a576'),
    'pinkw': ramp('#b48a7a', '#d0a898', '#e6c4b4'),
    'whitew': ramp('#c2bcae', '#dcd6c8', '#f0ebdf'),
    'redp': ramp('#6e2620', '#8a3328', '#a84636'),
    'ochrep': ramp('#8a6420', '#a87d2e', '#c69a44'),
    'greyp': ramp('#5c6670', '#76808a', '#929ca4'),
    'whitep': ramp('#a8a49a', '#c8c4b8', '#e0dcd0'),
})
R.update({
    'turf': ramp('#3f5e2c', '#527838', '#679344', '#82ad55', '#a6c972'),
    'shingle': ramp('#3a2a20', '#4f3a2b', '#664c38', '#80614a', '#9c7b5f'),
    'reed': ramp('#6f6234', '#8c7d45', '#a99857', '#c4b26e', '#ddcb8a'),
    'teal': ramp('#1f4d4f', '#2b6a6a', '#3a8a86', '#5aaca4', '#8ccfc4'),
    'whitedome': ramp('#a9a49a', '#c9c4b8', '#e2ddd2', '#f3f0e8', '#ffffff'),
    'tin': ramp('#5a5f66', '#757b82', '#8f959b', '#aab0b5', '#c4c9cd'),
    'ochre': ramp('#6b4a16', '#8f6622', '#b38432', '#cfa24a', '#e6c272'),
    'green': ramp('#284a32', '#345f40', '#467a50', '#5e9564', '#82b482'),
})
CULTURES = ['riverland', 'northern', 'highland']
CULT_NAMES = {'riverland': 'RIVERLAND', 'northern': 'NORTHERN', 'highland': 'HIGHLAND'}
TIERS = ['SLUM', 'POOR', 'MIDDLE', 'RICH', 'PALACE']


def jr(rp, rng, k=.07):
    j = rng.uniform(-k, k); return [lit(c, j) for c in rp]


def block(a, x, b, w, wh, rh, wallm, roof, rp, seed, win=(1, 2, 4, 3), lit_p=.45, dpos='c', dw=2, dh=3,
          winkind='sq', shadow=True, dcol=None, shut=False):
    top = b - wh - rh + 1
    fy = b - wh + 1
    if shadow: shadow_rect(a, x + 3, top + 3, w + 1, wh + rh - 1)
    wall(a, x, fy, w, wh, wallm, seed)
    dx = None
    if dpos:
        dx = {'l': x + 2, 'c': x + (w - dw) // 2, 'r': x + w - 2 - dw}[dpos]
    windows(a, x, fy, w, wh, win, lit_p, seed, (dx - 1, dw + 2, b - dh - 1) if dx is not None else None, winkind)
    if shut and win:
        rng = random.Random(seed)
        for yy in range(fy + 1, b - 1):
            for xx in range(x + 1, x + w - 1):
                if tuple(a[yy, xx]) in (tuple(C['lit2']), tuple(C['win'])) and tuple(a[yy, xx - 1]) not in (tuple(C['lit2']), tuple(C['win']), tuple(C['lit']), tuple(lit(C['win'], .3))):
                    put(a, xx - 1, yy, C['wood'][1])
    if dx is not None: door(a, dx, b - dh + 1, dw, dh, dcol, arch=winkind == 'arch')
    if roof == 'gable': roof_gable(a, x, top, w, rh, rp)
    elif roof == 'hip': roof_hip(a, x, top, w, rh, rp)
    elif roof == 'flat': roof_flat(a, x, top, w, rh, rp, seed)
    elif roof == 'crenel': roof_crenel(a, x, top, w, rh, rp)
    elif roof == 'cone': roof_cone(a, x, top, w, rh, rp)
    elif roof == 'thatch': roof_thatch(a, x, top, w, rh, rp, seed)
    return top


# ---------- props ----------
def flowerbox(a, x, y, rng):
    for i in range(2): put(a, x + i, y, [hx('#d5452d'), hx('#e8c84a'), hx('#c45aa8')][rng.randint(0, 2)])


def laundry(a, x, y, w, rng):
    hline(a, x, y, w, hx('#c9c2b0'))
    for i in range(1, w - 1, 2):
        put(a, x + i, y + 1, [hx('#e8e2d0'), R['K'][3], hx('#6a9ad3'), hx('#e8c84a')][rng.randint(0, 3)])
        if rng.random() < .5: put(a, x + i, y + 2, a[y + 1, x + i])


def woodpile(a, x, y):
    for i in range(3):
        for j in range(3 - i // 2):
            put(a, x + j * 2 + i % 2, y - i, C['wood'][2] if (i + j) % 2 else C['wood'][1])


def garden(a, x, y, w, h, rng, flowers=True):
    rect(a, x, y, w, h, C['grass'][2])
    hline(a, x, y, w, lit(C['grass'][2], .12))
    if flowers:
        for _ in range(max(1, w * h // 8)):
            put(a, x + rng.randint(0, w - 1), y + rng.randint(0, h - 1), [hx('#d5452d'), hx('#e8c84a'), hx('#f0efe2'), R['leaf'][3]][rng.randint(0, 3)])


def patch_roof(a, x, top, w, rh, rng):
    for _ in range(max(2, w // 3)):
        px, py = x + rng.randint(0, max(0, w - 2)), top + rng.randint(0, max(0, rh - 1))
        c = [R['tin'][2], R['tin'][3], C['wood'][1], hx('#8a7a5a'), R['K'][2], hx('#4579bb')][rng.randint(0, 5)]
        rect(a, px, py, 2, 1, c)


def goat(a, x, y):
    rect(a, x, y, 3, 2, hx('#e8e2d0')); put(a, x + 3, y - 1, hx('#e8e2d0')); put(a, x + 3, y - 2, hx('#8a7a5a'))
    put(a, x, y + 2, hx('#3a3530')); put(a, x + 2, y + 2, hx('#3a3530'))


def pergola(a, x, y, w, h):
    for xx in range(x, x + w, 2): vline(a, xx, y, h, C['wood'][2])
    hline(a, x, y, w, C['wood'][1])
    for xx in range(x, x + w):
        if (xx * 3) % 4: put(a, xx, y + 1, R['leaf'][3 if xx % 2 else 2])


def windcatcher(a, x, y, h, m):
    rect(a, x, y - h, 3, h, W[m][1]); vline(a, x, y - h, h, W[m][2]); vline(a, x + 2, y - h, h, W[m][0])
    rect(a, x, y - h + 1, 3, 2, C['win']); hline(a, x - 1, y - h - 1, 5, R['mud'][3])


def stairs_side(a, x, b, n, col):
    for i in range(n): hline(a, x + i, b - i, 2, col[1 if i % 2 else 2])


def tower(a, x, b, w, h, m, cap, seed, rp=None):
    wall(a, x, b - h + 1, w, h, m, seed)
    windows(a, x, b - h + 1, w, h, (1, 2, 3, 4) if w < 6 else (2, 2, 3, 4), .6, seed, kind='arch')
    if cap == 'dome': dome(a, x + w / 2, b - h, w / 2 + .3, w / 2.4, rp, seed)
    elif cap == 'cone': roof_cone(a, x - 1, b - h - w - 1, w + 2, w + 2, rp)
    elif cap == 'crenel': roof_crenel(a, x - 1, b - h - 2, w + 2, 3, rp)
    elif cap == 'flat': roof_flat(a, x, b - h - 1, w, 2, rp, clutter=False)


# =================================================================== RIVERLAND
RIV_WALLS = ['mudw', 'adobe', 'pinkw', 'whitew', 'mud']
RIV_ACC = [R['teal'], R['K'], K2['blue'], R['ochre'], R['green']]


def riverland(a, x, b, tier, seed, arch):
    rng = random.Random(seed); fx = []
    m = RIV_WALLS[rng.randint(0, len(RIV_WALLS) - 1)]; acc = RIV_ACC[rng.randint(0, 4)]
    if tier == 0:
        if arch == 0:  # reed hut with patched cloth
            w = rng.randint(6, 8); shadow_ell(a, x + w / 2 + 2, b + 1, w / 2 + 1, 2)
            wall(a, x, b - 2, w, 3, 'reedw', seed)
            for i in range(w + 2):
                put(a, x - 1 + i, b - 4 - (1 if 1 < i < w else 0), R['reed'][2 + (i % 2)]); put(a, x - 1 + i, b - 3, R['reed'][1])
            patch_roof(a, x, b - 5, w, 2, rng); rect(a, x + w // 2 - 1, b - 1, 2, 2, hx('#2a1d14'))
        elif arch == 1:  # cloth tarp lean-to on poles
            w = rng.randint(7, 9); shadow_rect(a, x + 2, b - 3, w, 4, .25)
            vline(a, x, b - 4, 5, C['wood'][1]); vline(a, x + w - 1, b - 2, 3, C['wood'][1])
            for i in range(w): put(a, x + i, b - 4 + i * 2 // w, acc[3] if i % 3 else acc[2]); put(a, x + i, b - 3 + i * 2 // w, acc[1])
            rect(a, x + 1, b - 1, w - 2, 2, hx('#b98e5e')); pot(a, x + 3, b)
        else:  # mud hovel half-ruined
            w = rng.randint(6, 7); bld(a, x, b, w, 3, 2, 'mud', 'flat', R['mud'], seed, win=None, dr=(2, 2))
            put(a, x + w - 1, b - 4, C['grass'][0]); put(a, x + w - 2, b - 4, C['grass'][0]); patch_roof(a, x, b - 4, w, 1, rng)
        if rng.random() < .5: goat(a, x + 9, b - 1)
        return fx
    if tier == 1:
        w = rng.randint(7, 10); wh = rng.randint(4, 5)
        top = block(a, x, b, w, wh, 3, m, 'flat', jr(R['mud'], rng), seed, (1, 2, rng.choice([3, 4, 5]), 3), .45, rng.choice('lcr'), dcol=acc[1])
        if arch == 0:
            rw = rng.randint(3, 5); rx = x + rng.choice([1, w - rw - 1])
            rect(a, rx, top - 3, rw, 3, W[m][1]); hline(a, rx, top - 3, rw, W[m][2]); put(a, rx + 1, top - 1, C['win'])
        elif arch == 1:
            stairs_side(a, x + w, b, wh, W[m]); laundry(a, x + 1, top + 1, w - 2, rng)
        else:
            w2 = rng.randint(5, 6); block(a, x + w, b, w2, wh - 1, 3, m, 'flat', R['mud'], seed + 1, (1, 1, 3, 3), .3, None, shadow=False)
            pot(a, x + w + 2, top + 1)
        if rng.random() < .5: pot(a, x - 2, b)
        return fx
    if tier == 2:
        if arch == 0:  # two-storey with arcade + rooftop pergola
            w = rng.randint(11, 13)
            top = block(a, x, b, w, 8, 4, m, 'flat', jr(R['mud'], rng), seed, (1, 2, 3, 3), .55, 'c', 2, 3, dcol=acc[1])
            for i in range(w - 2): put(a, x + 1 + i, b - 4, acc[3] if (i // 2) % 2 else W['plaster'][2])
            hline(a, x + 1, b - 3, w - 2, acc[1]); pergola(a, x + 2, top, w - 4, 3)
        elif arch == 1:  # house with wind catcher and front wall yard
            w = rng.randint(10, 12)
            top = block(a, x, b - 3, w, 6, 4, m, 'flat', jr(R['mud'], rng), seed, (1, 2, 3, 3), .5, 'r', dcol=acc[1])
            windcatcher(a, x + 2, top + 1, 6, m)
            rect(a, x - 1, b - 1, w + 2, 2, W[m][1]); hline(a, x - 1, b - 1, w + 2, W[m][2]); rect(a, x + w // 2 - 1, b - 1, 2, 2, acc[2])
            if rng.random() < .7: palm(a, x + w - 2, b - 9, seed)
        else:  # L-shaped with courtyard tree
            w = rng.randint(9, 11)
            top = block(a, x, b, w, 6, 4, m, 'flat', jr(R['mud'], rng), seed, (1, 2, 3, 3), .5, 'l', dcol=acc[1])
            block(a, x + w, b - 4, 6, 6, 3, m, 'flat', R['mud'], seed + 1, (1, 2, 3, 3), .5, None, shadow=False)
            garden(a, x + w, b - 3, 6, 4, rng); tree(a, x + w + 2, b - 6, 2, seed)
        return fx
    if tier == 3:
        if arch == 0:  # courtyard villa with dome
            w = rng.randint(16, 19)
            top = block(a, x, b, w, 6, 9, m, 'flat', jr(R['mud'], rng), seed, (2, 3, 4, 4), .6, 'c', 3, 3, 'arch', dcol=acc[1])
            garden(a, x + 4, top + 2, w - 8, 5, rng); rect(a, x + w // 2 - 1, top + 3, 3, 2, C['water'][3])
            palm(a, x + 5, top - 1, seed + 1); dome(a, x + w - 3, top - 1, 3, 2.6, acc, seed)
        elif arch == 1:  # garden villa behind a wall with gate & pool
            w = rng.randint(17, 20)
            rect(a, x - 1, b - 2, w + 2, 3, W[m][1]); hline(a, x - 1, b - 2, w + 2, W[m][2])
            garden(a, x, b - 9, w, 7, rng, False); pool(a, x + w - 7, b - 7, 5, 3)
            block(a, x + 1, b - 9, 10, 6, 5, m, 'flat', R['mud'], seed, (2, 2, 4, 3), .6, 'c', 2, 3, 'arch', shadow=False, dcol=acc[1])
            palm(a, x + 14, b - 15, seed); rect(a, x + 6, b - 2, 3, 3, acc[2]); put(a, x + 6, b - 2, acc[4])
        else:  # tower villa with terraces
            w = rng.randint(14, 16)
            top = block(a, x, b, w, 6, 4, m, 'flat', R['mud'], seed, (2, 2, 4, 3), .6, 'l', 3, 3, 'arch', dcol=acc[1])
            tower(a, x + w - 6, b - 4, 6, 12, m, 'dome', seed, acc)
            pergola(a, x + 1, top, 7, 3); hline(a, x, b - 6, w, acc[2])
        return fx
    # palaces
    if arch == 0:  # great dome + twin towers
        w = rng.randint(26, 30)
        top = block(a, x, b, w, 8, 6, 'whitew', 'flat', R['mud'], seed, (2, 3, 4, 4), .6, 'c', 4, 5, 'arch', dcol=acc[1])
        dome(a, x + w // 2, top - 2, 6, 5.4, acc, seed); put(a, x + w // 2, top - 8, C['gold'])
        for tx in (x - 1, x + w - 4): tower(a, tx, b, 5, 16, 'whitew', 'dome', seed + tx, acc)
        palm(a, x + 4, b + 1, seed); palm(a, x + w - 5, b + 1, seed + 5)
    elif arch == 1:  # courtyard palace with gate arch & four corner domes
        w = rng.randint(28, 32)
        rect(a, x, b - 3, w, 4, W['whitew'][1]); hline(a, x, b - 3, w, W['whitew'][2])
        garden(a, x + 2, b - 14, w - 4, 11, rng); rect(a, x + w // 2 - 3, b - 10, 6, 4, C['water'][3]); hline(a, x + w // 2 - 3, b - 10, 6, C['water'][4])
        block(a, x + 4, b - 14, w - 8, 6, 4, 'whitew', 'flat', R['mud'], seed, (2, 3, 4, 4), .6, 'c', 3, 4, 'arch', shadow=False, dcol=acc[1])
        for (tx, ty) in ((x, b), (x + w - 5, b)): tower(a, tx, ty, 5, 10, 'whitew', 'dome', seed + tx, acc)
        rect(a, x + w // 2 - 3, b - 6, 6, 7, W['whitew'][1]); rect(a, x + w // 2 - 2, b - 3, 4, 4, hx('#2a1d14')); dome(a, x + w // 2, b - 7, 3, 2, acc, seed)
    else:  # stepped terrace palace with hanging gardens
        w = rng.randint(26, 30)
        for k in range(3):
            ww = w - k * 8
            block(a, x + k * 4, b - k * 5, ww, 5, 3, m if k else 'whitew', 'flat', R['mud'], seed + k, (2, 2, 4, 3), .6, 'c' if k == 0 else None, 3, 3, 'arch', shadow=(k == 0), dcol=acc[1])
            for xx in range(x + k * 4, x + k * 4 + ww, 2): put(a, xx, b - k * 5 - 7, R['leaf'][3 if xx % 4 else 2])
        dome(a, x + w // 2, b - 18, 4, 3.6, acc, seed); put(a, x + w // 2, b - 22, C['gold'])
    banner(a, x + 7, b - 7, 3, acc); banner(a, x + w - 9, b - 7, 3, acc)
    return fx


# =================================================================== NORTHERN
NOR_PAINT = ['planks', 'redp', 'ochrep', 'greyp', 'whitep']


def northern(a, x, b, tier, seed, arch):
    rng = random.Random(seed); fx = []
    paint = NOR_PAINT[rng.randint(0, 4)]
    rroof = jr(rng.choice([R['shingle'], R['turf'], R['slate'], R['K']]), rng)
    if tier == 0:
        if arch == 0:  # turf mound hut
            w = rng.randint(7, 9); shadow_ell(a, x + w / 2 + 2, b + 1, w / 2 + 1, 2)
            dome(a, x + w / 2, b - 2, w / 2 + .5, 3.6, R['turf'], seed, top=b + 1)
            rect(a, x + w // 2 - 1, b - 2, 2, 3, hx('#1e1610')); hline(a, x + w // 2 - 2, b - 3, 4, C['wood'][1])
        elif arch == 1:  # plank lean-to against a rock
            rock(a, x + 2, b - 2, 3, seed)
            for i in range(6): vline(a, x + 3 + i, b - 4 + i // 2, 5 - i // 2, C['wood'][1 + (i % 2)])
            patch_roof(a, x + 3, b - 4, 6, 2, rng)
        else:  # tiny hide tent with snow-ish sheet
            w = 7
            for i in range(6): hline(a, x + 3 - i // 2, b - 5 + i, 1 + i, R['hide'][2 + (i % 2)])
            rect(a, x + 2, b - 1, 2, 2, hx('#1e1610'))
        woodpile(a, x + 10, b); fx.append(('smoke', x + 4, b - 6))
        return fx
    if tier == 1:
        w = rng.randint(8, 11); wh = rng.randint(3, 4)
        shadow_rect(a, x + 3, b - wh - 6, w + 1, wh + 6)
        wall(a, x, b - wh + 1, w, wh, 'logs', seed)
        for yy in range(b - wh + 1, b + 1, 2): hline(a, x, yy, w, W['logs'][0])
        dx = x + rng.choice([1, (w - 2) // 2, w - 3]); rect(a, dx, b - 2, 2, 3, C['door'])
        wx = x + (w - 3 if dx < x + w // 2 else 1); put(a, wx, b - 2, C['lit2']); put(a, wx + 1, b - 2, C['lit2'])
        roof_gable(a, x, b - wh - 6, w, 7, rroof if rng.random() < .6 else R['turf'])
        if arch == 1: block(a, x + w + 1, b, 5, 3, 4, 'planks', 'gable', R['shingle'], seed + 1, None, 0, None, shadow=False)
        elif arch == 2:
            hline(a, x - 1, b + 1, w + 2, C['wood'][2]); vline(a, x - 1, b - wh, wh + 1, C['wood'][1]); vline(a, x + w, b - wh, wh + 1, C['wood'][1])
        fx.append(chimney(a, x + w - 3, b - wh - 8, 3, 'stone')); woodpile(a, x - 6, b)
        return fx
    if tier == 2:
        if arch == 0:  # painted two-storey with balcony
            w = rng.randint(11, 13); wh = 8
            shadow_rect(a, x + 3, b - wh - 8, w + 1, wh + 8)
            wall(a, x, b - wh + 1, w, wh, paint, seed)
            for xx in range(x, x + w, 2): vline(a, xx, b - wh + 1, wh, W[paint][0])
            hline(a, x, b, w, W['stone'][1]); hline(a, x, b - 4, w, C['wood'][2]); hline(a, x, b - 3, w, C['wood'][0])
            windows(a, x, b - wh + 1, w, wh - 4, (2, 2, 4, 3), .6, seed); rect(a, x + w // 2 - 1, b - 2, 2, 3, C['door'])
            roof_gable(a, x, b - wh - 8, w, 9, rroof)
        elif arch == 1:  # long farmhouse + barn
            w = rng.randint(12, 14); wh = 5
            shadow_rect(a, x + 3, b - wh - 7, w + 9, wh + 7)
            wall(a, x, b - wh + 1, w, wh, paint, seed)
            for xx in range(x, x + w, 2): vline(a, xx, b - wh + 1, wh, W[paint][0])
            windows(a, x, b - wh + 1, w, wh, (2, 2, 4, 3), .6, seed, (x + 4, 4, b - 4)); rect(a, x + 5, b - 2, 2, 3, C['door'])
            roof_gable(a, x, b - wh - 7, w, 8, rroof)
            wall(a, x + w + 1, b - 5, 8, 6, 'redp', seed + 3); roof_gable(a, x + w + 1, b - 12, 8, 7, R['shingle'])
            rect(a, x + w + 3, b - 3, 4, 4, W['redp'][0]); put(a, x + w + 3, b - 3, hx('#e8e2d0')); put(a, x + w + 6, b, hx('#e8e2d0'))
        else:  # cottage with porch and fenced garden
            w = rng.randint(10, 12); wh = 5
            top = block(a, x, b, w, wh, 8, paint, 'gable', rroof, seed, (2, 2, 4, 3), .6, 'c', shut=True)
            hline(a, x - 1, b + 1, w + 2, C['wood'][2]); garden(a, x + w + 1, b - 4, 5, 5, rng); fence(a, x + w + 1, b + 1, 6)
        fx.append(chimney(a, x + 2, b - 16, 3, 'stone'))
        return fx
    if tier == 3:
        if arch == 0:  # carved longhouse w/ annex
            w = rng.randint(17, 20); wh = 6
            shadow_rect(a, x + 3, b - wh - 9, w + 7, wh + 9)
            wall(a, x, b - wh + 1, w, wh, 'planks', seed)
            for xx in range(x, x + w, 2): vline(a, xx, b - wh + 1, wh, W['planks'][0])
            hline(a, x, b, w, W['stone'][1]); hline(a, x, b - wh + 1, w, R['K'][2])
            windows(a, x, b - wh + 1, w, wh, (2, 2, 4, 3), .7, seed); door(a, x + w // 2 - 1, b - 2, 3, 3)
            roof_gable(a, x, b - wh - 9, w, 10, rroof)
            put(a, x - 2, b - wh - 10, C['wood'][2]); put(a, x - 3, b - wh - 11, C['wood'][2]); put(a, x + w + 1, b - wh - 10, C['wood'][2]); put(a, x + w + 2, b - wh - 11, C['wood'][2])
            block(a, x + w + 1, b, 6, 4, 6, 'logs', 'gable', R['turf'], seed + 1, None, 0, None, shadow=False)
        elif arch == 1:  # painted manor 2 storeys + side tower
            w = rng.randint(15, 17)
            top = block(a, x, b, w, 9, 9, paint, 'gable', rroof, seed, (2, 2, 4, 4), .7, 'c', 3, 3, shut=True)
            tower(a, x + w - 1, b, 5, 14, paint, 'cone', seed, rroof)
            fence(a, x - 2, b + 2, w + 8)
        else:  # farmstead square around yard
            w = rng.randint(18, 20)
            garden(a, x + 2, b - 9, w - 4, 7, rng, False)
            block(a, x, b - 9, w, 4, 6, paint, 'gable', rroof, seed, (2, 2, 4, 3), .6, 'c', shadow=True)
            block(a, x, b, 6, 4, 5, 'logs', 'gable', R['turf'], seed + 1, None, 0, 'c', shadow=False)
            block(a, x + w - 6, b, 6, 4, 5, 'redp', 'gable', R['shingle'], seed + 2, None, 0, 'c', shadow=False)
        fx.append(chimney(a, x + 3, b - 18, 3, 'stone'))
        return fx
    if arch == 0:  # great hall + stone towers
        w = rng.randint(26, 30); wh = 7
        shadow_rect(a, x + 4, b - wh - 12, w + 2, wh + 12, .34)
        wall(a, x, b - wh + 1, w, wh, 'planks', seed)
        for xx in range(x, x + w, 2): vline(a, xx, b - wh + 1, wh, W['planks'][0])
        hline(a, x, b, w, W['stone'][1]); hline(a, x, b - wh + 1, w, R['K'][2])
        windows(a, x, b - wh + 1, w, wh, (2, 3, 4, 4), .8, seed); door(a, x + w // 2 - 2, b - 3, 4, 4)
        roof_gable(a, x, b - wh - 12, w, 13, R['shingle'])
        for tx in (x - 3, x + w - 4): tower(a, tx, b, 7, 10, 'stone', 'cone', seed + tx, R['shingle'])
    elif arch == 1:  # stacked-roof timber palace (tiered roofs)
        w = rng.randint(22, 26)
        for k in range(3):
            ww = w - k * 7
            block(a, x + k * 3 + (k > 0) * k // 2, b - k * 7, ww, 4, 5, paint if k else 'planks', 'gable', rroof, seed + k, (2, 2, 4, 3), .7, 'c' if k == 0 else None, 4, 3, shadow=(k == 0))
        put(a, x + w // 2, b - 26, C['gold']); put(a, x + w // 2, b - 27, C['gold'])
    else:  # palisaded royal compound
        w = rng.randint(28, 32)
        for i in range(w):
            vline(a, x + i, b - 5, 6, C['wood'][2 if i % 2 else 1]); put(a, x + i, b - 6, C['wood'][2] if i % 2 == 0 else a[b - 7, x + i])
        rect(a, x + w // 2 - 2, b - 4, 4, 5, hx('#1e1610'))
        block(a, x + 4, b - 7, 12, 5, 9, 'planks', 'gable', R['shingle'], seed, (2, 2, 4, 3), .7, None, shadow=False)
        block(a, x + 18, b - 7, 9, 4, 7, paint, 'gable', rroof, seed + 1, (2, 2, 3, 3), .7, None, shadow=False)
        tower(a, x - 2, b, 5, 10, 'logs', 'cone', seed, R['shingle']); tower(a, x + w - 3, b, 5, 10, 'logs', 'cone', seed + 9, R['shingle'])
    flag(a, x + w // 2, b - 22, h=7)
    fx.append(('smoke', x + 8, b - 20))
    return fx


# =================================================================== HIGHLAND
def highland(a, x, b, tier, seed, arch):
    rng = random.Random(seed); fx = []
    rroof = jr(rng.choice([R['slate'], R['slate'], R['stone'], R['straw']]), rng)
    if tier == 0:
        if arch == 0:
            w = rng.randint(6, 8); shadow_rect(a, x + 2, b - 4, w + 1, 5)
            wall(a, x, b - 2, w, 3, 'stone', seed)
            for i in range(w + 2): put(a, x - 1 + i, b - 4, R['tin'][2 + (i % 2)]); put(a, x - 1 + i, b - 3, R['tin'][1])
            patch_roof(a, x, b - 5, w, 2, rng); rect(a, x + 1, b - 1, 2, 2, hx('#1e1610'))
        elif arch == 1:  # dug-in hut in a slope
            dome(a, x + 5, b - 1, 6, 4, R['stone'], seed, top=b + 1)
            rect(a, x + 3, b - 2, 3, 3, hx('#1e1610')); hline(a, x + 2, b - 3, 5, C['wood'][1])
        else:  # dry-stone shepherd hut, straw roof
            w = 7; wall(a, x, b - 2, w, 3, 'stone', seed); roof_thatch(a, x, b - 7, w, 5, R['straw'], seed); rect(a, x + 3, b - 1, 2, 2, hx('#1e1610'))
        rock(a, x + 10, b, 1.6, seed)
        return fx
    if tier == 1:
        w = rng.randint(8, 10); wh = rng.randint(4, 5)
        roof = ['gable', 'gable', 'thatch'][arch]
        top = block(a, x, b, w, wh, 5 if roof == 'gable' else 6, 'stone', roof, rroof if roof == 'gable' else R['straw'], seed, (1, 2, rng.choice([4, 5]), 3), .45, rng.choice('lcr'))
        if arch != 2: fx.append(chimney(a, x + (1 if rng.random() < .5 else w - 3), top - 2, 3, 'stone'))
        if arch == 1:
            for i in range(4): hline(a, x + w + 1, b - i, 4 - i, R['stone'][2 + (i % 2)])
        return fx
    if tier == 2:
        if arch == 0:  # townhouse with shop front
            w = rng.randint(11, 13)
            top = block(a, x, b, w, 8, 6, 'stone', 'gable', rroof, seed, (2, 2, 4, 3), .6, 'l', 2, 3, 'arch')
            for i in range(w - 4): put(a, x + 4 + i, b - 3, R['K'][3] if (i // 2) % 2 else W['plaster'][2])
            rect(a, x + 5, b - 2, w - 6, 2, C['lit2'])
            fx.append(chimney(a, x + w - 3, top - 2, 3, 'stone'))
        elif arch == 1:  # pair of row houses
            for k in range(2):
                top = block(a, x + k * 7, b, 7, 7, 6, 'stone', 'gable', jr(rroof, rng), seed + k, (2, 2, 3, 3), .6, 'c', shadow=(k == 0))
                fx.append(chimney(a, x + k * 7 + 4, top - 2, 3, 'stone'))
        else:  # house with walled garden
            w = rng.randint(10, 12)
            top = block(a, x, b, w, 6, 6, 'stone', 'hip', rroof, seed, (2, 2, 4, 3), .6, 'c', 2, 3, 'arch')
            garden(a, x + w + 1, b - 5, 6, 5, rng); rect(a, x + w + 1, b, 7, 1, W['stone'][1]); vline(a, x + w + 7, b - 5, 6, W['stone'][1])
            fx.append(chimney(a, x + 2, top - 2, 3, 'stone'))
        return fx
    if tier == 3:
        if arch == 0:  # tower house
            w = rng.randint(14, 16)
            top = block(a, x, b, w, 7, 6, 'stone', 'hip', R['slate'], seed, (2, 3, 4, 4), .65, 'c', 3, 4, 'arch')
            tower(a, x + w - 3, b, 6, 16, 'stone', rng.choice(['cone', 'crenel']), seed + 1, R['slate'])
            iron_fence(a, x - 2, b + 3, w + 8)
        elif arch == 1:  # manor with walled formal garden
            w = rng.randint(16, 18)
            rect(a, x - 2, b - 1, w + 4, 2, W['stone'][1]); hline(a, x - 2, b - 1, w + 4, W['stone'][2])
            garden(a, x, b - 6, w, 5, rng); rect(a, x + w // 2 - 1, b - 5, 3, 3, C['water'][3])
            block(a, x + 1, b - 6, w - 2, 7, 6, 'stone', 'hip', R['slate'], seed, (2, 3, 4, 4), .65, 'c', 3, 3, 'arch', shadow=False)
            for bx in (x + 1, x + w - 3): bush(a, bx, b - 3, seed + bx)
        else:  # terraced hillside villa
            w = rng.randint(16, 18)
            for k in range(2):
                block(a, x + k * 5, b - k * 6, w - k * 6, 5, 4 if k else 3, 'stone', 'flat' if k == 0 else 'gable', R['stone'] if k == 0 else R['slate'], seed + k, (2, 2, 4, 3), .6, 'c' if k == 0 else None, 3, 3, 'arch', shadow=(k == 0))
                garden(a, x + k * 5, b - k * 6 - 4, 4, 2, rng)
        fx.append(chimney(a, x + 4, b - 16, 3, 'stone'))
        return fx
    if arch == 0:  # twin-tower keep
        w = rng.randint(24, 28)
        block(a, x + 4, b, w - 8, 11, 4, 'fort', 'crenel', R['stone'], seed, (1, 3, 3, 4), .6, 'c', 4, 5, 'arch')
        for tx in (x, x + w - 6): tower(a, tx, b, 7, 16, 'fort', 'cone', seed + tx, R['slate'])
        wall(a, x + w // 2 - 3, b - 19, 6, 8, 'fort', seed + 7); roof_crenel(a, x + w // 2 - 4, b - 21, 8, 3)
    elif arch == 1:  # curtain wall + gatehouse + inner donjon
        w = rng.randint(28, 32)
        block(a, x + 8, b - 6, 14, 12, 4, 'fort', 'crenel', R['stone'], seed, (1, 3, 3, 4), .6, None, shadow=True)
        rect(a, x, b - 4, w, 5, W['fort'][1]); roof_crenel(a, x, b - 6, w, 3)
        tower(a, x + w // 2 - 4, b, 8, 9, 'fort', 'crenel', seed + 3, R['stone']); rect(a, x + w // 2 - 2, b - 4, 4, 5, hx('#14110e'))
        for tx in (x - 2, x + w - 4): tower(a, tx, b, 6, 10, 'fort', 'cone', seed + tx, R['slate'])
    else:  # single great donjon on terraces
        w = rng.randint(22, 26)
        for k in range(2):
            rect(a, x + k * 3, b - k * 3, w - k * 6, 3, W['fort'][2 - k]); hline(a, x + k * 3, b - k * 3, w - k * 6, R['stone'][4])
        tower(a, x + w // 2 - 6, b - 6, 12, 18, 'fort', 'crenel', seed, R['stone'])
        for tx in (x + w // 2 - 7, x + w // 2 + 4): tower(a, tx, b - 22, 4, 5, 'fort', 'cone', seed + tx, R['slate'])
    flag(a, x + w // 2, b - 24, h=7)
    banner(a, x + 6, b - 8); banner(a, x + w - 8, b - 8)
    return fx


GEN = {'riverland': riverland, 'northern': northern, 'highland': highland}
NARCH = {0: 3, 1: 3, 2: 3, 3: 3, 4: 3}


def house(a, x, b, culture, tier, seed, arch=None):
    if arch is None: arch = random.Random(seed * 7 + 1).randint(0, NARCH[tier] - 1)
    return GEN[culture](a, x, b, tier, seed, arch % NARCH[tier]) or []
