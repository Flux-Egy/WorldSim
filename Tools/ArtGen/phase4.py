"""Phase 4: 32 kingdom colours (data + baked flags/banners/UI/markers per colour), icon library (16 & 32 px),
portraits auto-cut from the creature atlases, weather & disaster FX."""
import os, math, random, json, colorsys
import numpy as np
from PIL import Image
from lib import *
from xcore import Atlas
from animals import R5

OUT = None
DONE = None

# ------------------------------------------------------------------ 32 kingdom colours (hue/sat/val chosen to stay distinct)
KINGDOMS = [   # picked greedily for the largest minimum colour distance (CIE Lab dE >= 21 between any two)
    ('scarlet', 6, .85, .95), ('coral', 12, .55, .98), ('ember', 22, .85, .85), ('brown', 25, .6, .42), ('bronze', 30, .7, .62), ('tan', 34, .4, .78), ('amber', 36, .85, .95),
    ('gold', 48, .8, .85), ('lemon', 58, .65, .98), ('olive', 62, .6, .5), ('lime', 80, .7, .85), ('grass', 110, .65, .65), ('forest', 135, .65, .4), ('mint', 150, .4, .92),
    ('jade', 158, .7, .62), ('teal', 176, .75, .55), ('sky', 200, .45, .98), ('azure', 210, .75, .85), ('slate', 210, .25, .55), ('cobalt', 220, .85, .7), ('navy', 228, .75, .38),
    ('lavender', 255, .3, .92), ('violet', 268, .55, .78), ('orchid', 300, .4, .85), ('plum', 300, .5, .42), ('magenta', 315, .75, .85), ('rose', 335, .5, .95),
    ('maroon', 350, .75, .4), ('crimson', 355, .75, .75), ('ivory', 45, .1, .98), ('steel', 200, .18, .75), ('charcoal', 220, .1, .25)]


def kramp(h, s, v):
    out = []
    for ds, dv in [(.12, -.36), (.06, -.18), (0, 0), (-.12, .12), (-.3, .24)]:
        r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, max(0, min(1, s + ds)), max(.05, min(1, v + dv)))
        out.append((int(r * 255), int(g * 255), int(b * 255)))
    return out


def palettes():
    pal = []
    for name, h, s, v in KINGDOMS:
        team = kramp(h, s, v)
        acc = kramp(h + 180 if s > .2 else 45, .55, .75) if s > .2 else kramp(45, .6, .8)
        pal.append(dict(name=name, team=['#%02x%02x%02x' % c for c in team], accent=['#%02x%02x%02x' % c for c in acc],
                        ui_tint='#%02x%02x%02x' % team[3], text_on='#0b0e13' if v > .8 and s < .5 else '#f3e6c8'))
    return pal


# ------------------------------------------------------------------ baked per-colour assets
def flag_frame(a, rp, acc, f, shape='swallow', sym=None):
    """16x14 flag on a pole, cloth waves (4 frames)."""
    vline(a, 1, 0, 14, hx('#8a8a90')); put(a, 1, 0, hx('#ffd34a'))
    for x in range(10):
        wave = int(round(math.sin(x / 2.2 - f * math.pi / 2) * (x / 10) * 1.6))
        top, bot = 1 + wave, 8 + wave
        if shape == 'swallow' and x >= 8: bot -= 2 if x == 9 else 1
        if shape == 'pennant': top, bot = 1 + wave + x // 3, 8 + wave - x // 3
        for y in range(top, bot):
            c = rp[3] if y == top else rp[1] if y == bot - 1 else rp[2]
            if wave < 0 and (x % 3 == 0): c = lit(c, .08)
            put(a, 2 + x, y, c)
        if shape != 'pennant': put(a, 2 + x, 4 + wave, acc[3])
    if sym:
        for j, row in enumerate(sym):
            for i, c in enumerate(row):
                if c == '#' and j < 5: put(a, 4 + i, 1 + j + int(round(math.sin(i / 2.2 - f * math.pi / 2) * .4)), acc[4])


def banner_h(a, rp, acc):
    hline(a, 0, 0, 10, hx('#6b4c34'))
    for y in range(1, 16):
        for x in range(1, 9):
            if y >= 13 and abs(x - 4.5) < (y - 12): continue
            put(a, x, y, rp[2] if x > 2 else rp[3])
    for j in range(5):            # diamond emblem (no cross shapes)
        hline(a, 4 - min(j, 4 - j), 4 + j, 2 * min(j, 4 - j) + 1, acc[3])
    put(a, 4, 6, acc[4])


def capital_marker(a, rp, acc):
    for x in range(12):
        put(a, 2 + x, 9, hx('#c8a040'))
    for i, h in enumerate((4, 7, 4, 7, 4)):
        vline(a, 2 + i * 3, 9 - h, h, hx('#ffd34a')); put(a, 2 + i * 3, 9 - h, hx('#fff0a0'))
    rect(a, 3, 10, 10, 3, rp[2]); hline(a, 3, 10, 10, rp[3]); put(a, 8, 11, acc[4])


def army_marker(a, rp, acc):
    dome(a, 8, 9, 7, 6, rp, 1)
    for i in range(5): put(a, 5 + i, 4 + i, hx('#f3e6c8')); put(a, 11 - i, 4 + i, hx('#f3e6c8'))
    put(a, 8, 2, acc[4])


def badge(a, rp, acc):
    for j in range(20):
        for i in range(18):
            if (i - 8.5) ** 2 / 81 + (j - 9.5) ** 2 / 100 <= 1: put(a, i, j, rp[2] if i > 6 else rp[3])
    for t in np.linspace(0, math.tau, 60): put(a, int(8.5 + 8.6 * math.cos(t)), int(9.5 + 9.6 * math.sin(t)), acc[2])


def btn(a, rp, pressed):
    rect(a, 0, 0, 32, 14, hx('#0b0e13'))
    rect(a, 1, 1, 30, 12, rp[1] if pressed else rp[2]); hline(a, 1, 1, 30, rp[0] if pressed else rp[3]); hline(a, 1, 12, 30, rp[3] if pressed else rp[0])


def ring(a, rp):
    for t in np.linspace(0, math.tau, 60):
        put(a, int(10 + 9 * math.cos(t)), int(5 + 4 * math.sin(t)), rp[3]); put(a, int(10 + 9 * math.cos(t)), int(6 + 4 * math.sin(t)), rp[1])


def tent(a, rp, acc):
    for y in range(10):
        hline(a, 8 - y // 1 * 7 // 10, 2 + y, 2 * (y * 7 // 10) + 1, rp[2] if y % 3 else rp[1])
    vline(a, 8, 0, 3, hx('#6b4c34')); put(a, 9, 0, acc[3]); rect(a, 7, 9, 3, 3, hx('#1e1814'))


def border_px(a, rp):
    for x in range(16):
        put(a, x, 0, rp[3]); put(a, x, 1, rp[2] if x % 4 else rp[4])


# ------------------------------------------------------------------ hand-drawn icon library (16x16 base, x2 = 32)
ICON_DEF = {}


def icon(name):
    def deco(fn): ICON_DEF[name] = fn; return fn
    return deco


def _bg(a, col):
    rect(a, 0, 0, 16, 16, (0, 0, 0)); a[...] = 0


def _sym(a, rows, cols, x0=0, y0=0):
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c != '.': put(a, x0 + i, y0 + j, cols[c])


RES_ICONS = {   # 16x16 pixel maps (char -> colour)
    'food': (["................", "......##........", ".....#cc#.......", "....#cccc#......", "...#cccccc#.....", "...#ccccccc#....", "..#cccccccc#....", "..#ccccccccc#...",
              "..#ccccccccc#...", "...#ccccccc#....", "....#ccccc#.....", ".....#####......", "................", "................", "................", "................"],
             {'#': hx('#7a2a1e'), 'c': hx('#d8542e')}),
    'wood': (["................", "................", "..##########....", ".#wwwwwwwwww#...", ".#wwwwwwwwwwr#..", ".#wwwwwwwwwwr#..", "..##########....", "....##########..", "...#wwwwwwwwww#.", "...#wwwwwwwwwwr#",
              "...#wwwwwwwwwwr#", "....##########..", "................", "................", "................", "................"],
             {'#': hx('#4a3020'), 'w': hx('#8c6844'), 'r': hx('#d8b07a')}),
    'stone': (["................", "................", ".....######.....", "....#ssssss#....", "...#sSsssssss#..", "..#sSSssssssss#.", "..#sssssssssss#.", "..#sssssssssdd#.", "...#sssssssdd#..",
               "....##########..", "................", "................", "................", "................", "................", "................"],
              {'#': hx('#3a3a3e'), 's': hx('#8a8a8e'), 'S': hx('#c4c4c8'), 'd': hx('#5a5a5e')}),
}
SIMPLE_ICONS = {  # name: (shape kind, colour) - drawn procedurally
    'iron': ('ingot', '#9aa4ae'), 'gold': ('ingot', '#e8c040'), 'copper': ('ingot', '#c87a4a'), 'crystal': ('gem', '#5fe0e8'), 'gem': ('gem', '#c83a7a'),
    'coal': ('lump', '#2a2a2e'), 'oil': ('drop', '#1e1e24'), 'uranium': ('gem', '#9ae04a'), 'water': ('drop', '#3a8ad8'), 'mana': ('drop', '#9a6ae8'),
    'cloth': ('roll', '#c8a8e8'), 'leather': ('roll', '#8a5a3a'), 'tools': ('hammer', '#9aa4ae'), 'weapons': ('sword', '#cfd4da'), 'meat': ('lump', '#c84a3a'),
    'fish': ('fishi', '#7aa4c8'), 'bread': ('lump', '#d8a050'), 'wine': ('drop', '#7a1a3a'), 'herbs': ('leaf', '#5aa43a'), 'wool': ('lump', '#ece8e0'),
    'salt': ('gem', '#f6f6f6'), 'spice': ('lump', '#d8742a'), 'paper': ('roll', '#f2ecdc'), 'books': ('book', '#7a3a2a'), 'coins': ('coin', '#e8c040'),
    'population': ('person', '#c89a74'), 'army': ('sword', '#c83a3a'), 'happiness': ('face', '#f0c42a'), 'unrest': ('face_bad', '#d8542e'), 'faith': ('flame', '#ffb84a'),
    'knowledge': ('book', '#3a6ac4'), 'health': ('heart', '#d8342e'), 'disease': ('skullish', '#9ab07a'), 'hunger': ('bowl', '#a8844e'), 'trade': ('scale', '#e8c040'),
    'diplomacy': ('hands', '#c89a74'), 'war': ('swords', '#c83a3a'), 'peace': ('leaf', '#7ac04a'), 'alliance': ('link', '#e8c040'), 'rebellion': ('fist', '#d8542e'),
    'culture': ('mask', '#c87ae8'), 'clan': ('tree', '#6a9a4a'), 'trait': ('star4', '#ffd34a'), 'age': ('hourglass', '#c8a46a'), 'speed': ('wing', '#cfd4da'),
    'attack': ('sword', '#e06a55'), 'defense': ('shield', '#7aa4c8'), 'range': ('bow', '#a88a5a'), 'magic': ('star4', '#c87ae8'), 'fire': ('flame', '#f4602a'),
    'cold': ('flake', '#a8d8f0'), 'poison': ('drop', '#7ac04a'), 'radiation': ('trefoilish', '#9ae04a'), 'lightning': ('bolt', '#d8e4ff'), 'sleep': ('zz', '#cfd4da'),
    'hungry': ('bowl', '#d8a050'), 'angry': ('face_bad', '#e04a3a'), 'scared': ('face_bad', '#a8c8e8'), 'love': ('heart', '#e86a9a'), 'possessed': ('swirl', '#5fe0e8'),
    'burning': ('flame', '#f4602a'), 'frozen': ('flake', '#cfefff'), 'poisoned': ('drop', '#9ae04a'), 'irradiated': ('trefoilish', '#9ae04a'), 'stunned': ('star4', '#ffe27a'),
    'cursed': ('swirl', '#7a4a9a'), 'blessed': ('star4', '#fff08a'), 'bleeding': ('drop', '#c8282a'), 'drunk': ('bubble', '#d8a050'), 'pregnant': ('heart', '#f0a8c8'),
    'king': ('crown', '#ffd34a'), 'hero': ('star4', '#e8c040'), 'traitor': ('mask', '#5a5a5e'), 'sick': ('skullish', '#9ab07a'), 'old': ('hourglass', '#b8b4ac'),
    'build': ('hammer', '#c8a46a'), 'farm': ('leaf', '#c9a94e'), 'mine': ('pick', '#9aa4ae'), 'chop': ('axe', '#8c6844'), 'fishing': ('fishi', '#5a8ac8'),
    'hunt': ('bow', '#8c6844'), 'herd': ('horn', '#c8b07a'), 'research': ('book', '#5fe0e8'), 'ritual': ('flame', '#ffb84a'), 'trade_route': ('link', '#c8a46a'),
    'ship': ('boat', '#8c6844'), 'tank': ('tankic', '#6a7a4a'), 'plane': ('planeic', '#9aa4ae'), 'missile': ('missileic', '#cfd4da'), 'nuke': ('trefoilish', '#ffd34a'),
    'storm': ('cloud', '#5a6a7a'), 'rain': ('cloud', '#7aa4c8'), 'snow': ('flake', '#ffffff'), 'quake': ('crack', '#8a6a4a'), 'volcano': ('peak', '#d5452d'),
    'tsunami': ('wave', '#3a8ad8'), 'tornado': ('swirl', '#a8b4c0'), 'meteor': ('bolt', '#f49a3c'), 'plague': ('skullish', '#7a9a3a'), 'drought': ('sunic', '#e8a03a'),
}


def draw_simple_icon(a, kind, col):
    c = hx(col); d = lit(c, -.3); l = lit(c, .3); ink = hx('#0b0e13')
    if kind == 'ingot':
        for y in range(6, 12):
            hline(a, 3 + (11 - y) // 2, y, 10 - (11 - y), c)
        hline(a, 6, 6, 5, l); hline(a, 3, 11, 10, d)
    elif kind == 'gem':
        for y in range(3, 13):
            w = (y - 2) if y < 7 else (13 - y) * 1.3
            hline(a, int(8 - w), y, int(2 * w) + 1, c if y > 6 else l)
        put(a, 6, 5, (255, 255, 255))
    elif kind == 'lump':
        dome(a, 8, 9, 5, 4, [d, d, c, l, l], 1)
    elif kind == 'drop':
        for y in range(2, 14):
            w = max(0, (y - 2) * .55) if y < 9 else math.sqrt(max(0, 16 - (y - 9.5) ** 2 * 1.4))
            hline(a, int(8 - w), y, int(2 * w) + 1, c)
        put(a, 6, 9, l); put(a, 6, 10, l)
    elif kind == 'roll':
        rect(a, 3, 5, 10, 7, c); hline(a, 3, 5, 10, l); hline(a, 3, 11, 10, d); vline(a, 12, 5, 7, d); dome(a, 3, 8, 1.5, 3.5, [d, d, c, l, l], 1)
    elif kind in ('hammer', 'pick', 'axe'):
        for i in range(10): put(a, 4 + i, 13 - i, hx('#8c6844'))
        if kind == 'hammer': rect(a, 9, 2, 6, 4, c); hline(a, 9, 2, 6, l)
        elif kind == 'pick':
            for i in range(9): put(a, 6 + i, 4 + abs(i - 4) // 2 - 2 + (1 if i in (0, 8) else 0), c)
        else: rect(a, 10, 2, 4, 5, c); vline(a, 10, 2, 5, l)
    elif kind in ('sword', 'swords'):
        for i in range(10): put(a, 4 + i, 12 - i, c); put(a, 5 + i, 12 - i, l)
        hline(a, 3, 10, 5, hx('#c8a040')); put(a, 3, 13, hx('#6b4c34'))
        if kind == 'swords':
            for i in range(10): put(a, 12 - i, 12 - i, d)
    elif kind == 'fishi':
        dome(a, 8, 8, 5, 3, [d, d, c, l, l], 1); put(a, 2, 6, c); put(a, 2, 10, c); put(a, 3, 8, c); put(a, 11, 7, ink)
    elif kind == 'book':
        rect(a, 3, 3, 10, 10, c); vline(a, 3, 3, 10, d); hline(a, 4, 11, 9, (240, 236, 220)); hline(a, 5, 5, 6, l)
    elif kind == 'coin':
        dome(a, 8, 8, 5, 5, [d, d, c, l, l], 1); vline(a, 8, 5, 6, d)
    elif kind == 'person':
        dome(a, 8, 5, 2.5, 2.5, [d, d, c, l, l], 1); rect(a, 5, 8, 7, 6, hx('#3a6086')); hline(a, 5, 8, 7, hx('#5a7ea0'))
    elif kind in ('face', 'face_bad'):
        dome(a, 8, 8, 6, 6, [d, d, c, l, l], 1); put(a, 6, 6, ink); put(a, 10, 6, ink)
        if kind == 'face': hline(a, 6, 10, 5, ink); put(a, 5, 9, ink); put(a, 11, 9, ink)
        else: hline(a, 6, 10, 5, ink); put(a, 5, 11, ink); put(a, 11, 11, ink)
    elif kind == 'flame':
        for y in range(2, 14):
            w = (y - 2) * .45 if y < 10 else (14 - y) * 1.2
            hline(a, int(8 - w), y, int(2 * w) + 1, c)
        for y in range(7, 13): hline(a, 7, y, 3, hx('#ffe27a'))
    elif kind == 'heart':
        for y in range(4, 14):
            for x in range(2, 15):
                if ((x - 5.5) ** 2 + (y - 6) ** 2 < 8 or (x - 10.5) ** 2 + (y - 6) ** 2 < 8) or (y >= 6 and abs(x - 8) < (14 - y) * .85): put(a, x, y, c)
        put(a, 5, 5, l)
    elif kind == 'skullish':
        dome(a, 8, 7, 5, 4.5, [d, d, c, l, l], 1); rect(a, 6, 11, 5, 2, c); put(a, 6, 7, ink); put(a, 10, 7, ink); put(a, 8, 9, ink)
    elif kind == 'bowl':
        for y in range(8, 13): hline(a, 3 + (y - 8), y, 11 - 2 * (y - 8), c)
        hline(a, 3, 8, 11, l)
    elif kind == 'scale':
        for y in range(9, 14): hline(a, 8 - (y - 9), y, 2 * (y - 9) + 1, d)   # triangle base
        for i in range(13): put(a, 2 + i, 4 + i // 4, c)                    # tilted beam
        for (s, yy) in ((3, 8), (13, 11)):
            hline(a, s - 2, yy, 5, l); put(a, s - 2, yy - 1, l); put(a, s + 2, yy - 1, l)
    elif kind == 'hands':
        rect(a, 2, 7, 6, 3, c); rect(a, 8, 7, 6, 3, d); hline(a, 2, 7, 12, l)
    elif kind == 'link':
        for t in np.linspace(0, math.tau, 30):
            put(a, int(6 + 3 * math.cos(t)), int(8 + 2 * math.sin(t)), c); put(a, int(10 + 3 * math.cos(t)), int(8 + 2 * math.sin(t)), l)
    elif kind == 'fist':
        rect(a, 4, 5, 8, 7, c); hline(a, 4, 5, 8, l); for_ = [put(a, 4 + 2 * i, 6, d) for i in range(4)]; rect(a, 5, 12, 6, 2, c)
    elif kind == 'mask':
        dome(a, 8, 8, 6, 5, [d, d, c, l, l], 1); rect(a, 5, 7, 2, 2, ink); rect(a, 10, 7, 2, 2, ink); hline(a, 6, 11, 5, d)
    elif kind == 'tree':
        dome(a, 8, 6, 5, 4, [d, d, c, l, l], 1); vline(a, 8, 9, 5, hx('#6b4c34'))
    elif kind == 'leaf':
        for i in range(10): hline(a, 3 + i, 12 - i, max(1, 5 - abs(i - 5)), c)
        for i in range(10): put(a, 3 + i, 13 - i, d)
    elif kind == 'star4':          # filled five-point star (UI 'star', no outline figure)
        pts = []
        for k in range(10):
            t = -math.pi / 2 + k * math.pi / 5
            r_ = 6.5 if k % 2 == 0 else 2.8
            pts.append((8 + r_ * math.cos(t), 8.5 + r_ * math.sin(t)))
        from PIL import Image as _I, ImageDraw as _D
        m = _I.new('L', (16, 16), 0); _D.Draw(m).polygon(pts, fill=255)
        mm = np.array(m) > 0
        for y, x in zip(*np.nonzero(mm)): put(a, x, y, l if y < 8 and x < 9 else c)
    elif kind == 'hourglass':
        hline(a, 4, 2, 9, d); hline(a, 4, 13, 9, d)
        for y in range(3, 13):
            w = abs(y - 7.5) * .8 + .5
            hline(a, int(8 - w), y, int(2 * w) + 1, c if y > 8 else l)
    elif kind == 'wing':
        for i in range(8): hline(a, 3 + i, 4 + i, 10 - i, c if i % 2 else l)
    elif kind == 'shield':
        for y in range(2, 14):
            w = 5 if y < 9 else (14 - y)
            hline(a, 8 - w, y, 2 * w + 1, c if y > 4 else l)
    elif kind == 'bow':
        for t in np.linspace(-1.2, 1.2, 20): put(a, int(5 + 5 * math.cos(t)), int(8 + 6 * math.sin(t)), c)
        vline(a, 7, 3, 11, (240, 236, 220))
    elif kind == 'flake':
        for ang in range(3):
            t = ang * math.pi / 3
            for i in range(-6, 7): put(a, int(round(8 + i * math.cos(t))), int(round(8 + i * math.sin(t))), c)
    elif kind == 'trefoilish':   # original 'hazard' mark: three dots in a ring (not the real trefoil)
        for t in np.linspace(0, math.tau, 40): put(a, int(8 + 6 * math.cos(t)), int(8 + 6 * math.sin(t)), c)
        for k in range(3):
            t = k * math.tau / 3 - math.pi / 2
            dome(a, 8 + 3 * math.cos(t), 8 + 3 * math.sin(t), 1.5, 1.5, [d, d, c, l, l], 1)
    elif kind == 'bolt':
        pts = [(10, 1), (5, 8), (8, 8), (6, 14), (12, 6), (9, 6), (11, 1)]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]; x1, y1 = pts[i + 1]
            for s in range(8): put(a, int(x0 + (x1 - x0) * s / 7), int(y0 + (y1 - y0) * s / 7), c)
    elif kind == 'zz':
        for (x, y, s) in ((3, 9, 4), (9, 3, 4)):
            hline(a, x, y, s, c); hline(a, x, y + s - 1, s, c)
            for i in range(s): put(a, x + s - 1 - i, y + i, c)
    elif kind == 'swirl':
        for t in np.linspace(0, 4 * math.pi, 70): put(a, int(8 + t * .45 * math.cos(t)), int(8 + t * .45 * math.sin(t)), c)
    elif kind == 'bubble':
        for (x, y, r) in ((6, 10, 3), (10, 6, 2), (11, 11, 1.5)):
            for t in np.linspace(0, math.tau, 24): put(a, int(x + r * math.cos(t)), int(y + r * math.sin(t)), c)
    elif kind == 'crown':
        hline(a, 3, 12, 11, c); rect(a, 3, 9, 11, 3, c)
        for i, h in enumerate((5, 7, 5)): vline(a, 3 + i * 5, 12 - h - 1, h, l)
    elif kind == 'horn':
        for i in range(10): rect(a, 3 + i, 4 + int(i * .6), 2, 1 + i // 3, c if i < 7 else l)
    elif kind == 'boat':
        for y in range(10, 13): hline(a, 2 + (y - 10), y, 13 - 2 * (y - 10), c)
        vline(a, 8, 3, 7, d); rect(a, 9, 4, 4, 5, (240, 236, 220))
    elif kind == 'tankic':
        rect(a, 2, 9, 12, 4, c); rect(a, 5, 6, 6, 3, l); hline(a, 10, 7, 5, d); hline(a, 2, 13, 12, hx('#2a2a2e'))
    elif kind == 'planeic':
        rect(a, 2, 7, 12, 2, c); put(a, 14, 8, l); hline(a, 2, 7, 12, l)            # side view fuselage
        for i in range(3): hline(a, 2, 4 + i, 2 + i, d)                              # tail fin
        for i in range(3): hline(a, 6 - i, 9 + i, 5, d)                              # swept wing
    elif kind == 'missileic':
        for i in range(10): put(a, 3 + i, 12 - i, c); put(a, 4 + i, 12 - i, l)
        put(a, 13, 2, hx('#d5452d')); put(a, 3, 13, hx('#ffb84a')); put(a, 2, 14, hx('#ffe27a'))
    elif kind == 'cloud':
        for (x, y, r) in ((5, 8, 3), (9, 6, 4), (12, 9, 2.5)): dome(a, x, y, r, r * .8, [d, d, c, l, l], 1)
        if col in ('#7aa4c8',):
            for i in range(3): vline(a, 4 + i * 4, 12, 2, hx('#3a8ad8'))
        if col == '#5a6a7a': put(a, 9, 12, hx('#ffe27a')); put(a, 8, 13, hx('#ffe27a'))
    elif kind == 'crack':
        hline(a, 1, 10, 14, d)
        x = 8
        for y in range(2, 14): x += random.Random(y).choice((-1, 0, 1)); put(a, x, y, c)
    elif kind == 'peak':
        for y in range(4, 14): hline(a, 8 - (y - 4), y, 2 * (y - 4) + 1, hx('#5a4a3a'))
        for i in range(4): put(a, 8 + random.Random(i).randint(-2, 2), 3 - i % 2, c)
    elif kind == 'wave':
        for x in range(16):
            y = int(8 + 3 * math.sin(x / 2.5))
            vline(a, x, y, 14 - y, c); put(a, x, y, l)
    elif kind == 'sunic':
        dome(a, 8, 8, 3.5, 3.5, [d, d, c, l, l], 1)
        for k in range(8):
            t = k * math.pi / 4
            put(a, int(8 + 6 * math.cos(t)), int(8 + 6 * math.sin(t)), c)


# ------------------------------------------------------------------ weather / disasters FX
def fx_rain(a, f, kind='rain'):
    r = random.Random(1)
    for i in range(40):
        x, y = r.randint(0, 63), (r.randint(0, 63) + f * 16) % 64
        if kind == 'rain': put(a, x, y, hx('#a8c8e8')); put(a, (x - 1) % 64, (y - 1) % 64, hx('#7aa4c8'))
        elif kind == 'snow': put(a, (x + int(2 * math.sin(f + i))) % 64, (r.randint(0, 63) + f * 4) % 64, hx('#ffffff'))
        elif kind == 'acid': put(a, x, y, hx('#9ae04a')); put(a, (x - 1) % 64, (y - 1) % 64, hx('#5ea02a'))
        elif kind == 'hail': rect(a, x, y, 2, 2, hx('#e8f6ff'))
        elif kind == 'ash': put(a, (x + f) % 64, (r.randint(0, 63) + f * 3) % 64, hx('#6a655c') if i % 3 else hx('#f49a3c'))


def fx_fog(a, f):
    n = smooth_noise(64, 64, 16, f)
    a[..., :3] = 230
    return n


def fx_tornado(a, f):
    for y in range(60):
        w = 2 + (60 - y) * .32
        cx = 32 + math.sin(y / 8 + f) * 4 * (y / 60)
        for x in range(int(cx - w), int(cx + w) + 1):
            if (x + y * 2 + f * 3) % 5 < 3: put(a, x, 63 - y, hx('#8a96a0') if x < cx else hx('#6a747e'))
    for i in range(8):
        t = i / 8 * math.tau + f
        put(a, int(32 + 14 * math.cos(t)), int(62 + 2 * math.sin(t)), hx('#8a6a4a'))


def fx_tsunami(a, f):
    h = [8, 18, 30, 40, 34, 20][f]
    for x in range(96):
        top = 62 - int(h * (.6 + .4 * math.sin(x / 15 + f * .5)))
        for y in range(top, 64):
            c = hx('#1d4a82') if y > top + 6 else hx('#3277b0') if y > top + 2 else hx('#e8f6fa')
            put(a, x, y, c)
        if f >= 2 and x % 6 == 0: put(a, x + 2, top - 1, hx('#ffffff'))


def fx_volcano(a, f):
    for y in range(30):
        hline(a, 32 - (y + 6) // 1, 63 - 30 + y, 2 * (y + 6), hx('#4a3a30') if y % 3 else hx('#5a4a3e'))
    blend_mask(a, ellipse_mask(a.shape[:2], 32, 34, 6, 2), hx('#ffb84a'), 1)
    r = random.Random(f)
    for i in range(10 + f * 4):
        t = r.uniform(-1.1, 1.1) - math.pi / 2
        d = r.uniform(4, 8 + f * 4)
        x, y = 32 + math.cos(t) * d * 1.3, 32 + math.sin(t) * d
        dome(a, x, y, 1.6, 1.6, R5('#5a140a', '#a82a10', '#e8521a', '#ff9a3a', '#ffe27a'), i)
    for i in range(3): blend_mask(a, ellipse_mask(a.shape[:2], 28 + i * 4, 18 - f * 2 - i * 3, 7 + f, 5 + f * .5), hx('#4a4640'), .7)
    for i in range(f + 1): vline(a, 30 + i * 3, 36, 6 + i * 4, hx('#ff6a1e'))


def fx_firework(a, f, col):
    c = hx(col)
    if f < 2:
        vline(a, 16, 30 - f * 12, 4, hx('#ffe27a')); return
    r = (f - 1) * 4
    for k in range(12):
        t = k / 12 * math.tau
        for s in range(2):
            put(a, int(16 + math.cos(t) * (r - s * 2)), int(14 + math.sin(t) * (r - s * 2) + (f - 2)), c if s == 0 else lit(c, .3))
    if f == 2: put(a, 16, 14, (255, 255, 255))


def fx_lightning(a, f):
    if f == 3: return
    x = 16; r = random.Random(7)
    for y in range(0, 60):
        x += r.choice((-1, 0, 0, 1))
        put(a, x, y, hx('#ffffff')); put(a, x + 1, y, hx('#b4c8ff'))
        if y % 13 == 7: [put(a, x + k, y + k, hx('#b4c8ff')) for k in range(5)]
    if f == 1: blend_mask(a, ellipse_mask(a.shape[:2], x, 60, 10, 4), hx('#e8f0ff'), .7)
    if f == 2: blend_mask(a, ellipse_mask(a.shape[:2], x, 60, 6, 2), hx('#1e1a16'), .6)


def fx_meteor(a, f):
    x, y = 8 + f * 14, 4 + f * 14
    for i in range(14): blend_mask(a, ellipse_mask(a.shape[:2], x - i * 1.4, y - i * 1.4, 4 - i * .25, 4 - i * .25), hx('#ffb84a') if i < 5 else hx('#8a8a8e'), .8 - i * .05)
    dome(a, x, y, 3, 3, R5('#2a1a14', '#4a2a1a', '#6a3a24', '#ffb84a', '#fff6c0'), 1)


def fx_aurora(a, f):
    for x in range(96):
        for k in range(3):
            y = int(10 + k * 5 + 4 * math.sin(x / 9 + f * .7 + k))
            col = [hx('#6af08a'), hx('#5fe0e8'), hx('#c87ae8')][k]
            for t in range(6): blend_rect(a, x, y + t, 1, 1, col, .55 - t * .08)


def fx_wildfire(a, f):
    r = random.Random(f)
    blend_mask(a, ellipse_mask(a.shape[:2], 16, 28, 15, 4), hx('#2a1e14'), .6)
    for i in range(16):
        x = r.randint(2, 30); h = r.randint(4, 14)
        for yy in range(h):
            c = hx('#ffe27a') if yy > h - 3 else hx('#f49a3c') if yy > h // 2 else hx('#d5452d')
            put(a, x + int(math.sin(yy + f + i)), 30 - (h - yy) - 2 + 2, c)


def fx_sandstorm(a, f):
    r = random.Random(3)
    for i in range(70):
        x, y = (r.randint(0, 63) + f * 12) % 64, r.randint(0, 63)
        hline(a, x, y, r.randint(1, 4), hx('#d8b878') if i % 2 else hx('#c4a066'))


def fx_quake(a, f):
    r = random.Random(11)
    for k in range(4 + f * 3):
        x, y = 32, 16
        ang = r.uniform(0, math.tau)
        for s in range(r.randint(8, 14 + f * 6)):
            x += math.cos(ang); y += math.sin(ang) * .5; ang += r.uniform(-.5, .5)
            put(a, int(x), int(y), hx('#1e1610')); put(a, int(x) + 1, int(y), hx('#4a3424'))
    if f == 2:
        for i in range(10): put(a, r.randint(10, 54), r.randint(4, 28), hx('#8a6a4a'))


def fx_rainbow(a):
    for k, col in enumerate(('#e04a3a', '#f49a3c', '#f0d050', '#6ac04a', '#3a8ad8', '#7a4ac8')):
        for t in np.linspace(math.pi, math.tau, 140):
            blend_rect(a, int(48 + (40 - k) * math.cos(t)), int(44 + (40 - k) * math.sin(t)), 1, 1, hx(col), .55)


def fx_blizzard(a, f):
    r = random.Random(5)
    for i in range(60):
        x, y = (r.randint(0, 63) + f * 10) % 64, (r.randint(0, 63) + f * 3) % 64
        hline(a, x, y, 2, hx('#ffffff')); put(a, (x + 2) % 64, y, hx('#cfefff'))


# ================================================================== exporters
def ex_kingdoms():
    at = Atlas('kingdom_colours', os.path.join(OUT, 'UI', 'Kingdoms'))
    pal = palettes()
    data_dir = os.path.join(os.path.dirname(OUT), 'WorldSimData'); os.makedirs(data_dir, exist_ok=True)
    json.dump({'palettes': pal, 'note': 'team ramp feeds WorldSimRecolor TEAM region (5 shades dark->light); accent = ACC2; 32 distinct kingdom colours'},
              open(os.path.join(data_dir, 'kingdom_palettes.json'), 'w'), indent=1)
    from culturegen import SYMBOLS
    syms = list(SYMBOLS)
    for i, p in enumerate(pal):
        rp = [hx(c) for c in p['team']]; acc = [hx(c) for c in p['accent']]
        n = p['name']
        for shape in ('swallow', 'square', 'pennant'):
            keys = []
            for f in range(4):
                key = f'flag_{n}_{shape}_{f}'
                at.add(key, lambda a, ctx, rp=rp, acc=acc, f=f, shape=shape, sym=SYMBOLS[syms[i % len(syms)]]: flag_frame(a, rp, acc, f, shape, sym if shape != 'pennant' else None), 14, 14, (1, 13),
                       keep_canvas=True, tags={'kingdom_colour': n, 'flag': shape, 'frame': f})
                keys.append(key)
            at.anim(f'flag_{n}_{shape}', keys, 6, True)
        at.add(f'banner_{n}', lambda a, ctx, rp=rp, acc=acc: banner_h(a, rp, acc), 10, 16, (5, 0), keep_canvas=True, tags={'kingdom_colour': n, 'ui': 'banner'})
        at.add(f'capital_{n}', lambda a, ctx, rp=rp, acc=acc: capital_marker(a, rp, acc), 16, 14, (8, 13), keep_canvas=True, tags={'kingdom_colour': n, 'ui': 'capital_marker'})
        at.add(f'army_marker_{n}', lambda a, ctx, rp=rp, acc=acc: army_marker(a, rp, acc), 16, 16, (8, 15), keep_canvas=True, tags={'kingdom_colour': n, 'ui': 'army_marker'})
        at.add(f'badge_{n}', lambda a, ctx, rp=rp, acc=acc: badge(a, rp, acc), 18, 20, (9, 10), keep_canvas=True, tags={'kingdom_colour': n, 'ui': 'badge'})
        for pr in (False, True):
            at.add(f'button_{n}_{"pressed" if pr else "normal"}', lambda a, ctx, rp=rp, pr=pr: btn(a, rp, pr), 32, 14, (0, 0), keep_canvas=True, tags={'kingdom_colour': n, 'ui': 'button', 'slice': [3, 3, 3, 3]})
        at.add(f'select_ring_{n}', lambda a, ctx, rp=rp: ring(a, rp), 21, 11, (10, 5), keep_canvas=True, tags={'kingdom_colour': n, 'ui': 'selection'})
        at.add(f'war_tent_{n}', lambda a, ctx, rp=rp, acc=acc: tent(a, rp, acc), 17, 13, (8, 12), keep_canvas=True, tags={'kingdom_colour': n, 'prop': 'war_camp_tent'})
        at.add(f'border_{n}', lambda a, ctx, rp=rp: border_px(a, rp), 16, 2, (0, 0), keep_canvas=True, tags={'kingdom_colour': n, 'ui': 'territory_border', 'tileable_x': True})
    # swatch strip for the docs
    DONE('kingdom_colours', at)


def ex_icons():
    at = Atlas('icons', os.path.join(OUT, 'UI', 'Icons'))
    def both(key, fn, tags):
        at.add(f'{key}_16', lambda a, ctx: fn(a), 16, 16, (8, 8), keep_canvas=True, tags=dict(tags, size=16))
        at.add(f'{key}_32', lambda a, ctx: _x2(a, fn), 32, 32, (16, 16), keep_canvas=True, tags=dict(tags, size=32))
    for name, (rows, cols) in RES_ICONS.items():
        both(f'ic_{name}', lambda a, rows=rows, cols=cols: _sym(a, rows, cols), {'icon': name})
    for name, (kind, col) in SIMPLE_ICONS.items():
        both(f'ic_{name}', lambda a, kind=kind, col=col: draw_simple_icon(a, kind, col), {'icon': name, 'shape': kind})
    # portraits auto-cut from the creature / being / titan / building atlases
    srcs = [('Characters/Fauna/fauna_land', 'a_', '_adult_idle_0'), ('Characters/Fauna/fauna_critters', 'c_', '_adult_idle_0'), ('Characters/Fauna/fauna_sea', 's_', '_adult_swim_0'),
            ('Characters/Magic/beings', 'm_', '_idle_0'), ('Characters/Titans/titans', 't_', '_idle_0'), ('Buildings/buildings_eras', 'b_', '_v0'), ('Buildings/world_structures', 'wonder_', '')]
    for rel, pre, suf in srcs:
        meta = json.load(open(os.path.join(OUT, rel + '.json')))
        pages = [np.array(Image.open(os.path.join(OUT, os.path.dirname(rel), p['image'])).convert('RGBA')) for p in meta['pageList']]
        for fr in meta['frameList']:
            nm = fr['name']
            if not (nm.startswith(pre) and nm.endswith(suf)) or '__' in nm: continue
            sp = pages[fr['page']][fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
            key = nm[len(pre):len(nm) - len(suf)] if suf else nm[len(pre):]
            big = portrait(sp, 32); small = big[::2, ::2].copy()
            at.add_array(f'portrait_{pre.strip("_")}_{key}_32', big, (16, 16), {'portrait': key, 'source': rel, 'size': 32})
            at.add_array(f'portrait_{pre.strip("_")}_{key}_16', small, (8, 8), {'portrait': key, 'source': rel, 'size': 16})
    DONE('icons', at)


def _x2(a, fn):
    t = np.zeros((16, 16, 3), np.uint8); t[:] = a[0, 0]
    fn(t)
    a[:] = upscale(t, 2)


def portrait(sp, S):
    """fit a sprite into an SxS framed portrait: crop head end (right/top) if too big, nearest-scale by 1/2 if huge."""
    sp = sp.copy()
    while sp.shape[0] > S * 2.2 or sp.shape[1] > S * 2.2: sp = sp[::2, ::2]
    h, w = sp.shape[:2]
    inner = S - 4
    if h > inner or w > inner:
        ys, xs = np.nonzero(sp[..., 3] > 200)
        cy, cx = (ys.mean(), xs.mean()) if len(xs) else (h / 2, w / 2)
        cy -= inner / 6; cx += inner / 6
        y0 = int(min(max(cy - inner / 2, 0), max(h - inner, 0))); x0 = int(min(max(cx - inner / 2, 0), max(w - inner, 0)))
        sp = sp[y0:y0 + inner, x0:x0 + inner]; h, w = sp.shape[:2]
    out = np.zeros((S, S, 4), np.uint8)
    for y in range(S):
        for x in range(S):
            if (x - S / 2 + .5) ** 2 + (y - S / 2 + .5) ** 2 <= (S / 2) ** 2: out[y, x] = (*hx('#1e2633'), 255)
            if (S / 2 - 1.2) ** 2 < (x - S / 2 + .5) ** 2 + (y - S / 2 + .5) ** 2 <= (S / 2) ** 2: out[y, x] = (*hx('#c8a050'), 255)
    oy, ox = (S - h) // 2 + (1 if h < inner else 0), (S - w) // 2
    al = sp[..., 3:4] / 255.
    reg = out[oy:oy + h, ox:ox + w]
    reg[..., :3] = (reg[..., :3] * (1 - al) + sp[..., :3] * al).astype(np.uint8)
    reg[..., 3] = np.maximum(reg[..., 3], sp[..., 3])
    return out


def ex_weather():
    at = Atlas('weather_fx', os.path.join(OUT, 'FX', 'Weather'))
    def seq(name, n, W, H, fn, piv, loop=True, tags=None, keep=False, ev=None):
        keys = []
        for f in range(n):
            key = f'wx_{name}_{f}'
            at.add(key, lambda a, ctx, f=f: fn(a, f), W, H, piv, keep_canvas=keep, tags=dict(tags or {}, fx=name, frame=f)); keys.append(key)
        at.anim(f'wx_{name}', keys, 8, loop, ev or [])
    for kind in ('rain', 'snow', 'acid', 'hail', 'ash'):
        seq(f'{kind}_tile', 4, 64, 64, lambda a, f, kind=kind: fx_rain(a, f, kind), (0, 0), tags={'tileable': True, 'layer': 'screen overlay'}, keep=True)
    seq('blizzard_tile', 4, 64, 64, fx_blizzard, (0, 0), tags={'tileable': True}, keep=True)
    seq('sandstorm_tile', 4, 64, 64, fx_sandstorm, (0, 0), tags={'tileable': True}, keep=True)
    for f in range(2):
        n = smooth_noise(64, 64, 16, f + 3)
        img = np.zeros((64, 64, 4), np.uint8); img[..., :3] = 236; img[..., 3] = (np.clip(n - .3, 0, 1) * 200).astype(np.uint8)
        at.add_array(f'wx_fog_tile_{f}', img, (0, 0), {'fx': 'fog', 'tileable': True})
    seq('tornado', 6, 64, 66, fx_tornado, (32, 63), ev=[(0, 'sfx:tornado')])
    seq('tsunami', 6, 96, 66, fx_tsunami, (48, 63), loop=False, ev=[(2, 'hit_area'), (0, 'sfx:tsunami')])
    seq('volcano', 6, 64, 66, fx_volcano, (32, 63), ev=[(1, 'spawn_lava'), (0, 'sfx:volcano')])
    seq('lightning_strike', 4, 32, 64, fx_lightning, (16, 60), loop=False, ev=[(1, 'hit_area'), (1, 'sfx:thunder')])
    seq('meteor', 4, 64, 64, fx_meteor, (50, 50), loop=False, ev=[(3, 'impact')])
    seq('wildfire', 4, 32, 32, fx_wildfire, (16, 30), ev=[(0, 'spread_fire')])
    seq('quake', 3, 64, 32, fx_quake, (32, 16), loop=False, ev=[(0, 'camera_shake'), (0, 'sfx:quake')])
    seq('aurora', 4, 96, 34, fx_aurora, (48, 17), tags={'layer': 'sky'})
    at.add('wx_rainbow', lambda a, ctx: fx_rainbow(a), 96, 46, (48, 45), tags={'fx': 'rainbow', 'layer': 'sky'})
    for col in ('#e04a3a', '#3a8ad8', '#6ac04a', '#f0d050', '#c87ae8', '#ffffff'):
        seq(f'firework_{col[1:]}', 6, 32, 32, lambda a, f, col=col: fx_firework(a, f, col), (16, 31), loop=False, ev=[(2, 'sfx:firework')])
    # day/night + season light tints as data
    DONE('weather_fx', at)


CATS = {'kingdoms': ex_kingdoms, 'icons': ex_icons, 'weather': ex_weather}
