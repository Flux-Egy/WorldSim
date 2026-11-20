"""Same era (medieval), three cultures -> three different city patterns, materials, palettes, nature."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from buildings import BUILD, fence, flag, banner
from houses import house, W, R
from catalog import fine_fx
from chars import person, sheep, cow, horse, deer, wolf, chicken, camel

SENT = (1, 254, 3)


def measure_fn(fn):
    a = np.zeros((110, 140, 3), np.uint8); a[:] = SENT
    fn(a, 50, 80)
    ys, xs = np.nonzero(np.any(a != SENT, axis=2))
    return int(xs.min()) - 50, int(xs.max()) - 50, int(ys.min()) - 80, int(ys.max()) - 80


def pine(a, x, y, s, seed, snow=False):
    rp = [hx('#1c3a2c'), hx('#24493a'), hx('#2f5c45'), hx('#3d7253'), hx('#558a63')]
    shadow_ell(a, x + 2, y + s * 2 + 1, s * .8 + 1, 1.5)
    vline(a, x, y + s * 2 - 1, 2, C['wood'][0])
    for k in range(3):
        top = y + k * s * 2 // 3; hw = 1 + k + s // 3
        for j in range(s):
            ww = max(0, int(hw * (j + 1) / s))
            for i in range(-ww, ww + 1):
                c = rp[3] if i < -ww // 2 else rp[2] if i < ww // 2 else rp[1]
                if j == 0 and snow: c = hx('#e8eef2')
                put(a, x + i, top + j, c)
    put(a, x, y - 1, rp[4])


def field(a, x, y, w, h, kind, rng):
    cols = {'wheat': [hx('#c9a94e'), hx('#d8bb5e')], 'green': [hx('#5b8f3a'), hx('#6ea447')],
            'flax': [hx('#7f9a5a'), hx('#8fae68')], 'soil': [hx('#7a5a3a'), hx('#8a6a46')]}[kind]
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            put(a, xx, yy, cols[(yy - y) % 2] if kind != 'soil' else cols[(xx // 2 + yy) % 2])
    hline(a, x, y + h, w, lit(cols[0], -.3))


def river(a, occ, y0, h, seed):
    n = smooth_noise(a.shape[1], 8, 10, seed)[3]
    for xx in range(a.shape[1]):
        off = int(n[xx] * 6) - 3
        yt, yb = y0 + off, y0 + off + h
        for yy in range(yt - 2, yb + 3):
            if 0 <= yy < a.shape[0]:
                if yy < yt or yy >= yb: a[yy, xx] = hx('#c8b07a') if (xx + yy) % 5 else hx('#b49a64')
                else:
                    d = min(yy - yt, yb - 1 - yy)
                    a[yy, xx] = C['water'][min(3, 1 + d)] if (xx * 3 + yy * 7) % 23 else C['water'][4]
                occ[yy, xx] = True
                WATER[yy, xx] = True


WATER = np.zeros((104, 168), bool)


def lake(a, occ, cx, cy, rx, ry):
    m = ellipse_mask(a.shape[:2], cx, cy, rx, ry)
    a[m] = C['water'][2]
    m2 = ellipse_mask(a.shape[:2], cx - 1, cy - 1, rx - 2, ry - 2); a[m2] = C['water'][1]
    edge = ellipse_mask(a.shape[:2], cx, cy, rx + 1, ry + 1) & ~m; a[edge] = hx('#7a8a5a')
    occ[ellipse_mask(a.shape[:2], cx, cy, rx + 3, ry + 3)] = True; WATER[ellipse_mask(a.shape[:2], cx, cy, rx + 1, ry + 1)] = True


def road(a, occ, pts, w, col):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            x = x0 + (x1 - x0) * i / max(1, n - 1); y = y0 + (y1 - y0) * i / max(1, n - 1)
            for dy in range(w):
                for dx in range(w):
                    xx, yy = int(x) + dx, int(y) + dy
                    if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]:
                        a[yy, xx] = col[(xx * 7 + yy * 3) % len(col)]; occ[yy, xx] = True


def place(a, occ, bocc, items, scorefn, rng, gap=1, step=2):
    H, Wd = occ.shape
    placed = []
    for (key, fn, dims) in items:
        x0, x1, y0, y1 = dims
        best = None
        for ax in range(2 - x0, Wd - 2 - x1, step):
            for ab in range(2 - y0, H - 2 - y1, step):
                bx0, bx1, by0, by1 = ax + x0, ax + x1, ab + y0, ab + y1
                if occ[max(by0 - gap, 0):by1 + gap + 1, max(bx0 - gap, 0):bx1 + gap + 1].any(): continue
                sc = scorefn(key, (bx0 + bx1) / 2, by1, rng)
                if sc is None: continue
                if best is None or sc < best[0]: best = (sc, ax, ab)
        if best is None: continue
        _, ax, ab = best
        occ[ab + y0 - gap:ab + y1 + gap + 1, ax + x0 - gap:ax + x1 + gap + 1] = True
        bocc[max(ab + y0 - 2, 0):ab + y1 + 4, max(ax + x0 - 2, 0):ax + x1 + 3] = True
        placed.append((ab, ax, fn))
    return placed


SW, SH = 168, 104


def hfn(cult, tier, seed, arch=None):
    return lambda a, x, b: house(a, x, b, cult, tier, seed, arch)


def city(cult, seed=5):
    rng = random.Random(seed); WATER[:] = False
    occ = np.zeros((SH, SW), bool); bocc = np.zeros((SH, SW), bool)
    deco = []
    if cult == 'riverland':
        a = grass_ground(SW, SH, seed, tint=(hx('#cdb27c'), .42))
        river(a, occ, 80, 9, seed)
        cx, cy = 84, 46
        road(a, occ, [(0, 60), (SW, 60)], 4, [hx('#b89a68'), hx('#c4a674'), hx('#a88a5a')])
        road(a, occ, [(cx - 1, 12), (cx - 1, 78)], 4, [hx('#b89a68'), hx('#c4a674'), hx('#a88a5a')])
        for k, (fx_, fy, fw) in enumerate([(4, 66, 30), (40, 66, 22), (112, 66, 26), (142, 66, 24)]):
            field(a, fx_, fy, fw, 8, ['green', 'wheat', 'green', 'flax'][k], rng); occ[fy - 1:fy + 10, fx_ - 1:fx_ + fw + 1] = True
        for k in range(14): deco.append(('palm', rng.randint(4, SW - 6), rng.choice([64, 76, 92, 96]) + rng.randint(-2, 2)))
        seat = hfn(cult, 4, 7, 0)
        items = [('seat', seat)] + [('rich', hfn(cult, 3, 300 + i, i)) for i in range(3)] + \
                [('mid', hfn(cult, 2, 200 + i, i % 3)) for i in range(7)] + [('poor', hfn(cult, 1, 100 + i, i % 3)) for i in range(10)] + \
                [('slum', hfn(cult, 0, 50 + i, i % 3)) for i in range(5)] + [('market', BUILD[2]['commerce']), ('craft', BUILD[1]['industry'])]
        def sc(k, x, b, r):
            d = math.hypot(x - cx, (b - cy) * 1.4)
            if k == 'seat': return d
            if k == 'slum': return -abs(x - cx) + (0 if b > 60 else 30) + r.random() * 10   # slums on riverbank edges
            if k == 'market': return abs(x - cx - 16) + abs(b - 58)
            return d * (1 if k in ('rich',) else 1.0) + r.random() * (4 if k == 'rich' else 8)
        gap = 1; label_col = R['teal']
    elif cult == 'northern':
        a = grass_ground(SW, SH, seed, tint=(hx('#3f6a3c'), .35))
        lake(a, occ, 140, 82, 20, 12)
        cx, cy = 76, 50
        road(a, occ, [(0, 72), (40, 66), (76, 58), (120, 56), (SW, 40)], 2, C['dirt'])
        for k in range(3):
            fx_, fy = [(10, 20), (118, 18), (16, 84)][k]
            field(a, fx_, fy, 22, 9, ['soil', 'wheat', 'flax'][k], rng); occ[fy - 1:fy + 11, fx_ - 1:fx_ + 23] = True
            fence(a, fx_, fy + 10, 22)
        seat = hfn(cult, 4, 7, 0)
        items = [('seat', seat)] + [('rich', hfn(cult, 3, 300 + i, i)) for i in range(3)] + \
                [('mid', hfn(cult, 2, 200 + i, i % 3)) for i in range(6)] + [('poor', hfn(cult, 1, 100 + i, i % 3)) for i in range(7)] + \
                [('slum', hfn(cult, 0, 50 + i, i % 3)) for i in range(3)] + [('craft', BUILD[2]['industry']), ('market', BUILD[1]['commerce'])]
        def sc(k, x, b, r):
            d = math.hypot(x - cx, (b - cy) * 1.2)
            if k == 'seat': return d
            return abs(d - {'rich': 18, 'mid': 26, 'poor': 34, 'slum': 46, 'craft': 30, 'market': 20}[k]) * 1.0 + r.random() * 14
        gap = 3; label_col = K2['blue']
    else:  # highland
        a = grass_ground(SW, SH, seed, tint=(hx('#8a9478'), .38))
        # terraces: horizontal stone retaining walls make a hillside
        for ty in (30, 50, 70):
            for xx in range(SW):
                yy = ty + int(3 * math.sin(xx / 13 + ty))
                a[yy, xx] = W['stone'][2]; a[yy + 1, xx] = W['stone'][0]
                blend_rect(a, xx, yy + 2, 1, 2, (0, 0, 0), .18)
        cx, cy = 84, 26
        road(a, occ, [(cx, 30), (40, 44), (128, 62), (30, 80), (60, SH)], 2, C['cobble'])
        for k in range(8): deco.append(('rock', rng.randint(4, SW - 6), rng.randint(10, SH - 4)))
        for k in range(2):
            px, py = [(4, 84), (128, 84)][k]
            for i in range(30): put(a, px + i, py, W['stone'][2 if i % 2 else 1]); put(a, px + i, py + 14, W['stone'][2 if i % 2 else 1])
            occ[py:py + 15, px:px + 30] = True
        seat = hfn(cult, 4, 7, 1)
        items = [('seat', seat)] + [('rich', hfn(cult, 3, 300 + i, i)) for i in range(3)] + \
                [('mid', hfn(cult, 2, 200 + i, i % 3)) for i in range(7)] + [('poor', hfn(cult, 1, 100 + i, i % 3)) for i in range(8)] + \
                [('slum', hfn(cult, 0, 50 + i, i % 3)) for i in range(4)] + [('mine', BUILD[2]['mine']), ('craft', BUILD[2]['industry'])]
        def sc(k, x, b, r):
            if k == 'seat': return abs(x - cx) + abs(b - 34) * 2
            band = {'rich': 46, 'mid': 64, 'poor': 80, 'slum': 98, 'craft': 88, 'mine': 20}[k]
            if k == 'mine': return abs(b - 22) + abs(x - 150)
            return abs(b - band) * 2 + abs(x - cx) * .25 + r.random() * 10
        gap = 1; label_col = K2['violet']
    occ[0:12, 0:56] = True
    items = [(k, fn, measure_fn(fn)) for k, fn in items]
    items.sort(key=lambda t: (t[0] != 'seat', -(t[2][1] - t[2][0])))
    placed = place(a, occ, bocc, items, sc, rng, gap)
    # nature filler
    n_tree = {'riverland': 6, 'northern': 70, 'highland': 18}[cult]
    tries = 0
    while n_tree and tries < 3000:
        tries += 1
        x, y = rng.randint(3, SW - 5), rng.randint(6, SH - 6)
        if occ[max(y - 3, 0):y + 7, max(x - 3, 0):x + 4].any(): continue
        occ[max(y - 3, 0):y + 7, max(x - 2, 0):x + 3] = True; bocc[max(y - 3, 0):y + 7, max(x - 2, 0):x + 3] = True
        placed.append((y + 6, x, 'pine' if cult != 'riverland' else 'tree')); n_tree -= 1
    for d in deco:
        placed.append((d[2] + 8 if d[0] == 'palm' else d[2], d[1], d[0]))
    placed.sort(key=lambda t: t[0])
    fx = []
    for (ab, ax, fn) in placed:
        if fn == 'pine': pine(a, ax, ab - 8, rng.choice([4, 4, 5]), ax * 3 + ab, snow=False)
        elif fn == 'tree': tree(a, ax, ab - 4, 4, ax)
        elif fn == 'palm': palm(a, ax, ab - 8, ax)
        elif fn == 'rock': rock(a, ax, ab, 1.8, ax)
        else: fx += fn(a, ax, ab) or []
    return a, bocc, fx, label_col


ANIM = {'riverland': [camel, camel, sheep, chicken, chicken], 'northern': [deer, deer, horse, sheep, sheep, wolf], 'highland': [sheep, sheep, sheep, cow, cow, horse]}


def people(f, occ, cult, seed):
    rng = random.Random(seed)
    spots = []
    for _ in range(4000):
        if len(spots) >= 22: break
        x, y = rng.randint(4, SW - 6), rng.randint(14, SH - 4)
        if occ[max(y - 6, 0):y + 2, max(x - 2, 0):x + 3].any() or WATER[max(y - 2, 0):y + 2, max(x - 2, 0):x + 3].any(): continue
        if all(math.hypot(x - sx, y - sy) > 6 for sx, sy in spots): spots.append((x, y))
    roles = ['poor', 'worker', 'poor', 'rich', 'soldier', 'scholar', 'worker']
    sp = [(y, x, 'p', roles[i % len(roles)], i) for i, (x, y) in enumerate(spots[:15])]
    for i, fn in enumerate(ANIM[cult]):
        if 15 + i < len(spots): x, y = spots[15 + i]; sp.append((y, x, 'a', fn, i))
    sp.sort(key=lambda t: t[0])
    for (y, x, k, r, i) in sp:
        if k == 'p': person(f, x * 2 - 4, y * 2 - 13, 2, r, i % 2, seed=i + seed)
        else: r(f, x * 2, y * 2 - 8, i % 2)


def render_city(cult, name):
    a, occ, fx, lc = city(cult)
    f = upscale(a, 2); fine_fx(f, fx, 2); people(f, occ, cult, 11)
    w = text_w(name) + 14
    panel(f, 4, 4, w + 4, 11, .82)
    rect(f, 6, 6, 7, 7, lc[2]); rect(f, 7, 7, 5, 5, lc[3]); put(f, 9, 9, hx('#f3e6c8'))
    text(f, 16, 7, name, UI['txt'])
    return vignette(Image.fromarray(f), .1)


INFO = {
    'riverland': ('RIVERLAND', 'QARNAH', 'dense river-bank grid - flat roofs, domes, wind-catchers, palms, slums on the floodplain'),
    'northern': ('NORTHERN', 'VELMORA', 'scattered farmsteads in a forest clearing - timber & turf roofs, painted planks, lake'),
    'highland': ('HIGHLAND', 'SHAARIN', 'hill town in terraces - castle on top, rich below it, poor at the foot; stone, slate, sheep pastures'),
}

if __name__ == '__main__':
    S = 3
    tiles = {c: render_city(c, INFO[c][1]) for c in INFO}
    tw, th = tiles['riverland'].width * S, tiles['riverland'].height * S
    TH, GAP, HH = 74, 16, 56
    out = Image.new('RGB', (tw + 2 * GAP, TH + 3 * (th + HH + GAP)), (18, 22, 28))
    d = ImageDraw.Draw(out)
    fb = ImageFont.load_default(size=32); fm = ImageFont.load_default(size=24); fs = ImageFont.load_default(size=19)
    d.text((GAP, TH // 2), 'SAME ERA (MEDIEVAL)  -  3 CULTURES, 3 DIFFERENT CITIES', fill=(240, 228, 200), font=fb, anchor='lm')
    for r, c in enumerate(INFO):
        y = TH + r * (th + HH + GAP)
        d.text((GAP, y + 26), INFO[c][0], fill=(232, 180, 106), font=fm, anchor='lm')
        d.text((GAP + 170, y + 26), INFO[c][2], fill=(200, 205, 212), font=fs, anchor='lm')
        out.paste(tiles[c].resize((tw, th), Image.NEAREST), (GAP, y + HH))
    out.save('cultures_medieval.png'); print(out.size)
