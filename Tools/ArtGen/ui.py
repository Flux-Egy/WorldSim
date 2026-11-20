"""UI mockups: FAR / MID / CLOSE zoom + city panel + progress tree. Phone screen = 240x520 fine px, shown x3."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from buildings import BUILD, ERAS
from catalog import measure, fine_fx
from chars import person
import scenes

PW, PH = 240, 520
GOOD, BAD, ACC, TXT, DIM = UI['good'], UI['bad'], UI['acc'], UI['txt'], UI['dim']
KR = {'K': R['K'], 'blue': K2['blue'], 'violet': K2['violet'], 'gold': K2['gold']}


# ---------------------------------------------------------------- shared chrome
def top_hud(f, year, era, alert=None):
    panel(f, 0, 0, PW, 15, .92, edge=False)
    hline(f, 0, 15, PW, UI['edge'])
    icon(f, 3, 4, 'globe')
    x = text(f, 13, 5, 'YEAR ' + str(year), TXT)
    rect(f, x + 3, 3, text_w(era) + 6, 9, R['K'][1]); text(f, x + 6, 5, era, TXT)
    # speed controls
    for i, lab in enumerate(['||', '>', '>>']):
        bx = PW - 46 + i * 15
        rect(f, bx, 3, 13, 9, UI['bg2'] if i != 1 else R['K'][1])
        text(f, bx + 7 - text_w(lab) // 2, 5, lab, TXT if i == 1 else DIM)
    if alert:
        w = text_w(alert) + 16
        panel(f, (PW - w) // 2, 19, w, 11, .9)
        rect(f, (PW - w) // 2, 19, 3, 11, ACC)
        text(f, (PW - w) // 2 + 8, 22, alert, TXT)


DOCK = [('globe', 'NATURE'), ('pop', 'PEOPLE'), ('flag', 'NATIONS'), ('know', 'PROGRESS'), ('storm', 'POWERS')]


def dock(f, active=0):
    y0 = PH - 38
    panel(f, 0, y0, PW, 38, .94, edge=False); hline(f, 0, y0, PW, UI['edge'])
    bw = PW // len(DOCK)
    for i, (ic, lab) in enumerate(DOCK):
        bx = i * bw
        if i == active:
            rect(f, bx + 3, y0 + 3, bw - 6, 32, UI['bg2']); hline(f, bx + 3, y0 + 3, bw - 6, ACC)
        icon(f, bx + bw // 2 - 7, y0 + 7, ic, 2)
        text(f, bx + bw // 2 - text_w(lab) // 2, y0 + 25, lab, TXT if i == active else DIM)


def zoom_rail(f, level):
    x, y = PW - 12, 150
    panel(f, x - 3, y - 4, 12, 66, .85)
    for i, lab in enumerate(['C', 'M', 'F']):
        yy = y + i * 21
        rect(f, x, yy, 6, 14, R['K'][2] if 2 - i == level else UI['bg2'])
        text(f, x + 2, yy + 5, lab, TXT if 2 - i == level else DIM)


def crest(f, x, y, rp=None):
    rp = rp or R['K']
    rows = ["..KKK..", ".KkkkK.", "KkLkLkK", "KkkLkkK", ".KkkkK.", "..KKK.."]
    cm = {'K': rp[0], 'k': rp[2], 'L': hx('#f3e6c8')}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.': put(f, x + i, y + j, cm[ch])


def tag(f, x, y, name, sub=None, rp=None, center=True):
    w = text_w(name) + 12 + (text_w(sub) + 4 if sub else 0)
    if center: x -= w // 2
    panel(f, x, y, w, 9, .82)
    crest(f, x + 1, y + 1, rp)
    ex = text(f, x + 10, y + 2, name, TXT)
    if sub: text(f, ex + 3, y + 2, sub, ACC)
    return w


# ---------------------------------------------------------------- A: FAR ZOOM
def world_map(seed=4):
    W_, H_ = PW, PH
    n = smooth_noise(W_, H_, 70, seed) * .55 + smooth_noise(W_, H_, 24, seed + 1) * .3 + smooth_noise(W_, H_, 7, seed + 9) * .15
    yy, xx = np.mgrid[0:H_, 0:W_]
    edge = np.minimum.reduce([xx, W_ - xx, yy, H_ - yy]) / 50.0
    n = n - .2 * np.clip(1 - edge, 0, 1)
    m2 = smooth_noise(W_, H_, 40, seed + 2); m3 = smooth_noise(W_, H_, 12, seed + 3); m4 = smooth_noise(W_, H_, 5, seed + 4)
    rnd = np.random.default_rng(seed).random((H_, W_))
    land = n > .5
    a = np.zeros((H_, W_, 3), np.uint8)
    d = .5 - n
    a[:] = C['water'][0]
    a[(d < .1)] = C['water'][1]; a[(d < .05)] = C['water'][2]; a[(d < .02)] = C['water'][3]
    a[~land & (rnd > .985)] = C['water'][2]
    lat = yy / H_
    g = grass_ground(W_, H_, seed + 7)
    a[land] = g[land]
    forest = land & (m3 > .55)
    a[forest] = R['leaf'][2]; a[forest & (rnd > .55)] = R['leaf'][1]; a[forest & (rnd > .92)] = R['leaf'][3]
    desert = land & (m2 > .64) & (lat > .3) & (lat < .78)
    a[desert] = hx('#d9c08a'); a[desert & (rnd > .8)] = hx('#c9ad78'); a[desert & (rnd > .97)] = hx('#e8d6a6')
    mtn = land & (n + (m4 - .5) * .08 > .72)
    a[mtn] = R['stone'][1]; a[mtn & (m4 > .5)] = R['stone'][2]; a[mtn & (m4 > .68)] = R['stone'][3]
    a[mtn & (n > .8) & (m4 > .45)] = hx('#f2f4f6')
    snow = land & ((lat < .07) | (lat > .93))
    a[snow] = hx('#e8eef2'); a[snow & (rnd > .8)] = hx('#d2dbe1')
    coast = land & (n < .512)
    a[coast & ~snow] = hx('#dcc896')
    return a, land


def far_screen():
    a, land = world_map()
    rng = random.Random(2)
    caps = [(70, 150, 'K', 'QARNAH', 'MEDIEVAL', 'castle'), (170, 210, 'blue', 'VELMORA', 'INDUSTRIAL', 'factory'),
            (80, 340, 'violet', 'SHAARIN', 'ANCIENT', 'palace'), (175, 400, 'gold', 'OKKU', 'STONE', 'tent')]
    # snap to land
    ys, xs = np.nonzero(land)
    caps2 = []
    for (x, y, k, n, e, t) in caps:
        i = np.argmin((xs - x) ** 2 + (ys - y) ** 2); caps2.append((int(xs[i]), int(ys[i]), k, n, e, t))
    kid = -np.ones(land.shape, int)
    yy, xx = np.mgrid[0:PH, 0:PW]
    dist = np.stack([np.hypot(xx - x, yy - y) for (x, y, *_r) in caps2])
    jitter = (smooth_noise(PW, PH, 16, 77) - .5) * 34
    dist = dist + jitter[None]
    near = dist.argmin(0); dmin = dist.min(0)
    kid[land & (dmin < 52)] = near[land & (dmin < 52)]
    keys = [c[2] for c in caps2]
    for i, k in enumerate(keys):
        m = kid == i
        blend_mask(a, m, KR[k][2], .26)
        b = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        dash = b & (((xx + yy) // 2) % 2 == 0)
        a[dash] = KR[k][3]; a[b & ~dash] = KR[k][1]
    f = a.copy()
    towns = []
    names = ['IRONVALE', 'TALEM', 'RUSA', 'BEKA', 'MIRO', 'DUNE', 'KESH', 'ALBA']
    for i, (x, y, k, n, e, t) in enumerate(caps2):
        for j in range(2):
            for _ in range(400):
                tx, ty = x + rng.randint(-40, 40), y + rng.randint(-40, 40)
                pts = [(c[0], c[1]) for c in caps2] + [(t[0], t[1]) for t in towns]
                if 20 <= tx < PW - 20 and 30 <= ty < PH - 80 and kid[ty, tx] == i and all(abs(tx - px) > 26 or abs(ty - py) > 16 for px, py in pts):
                    towns.append((tx, ty, k, names[(i * 2 + j) % len(names)])); break
    for (tx, ty, k, n) in towns:
        rect(f, tx - 2, ty - 2, 5, 5, KR[k][0]); rect(f, tx - 1, ty - 1, 3, 3, KR[k][3]); put(f, tx, ty, TXT)
        w = text_w(n) + 4
        blend_rect(f, tx - w // 2, ty + 4, w, 7, UI['bg'], .7); text(f, tx - w // 2 + 2, ty + 5, n, TXT)
    for (x, y, k, n, e, t) in caps2:
        icon_era(f, x - 5, y - 9, t, KR[k])
        tag(f, x, y + 4, n, e, KR[k])
    # roads between capitals (trade routes)
    for (x1, y1, *_a), (x2, y2, *_b) in [(caps2[0], caps2[1]), (caps2[0], caps2[2])]:
        L = int(math.hypot(x2 - x1, y2 - y1))
        for t in range(0, L, 3):
            px, py = int(x1 + (x2 - x1) * t / L), int(y1 + (y2 - y1) * t / L)
            if land[py, px]: put(f, px, py, hx('#c9a35a'))
    top_hud(f, 1342, 'MEDIEVAL', 'COAL FOUND NEAR IRONVALE')
    zoom_rail(f, 2)
    # legend
    panel(f, 4, PH - 76, 106, 34, .85)
    for i, (k, n, e) in enumerate([('K', 'QARNAH', 'MEDIEVAL'), ('blue', 'VELMORA', 'INDUSTRIAL'), ('violet', 'SHAARIN', 'ANCIENT'), ('gold', 'OKKU', 'STONE')]):
        y = PH - 72 + i * 7
        rect(f, 8, y, 5, 5, KR[k][2]); text(f, 16, y, n, TXT); text(f, 52, y, e, DIM)
    dock(f, 2)
    return f


def icon_era(f, x, y, t, rp):
    """10x9 map pin showing what era a nation is in."""
    shadow_ell(f, x + 6, y + 9, 5, 1.4, .4)
    rect(f, x, y, 11, 9, UI['bg']); rect(f, x + 1, y + 1, 9, 7, rp[1]); hline(f, x + 1, y + 1, 9, rp[3])
    if t == 'castle':
        rect(f, x + 2, y + 4, 7, 4, W['fort'][2]); for_ = [put(f, x + 2 + i * 2, y + 3, W['fort'][2]) for i in range(4)]; rect(f, x + 5, y + 6, 1, 2, UI['bg'])
    elif t == 'factory':
        rect(f, x + 2, y + 5, 7, 3, W['brick'][2]); vline(f, x + 7, y + 2, 4, W['brick'][2]); put(f, x + 3, y + 4, W['brick'][2]); put(f, x + 5, y + 4, W['brick'][2])
    elif t == 'palace':
        for i in range(3): hline(f, x + 2 + i, y + 7 - i * 2, 7 - 2 * i, R['stone'][3]); hline(f, x + 2 + i, y + 6 - i * 2, 7 - 2 * i, R['stone'][4])
    elif t == 'tent':
        for i in range(5): hline(f, x + 5 - i // 2 - (i % 2) * 0, y + 3 + i, 1 + i, R['hide'][3])
    put(f, x + 5, y + 9, UI['bg'])


# ---------------------------------------------------------------- B: MID ZOOM
def place(a, occ, items, rng, cx, cy, W_, H_, pref):
    fx = []
    dims = [(be, cat, measure(BUILD[be][cat])) for (be, cat) in items]
    dims.sort(key=lambda t: -(t[2][1] - t[2][0]) * (t[2][3] - t[2][2]))
    placed = []
    for (be, cat, (x0, x1, y0, y1)) in dims:
        best = None
        cands = [(ax, ab) for ax in range(2 - x0, W_ - 2 - x1, 2) for ab in range(2 - y0, H_ - 2 - y1, 2)]
        rng.shuffle(cands)
        for (ax, ab) in cands:
            bx0, bx1, by0, by1 = ax + x0, ax + x1, ab + y0, ab + y1
            if occ[max(by0 - 1, 0):by1 + 2, max(bx0 - 1, 0):bx1 + 2].any(): continue
            sc = pref(be, cat, (bx0 + bx1) / 2, (by0 + by1) / 2) + rng.random() * 8
            if best is None or sc < best[0]: best = (sc, ax, ab)
        if best is None: continue
        _, ax, ab = best
        occ[ab + y0 - 1:ab + y1 + 2, ax + x0 - 1:ax + x1 + 2] = True
        placed.append((ab, ax, be, cat))
    placed.sort()
    for (ab, ax, be, cat) in placed:
        fx += BUILD[be][cat](a, ax, ab, ax + ab) or []
    return fx, placed


def mid_screen():
    W_, H_ = PW, PH
    rng = random.Random(11)
    a = grass_ground(W_, H_, 21)
    occ = np.zeros((H_, W_), bool)
    occ[:18, :] = True; occ[H_ - 40:, :] = True
    # river
    for y in range(H_):
        cx = int(30 + 10 * math.sin(y / 40))
        for x in range(cx - 5, cx + 6):
            a[y, x] = C['water'][2] if abs(x - cx) < 4 else C['water'][3]
            occ[y, x] = True
        if y % 9 == 0: put(a, cx - 1, y, C['water'][4])
    # road grid: old town cobble (north), industrial district brick-grey (south)
    for ry in (120, 250, 380):
        k = 'cobble'
        for x in range(36, W_):
            for t in range(3): a[ry + t, x] = C['cobble'][1] if (x // 2 + t) % 2 else C['cobble'][2]; occ[ry + t, x] = True
    for rx in (90, 160, 222):
        for y in range(18, H_ - 40):
            for t in range(3): a[y, rx + t] = C['cobble'][1] if (y // 2 + t) % 2 else C['cobble'][2]; occ[y, rx + t] = True
    for y in (120, 250, 380):
        for x in range(24, 38): a[y:y + 3, x] = C['wood'][1]  # bridges
    # rail line south
    for x in range(36, W_):
        put(a, x, 318, R['metal'][3]); put(a, x, 320, R['metal'][3])
        if x % 2 == 0: put(a, x, 319, C['wood'][0])
        occ[317:322, x] = True
    items = [(2, 'seat'), (3, 'seat')] + [(2, 'poor')] * 7 + [(2, 'rich')] * 3 + [(2, 'commerce')] * 2 + [(2, 'research'), (2, 'energy'), (2, 'military'), (2, 'defense')] + \
            [(3, 'industry')] * 3 + [(3, 'poor')] * 10 + [(3, 'mine'), (3, 'energy'), (3, 'commerce'), (3, 'commerce'), (3, 'rich'), (3, 'rich'), (3, 'research'), (3, 'military'),
             (2, 'mine'), (2, 'industry')] + [(2, 'poor')] * 5

    def pref(cat, x, y):
        return 0
    def pref2(be, cat, x, y):
        if cat == 'mine': t = (200, 450)
        elif be == 2: t = (140, 170)
        elif cat in ('industry', 'energy'): t = (150, 400)
        else: t = (150, 300)
        return math.hypot(x - t[0], y - t[1])
    fx, placed = place(a, occ, items, rng, 130, 200, W_, H_, pref2)
    for _ in range(40):
        x, y = rng.randint(40, W_ - 6), rng.randint(22, H_ - 48)
        if not occ[max(y - 4, 0):y + 7, max(x - 4, 0):x + 6].any():
            tree(a, x, y, rng.choice([3, 4]), x + y); occ[max(y - 4, 0):y + 7, max(x - 4, 0):x + 6] = True
    f = a.copy()
    fine_fx(f, [e for e in fx if e[0] in ('smoke', 'steam')], 1)
    # LOD: people become moving dots on roads
    for _ in range(140):
        ry = rng.choice([121, 251, 381]); x = rng.randint(40, W_ - 2)
        put(f, x, ry, rng.choice([R['K'][3], hx('#e8eef6'), hx('#3f5f86'), hx('#d6b04b')]))
        rx = rng.choice([91, 161, 223]); y = rng.randint(20, H_ - 42)
        put(f, rx, y, rng.choice([R['K'][3], hx('#e8eef6'), hx('#3f5f86')]))
    for x in range(60, 200, 14):
        rect(f, x, 316, 4, 2, W['brick'][1])  # train wagons
    rect(f, 200, 316, 6, 2, hx('#2b2c30'))
    # district labels
    tag(f, 130, 60, 'QARNAH', 'POP 5200')
    for (x, y, n) in [(150, 200, 'OLD TOWN'), (150, 340, 'MILL DISTRICT'), (200, 470, 'COAL FIELDS'), (34, 300, 'RIVER ESK')]:
        w = text_w(n) + 6
        blend_rect(f, x - w // 2, y, w, 8, UI['bg'], .7); text(f, x - w // 2 + 3, y + 2, n, ACC)
    # tooltip on a building
    tx, ty = 40, 436
    panel(f, tx, ty, 108, 30, .9)
    icon(f, tx + 4, ty + 4, 'gear'); text(f, tx + 14, ty + 5, 'FACTORY  LV 2', TXT)
    text(f, tx + 4, ty + 14, '34 WORKERS  +12 GOODS', DIM)
    text(f, tx + 4, ty + 21, 'NEEDS: COAL 8/DAY', ACC)
    top_hud(f, 1402, 'INDUSTRIAL')
    zoom_rail(f, 1)
    dock(f, 1)
    return f


# ---------------------------------------------------------------- C: CLOSE + CITY PANEL
def close_screen():
    sv = (scenes.SW, scenes.SH, scenes.CXC, scenes.RY)
    scenes.SW, scenes.SH, scenes.CXC, scenes.RY = 120, 136, 60, 80
    a, bocc, fx = scenes.build_scene(2, 1, seed=5)
    f2 = upscale(a, 2)
    fine_fx(f2, fx, 2)
    scenes.populate(f2, bocc, 2, 1, seed=5)
    scenes.SW, scenes.SH, scenes.CXC, scenes.RY = sv
    f = np.zeros((PH, PW, 3), np.uint8)
    f[:] = f2[:PH, :PW] if f2.shape[0] >= PH else np.pad(f2, ((0, PH - f2.shape[0]), (0, 0), (0, 0)))[:PH, :PW]
    # selection ring on the seat
    m = ellipse_mask(f.shape[:2], 121, 160, 36, 10) & ~ellipse_mask(f.shape[:2], 121, 160, 34.5, 9)
    f[m] = ACC
    top_hud(f, 1342, 'MEDIEVAL')
    # ---- bottom sheet
    y0 = 214
    panel(f, 0, y0, PW, PH - y0, .96, edge=False)
    rect(f, PW // 2 - 12, y0 + 3, 24, 2, UI['edge'])
    crest(f, 6, y0 + 10)
    text(f, 16, y0 + 9, 'QARNAH', TXT, 2)
    cx = 16 + text_w('QARNAH', 2) + 6
    for lab, col in (('TOWN', UI['bg2']), ('CAPITAL', R['K'][1])):
        rect(f, cx, y0 + 10, text_w(lab) + 6, 9, col); text(f, cx + 3, y0 + 12, lab, TXT); cx += text_w(lab) + 9
    text(f, 6, y0 + 24, 'MEDIEVAL ERA  -  STAGE 3/4 FLOURISHING', DIM)
    for i in range(4):
        rect(f, 6 + i * 57, y0 + 32, 53, 3, ACC if i < 3 else UI['bg2'])
    # leader card
    ly = y0 + 41
    panel(f, 4, ly, PW - 8, 40, .9, col=UI['bg2'])
    rect(f, 7, ly + 3, 26, 34, hx('#0c1016'))
    port = np.zeros((15, 9, 3), np.uint8); port[:] = hx('#2a3542')
    person(port, 0, 0, 2, 'chief', 0, seed=3, shadow=False)
    pimg = np.asarray(Image.fromarray(port).resize((18, 30), Image.NEAREST))
    f[ly + 5:ly + 35, 11:29] = pimg
    text(f, 38, ly + 4, 'LORD ORAN', TXT, 2)
    text(f, 38, ly + 17, 'LEADER  -  RULES 14 YRS', DIM)
    tx = 38
    for t, col in (('WISE', GOOD), ('AMBITIOUS', ACC), ('GREEDY', BAD)):
        rect(f, tx, ly + 26, text_w(t) + 6, 9, lit(col, -.55)); text(f, tx + 3, ly + 28, t, col); tx += text_w(t) + 9
    # population classes
    py = ly + 46
    text(f, 6, py, 'POPULATION 1300', TXT)
    for i, (lab, v, frac, col) in enumerate((('POOR', 820, .63, hx('#a8a39a')), ('MIDDLE', 390, .3, ACC), ('RICH', 90, .07, C['gold']))):
        yy = py + 9 + i * 8
        text(f, 6, yy, lab, DIM); bar(f, 34, yy, 150, 5, frac, col); text(f, 190, yy, str(v), TXT)
    # resources
    ry = py + 37
    text(f, 6, ry, 'RESOURCES', TXT)
    res = [('food', '1240', GOOD), ('wood', '860', TXT), ('stone', '540', TXT), ('iron', '210', TXT),
           ('copper', '95', TXT), ('coal', 'NEW!', ACC), ('gold', '120', TXT), ('know', '+8/D', hx('#9cc0e8'))]
    for i, (ic, v, col) in enumerate(res):
        bx, by = 6 + (i % 4) * 58, ry + 9 + (i // 4) * 15
        rect(f, bx, by, 54, 13, UI['bg2']); icon(f, bx + 3, by + 3, ic); text(f, bx + 13, by + 4, v, col)
    # next era
    ny = ry + 42
    panel(f, 4, ny, PW - 8, 66, .9, col=hx('#1a2016'))
    text(f, 9, ny + 5, 'NEXT ERA: INDUSTRIAL', ACC)
    text(f, PW - 30, ny + 5, '62%', TXT)
    bar(f, 9, ny + 13, PW - 18, 4, .62, ACC)
    checks = [(True, 'COAL DEPOSIT DISCOVERED'), (True, 'IRON MINE LEVEL 2'), (False, 'RESEARCH STEAM ENGINE  62%'), (False, 'POPULATION 1500  (1300)')]
    for i, (ok, t) in enumerate(checks):
        yy = ny + 22 + i * 10
        rect(f, 9, yy - 1, 7, 7, lit(GOOD if ok else BAD, -.55)); text(f, 11, yy, '@' if ok else '~', GOOD if ok else BAD)
        text(f, 20, yy, t, TXT if ok else DIM)
    # actions
    by = ny + 70
    for i, lab in enumerate(['BUILDINGS', 'LAWS', 'RESEARCH']):
        bx = 4 + i * 78
        rect(f, bx, by, 74, 14, R['K'][1] if i == 2 else UI['bg2']); hline(f, bx, by, 74, R['K'][3] if i == 2 else UI['edge'])
        text(f, bx + 37 - text_w(lab) // 2, by + 5, lab, TXT)
    dock(f, 1)
    return f


# ---------------------------------------------------------------- D: PROGRESS TREE
def tree_screen():
    f = np.zeros((PH, PW, 3), np.uint8)
    bg = grass_ground(PW, PH, 30)
    f[:] = (bg * .35 + np.array(UI['bg']) * .65).astype(np.uint8)
    top_hud(f, 1342, 'MEDIEVAL')
    text(f, 6, 22, 'PROGRESS', TXT, 2); text(f, 80, 26, 'QARNAH', ACC)
    # tabs
    for i, lab in enumerate(['ERAS', 'RESEARCH', 'DISCOVERIES']):
        bx = 6 + i * 76
        rect(f, bx, 36, 72, 12, R['K'][1] if i == 1 else UI['bg2']); text(f, bx + 36 - text_w(lab) // 2, 40, lab, TXT)
    # era timeline
    ey = 56
    names = ['STONE', 'ANCIENT', 'MEDIEV.', 'INDUST.', 'MODERN', 'FUTURE']
    for i, n in enumerate(names):
        bx = 4 + i * 39
        state = 'done' if i < 2 else ('cur' if i == 2 else 'lock')
        col = {'done': hx('#24402a'), 'cur': R['K'][1], 'lock': UI['bg2']}[state]
        rect(f, bx, ey, 36, 20, col)
        if state == 'cur': hline(f, bx, ey, 36, ACC)
        text(f, bx + 18 - text_w(n) // 2, ey + 4, n, TXT if state != 'lock' else DIM)
        text(f, bx + 18 - 2, ey + 12, '@' if state == 'done' else ('3/4' if state == 'cur' else '~'), GOOD if state == 'done' else (ACC if state == 'cur' else DIM)) if state != 'cur' else text(f, bx + 18 - text_w('3/4') // 2, ey + 12, '3/4', ACC)
        if i < 5: hline(f, bx + 36, ey + 10, 3, UI['edge'])
    # research nodes
    nodes = [  # col,row, icon, name, state, pct
        (0, 0, 'food', 'FARMING II', 'done', 1), (1, 0, 'stone', 'MASONRY', 'done', 1), (2, 0, 'iron', 'IRON WORK', 'done', 1),
        (0, 1, 'gold', 'GUILDS', 'done', 1), (1, 1, 'tree', 'MILLS', 'done', 1), (2, 1, 'know', 'PRINTING', 'prog', .4),
        (0, 2, 'sword', 'GUNPOWDER', 'lock', 0), (1, 2, 'crown', 'BANKING', 'lock', 0), (2, 2, 'gear', 'STEAM ENGINE', 'sel', .62)]
    ny0 = 86
    pos = {}
    for (c, r, ic, n, st, p) in nodes:
        x, y = 14 + c * 78, ny0 + r * 50
        pos[(c, r)] = (x, y)
    links = [((0, 0), (0, 1)), ((1, 0), (1, 1)), ((2, 0), (2, 1)), ((0, 1), (0, 2)), ((0, 1), (1, 2)), ((1, 1), (2, 2)), ((2, 0), (2, 2))]
    for (s, e) in links:
        (x1, y1), (x2, y2) = pos[s], pos[e]
        sx, sy, ex, ey2 = x1 + 25, y1 + 30, x2 + 25, y2
        midy = (sy + ey2) // 2
        vline(f, sx, sy, midy - sy, UI['edge']); hline(f, min(sx, ex), midy, abs(ex - sx) + 1, UI['edge']); vline(f, ex, midy, ey2 - midy, UI['edge'])
    for (c, r, ic, n, st, p) in nodes:
        x, y = pos[(c, r)]
        col = {'done': hx('#24402a'), 'prog': hx('#3a3420'), 'lock': UI['bg2'], 'sel': R['K'][1]}[st]
        rect(f, x, y, 50, 30, col)
        edge = {'done': GOOD, 'prog': ACC, 'lock': UI['edge'], 'sel': ACC}[st]
        hline(f, x, y, 50, edge); hline(f, x, y + 29, 50, edge); vline(f, x, y, 30, edge); vline(f, x + 49, y, 30, edge)
        if st == 'lock': icon(f, x + 18, y + 4, 'lock', 2)
        else: icon(f, x + 18, y + 4, ic, 2)
        if st in ('prog', 'sel'): bar(f, x + 3, y + 25, 44, 2, p, ACC)
        if st == 'done': text(f, x + 43, y + 3, '@', GOOD)
        text(f, x + 25 - text_w(n) // 2, y + 33, n, TXT if st != 'lock' else DIM)
    # detail card
    dy = ny0 + 152
    panel(f, 4, dy, PW - 8, 150, .95, col=hx('#1f1814'))
    hline(f, 4, dy, PW - 8, ACC)
    icon(f, 9, dy + 6, 'gear', 2)
    text(f, 28, dy + 6, 'STEAM ENGINE', TXT, 2)
    text(f, 28, dy + 18, 'UNLOCKS THE INDUSTRIAL ERA', ACC)
    bar(f, 9, dy + 28, PW - 18, 4, .62, ACC); text(f, PW - 30, dy + 34, '62%', TXT)
    text(f, 9, dy + 36, 'REQUIRES', DIM)
    reqs = [(True, 'coal', 'COAL DEPOSIT FOUND'), (True, 'pick', 'IRON MINE LEVEL 2'), (True, 'know', 'UNIVERSITY BUILT'), (False, 'pop', 'SCHOLARS 12 / 20')]
    for i, (ok, ic, t) in enumerate(reqs):
        yy = dy + 46 + i * 11
        icon(f, 9, yy - 1, ic); text(f, 20, yy, t, TXT if ok else DIM)
        text(f, PW - 16, yy, '@' if ok else '~', GOOD if ok else BAD)
    text(f, 9, dy + 94, 'UNLOCKS', DIM)
    unl = [('gear', 'FACTORY'), ('house', 'TERRACES'), ('energy', 'COAL PLANT'), ('flag', 'RAILWAY')]
    for i, (ic, t) in enumerate(unl):
        bx = 9 + i * 57
        rect(f, bx, dy + 102, 53, 26, UI['bg2']); icon(f, bx + 19, dy + 104, ic, 2); text(f, bx + 26 - text_w(t) // 2, dy + 121, t, TXT)
    rect(f, 9, dy + 132, PW - 18, 13, R['K'][1]); hline(f, 9, dy + 132, PW - 18, R['K'][3])
    text(f, PW // 2 - text_w('FOCUS RESEARCH') // 2, dy + 136, 'FOCUS RESEARCH', TXT)
    vy = dy + 156
    text(f, 6, vy, 'DISCOVERED DEPOSITS', TXT)
    deps = [('coal', 'COAL', 'IRONVALE HILLS', 'NEW'), ('iron', 'IRON', 'TALEM RIDGE', 'LV2'), ('copper', 'COPPER', 'QARNAH PIT', 'LOW'),
            ('lock', '???', '3 HIDDEN DEPOSITS - SEND EXPLORERS', '')]
    for i, (ic, n, loc, st) in enumerate(deps):
        yy = vy + 9 + i * 11
        rect(f, 4, yy - 2, PW - 8, 10, UI['bg2'])
        icon(f, 7, yy - 1, ic); text(f, 18, yy, n, TXT if ic != 'lock' else DIM); text(f, 50, yy, loc, DIM)
        if st: text(f, PW - 10 - text_w(st), yy, st, ACC if st == 'NEW' else GOOD)
    text(f, 6, PH - 50, 'SCHOLARS 12   +8 KNOWLEDGE / DAY', DIM)
    dock(f, 3)
    return f


def compose(screens, labels, path, S=3):
    TH = 64
    imgs = [Image.fromarray(s).resize((PW * S, PH * S), Image.NEAREST) for s in screens]
    gap = 24
    out = Image.new('RGB', (len(imgs) * (PW * S + gap) + gap, PH * S + TH + gap), (18, 22, 28))
    d = ImageDraw.Draw(out)
    fb = ImageFont.load_default(size=30)
    for i, (im, lab) in enumerate(zip(imgs, labels)):
        x = gap + i * (PW * S + gap)
        d.text((x, TH // 2), lab, fill=(240, 228, 200), font=fb, anchor='lm')
        d.rounded_rectangle([x - 6, TH - 6, x + PW * S + 6, TH + PH * S + 6], 18, outline=(60, 70, 84), width=4)
        out.paste(im, (x, TH))
    out.save(path); print(path, out.size)


if __name__ == '__main__':
    compose([far_screen(), mid_screen()], ['FAR ZOOM: WORLD & NATIONS', 'MID ZOOM: CITY DISTRICTS'], 'ui_zoom_far_mid.png')
    compose([close_screen(), tree_screen()], ['CLOSE ZOOM + CITY PANEL', 'PROGRESS / RESEARCH'], 'ui_city_progress.png')
