"""Shared drawing library for the WorldSim preview (original art, procedural)."""
import math, random
import numpy as np
from PIL import Image

LX, LY = -0.6, -0.8  # light from top-left


def hx(c):
    c = c.lstrip('#'); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def ramp(*cs):
    return [hx(c) for c in cs]


def lit(c, k):
    """k>0 lighten, k<0 darken (fraction)."""
    if k >= 0:
        return tuple(int(v + (255 - v) * k) for v in c)
    return tuple(int(v * (1 + k)) for v in c)


SHADOW = (20, 34, 26)

# ---------------- materials ----------------
W = {  # wall ramps dark..light
    'hide': ramp('#6e5034', '#93714b', '#b79262'),
    'mud': ramp('#86643f', '#a6815a', '#c5a074'),
    'mudw': ramp('#b9a382', '#d6c3a0', '#ebdcbd'),     # whitewashed mud
    'plaster': ramp('#b8a98c', '#d9ccb0', '#ece2ca'),
    'stone': ramp('#6a6760', '#87837a', '#a6a196'),
    'fort': ramp('#57544f', '#736f68', '#938e85'),
    'brick': ramp('#6b3127', '#8a4332', '#a8573f'),
    'concrete': ramp('#a29c8e', '#bdb7a9', '#d6d0c2'),
    'glass': ramp('#33485c', '#45607a', '#5d7d97'),
    'metal': ramp('#545b63', '#6c747c', '#8b939a'),
    'marble': ramp('#c4bfb3', '#dfdacf', '#f3f0e8'),
    'white': ramp('#b9c0c7', '#d9dee3', '#f2f5f7'),
    'dark': ramp('#262b33', '#343a44', '#474f5b'),
}
R = {  # roof ramps (5) dark..light
    'K': ramp('#6e2a22', '#9a3c2c', '#c4563d', '#de7a55', '#f0a07a'),
    'straw': ramp('#6b4d27', '#8f6a35', '#b48c48', '#d4b066', '#ead08a'),
    'hide': ramp('#5d4229', '#7d5c3a', '#9e7a50', '#bd9867', '#d6b585'),
    'mud': ramp('#6f5232', '#8c6b45', '#a8865c', '#c4a275', '#dcbd92'),
    'slate': ramp('#2b313c', '#3a4250', '#4c5666', '#626e80', '#8794a6'),
    'copper': ramp('#2c5850', '#3c7466', '#53917b', '#73ad94', '#a2ceb6'),
    'gold': ramp('#7a5418', '#a8752a', '#d19a3a', '#ecc25c', '#f8e08e'),
    'metal': ramp('#474d55', '#5b626b', '#737b84', '#929aa2', '#b4bac0'),
    'concrete': ramp('#8a8579', '#a29c8e', '#bdb7a9', '#d6d0c2', '#e9e4d8'),
    'glass': ramp('#26384a', '#38516b', '#52718e', '#7c9fba', '#b3cfe0'),
    'white': ramp('#97a0a8', '#b6bec5', '#d4dadf', '#eaeef1', '#ffffff'),
    'leaf': ramp('#284f37', '#356a3e', '#4a8545', '#68a24f', '#8fbd5c'),
    'stone': ramp('#55524c', '#6d6a63', '#87837a', '#a29d92', '#bdb8ad'),
    'palm': ramp('#2f5a2c', '#3f7535', '#55913e', '#74ad4c', '#9cc865'),
}
C = {
    'lit': hx('#ffd98a'), 'lit2': hx('#f2b65a'), 'win': hx('#26303a'), 'door': hx('#4a3628'),
    'wood': ramp('#4a3628', '#6b4c34', '#8c6844'), 'beam': hx('#5e412b'),
    'cyan': hx('#5fe0e8'), 'cyan2': hx('#a8f6fa'), 'magenta': hx('#e85fc4'),
    'water': ramp('#1d4a82', '#255c98', '#3277b0', '#4b95c2', '#d6eef2'),
    'grass': ramp('#6c9e4c', '#70a34f', '#74a753'), 'dirt': ramp('#8a6f49', '#9c7f55', '#ad9063'),
    'cobble': ramp('#6f6a61', '#8b867a', '#a29c8e'), 'asph': ramp('#33363b', '#3c3f45', '#43464c'),
    'side': ramp('#a29f96', '#b4b1a8', '#c4c1b8'), 'line': hx('#e8d27a'),
    'coal': ramp('#1c1d20', '#2b2c30', '#3d3e44'), 'ore_cu': hx('#3fb39a'), 'ore_fe': hx('#9a4a32'),
    'gold': hx('#ecc25c'), 'fire': ramp('#d5452d', '#f49a3c', '#ffe27a'),
}
K2 = {  # other kingdoms (for maps)
    'blue': ramp('#22406e', '#2f5a96', '#4579bb', '#6a9ad3', '#9cc0e8'),
    'violet': ramp('#45285e', '#5f3a80', '#7d52a3', '#9d76c2', '#c2a3dc'),
    'gold': ramp('#6b4a12', '#93681f', '#bf8d2e', '#ddb04c', '#f0d185'),
}


# ---------------- canvas helpers ----------------
def put(a, x, y, c):
    x, y = int(x), int(y)
    if 0 <= x < a.shape[1] and 0 <= y < a.shape[0]:
        a[y, x] = c[:3]


def rect(a, x, y, w, h, c):
    x0, y0, x1, y1 = max(int(x), 0), max(int(y), 0), min(int(x + w), a.shape[1]), min(int(y + h), a.shape[0])
    if x1 > x0 and y1 > y0:
        a[y0:y1, x0:x1] = c[:3]


def hline(a, x, y, w, c): rect(a, x, y, w, 1, c)
def vline(a, x, y, h, c): rect(a, x, y, 1, h, c)


def blend_mask(a, mask, color, alpha):
    if mask.any():
        a[mask] = (a[mask] * (1 - alpha) + np.array(color[:3]) * alpha).astype(np.uint8)


def blend_rect(a, x, y, w, h, color, alpha):
    m = np.zeros(a.shape[:2], bool)
    m[max(int(y), 0):max(int(y + h), 0), max(int(x), 0):max(int(x + w), 0)] = True
    blend_mask(a, m, color, alpha)


def ellipse_mask(shape, cx, cy, rx, ry):
    y0, y1 = max(int(cy - ry - 1), 0), min(int(cy + ry + 2), shape[0])
    x0, x1 = max(int(cx - rx - 1), 0), min(int(cx + rx + 2), shape[1])
    m = np.zeros(shape, bool)
    if y1 <= y0 or x1 <= x0: return m
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m[y0:y1, x0:x1] = ((xx + .5 - cx) / rx) ** 2 + ((yy + .5 - cy) / ry) ** 2 <= 1
    return m


def shadow_ell(a, cx, cy, rx, ry, alpha=.3):
    blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, rx, ry), SHADOW, alpha)


def shadow_rect(a, x, y, w, h, alpha=.32):
    blend_rect(a, x, y, w, h, SHADOW, alpha)


BAYER = [[0, 2], [3, 1]]


def dome(a, cx, cy, rx, ry, rp, seed=0, rough=0.0, top=None):
    """Lit dome with banded shading + ordered dither. top: only draw rows < top (cut)."""
    r = random.Random(seed)
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        if top is not None and y >= top: break
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = nx * nx + ny * ny
            if d > 1 + rough * (r.random() - .5): continue
            nz = math.sqrt(max(0, 1 - min(d, 1)))
            l = nx * LX + ny * LY + nz * .55
            v = (l + .6) / 1.75 * (len(rp) - 1) + (BAYER[y % 2][x % 2] / 4 - .375) * .9
            put(a, x, y, rp[int(max(0, min(len(rp) - 1, round(v))))])


def smooth_noise(w, h, cell, seed):
    r = np.random.default_rng(seed)
    g = r.random((h // cell + 3, w // cell + 3)).astype(np.float32)
    img = Image.fromarray((g * 255).astype(np.uint8)).resize(((w // cell + 3) * cell, (h // cell + 3) * cell), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32)[:h, :w] / 255.0


def grass_ground(w, h, seed=1, tint=None):
    a = np.zeros((h, w, 3), np.uint8)
    n = smooth_noise(w, h, 18, seed)
    gi = np.clip((n * 3).astype(int), 0, 2)
    a[:] = np.array(C['grass'])[gi]
    r = np.random.default_rng(seed + 5)
    jit = r.integers(-3, 4, (h // 2 + 1, w // 2 + 1)).repeat(2, 0).repeat(2, 1)[:h, :w]
    a[:] = np.clip(a.astype(int) + jit[..., None], 0, 255).astype(np.uint8)
    for _ in range(w * h // 260):
        x, y = r.integers(0, w), r.integers(0, h)
        a[y, x] = [hx('#e4d27a'), hx('#d98a8a'), hx('#e4d27a')][r.integers(0, 3)]
    if tint is not None:
        a[:] = (a * (1 - tint[1]) + np.array(tint[0]) * tint[1]).astype(np.uint8)
    return a


def upscale(a, k):
    return np.asarray(Image.fromarray(a).resize((a.shape[1] * k, a.shape[0] * k), Image.NEAREST)).copy()


def vignette(img, k=.14):
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    f = 1 - k * np.clip(r - .25, 0, None)
    return Image.fromarray(np.clip(a * f[..., None], 0, 255).astype(np.uint8))


# ---------------- tree helpers ----------------
def tree(a, x, y, s, seed, rp=None):
    rp = rp or R['leaf']
    shadow_ell(a, x + 2, y + s + 2, s + 1, max(2, s // 2))
    rect(a, x, y + s - 1, 2, 4, C['wood'][0]); put(a, x, y + s - 1, C['wood'][1]); put(a, x, y + s, C['wood'][1])
    r = random.Random(seed)
    for (ox, oy, k) in [(-s * .45, .2 * s, .75), (s * .45, .25 * s, .7), (0, -.15 * s, 1.0)]:
        dome(a, x + 1 + ox, y + oy, s * k, s * k * .92, rp, seed + r.randint(0, 99), rough=.25)


def palm(a, x, y, seed=0):
    shadow_ell(a, x + 3, y + 9, 4, 1.5)
    for i in range(8):
        put(a, x + (1 if i < 3 else 0), y + 8 - i, C['wood'][1 if i % 2 else 2])
    rp = R['palm']
    for (dx, dy) in [(-4, 1), (-3, 0), (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1), (3, 0), (4, 1), (-3, 1), (3, 1),
                     (-1, -2), (0, -2), (1, -2), (-5, 2), (5, 2), (0, 0)]:
        put(a, x + dx, y + dy, rp[3 if dx < 0 else 2] if dy > -2 else rp[4])
    put(a, x + 4, y + 2, rp[1]); put(a, x - 5, y + 2, rp[2]); put(a, x, y, rp[1])


def bush(a, x, y, seed=0):
    shadow_ell(a, x + 1.5, y + 2, 2.5, 1)
    dome(a, x, y, 2.2, 1.9, R['leaf'], seed)


def rock(a, x, y, s=2, seed=0):
    shadow_ell(a, x + s * .7, y + s * .7, s, s * .5, .25)
    dome(a, x, y, s, s * .8, R['stone'], seed)


# ---------------- 3x5 pixel font ----------------
_G = {
 'A': "010101111101101", 'B': "110101110101110", 'C': "011100100100011", 'D': "110101101101110",
 'E': "111100110100111", 'F': "111100110100100", 'G': "011100101101011", 'H': "101101111101101",
 'I': "111010010010111", 'J': "001001001101010", 'K': "101101110101101", 'L': "100100100100111",
 'M': "101111111101101", 'N': "110101101101101", 'O': "010101101101010", 'P': "110101110100100",
 'Q': "010101101110011", 'R': "110101110101101", 'S': "011100010001110", 'T': "111010010010010",
 'U': "101101101101111", 'V': "101101101101010", 'W': "101101111111101", 'X': "101101010101101",
 'Y': "101101010010010", 'Z': "111001010100111",
 '0': "111101101101111", '1': "010110010010111", '2': "110001010100111", '3': "110001010001110",
 '4': "101101111001001", '5': "111100110001110", '6': "011100111101111", '7': "111001010010010",
 '8': "111101111101111", '9': "111101111001110",
 '.': "000000000000010", ':': "000010000010000", '-': "000000111000000", '/': "001001010100100",
 '%': "101001010100101", '+': "000010111010000", '(': "010100100100010", ')': "010001001001010",
 "'": "010010000000000", ',': "000000000010100", '>': "100010001010100", '<': "001010100010001",
 '!': "010010010000010", '?': "110001010000010", '@': "000001101010000", '~': "000101010101000",
 '#': "101111101111101", ' ': "000000000000000", '=': "000111000111000", '|': "010010010010010",
}


def text(a, x, y, s, col, scale=1, shadow=None):
    s = s.upper()
    if shadow is not None:
        text(a, x + scale, y + scale, s, shadow, scale)
    cx = x
    for ch in s:
        g = _G.get(ch, _G['?'])
        for j in range(5):
            for i in range(3):
                if g[j * 3 + i] == '1':
                    rect(a, cx + i * scale, y + j * scale, scale, scale, col)
        cx += 4 * scale
    return cx


def text_w(s, scale=1):
    return len(s) * 4 * scale - scale


# ---------------- icons (7x7) ----------------
ICONS = {
 'food': (["...y...", "..yYy..", "...y...", "..yYy..", "...y...", "..yYy..", "...g..."], {'y': '#d6b04b', 'Y': '#f0d27a', 'g': '#6a9a3e'}),
 'wood': (["......", ".bbbbb.", "bBbBbBb", ".bbbbb.", "......."], {'b': '#6b4c34', 'B': '#a37a52'}),
 'stone': (["......", "..sss..", ".sSsss.", "sSsssss", "sssssds", ".ddddd."], {'s': '#87837a', 'S': '#bdb8ad', 'd': '#5f5b55'}),
 'copper': (["......", "..ooo..", ".oOoco.", "oocoooo", ".oooco.", "..ooo.."], {'o': '#b8693a', 'O': '#e6a06a', 'c': '#3fb39a'}),
 'iron': ([".......", ".......", "..iiii.", ".iIiii.", "iiiiid.", "dddddd."], {'i': '#8b939a', 'I': '#d0d6da', 'd': '#545b63'}),
 'coal': ([".......", "..ccc..", ".cCccc.", "ccccccc", ".ccccc.", "..ccc.."], {'c': '#2b2c30', 'C': '#6d6f78'}),
 'oil': (["...o...", "..ooo..", ".ooOoo.", ".ooooo.", "..ooo.."], {'o': '#2a2633', 'O': '#8a7fa8'}),
 'uranium': (["..ggg..", ".gGggg.", "ggg.ggg", "gg.g.gg", "ggg.ggg", ".ggggg.", "..ggg.."], {'g': '#6fd35a', 'G': '#c8ff9a'}),
 'gold': (["..yyy..", ".yYyyy.", "yyYyyyy", "yyyyyyy", "yyyyyyd", ".yyyyd.", "..ddd.."], {'y': '#ecc25c', 'Y': '#fff2b0', 'd': '#a8752a'}),
 'know': (["bbb.bbb", "bWbbbWb", "bWbbbWb", "bWbbbWb", "bbbbbbb", "...b..."], {'b': '#4579bb', 'W': '#e8eef6'}),
 'pop': (["..sss..", "..sss..", "...s...", ".ccccc.", "c.ccc.c", "..c.c..", "..c.c.."], {'s': '#e0b48c', 'c': '#c4563d'}),
 'energy': (["...yy..", "..yy...", ".yyyyy.", "...yy..", "..yy...", ".yy....", ".y....."], {'y': '#ffd34a'}),
 'joy': ([".yyyyy.", "yyyyyyy", "yDyyyDy", "yyyyyyy", "yDyyyDy", "yyDDDyy", ".yyyyy."], {'y': '#f2c25a', 'D': '#6b4a12'}),
 'sword': (["......w", ".....w.", "....w..", "g..w...", ".gw....", ".bg....", "b..g..."], {'w': '#d0d6da', 'g': '#c8a23a', 'b': '#6b4c34'}),
 'shield': (["kkkkkkk", "kKKkKKk", "kKkkkKk", "kKKkKKk", ".kKKKk.", "..kKk..", "...k..."], {'k': '#6e2a22', 'K': '#c4563d'}),
 'flask': (["..www..", "...w...", "...w...", "..w.w..", ".wcccw.", "wcccccw", "wwwwwww"], {'w': '#d0d6da', 'c': '#5fe0e8'}),
 'pick': (["sssss..", "s...ss.", "....bs.", "...b..s", "..b....", ".b.....", "b......"], {'s': '#8b939a', 'b': '#8c6844'}),
 'crown': (["y..y..y", "yy.y.yy", "yyyyyyy", "yrryrry", "yyyyyyy"], {'y': '#ecc25c', 'r': '#c4563d'}),
 'globe': ([".bbbbb.", "bggbbgb", "bgggbbb", "bbggbgb", "bbbgggb", "bbbbggb", ".bbbbb."], {'b': '#3277b0', 'g': '#6c9e4c'}),
 'tree': (["..ggg..", ".gGggg.", "gGggggg", ".ggggg.", "..ggg..", "...b...", "...b..."], {'g': '#4a8545', 'G': '#8fbd5c', 'b': '#6b4c34'}),
 'bolt2': ([".......", "...cc..", "..cc...", ".ccccc.", "...cc..", "..cc...", "......."], {'c': '#5fe0e8'}),
 'gear': (["..g.g..", ".ggggg.", "ggg.ggg", ".g...g.", "ggg.ggg", ".ggggg.", "..g.g.."], {'g': '#8b939a'}),
 'hammer': ([".sss...", ".ssss..", "..sb...", "...b...", "...b...", "...b...", "...b..."], {'s': '#8b939a', 'b': '#8c6844'}),
 'eye': ([".......", "..www..", ".wbbbw.", "wbbKbbw", ".wbbbw.", "..www..", "......."], {'w': '#e8eef6', 'b': '#4579bb', 'K': '#141a22'}),
 'storm': (["..ggg..", ".ggggg.", "ggggggg", "...y...", "..y....", "...y...", "..y...."], {'g': '#8b939a', 'y': '#ffd34a'}),
 'flag': (["p......", "pkkkk..", "pkKkkk.", "pkkkk..", "p......", "p......", "p......"], {'p': '#c4bfb3', 'k': '#c4563d', 'K': '#f0a07a'}),
 'house': (["...k...", "..kkk..", ".kkkkk.", "kkkkkkk", ".wwdww.", ".wwdww.", ".wwdww."], {'k': '#c4563d', 'w': '#ece2ca', 'd': '#4a3628'}),
 'lock': (["..ggg..", ".g...g.", ".g...g.", "ggggggg", "gggKggg", "gggKggg", "ggggggg"], {'g': '#6c747c', 'K': '#141a22'}),
}


def icon(a, x, y, name, scale=1):
    rows, cmap = ICONS[name]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.':
                rect(a, x + i * scale, y + j * scale, scale, scale, hx(cmap[ch]))


# ---------------- UI panels ----------------
UI = {'bg': hx('#141a22'), 'bg2': hx('#1d2530'), 'edge': hx('#2c3846'), 'txt': hx('#f3e6c8'),
      'dim': hx('#8a94a3'), 'acc': hx('#e8b46a'), 'good': hx('#7cc46a'), 'bad': hx('#e06a55'), 'K': R['K'][2]}


def panel(a, x, y, w, h, alpha=.9, edge=True, col=None):
    blend_rect(a, x, y, w, h, col or UI['bg'], alpha)
    if edge:
        hline(a, x + 1, y, w - 2, UI['edge']); hline(a, x + 1, y + h - 1, w - 2, UI['edge'])
        vline(a, x, y + 1, h - 2, UI['edge']); vline(a, x + w - 1, y + 1, h - 2, UI['edge'])


def bar(a, x, y, w, h, frac, col, bg=None):
    rect(a, x, y, w, h, bg or hx('#0c1016'))
    rect(a, x, y, max(1, int(w * frac)), h, col)
    hline(a, x, y, max(1, int(w * frac)), lit(col, .35))
