"""Phase 3 world structures (world grid, upscaled x2 by the exporter).  3/4 view, light top-left, footprint base row = b.
Walls & gates per era, keeps, bridges, docks, farms (crop stages), pens, wells, markets, statues, fountains, lamps,
12 wonders, fictional creed sanctums (crest symbols only), roads/rails autotiles, ships & vehicles in 8 directions."""
import math, random
import numpy as np
from lib import *
from buildings import wall, palisade, roof_crenel, roof_gable, roof_cone, roof_flat, flag, banner, door, windows, columns, pediment, fence, stall, crates, bld
from culturegen import SYMBOLS
from animals import R5

def _x5(rp):
    rp = list(rp)
    return rp if len(rp) >= 5 else [lit(rp[0], -.12)] + rp + [lit(rp[-1], .15)] * (4 - len(rp))


WX = {k: _x5(v) for k, v in W.items()}
WOOD = _x5(C['wood'])
ERA_MAT = ['wood', 'mud', 'fort', 'brick', 'concrete', 'metal']
ERA_ROOF = [R['straw'], R['mud'], R['slate'], R['copper'], R['concrete'], R['metal']]


def _top(a, x, y, w, rp):
    hline(a, x, y, w, rp[3]); hline(a, x, y + 1, w, rp[2])


# ------------------------------------------------------------------ city walls
def wall_piece(a, x, b, era, piece):
    """x,b = left/base of a 16 px wide cell."""
    mat = ERA_MAT[era]
    h = [7, 8, 10, 10, 9, 10][era]
    if piece == 'v':        # run going away from the camera: narrow face + long top
        shadow_rect(a, x + 8, b - h - 10, 6, h + 10)
        if mat == 'wood':
            for yy in range(b - 12, b + 1, 2): palisade(a, x + 6, yy, 4, h - 2)
            return
        rect(a, x + 6, b - h - 10, 4, 11, WX[mat if mat != 'metal' else 'metal'][2]); vline(a, x + 6, b - h - 10, 11, WX[mat if mat != 'metal' else 'metal'][3])
        wall(a, x + 6, b - h + 1, 4, h, mat)
        return
    if piece in ('h', 'corner', 'gate_closed', 'gate_open'):
        shadow_rect(a, x + 2, b - h + 2, 16, h)
        if mat == 'wood':
            palisade(a, x, b, 16, h)
        else:
            wall(a, x, b - h + 1, 16, h, mat, era * 7)
            if era in (2, 3): roof_crenel(a, x, b - h - 1, 16, 2)
            elif era == 4: hline(a, x, b - h, 16, WX['concrete'][3]); hline(a, x, b - h + 1, 16, WX['concrete'][0])
            elif era == 5:
                hline(a, x, b - h, 16, hx('#5fe0e8')); hline(a, x, b - h + 1, 16, WX['metal'][3])
                for xx in range(x + 1, x + 16, 4): put(a, xx, b - h // 2, hx('#5fe0e8'))
            elif era == 1: hline(a, x, b - h, 16, WX['mud'][3])
        if piece == 'corner':
            tower(a, x + 2, b, era, small=True)
        if piece.startswith('gate'):
            gx = x + 4
            if piece == 'gate_closed':
                rect(a, gx, b - 5, 8, 6, WOOD[1])
                for xx in range(gx, gx + 8, 2): vline(a, xx, b - 5, 6, WOOD[0])
                if era >= 3: rect(a, gx, b - 5, 8, 6, hx('#4a4e56')); [vline(a, xx, b - 5, 6, hx('#2a2c30')) for xx in range(gx, gx + 8, 2)]
            else:
                rect(a, gx, b - 5, 8, 6, hx('#1e1814')); put(a, gx, b - 5, WOOD[1]); vline(a, gx - 1, b - 5, 6, WOOD[1]); vline(a, gx + 8, b - 5, 6, WOOD[1])
            hline(a, gx - 1, b - 6, 10, lit(W.get(mat, WX['stone'])[0], -.1) if mat != 'wood' else WOOD[0])
            banner(a, gx - 3, b - h + 1, 3); banner(a, gx + 9, b - h + 1, 3)
        return
    if piece == 'tower':
        tower(a, x, b, era)


def tower(a, x, b, era, small=False):
    mat = ERA_MAT[era]
    w = 8 if small else 12
    h = (12 if small else 18) + era
    shadow_rect(a, x + 3, b - h + 3, w, h)
    if mat == 'wood':
        for i in range(4): vline(a, x + 1 + i * (w - 2) // 3, b - h + 3, h - 2, WOOD[1 + i % 2])
        rect(a, x - 1, b - h + 1, w + 2, 3, WOOD[2]); hline(a, x - 1, b - h + 1, w + 2, WOOD[3] if len(WOOD) > 3 else WOOD[2])
        roof_gable(a, x - 1, b - h - 4, w + 2, 4, R['straw'])
        return
    wall(a, x, b - h + 1, w, h, mat, era)
    windows(a, x, b - h + 1, w, h, (1, 2, 3, 4), .4, era, None, 'arch' if era == 2 else 'sq')
    if era in (1, 2, 3): roof_crenel(a, x - 1, b - h - 1, w + 2, 2)
    if era == 2 and not small: roof_cone(a, x - 1, b - h - 7, w + 2, 6, R['slate']); flag(a, x + w // 2, b - h - 7)
    if era == 4: rect(a, x - 1, b - h - 2, w + 2, 3, WX['concrete'][2]); put(a, x + w // 2, b - h - 4, hx('#d5452d'))
    if era == 5:
        dome(a, x + w / 2, b - h, w / 2 + 1, 3, R5('#2a4a5a', '#3a6a7a', '#5a9aaa', '#8ad0e0', '#d8f8ff'), era)
        put(a, x + w // 2, b - h - 3, hx('#5fe0e8'))


def keep(a, x, b, era, big=False):
    mat = ERA_MAT[era] if era else 'mud'
    w = 30 if big else 22
    if mat == 'wood':
        palisade(a, x, b, w, 7); bld(a, x + 5, b - 3, 12, 6, 5, 'mud', 'thatch', R['straw'], 3, None, .3, (2, 3))
        flag(a, x + 3, b - 8); return
    tower(a, x, b, era); tower(a, x + w - 12, b, era)
    h = 14 + era
    wall(a, x + 10, b - h + 1, w - 20, h, mat, era)
    if era in (1, 2, 3): roof_crenel(a, x + 9, b - h - 1, w - 18, 2)
    door(a, x + w // 2 - 2, b - 4, 4, 5, None, arch=True)
    if big:
        tower(a, x + w // 2 - 6, b - 8, era)
    banner(a, x + 11, b - h + 3, 4); banner(a, x + w - 13, b - h + 3, 4)
    flag(a, x + w // 2, b - h - (12 if big else 2))


# ------------------------------------------------------------------ bridges & docks
BRIDGE = {'wood': (WOOD, 'wood'), 'stone': (WX['stone'], 'stone'), 'iron': (R['metal'], 'iron'), 'modern': (WX['concrete'], 'modern')}


def bridge(a, x, b, kind, piece):
    rp = BRIDGE[kind][0]
    if piece in ('h', 'h_end'):
        y = b - 5
        rect(a, x, y, 16, 4, rp[2]); hline(a, x, y, 16, rp[3] if len(rp) > 3 else rp[2]); hline(a, x, y + 3, 16, rp[0])
        if kind == 'wood':
            for xx in range(x, x + 16, 2): vline(a, xx, y, 4, rp[1])
        if kind == 'stone':
            for i in range(2):
                for t in range(8):
                    put(a, x + i * 8 + t, y + 4 + int(3 * math.sin(t / 7 * math.pi)), rp[1])
        if kind == 'iron':
            for xx in range(x, x + 16, 4): line_(a, xx, y - 4, xx + 4, y, rp[1]); line_(a, xx + 4, y - 4, xx, y, rp[1])
            hline(a, x, y - 4, 16, rp[2])
        if kind == 'modern': hline(a, x, y + 1, 16, hx('#e8e0a0') if False else rp[1]); [put(a, xx, y + 1, hx('#f6f2ea')) for xx in range(x + 1, x + 16, 4)]
        hline(a, x, y - 1, 16, rp[1])
        for xx in (x + 1, x + 9): vline(a, xx, y + 4, 4, rp[0])
        if piece == 'h_end': rect(a, x, y - 2, 2, 6, rp[1])
    else:   # vertical (going away)
        rect(a, x + 4, b - 16, 8, 17, rp[2]); vline(a, x + 4, b - 16, 17, rp[1]); vline(a, x + 11, b - 16, 17, rp[0])
        if kind == 'wood':
            for yy in range(b - 16, b + 1, 2): hline(a, x + 4, yy, 8, rp[1])
        if kind == 'modern':
            for yy in range(b - 15, b, 4): put(a, x + 8, yy, hx('#f6f2ea'))


def line_(a, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0)) + 1
    for i in range(n): put(a, int(round(x0 + (x1 - x0) * i / max(n - 1, 1))), int(round(y0 + (y1 - y0) * i / max(n - 1, 1))), c)


def dock(a, x, b, era):
    rp = WOOD if era < 4 else WX['concrete']
    rect(a, x, b - 4, 24, 4, rp[2]); hline(a, x, b - 4, 24, lit(rp[2], .15))
    for xx in range(x, x + 24, 2 if era < 4 else 6): vline(a, xx, b - 4, 4, rp[1])
    for xx in (x + 1, x + 11, x + 22): vline(a, xx, b, 3, rp[0])
    if era >= 1: crates(a, x + 2, b - 6, 2)
    if era >= 3: vline(a, x + 18, b - 16, 12, hx('#c8a040')); line_(a, x + 18, b - 16, x + 26, b - 14, hx('#c8a040'))  # crane
    if era >= 4: rect(a, x + 6, b - 8, 6, 4, hx('#c84a2a')); rect(a, x + 12, b - 8, 6, 4, hx('#2a6ac8'))


# ------------------------------------------------------------------ farms
CROPS = {'wheat': ('#c9a94e', '#e0c46a'), 'rice': ('#7ab45a', '#a8d07a'), 'corn': ('#5e9a3a', '#e8c84a'), 'vegetables': ('#4e8a3a', '#d5452d'),
         'cotton': ('#6a9a4a', '#f6f2ea'), 'grapes': ('#4a7a34', '#6a2a7a'), 'potato': ('#5a8a3a', '#a8844e'), 'sunflower': ('#4e8a3a', '#f0c42a')}
STAGES = ['plowed', 'sprout', 'young', 'ripe', 'harvested', 'withered', 'burnt', 'flooded']


def farm_tile(a, crop, stage, seed=0):
    """32x16 world-px plot (fine 64x32)."""
    leaf, fruit = hx(CROPS[crop][0]), hx(CROPS[crop][1])
    soil = R5('#4a3424', '#5e4430', '#74563c', '#8a6a4c', '#a8865e')
    rect(a, 0, 0, 32, 16, soil[2])
    for y in range(0, 16, 3): hline(a, 0, y, 32, soil[1]); hline(a, 0, y + 1, 32, soil[3])
    r = random.Random(seed)
    if stage == 'flooded':
        blend_rect(a, 0, 0, 32, 16, hx('#3277b0'), .6)
        for _ in range(8): hline(a, r.randint(0, 28), r.randint(0, 15), 3, hx('#a8d4f0'))
        return
    if stage == 'burnt':
        blend_rect(a, 0, 0, 32, 16, hx('#1e1a16'), .7)
        for _ in range(10): put(a, r.randint(0, 31), r.randint(0, 15), hx('#f49a3c') if r.random() < .3 else hx('#4a4640'))
        return
    if stage == 'plowed': return
    for y in range(1, 16, 3):
        for x in range(1, 32, 2):
            if stage == 'sprout':
                if (x + y) % 4 == 1: put(a, x, y, leaf)
            elif stage == 'young':
                put(a, x, y, leaf); put(a, x, y - 1, lit(leaf, .15))
            elif stage == 'ripe':
                put(a, x, y, leaf); put(a, x, y - 1, lit(leaf, .1))
                if crop in ('wheat',): put(a, x, y - 1, fruit); put(a, x, y - 2, lit(fruit, .15))
                elif crop == 'sunflower':
                    if (x // 2) % 2 == 0: put(a, x, y - 2, fruit); put(a, x, y - 1, hx('#5a3a1a'))
                elif (x + y) % 3 == 0: put(a, x, y - 1, fruit)
            elif stage == 'harvested':
                if (x + y) % 3 == 0: put(a, x, y, hx('#c8b07a'))
            elif stage == 'withered':
                put(a, x, y, hx('#8a7a4a') if (x + y) % 2 else hx('#6a5a3a'))


def pen(a, x, b, size, animal_kind='wood'):
    w, h = [(20, 10), (28, 14), (36, 18)][size]
    rect(a, x, b - h, w, h, hx('#8a7a4a'))
    for _ in range(w): put(a, x + random.Random(_).randint(0, w - 1), b - random.Random(_ + 9).randint(1, h - 1), hx('#6a5a34'))
    fence(a, x, b - h, w); fence(a, x, b, w)
    for yy in range(b - h, b + 1): put(a, x, yy, WOOD[1]); put(a, x + w - 1, yy, WOOD[0])
    rect(a, x + w // 2 - 2, b, 4, 1, hx('#8a7a4a'))   # gate gap
    rect(a, x + 2, b - 3, 4, 2, WOOD[1]); hline(a, x + 2, b - 3, 4, hx('#6a8ab4'))  # trough


def barn(a, x, b, era):
    bld(a, x, b, 18, 9, 6, 'plaster' if era < 3 else 'brick', 'gable', R5('#6a2020', '#8a2a2a', '#a84040', '#c45a50', '#d87a6a') if era >= 2 else R['straw'], 4, None, .1, (6, 6))


# ------------------------------------------------------------------ civic props
def well(a, x, b, era):
    shadow_ell(a, x + 5, b + 1, 5, 1.5)
    rp = WX['stone'] if era < 4 else WX['concrete']
    rect(a, x + 1, b - 3, 8, 4, rp[1]); hline(a, x + 1, b - 3, 8, rp[2]); dome(a, x + 5, b - 3, 3, 1, R5('#1d3a5a', '#255c98', '#3277b0', '#5aa4e0', '#a8d4f0'), 1)
    if era < 3:
        vline(a, x + 1, b - 9, 6, WOOD[1]); vline(a, x + 8, b - 9, 6, WOOD[1]); roof_gable(a, x, b - 12, 10, 3, R['straw'] if era == 0 else R['slate'])
        vline(a, x + 5, b - 8, 4, hx('#c8b07a'))
    else:
        vline(a, x + 8, b - 7, 5, hx('#4a4e56')); hline(a, x + 6, b - 7, 3, hx('#4a4e56'))


def market(a, x, b, era, seed):
    r = random.Random(seed)
    cols = [R5('#6a2020', '#8a2a2a', '#c43a3a', '#e05a50', '#f08a7a'), R5('#1e3a6a', '#2a4e8a', '#3a6ac4', '#5a88dc', '#80a8f0'),
            R5('#6a5a1e', '#8a7a2a', '#c8a83a', '#e0c45a', '#f0dc8a'), R5('#1e5a3a', '#2a7a4e', '#3a9a64', '#5ab47e', '#80cc9c')]
    if era < 4:
        stall(a, x, b, r.choice(cols)[2], r.choice(cols)[3], 10)
        crates(a, x + 11, b - 2, 2)
    else:
        bld(a, x, b, 16, 7, 2, 'glass' if era == 5 else 'concrete', 'flat', R['concrete'], seed, (2, 1, 3, 2), .6, (4, 4))
        rect(a, x, b - 9, 16, 2, r.choice(cols)[2])


def statue(a, x, b, style, mat):
    rp = {'stone': WX['stone'], 'bronze': R5('#3a2a14', '#5a4020', '#7a5a2c', '#9a7a40', '#c8a060'), 'gold': R['gold'], 'marble': WX['marble']}[mat]
    shadow_ell(a, x + 6, b + 1, 6, 1.5)
    rect(a, x + 1, b - 4, 10, 5, WX['stone'][1]); hline(a, x + 1, b - 4, 10, WX['stone'][3] if len(WX['stone']) > 3 else WX['stone'][2])
    if style == 'figure':
        dome(a, x + 6, b - 13, 1.6, 1.6, rp, 1); rect(a, x + 5, b - 11, 3, 5, rp[2]); vline(a, x + 5, b - 11, 5, rp[3])
        line_(a, x + 7, b - 10, x + 9, b - 14, rp[2]); vline(a, x + 5, b - 6, 2, rp[1]); vline(a, x + 7, b - 6, 2, rp[1])
    elif style == 'beast':
        dome(a, x + 6, b - 7, 4, 2.4, rp, 2); dome(a, x + 9, b - 10, 2, 1.8, rp, 3); vline(a, x + 3, b - 6, 2, rp[1]); vline(a, x + 8, b - 6, 2, rp[1])
    elif style == 'obelisk':
        for i in range(12): hline(a, x + 4 + i // 6, b - 5 - i, 4 - (i // 6) * 2, rp[2] if i % 3 else rp[1])
        put(a, x + 5, b - 17, rp[4])
    elif style == 'orb':
        vline(a, x + 6, b - 9, 5, rp[1]); dome(a, x + 6, b - 11, 3, 3, rp, 4)
    elif style == 'rider':
        dome(a, x + 6, b - 7, 4, 2, rp, 2); dome(a, x + 10, b - 9, 1.6, 1.4, rp, 3); rect(a, x + 5, b - 12, 2, 4, rp[2]); dome(a, x + 6, b - 13, 1.2, 1.2, rp, 1)
        vline(a, x + 3, b - 6, 2, rp[1]); vline(a, x + 9, b - 6, 2, rp[1])
    elif style == 'abstract':
        for i in range(10): put(a, x + 6 + int(3 * math.sin(i / 2)), b - 5 - i, rp[2]); put(a, x + 7 + int(3 * math.sin(i / 2)), b - 5 - i, rp[1])


def fountain(a, x, b, f):
    shadow_ell(a, x + 9, b + 1, 9, 2)
    rect(a, x, b - 4, 18, 5, WX['marble'][1]); hline(a, x, b - 4, 18, WX['marble'][2])
    blend_mask(a, ellipse_mask(a.shape[:2], x + 9, b - 3, 8, 1.6), hx('#3277b0'), 1)
    vline(a, x + 9, b - 9, 6, WX['marble'][2])
    for i in range(5):
        t = (i + f) % 5
        put(a, x + 9 - t, b - 10 + t // 2 + (t * t) // 6, hx('#a8d4f0')); put(a, x + 9 + t, b - 10 + t // 2 + (t * t) // 6, hx('#a8d4f0'))
    put(a, x + 9, b - 11, hx('#e8f6ff'))


def lamp(a, x, b, era, lit_on):
    col = [WOOD[1], WOOD[1], hx('#2b2c30'), hx('#2b2c30'), hx('#6a707a'), hx('#cfd4da')][era]
    vline(a, x + 2, b - 9, 10, col)
    if era < 2:
        put(a, x + 2, b - 10, hx('#ffb84a') if lit_on else hx('#4a3424')); put(a, x + 2, b - 11, hx('#ffe27a') if lit_on else hx('#4a3424'))
    elif era < 4:
        rect(a, x + 1, b - 12, 3, 3, col); put(a, x + 2, b - 11, hx('#ffe27a') if lit_on else hx('#5a5440'))
    else:
        hline(a, x + 2, b - 10, 3, col); put(a, x + 4, b - 9, hx('#f6f2ea') if lit_on else hx('#8a8a90'))
        if era == 5: put(a, x + 4, b - 9, hx('#5fe0e8') if lit_on else hx('#3a5a60'))
    if lit_on: blend_mask(a, ellipse_mask(a.shape[:2], x + 3, b - 10, 4, 4), hx('#ffe27a') if era < 5 else hx('#5fe0e8'), .25)


# ------------------------------------------------------------------ wonders (12, original designs)
WONDERS = ['great_ziggurat', 'colossus_statue', 'great_wall', 'sea_lighthouse', 'terrace_gardens', 'star_observatory', 'grand_library',
           'arena', 'great_dam', 'sky_tower', 'space_elevator', 'crystal_spire']


def wonder(a, x, b, name):
    if name == 'great_ziggurat':
        for i in range(6):
            w = 48 - i * 7; h = 4
            wall(a, x + 24 - w // 2, b - (i + 1) * h + 1, w, h, 'mud', i)
        rect(a, x + 22, b - 26, 4, 3, R['gold'][2]); vline(a, x + 23, b - 23, 23, R['mud'][1])
    elif name == 'colossus_statue':
        rect(a, x + 14, b - 6, 20, 7, WX['stone'][1]); hline(a, x + 14, b - 6, 20, WX['stone'][2])
        rp = R5('#3a2a14', '#5a4020', '#7a5a2c', '#9a7a40', '#c8a060')
        for side in (-1, 1): rect(a, x + 23 + side * 3, b - 22, 3, 16, rp[2 if side < 0 else 1])
        rect(a, x + 19, b - 36, 11, 15, rp[2]); vline(a, x + 19, b - 36, 15, rp[3])
        dome(a, x + 24.5, b - 40, 3.4, 3.6, rp, 1)
        line_(a, x + 29, b - 34, x + 34, b - 46, rp[2]); dome(a, x + 34, b - 48, 2.2, 2.2, R['gold'], 2)
        line_(a, x + 19, b - 34, x + 16, b - 24, rp[1])
    elif name == 'great_wall':
        for i in range(4):
            wall(a, x + i * 12, b - 8 - i * 3 + 1, 12, 8, 'fort', i); roof_crenel(a, x + i * 12, b - 10 - i * 3, 12, 2)
        tower(a, x + 18, b - 4, 2, small=True)
    elif name == 'sea_lighthouse':
        rect(a, x + 12, b - 6, 24, 7, WX['stone'][1])
        for i in range(30):
            w = 12 - i // 5
            hline(a, x + 24 - w // 2, b - 6 - i, w, WX['white'][2] if (i // 5) % 2 == 0 else hx('#c43a3a'))
            put(a, x + 24 - w // 2, b - 6 - i, WX['white'][3] if len(WX['white']) > 3 else WX['white'][2])
        rect(a, x + 20, b - 40, 8, 4, hx('#2b2c30')); rect(a, x + 21, b - 39, 6, 2, hx('#ffe27a'))
        blend_mask(a, ellipse_mask(a.shape[:2], x + 24, b - 38, 12, 5), hx('#ffe27a'), .25)
    elif name == 'terrace_gardens':
        for i in range(4):
            w = 44 - i * 9
            wall(a, x + 24 - w // 2, b - (i + 1) * 6 + 1, w, 6, 'marble', i)
            for xx in range(x + 24 - w // 2, x + 24 + w // 2, 2): put(a, xx, b - (i + 1) * 6, R['leaf'][2 + (xx % 2)]); put(a, xx, b - (i + 1) * 6 + 1, R['leaf'][1])
            for xx in range(x + 26 - w // 2, x + 22 + w // 2, 5): vline(a, xx, b - (i + 1) * 6 + 2, 3, R['leaf'][2])
    elif name == 'star_observatory':
        bld(a, x + 8, b, 32, 10, 0, 'marble', None, None, 3, (2, 2, 4, 3), .6, (4, 4))
        dome(a, x + 24, b - 10, 14, 10, R5('#3a4a5a', '#5a6a7a', '#7a8a9a', '#a0aeba', '#cfd8e0'), 3, top=b - 9)
        rect(a, x + 23, b - 20, 3, 6, hx('#1e2a3a')); line_(a, x + 24, b - 18, x + 32, b - 26, hx('#4a4e56'))
    elif name == 'grand_library':
        bld(a, x + 4, b, 40, 14, 0, 'marble', None, None, 5, (2, 3, 3, 4), .5, (4, 5), winkind='arch')
        columns(a, x + 6, b - 12, 36, 12); pediment(a, x + 4, b - 22, 40)
    elif name == 'arena':
        dome(a, x + 24, b - 8, 24, 10, WX['stone'], 3, top=None)
        blend_mask(a, ellipse_mask(a.shape[:2], x + 24, b - 10, 16, 6), hx('#c8a46a'), 1)
        for t in range(0, 24):
            ang = math.pi + t / 23 * math.pi
            for k in range(3): put(a, int(x + 24 + math.cos(ang) * (24 - k)), int(b - 8 + math.sin(ang) * (10 - k * .5)), WX['stone'][3 - k % 2] if t % 3 else WX['stone'][0])
        for i in range(8): put(a, x + 4 + i * 6, b - 2, hx('#1e1814')); put(a, x + 4 + i * 6, b - 3, hx('#1e1814'))
    elif name == 'great_dam':
        for i in range(20):
            hline(a, x + 4 + i // 2, b - 20 + i, 40 - i, WX['concrete'][1 + (i % 3 == 0)])
        rect(a, x + 4, b - 22, 40, 2, WX['concrete'][3] if len(WX['concrete']) > 3 else WX['concrete'][2])
        for gx_ in (x + 14, x + 24, x + 34):
            for yy in range(b - 18, b + 1): put(a, gx_ + (yy % 2), yy, hx('#a8d4f0') if yy % 3 else hx('#ffffff'))
    elif name == 'sky_tower':
        for i in range(60):
            w = 10 - i // 8
            hline(a, x + 24 - w // 2, b - i, w, WX['glass'][2] if (i // 2) % 2 else WX['glass'][1])
            put(a, x + 24 - w // 2, b - i, WX['glass'][3] if len(WX['glass']) > 3 else WX['glass'][2])
        rect(a, x + 18, b - 40, 12, 4, WX['concrete'][2]); vline(a, x + 24, b - 72, 12, hx('#cfd4da')); put(a, x + 24, b - 73, hx('#d5452d'))
    elif name == 'space_elevator':
        rect(a, x + 10, b - 8, 28, 9, WX['metal'][1]); hline(a, x + 10, b - 8, 28, WX['metal'][2])
        for yy in range(b - 90, b - 8): put(a, x + 24, yy, hx('#cfd4da')); put(a, x + 25, yy, hx('#8a919a'))
        rect(a, x + 21, b - 50, 8, 4, hx('#5fe0e8')); blend_mask(a, ellipse_mask(a.shape[:2], x + 25, b - 48, 7, 4), hx('#5fe0e8'), .3)
        dome(a, x + 24, b - 8, 6, 4, R5('#2a4a5a', '#3a6a7a', '#5a9aaa', '#8ad0e0', '#d8f8ff'), 2)
    elif name == 'crystal_spire':
        for i in range(44):
            w = max(1, 14 - i // 3)
            for xx in range(w):
                c = hx('#c8a8ff') if xx < w // 3 else hx('#8a5ae8') if xx < 2 * w // 3 else hx('#5a2ab8')
                put(a, x + 24 - w // 2 + xx, b - i, c)
        for i in (12, 24, 34): put(a, x + 22, b - i, hx('#ffffff'))
        blend_mask(a, ellipse_mask(a.shape[:2], x + 24, b - 22, 14, 26), hx('#c87ae8'), .15)


# ------------------------------------------------------------------ fictional creed sanctums (no real-world religious forms)
def sanctum(a, x, b, symbol, tier, rp):
    """stone circle (tier 0), hall with crest (tier 1), grand hall with braziers (tier 2).  Emblem = a culture crest symbol."""
    sym = SYMBOLS[symbol]
    if tier == 0:
        shadow_ell(a, x + 16, b, 15, 3)
        for i in range(8):
            ang = i / 8 * math.tau
            sx, sy = int(x + 16 + math.cos(ang) * 13), int(b - 4 + math.sin(ang) * 4)
            rect(a, sx, sy - 6, 2, 6, WX['stone'][2]); put(a, sx, sy - 6, WX['stone'][3] if len(WX['stone']) > 3 else WX['stone'][2])
        rect(a, x + 13, b - 6, 7, 3, WX['stone'][1])
        _emblem(a, x + 14, b - 15, sym, rp[3])
        return
    w = 26 if tier == 1 else 38
    bld(a, x + 2, b, w, 10 + tier * 3, 6 + tier, 'marble' if tier == 2 else 'stone', 'gable', rp, symbol.__len__(), (2, 2, 4, 3), .4, (4, 5), winkind='arch')
    _emblem(a, x + 2 + w // 2 - 2, b - 10 - tier * 3 - 6 - tier, sym, R['gold'][3])
    for bx in (x, x + w + 2):
        rect(a, bx, b - 4, 3, 4, WX['stone'][1]); put(a, bx + 1, b - 5, hx('#f49a3c')); put(a, bx + 1, b - 6, hx('#ffe27a'))
    if tier == 2:
        banner(a, x + 6, b - 14, 5, rp); banner(a, x + w - 4, b - 14, 5, rp)


def _emblem(a, x, y, sym, col):
    for j, rowc in enumerate(sym):
        for i, c in enumerate(rowc):
            if c == '#': put(a, x + i, y + j, col)


# ------------------------------------------------------------------ roads & rails (16-mask autotile, 16 px)
ROADS = {'dirt': (R5('#5e4430', '#74563c', '#8a6a4c', '#a8865e', '#c4a47a'), None), 'cobble': (R5('#5a5650', '#74706a', '#8e8a82', '#aaa59c', '#c6c0b6'), 'cobble'),
         'paved': (R5('#6a6a6e', '#828286', '#9a9a9e', '#b4b4b8', '#cecece'), 'slab'), 'asphalt': (R5('#26262a', '#323236', '#3e3e44', '#4e4e54', '#626268'), 'line')}


def road_tile(a, kind, mask):
    """mask bits: 1=N 2=E 4=S 8=W.  16x16 world px; road width 8."""
    rp, pat = ROADS[kind]
    def fill(x0, y0, w, h):
        for yy in range(y0, y0 + h):
            for xx in range(x0, x0 + w):
                c = rp[2]
                if pat == 'cobble' and (xx // 2 + yy // 2) % 2: c = rp[1]
                if pat == 'cobble' and (xx % 2 == 0 and yy % 2 == 0): c = rp[3]
                if pat == 'slab' and (xx % 4 == 0 or yy % 4 == 0): c = rp[1]
                if pat is None and (xx * 7 + yy * 3) % 11 == 0: c = rp[1]
                put(a, xx, yy, c)
    fill(4, 4, 8, 8)
    if mask & 1: fill(4, 0, 8, 4)
    if mask & 4: fill(4, 12, 8, 4)
    if mask & 8: fill(0, 4, 4, 8)
    if mask & 2: fill(12, 4, 4, 8)
    if pat == 'line':
        if mask & 5 == 5 and not mask & 10: [put(a, 8, yy, hx('#e8d06a')) for yy in range(0, 16, 3)]
        if mask & 10 == 10 and not mask & 5: [put(a, xx, 8, hx('#e8d06a')) for xx in range(0, 16, 3)]
    # kerbs
    edge = rp[0] if kind != 'asphalt' else hx('#9a9a9e')
    if not mask & 1: hline(a, 4, 4, 8, edge)
    if not mask & 4: hline(a, 4, 11, 8, edge)
    if not mask & 8: vline(a, 4, 4, 8, edge)
    if not mask & 2: vline(a, 11, 4, 8, edge)


def rail_tile(a, mask):
    tie, steel = WOOD[1], hx('#8a919a')
    if mask & 5 or mask == 0:
        for yy in range(0 if mask & 1 else 4, 16 if mask & 4 else 12, 2): hline(a, 4, yy, 8, tie)
        if mask & 5: vline(a, 5, 0 if mask & 1 else 4, 12 + 4 * bool(mask & 1 and mask & 4), steel); vline(a, 10, 0 if mask & 1 else 4, 12 + 4 * bool(mask & 1 and mask & 4), steel)
    if mask & 10:
        for xx in range(0 if mask & 8 else 4, 16 if mask & 2 else 12, 2): vline(a, xx, 4, 8, tie)
        hline(a, 0 if mask & 8 else 4, 5, 12 + 4 * bool(mask & 8 and mask & 2), steel); hline(a, 0 if mask & 8 else 4, 10, 12 + 4 * bool(mask & 8 and mask & 2), steel)


# ------------------------------------------------------------------ ships (top-down 3/4, 8 directions) & vehicles
SHIPS = {  # era: (trade hull length, war hull length, sail kind)
    0: ('raft', 'canoe'), 1: ('trireme_trade', 'trireme'), 2: ('cog', 'galleon'), 3: ('steamer', 'ironclad'), 4: ('freighter', 'destroyer'), 5: ('hover_barge', 'stealth_frigate'),
}


def ship(a, cx, cy, era, war, d, f):
    """d = 0..7 (0 = east, counter-clockwise 45 deg). Hull is drawn as a rotated capsule; sails/turrets on top."""
    ang = -d / 8 * math.tau
    L = [8, 14, 18, 20, 24, 22][era] + (4 if war else 0)
    Wd = [3, 4, 5, 5, 5, 5][era] + (1 if war else 0)
    hull = [WOOD, WOOD, WOOD, R5('#2a2a2e', '#3a3a40', '#4a4a52', '#5e5e66', '#76767e'), R5('#3a4048', '#4e5660', '#66707a', '#808a94', '#9aa4ae'),
            R5('#1e2a34', '#2a3a48', '#3a4e60', '#5a7088', '#8aa4bc')][era]
    ca, sa = math.cos(ang), math.sin(ang)
    # wake
    for i in range(6):
        put(a, int(cx - ca * (L / 2 + i * 1.5)), int(cy - sa * (L / 2 + i * 1.5) * .6 + (i % 2) * (1 if f else -1)), hx('#d6eef2'))
    for t in range(-int(L / 2), int(L / 2) + 1):
        u = t / (L / 2)
        w = Wd * math.sqrt(max(0, 1 - max(u, 0) ** 2 * .9)) * (1 if u > -.85 else .7)
        for s in np.arange(-w, w + .1, .5):
            px, py = cx + ca * t - sa * s, cy + (sa * t + ca * s) * .6
            c = hull[3] if s < -w * .3 else hull[2] if s < w * .4 else hull[1]
            put(a, int(round(px)), int(round(py)), c)
    put(a, int(round(cx + ca * L / 2)), int(round(cy + sa * L / 2 * .6)), hull[4])
    team = R['K']
    if era <= 2:
        masts = 1 if era < 2 or not war else 2
        for m_ in range(masts):
            off = (m_ - (masts - 1) / 2) * 6
            mx, my = cx + ca * off, cy + sa * off * .6
            vline(a, int(mx), int(my - 9), 9, WOOD[0])
            sw = 4 if era else 2
            billow = 1 if f else 0
            for yy in range(int(my - 9), int(my - 3)):
                for k in range(-sw, sw + 1):
                    put(a, int(mx + k * abs(sa) + billow * (k == 0)), yy, team[3] if k < 0 else team[2] if k < sw else team[1])
        if era == 1:
            for i in range(-3, 4, 2): line_(a, int(cx + ca * i * 2 - sa * Wd), int(cy + sa * i * 2 * .6 + ca * Wd * .6), int(cx + ca * i * 2 - sa * (Wd + 3)), int(cy + (sa * i * 2 + ca * (Wd + 3)) * .6 + (1 if f else 0)), WOOD[2])
    else:
        # superstructure
        dome(a, cx - ca * 2, cy - sa * 2 * .6 - 2, 3, 2, [lit(c, .1) for c in hull], 3)
        if era == 3: vline(a, int(cx - ca * 1), int(cy - sa * .6 - 7), 5, hx('#2a2a2e')); blend_mask(a, ellipse_mask(a.shape[:2], cx - ca, cy - 9 - f, 2.5, 2), hx('#a8a8b0'), .7)
        if war:
            for off in (L / 3, -L / 3):
                tx, ty = cx + ca * off, cy + sa * off * .6
                dome(a, tx, ty - 1, 1.6, 1.2, hull, 1)
                line_(a, int(tx), int(ty - 1), int(tx + ca * 4), int(ty - 1 + sa * 4 * .6), hull[0])
        put(a, int(cx - ca * 3), int(cy - sa * 3 * .6 - 4), team[2]); put(a, int(cx - ca * 3) + 1, int(cy - sa * 3 * .6 - 4), team[3])
        if era == 5: blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, L / 2 + 2, Wd + 2), hx('#5fe0e8'), .15)


VEHICLES = ['ox_cart', 'war_wagon', 'steam_tractor', 'truck', 'tank', 'apc', 'hover_tank', 'mobile_artillery']


def vehicle(a, cx, cy, kind, d, f):
    ang = -d / 8 * math.tau
    ca, sa = math.cos(ang), math.sin(ang)
    team = R['K']
    def box(L, Wd, hgt, rp, off=0.0):
        for t in np.arange(-L / 2, L / 2 + .1, .5):
            for s in np.arange(-Wd / 2, Wd / 2 + .1, .5):
                px, py = cx + ca * (t + off) - sa * s, cy + (sa * (t + off) + ca * s) * .6 - hgt
                put(a, int(round(px)), int(round(py)), rp[3] if s < -Wd / 4 else rp[2] if s < Wd / 4 else rp[1])
    def wheels(L, Wd, col, n=2):
        for i in range(n):
            t = -L / 2 + 1 + i * (L - 2) / max(n - 1, 1)
            for s in (-Wd / 2 - .5, Wd / 2 + .5):
                px, py = cx + ca * t - sa * s, cy + (sa * t + ca * s) * .6
                put(a, int(round(px)), int(round(py)), col); put(a, int(round(px)), int(round(py)) + 1, lit(col, -.2) if f else col)
    def tracks(L, Wd):
        for s in (-Wd / 2 - .5, Wd / 2 + .5):
            for t in np.arange(-L / 2, L / 2 + .1, .5):
                px, py = cx + ca * t - sa * s, cy + (sa * t + ca * s) * .6
                put(a, int(round(px)), int(round(py)), hx('#2a2a2e') if int(t * 2 + f) % 2 else hx('#4a4a50'))
    def barrel(L, hgt, col):
        for t in range(int(L)): put(a, int(round(cx + ca * t)), int(round(cy + sa * t * .6 - hgt)), col)
    shadow_ell(a, cx + 1, cy + 1, 7, 3, .25)
    if kind == 'ox_cart':
        wheels(8, 5, WOOD[0]); box(8, 5, 2, WOOD)
        for i in range(3): put(a, int(cx + ca * (5 + i)), int(cy + sa * (5 + i) * .6 - 1), WOOD[0])
    elif kind == 'war_wagon':
        wheels(10, 6, WOOD[0], 3); box(10, 6, 2, WOOD); box(8, 5, 5, [team[0], team[1], team[2], team[3], team[4]])
    elif kind == 'steam_tractor':
        wheels(10, 6, hx('#2a2a2e')); box(10, 5, 2, R5('#2a2a2e', '#3a3a40', '#4a4a52', '#5e5e66', '#76767e')); vline(a, int(cx + ca * 3), int(cy + sa * 3 * .6 - 9), 6, hx('#2a2a2e'))
        blend_mask(a, ellipse_mask(a.shape[:2], cx + ca * 3, cy + sa * 2 - 11 - f, 2, 1.5), hx('#a8a8b0'), .7)
    elif kind == 'truck':
        wheels(12, 6, hx('#1e1e22'), 3); box(12, 6, 2, R5('#3a4048', '#4e5660', '#66707a', '#808a94', '#9aa4ae')); box(4, 6, 5, [team[0], team[1], team[2], team[3], team[4]], 4)
    elif kind == 'tank':
        tracks(14, 8); box(14, 8, 2, [team[0], team[1], team[2], team[3], team[4]]); box(6, 5, 5, [lit(c, .05) for c in team]); barrel(12, 5, team[0])
    elif kind == 'apc':
        wheels(13, 7, hx('#1e1e22'), 4); box(13, 7, 3, [team[0], team[1], team[2], team[3], team[4]]); barrel(6, 6, team[0])
    elif kind == 'hover_tank':
        blend_mask(a, ellipse_mask(a.shape[:2], cx, cy + 1, 8, 3), hx('#5fe0e8'), .35 + .1 * f)
        box(14, 8, 4, R5('#2a3a48', '#3a4e60', '#5a7088', '#8aa4bc', '#c8dcec')); box(6, 5, 7, [team[0], team[1], team[2], team[3], team[4]]); barrel(12, 7, hx('#5fe0e8'))
    elif kind == 'mobile_artillery':
        tracks(14, 8); box(14, 8, 2, [team[0], team[1], team[2], team[3], team[4]]); box(7, 6, 5, team)
        for t in range(14): put(a, int(round(cx + ca * t * .8)), int(round(cy + sa * t * .8 * .6 - 5 - t * .5)), team[0])
