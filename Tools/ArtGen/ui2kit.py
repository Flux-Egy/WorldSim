"""v2 UI kit: 5x7 pixel font, pixel Arabic (aliased DejaVu Bold), ornate 9-slice frames in kingdom colour,
ribbon titles, bevel buttons, chips, sparklines, power icons (11x11)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *

INK = hx('#0b0e13'); BG = hx('#151b25'); BG2 = hx('#1e2633'); BG3 = hx('#28323f')
GOLD = [hx('#6e4e1e'), hx('#9a7030'), hx('#c8a050'), hx('#e6c47a'), hx('#fbe6b0')]
TXT = hx('#f3e6c8'); DIM = hx('#8f99a8'); ACC = hx('#e8b46a'); GOOD = hx('#7cc46a'); BAD = hx('#e06a55'); CYAN = hx('#5fe0e8')
KR = {'K': R['K'], 'blue': K2['blue'], 'violet': K2['violet'], 'gold': K2['gold'], 'teal': ramp('#163c3e', '#1f4d4f', '#2b6a6a', '#3a8a86', '#5aaca4')}

_F = {
 'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"], 'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
 'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."], 'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
 'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"], 'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
 'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."], 'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
 'I': ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"], 'J': ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
 'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"], 'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
 'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"], 'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
 'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."], 'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
 'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"], 'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
 'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."], 'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
 'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."], 'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
 'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"], 'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
 'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."], 'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
 '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."], '1': [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"],
 '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"], '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
 '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."], '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
 '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."], '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
 '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."], '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
 ' ': ["..", "..", "..", "..", "..", "..", ".."], '.': [".", ".", ".", ".", ".", ".", "#"], ',': [".", ".", ".", ".", ".", "#", "#"],
 ':': [".", ".", "#", ".", ".", "#", "."], '-': ["...", "...", "...", "###", "...", "...", "..."],
 '+': [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."], '%': ["##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"],
 '/': ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."], '!': ["#", "#", "#", "#", "#", ".", "#"],
 '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."], "'": ["#", "#", ".", ".", ".", ".", "."],
 '(': [".#", "#.", "#.", "#.", "#.", "#.", ".#"], ')': ["#.", ".#", ".#", ".#", ".#", ".#", "#."],
 'x': [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"], '>': ["#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."],
 '<': ["....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"], '|': ["#", "#", "#", "#", "#", "#", "#"],
 '*': [".", ".", ".", "#", ".", ".", "."], '^': ["..#..", ".###.", "#.#.#", "..#..", "..#..", "..#..", "..#.."],
 'v': ["..#..", "..#..", "..#..", "#.#.#", ".###.", "..#..", "....."], '#': [".#.#.", "#####", ".#.#.", ".#.#.", "#####", ".#.#.", "....."],
}


def t7(f, x, y, s, col=TXT, sh=True, scale=1):
    s = s.upper().replace('X', 'X') if False else s
    cx = x
    for ch in s:
        g = _F.get(ch if ch in _F else ch.upper(), _F['?'])
        for j, row in enumerate(g):
            for i, c in enumerate(row):
                if c == '#':
                    if sh: rect(f, cx + i * scale + scale, y + j * scale + scale, scale, scale, INK)
                    rect(f, cx + i * scale, y + j * scale, scale, scale, col)
        cx += (len(g[0]) + 1) * scale
    return cx - scale


def t7w(s, scale=1):
    return sum((len(_F.get(c if c in _F else c.upper(), _F['?'])[0]) + 1) * scale for c in s) - scale


_ARF = {}


def arfont(size):
    if size not in _ARF:
        _ARF[size] = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size, layout_engine=ImageFont.Layout.RAQM)
    return _ARF[size]


def ar(f, xr, y, s, col=TXT, size=11, sh=True, anchor='r'):
    """pixel Arabic: aliased glyphs drawn straight into the fine grid. xr = right edge (or centre with anchor='c')."""
    fnt = arfont(size)
    l, t, r, b = fnt.getbbox(s, direction='rtl')
    w, h = r - l + 2, b - t + 2
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im); d.fontmode = '1'
    d.text((-l + 1, -t + 1), s, font=fnt, fill=255, direction='rtl')
    m = np.asarray(im) > 128
    x0 = xr - w if anchor == 'r' else xr - w // 2 if anchor == 'c' else xr
    H, W_ = f.shape[:2]
    ys, xs = np.nonzero(m)
    for (yy, xx) in zip(ys, xs):
        X, Y = x0 + xx, y + yy
        if sh and 0 <= Y + 1 < H and 0 <= X + 1 < W_ and not m[min(yy + 1, h - 1), min(xx + 1, w - 1)]: f[Y + 1, X + 1] = INK
    for (yy, xx) in zip(ys, xs):
        X, Y = x0 + xx, y + yy
        if 0 <= Y < H and 0 <= X < W_: f[Y, X] = col
    return x0, w


def arw(s, size=11):
    l, t, r, b = arfont(size).getbbox(s, direction='rtl'); return r - l + 2


def plate(f, x, y, w, h, base=BG, alpha=.94):
    blend_rect(f, x, y, w, h, base, alpha)


def frame(f, x, y, w, h, rp=None, title=None, ar_title=None, alpha=.94, ribbon_w=None):
    """ornate 9-slice: ink outline, bevelled gold rail, kingdom inner line, corner gems, optional ribbon title."""
    rp = rp or R['K']
    plate(f, x, y, w, h, BG, alpha)
    # subtle inner vertical gradient
    for i in range(min(10, h // 3)): blend_rect(f, x + 3, y + 3 + i, w - 6, 1, rp[2], .06 * (1 - i / 10))
    hline(f, x, y, w, INK); hline(f, x, y + h - 1, w, INK); vline(f, x, y, h, INK); vline(f, x + w - 1, y, h, INK)
    hline(f, x + 1, y + 1, w - 2, GOLD[3]); vline(f, x + 1, y + 1, h - 2, GOLD[3])
    hline(f, x + 1, y + h - 2, w - 2, GOLD[1]); vline(f, x + w - 2, y + 1, h - 2, GOLD[1])
    hline(f, x + 2, y + 2, w - 4, GOLD[0]); vline(f, x + 2, y + 2, h - 4, GOLD[0])
    hline(f, x + 3, y + 3, w - 6, rp[1]); vline(f, x + 3, y + 3, h - 6, rp[1]); hline(f, x + 3, y + h - 4, w - 6, rp[0]); vline(f, x + w - 4, y + 3, h - 6, rp[0])
    for (cx, cy) in ((x, y), (x + w - 7, y), (x, y + h - 7), (x + w - 7, y + h - 7)):
        gem(f, cx, cy, rp)
    if title or ar_title:
        ribbon(f, x + w // 2, y - 5, title, ar_title, rp, ribbon_w)


def gem(f, x, y, rp):
    pat = ["..ggg..", ".gGGGg.", "gGkKkGg", "gGKkkGg", "gGkkkgg", ".gggg..", "..gg..."]
    cm = {'g': GOLD[1], 'G': GOLD[3], 'k': rp[2], 'K': rp[4] if len(rp) > 4 else rp[-1]}
    for j, row in enumerate(pat):
        for i, c in enumerate(row):
            if c != '.': put(f, x + i, y + j, cm[c])
    put(f, x + 2, y + 1, GOLD[4])


def ribbon(f, cx, y, title=None, ar_title=None, rp=None, w=None):
    rp = rp or R['K']
    tw = t7w(title) if title else arw(ar_title, 11)
    w = w or tw + 24
    x = cx - w // 2
    h = 13 if title else 15
    # tails
    for i in range(5):
        vline(f, x - 6 + i, y + 3 + abs(2 - i) // 2, h - 3 - abs(2 - i), rp[0])
        vline(f, x + w + 1 + i, y + 3 + abs(2 - i) // 2, h - 3 - abs(2 - i), rp[0])
    rect(f, x - 1, y + 2, w + 2, h - 1, INK)
    rect(f, x, y, w, h, rp[2]); hline(f, x, y, w, rp[3]); hline(f, x, y + 1, w, lit(rp[3], -.05)); hline(f, x, y + h - 1, w, rp[1])
    hline(f, x + 2, y + 2, w - 4, GOLD[2]); hline(f, x + 2, y + h - 3, w - 4, GOLD[1])
    put(f, x + 3, y + h // 2, GOLD[3]); put(f, x + w - 4, y + h // 2, GOLD[3])
    if title: t7(f, cx - tw // 2, y + 3, title, TXT)
    else: ar(f, cx, y + 1, ar_title, TXT, 11, anchor='c')


def button(f, x, y, w, h, label=None, ar_label=None, ic=None, style='ghost', rp=None, size=1):
    rp = rp or R['K']
    if style == 'primary': c = [rp[1], rp[2], rp[3]]
    elif style == 'gold': c = [GOLD[1], GOLD[2], GOLD[3]]
    elif style == 'on': c = [hx('#2e5a3a'), hx('#3e7a4e'), hx('#5a9a68')]
    else: c = [BG2, BG3, hx('#36424f')]
    rect(f, x + 1, y + 1, w, h, INK)
    rect(f, x, y, w, h, c[1]); hline(f, x, y, w, c[2]); vline(f, x, y, h, c[2]); hline(f, x, y + h - 1, w, c[0]); vline(f, x + w - 1, y, h, c[0])
    if style == 'gold': hline(f, x + 1, y + 1, w - 2, GOLD[4])
    tc = INK if style == 'gold' else TXT
    if ar_label:
        if ic: icon(f, x + w - 11, y + (h - 7) // 2, ic)
        ar(f, x + w - (14 if ic else 4) - (w - (14 if ic else 4) - 4 - arw(ar_label)) // 2, y + (h - 14) // 2, ar_label, tc, 11, sh=style != 'gold')
    else:
        lw = (t7w(label) if label else 0) + (10 if ic else 0)
        lx = x + (w - lw) // 2
        if ic: icon(f, lx, y + (h - 7) // 2, ic); lx += 10
        t7(f, lx, y + (h - 7) // 2, label, tc, sh=style != 'gold')


def chip(f, x, y, label, col, ar_label=None, fill=None):
    w = (t7w(label) if label else arw(ar_label)) + 8
    h = 11 if label else 15
    rect(f, x, y, w, h, fill or lit(col, -.55)); hline(f, x, y, w, lit(col, -.3)); rect(f, x, y, 2, h, col)
    if label: t7(f, x + 5, y + 2, label, col if not fill else TXT, sh=False)
    else: ar(f, x + w - 3, y, ar_label, TXT, 11, sh=False)
    return w


def spark(f, x, y, w, h, data, col):
    d = np.array(data, float); d = (d - d.min()) / max(1e-6, d.max() - d.min())
    pts = [(x + int(i * (w - 1) / (len(d) - 1)), y + h - 1 - int(v * (h - 1))) for i, v in enumerate(d)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for xx in range(x0, x1 + 1):
            yy = int(round(y0 + (y1 - y0) * (xx - x0) / max(1, x1 - x0)))
            blend_rect(f, xx, yy + 1, 1, y + h - yy - 1, col, .18)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0)) + 1
        for i in range(n):
            put(f, int(round(x0 + (x1 - x0) * i / max(1, n - 1))), int(round(y0 + (y1 - y0) * i / max(1, n - 1))), col)
    ex, ey = pts[-1]; rect(f, ex - 1, ey - 1, 3, 3, lit(col, .4)); put(f, ex, ey, TXT)


def meter(f, x, y, w, h, frac, col):
    rect(f, x, y, w, h, INK); rect(f, x + 1, y + 1, w - 2, h - 2, hx('#0f141b'))
    fw = max(1, int((w - 2) * frac))
    rect(f, x + 1, y + 1, fw, h - 2, col); hline(f, x + 1, y + 1, fw, lit(col, .35)); hline(f, x + 1, y + h - 2, fw, lit(col, -.25))
    for xx in range(x + 1, x + 1 + fw, 4): put(f, xx, y + h - 2, lit(col, -.35))


PI = {  # 11x11 power icons
 'rain': (["...ggggg...", "..gGGGGGg..", ".gGGgggGGg.", "gGgggggggGg", "ggggggggggg", "..b..b..b..", ".b..b..b...", "....b..b..b", "...b..b..b.", "..........."], {'g': '#8b939a', 'G': '#c8ced4', 'b': '#5aa4e8'}),
 'bolt': (["......yy...", ".....yy....", "....yy.....", "...yyyyy...", "....yYy....", "...yYy.....", "..yYyyyy...", "....yy.....", "...yy......", "..y........"], {'y': '#ffd34a', 'Y': '#fff2b0'}),
 'quake': (["...........", "bbbbbbbbbbb", "bBBBb.bBBBb", "bbbb..bbbbb", "bbbbb.bbbbb", "bbbb..bbbbb", "bbbbb..bbbb", "bbbbbb.bbbb", "...........", "...........", "..........."], {'b': '#8a6a46', 'B': '#b08a5e'}),
 'meteor': (["y..........", ".yo........", "..ooo......", "...oor.....", "....rrrr...", ".....rRRr..", "....rRRRRr.", "....rRRRRr.", ".....rRRr..", "......rr...", "..........."], {'y': '#fff2b0', 'o': '#f49a3c', 'r': '#7a3a2a', 'R': '#b8582e'}),
 'fire': (["....y......", "...yo..y...", "...oo.yo...", "..ooo.oo...", "..oroooo.o.", ".oorrooooo.", ".orrRrroor.", ".orRRRrrr..", "..rRRRRr...", "...rrrr....", "..........."], {'y': '#ffe27a', 'o': '#f49a3c', 'r': '#d5452d', 'R': '#fff2b0'}),
 'drought': (["....yyy....", "..y.yYy.y..", "...yyyyy...", "..yyYYYyy..", "...yyyyy...", "..y.yyy.y..", "...........", "ddddddddddd", "dDd.dDd.dDd", "dd.dd.dd.dd", "..........."], {'y': '#ffb84a', 'Y': '#fff0a0', 'd': '#9a7a4a', 'D': '#c4a06a'}),
 'human': (["....sss....", "...sssss...", "...sSsss...", "....sss....", "..ccccccc..", ".cccccccc..", ".c.ccccc.c.", "...cc.cc...", "...cc.cc...", "...bb.bb..."], {'s': '#d4a882', 'S': '#f0d0b4', 'c': '#3a62a0', 'b': '#3a2a1e'}),
 'sheep': (["...........", "..wwwwww...", ".wWWwwwwwkk", "wWwwwwwwwkk", "wwwwwwwwwk.", ".wwwwwww...", "..k.k.k.k..", "..k.k.k.k..", "...........", "...........", "..........."], {'w': '#e4e0d4', 'W': '#ffffff', 'k': '#2e2721'}),
 'tree': (["....ggg....", "..ggGGgg...", ".gGGggggg..", "ggggggggg..", ".ggggggggg.", "..ggggggg..", "....bb.....", "....bb.....", "...bbbb....", "..........."], {'g': '#4a8545', 'G': '#8fbd5c', 'b': '#6b4c34'}),
 'bless': ([".....y.....", "..y..y..y..", "...y.y.y...", "....yyy....", "yyyyyWyyyyy", "....yyy....", "...y.y.y...", "..y..y..y..", ".....y.....", "..........."], {'y': '#ecc25c', 'W': '#ffffff'}),
 'plague': (["...ggggg...", "..gGgggGg..", ".ggkgggkgg.", ".gggggggg..", "..ggkkkgg..", "...ggggg...", "..g.g.g.g..", ".g.......g.", "...........", "..........."], {'g': '#7aa83a', 'G': '#b8e06a', 'k': '#1e2a12'}),
 'inspire': (["....yyy....", "...yYYYy...", "..yYYwYYy..", "..yYYYYYy..", "...yYYYy...", "....yyy....", "....ggg....", "....ggg....", ".....g.....", "..........."], {'y': '#ffd34a', 'Y': '#fff2b0', 'w': '#ffffff', 'g': '#8b939a'}),
 'crown': (["...........", "y...y...y..", "yy.yyy.yy..", "yyyyyyyyy..", "yrryyyrry..", "yyyyyyyyy..", "ddddddddd..", "...........", "...........", "..........."], {'y': '#ecc25c', 'r': '#c4563d', 'd': '#a8752a'}),
 'war': (["w.........w", ".w.......w.", "..w.....w..", "...w...w...", "....w.w....", ".....w.....", "....g.g....", "...g...g...", "..b.....b..", ".b.......b."], {'w': '#d0d6da', 'g': '#c8a23a', 'b': '#6b4c34'}),
 'peace': (["...........", "..ww.......", ".wWww......", "wwwwww.....", ".wwwwwwww..", "..wwwwwwwwg", "...wwwww.gg", "....ww...g.", "...........", "..........."], {'w': '#e8eef6', 'W': '#ffffff', 'g': '#6c9e4c'}),
 'eye': (["...........", "...wwwww...", ".wwbbbbbww.", "wwbbBkbbbww", "wbbbkkkbbbw", "wwbbbkbbbww", ".wwbbbbbww.", "...wwwww...", "...........", "..........."], {'w': '#e8eef6', 'b': '#4579bb', 'B': '#9cc0e8', 'k': '#141a22'}),
 'book': (["...........", ".bbbb.bbbb.", ".bWWb.bWWb.", ".bWWb.bWWb.", ".bWWb.bWWb.", ".bWWb.bWWb.", ".bbbbbbbbb.", "....bbb....", "...........", "..........."], {'b': '#8a3a30', 'W': '#f3e6c8'}),
}


def picon(f, x, y, name, scale=1):
    rows, cm = PI[name]
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c != '.': rect(f, x + i * scale, y + j * scale, scale, scale, hx(cm[c]))


def portrait(f, x, y, culture, cls, age, gender, seed, rp=None, sc=2):
    from people import person2
    rp = rp or R['K']
    c = np.zeros((28, 16, 3), np.uint8); c[:] = lit(rp[1], -.25)
    for j in range(28): c[j, :] = lit(rp[1], -.5 + j * .012)
    person2(c, 0, 4, culture, cls, age, gender, 0, seed=seed, shadow=False)
    crop = c[2:20]
    img = np.asarray(Image.fromarray(crop).resize((16 * sc, 18 * sc), Image.NEAREST))
    rect(f, x - 2, y - 2, 16 * sc + 4, 18 * sc + 4, INK); rect(f, x - 1, y - 1, 16 * sc + 2, 18 * sc + 2, GOLD[2])
    hline(f, x - 1, y - 1, 16 * sc + 2, GOLD[3]); vline(f, x - 1, y - 1, 18 * sc + 2, GOLD[3])
    f[y:y + 18 * sc, x:x + 16 * sc] = img
