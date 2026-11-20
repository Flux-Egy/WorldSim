"""Era progression scenes: same city (QARNAH) at founding vs flourishing of each era."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from buildings import BUILD, ERAS, cart
from catalog import measure, fine_fx
from chars import person, sheep, cow, horse, deer, wolf, chicken, camel, robodog

SW, SH = 144, 96
CXC, RY = SW // 2, 60

ROAD = {0: 'dirt', 1: 'dirt', 2: 'cobble', 3: 'cobble', 4: 'asph', 5: 'future'}


def draw_road(a, occ, x, y, w, h, kind):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if not (0 <= yy < SH and 0 <= xx < SW): continue
            if kind == 'dirt':
                c = C['dirt'][(xx * 7 + yy * 3) % 3]
                if (xx * 13 + yy * 5) % 11 == 0: continue
            elif kind == 'cobble':
                c = C['cobble'][1] if (xx // 2 + yy // 2) % 2 else C['cobble'][2]
                if xx in (x, x + w - 1) and w > h or yy in (y, y + h - 1) and h >= w: c = C['cobble'][0]
            elif kind == 'asph':
                c = C['asph'][1]
                if w > h and (yy == y or yy == y + h - 1) or h >= w and (xx == x or xx == x + w - 1): c = C['side'][1]
                elif w > h and yy == y + h // 2 and (xx // 3) % 2 == 0: c = C['line']
                elif h >= w and xx == x + w // 2 and (yy // 3) % 2 == 0: c = C['line']
            else:
                c = W['white'][1]
                if w > h and (yy == y or yy == y + h - 1) or h >= w and (xx == x or xx == x + w - 1): c = C['cyan']
            a[yy, xx] = c
            occ[yy, xx] = True


def layout(era, stage):
    e = era
    if stage == 1:
        return [(e, 'seat'), (e, 'poor'), (e, 'poor'), (e, 'poor'), (e, 'rich'), (e, 'rich'), (e, 'commerce'),
                (e, 'industry'), (e, 'mine'), (e, 'research'), (e, 'energy'), (e, 'military'), (e, 'defense'), (e, 'poor')]
    if e == 0:
        return [(0, 'poor'), (0, 'poor'), (0, 'poor'), (0, 'energy'), (0, 'industry'), (0, 'poor')]
    p = e - 1
    new = {1: [(1, 'poor'), (1, 'mine'), (1, 'industry')],
           2: [(2, 'poor'), (2, 'mine'), (2, 'industry')],
           3: [(3, 'poor'), (3, 'mine'), (3, 'industry')],
           4: [(4, 'poor'), (4, 'mine'), (4, 'research')],
           5: [(5, 'poor'), (5, 'energy'), (5, 'research')]}[e]
    return [(p, 'seat'), (p, 'poor'), (p, 'poor'), (p, 'rich'), (p, 'commerce'), (p, 'defense')] + new


PREF = {'seat': 'center', 'poor': 'near', 'rich': 'near', 'commerce': 'cross', 'industry': 'far', 'mine': 'corner',
        'research': 'near', 'energy': 'far', 'military': 'edge', 'defense': 'edge'}


def score(kind, cx, cy, rng):
    d = math.hypot(cx - CXC, cy - 50)
    j = rng.random() * 6
    if kind == 'near': return d + j
    if kind == 'cross': return math.hypot(cx - CXC - 14, cy - RY - 8) + j
    if kind == 'far': return -d + j
    if kind == 'corner': return math.hypot(cx - SW + 14, cy - 12) + j
    if kind == 'edge': return min(cx, SW - cx, cy, SH - cy) * 3 + j
    return d


def build_scene(era, stage, seed=1):
    rng = random.Random(seed * 10 + era * 3 + stage)
    a = grass_ground(SW, SH, seed + era * 5 + stage)
    if era >= 4 and stage == 1:
        blend_rect(a, 0, 0, SW, SH, C['side'][0], .12)
    occ = np.zeros((SH, SW), bool)
    bocc = np.zeros((SH, SW), bool)
    rk = ROAD[era if stage else max(era - 1, 0)]
    if era == 0 and stage == 0: rk = 'dirt'
    rw = 4 if rk in ('asph', 'future') else 3
    draw_road(a, occ, 0, RY, SW, rw, rk)
    draw_road(a, occ, CXC - 1, RY, rw, SH - RY, rk)
    if stage == 1 and era >= 3:
        draw_road(a, occ, 24, 0, rw, RY, rk); draw_road(a, occ, SW - 28, RY, rw, SH - RY, rk)
    occ[0:11, 0:46] = True
    # river / coast strip at the left bottom for flavour
    fx_all, placed = [], []
    items = layout(era, stage)
    dims = [(be, cat, measure(BUILD[be][cat])) for (be, cat) in items]
    dims.sort(key=lambda t: (t[1] != 'seat', -(t[2][1] - t[2][0]) * (t[2][3] - t[2][2])))
    for (be, cat, (x0, x1, y0, y1)) in dims:
        fn = BUILD[be][cat]
        w, h = x1 - x0 + 1, y1 - y0 + 1
        best = None
        if cat == 'seat':
            ax = CXC + 1 - w // 2 - x0; ab = RY - 3 - y1
            cands = [(ax, ab)]
        else:
            cands = [(ax, ab) for ax in range(2 - x0, SW - 2 - x1, 2) for ab in range(2 - y0, SH - 2 - y1, 2)]
            rng.shuffle(cands)
        for (ax, ab) in cands:
            bx0, bx1, by0, by1 = ax + x0, ax + x1, ab + y0, ab + y1
            if bx0 < 1 or by0 < 1 or bx1 >= SW - 1 or by1 >= SH - 1: continue
            if occ[max(by0 - 1, 0):by1 + 2, max(bx0 - 1, 0):bx1 + 2].any(): continue
            sc = score(PREF[cat], (bx0 + bx1) / 2, (by0 + by1) / 2, rng)
            if best is None or sc < best[0]: best = (sc, ax, ab)
        if best is None: continue
        _, ax, ab = best
        occ[ab + y0 - 1:ab + y1 + 2, ax + x0 - 1:ax + x1 + 2] = True
        bocc[ab + y0 - 2:ab + y1 + 4, ax + x0 - 2:ax + x1 + 3] = True
        placed.append((ab, ax, be, cat, fn))
    # nature: trees fewer in later eras / flourishing
    ntrees = max(3, int((26 - era * 4) * (0.6 if stage else 1)))
    tries = 0
    while ntrees > 0 and tries < 800:
        tries += 1
        x, y = rng.randint(2, SW - 6), rng.randint(3, SH - 8)
        if occ[max(y - 4, 0):y + 7, max(x - 4, 0):x + 6].any(): continue
        occ[max(y - 4, 0):y + 7, max(x - 4, 0):x + 6] = True
        bocc[max(y - 3, 0):y + 7, max(x - 3, 0):x + 5] = True
        placed.append((y + 4, x, -1, 'tree', None)); ntrees -= 1
    for _ in range(10):
        x, y = rng.randint(2, SW - 4), rng.randint(3, SH - 4)
        if not occ[y - 1:y + 3, x - 1:x + 3].any():
            placed.append((y + 1, x, -1, 'bush' if rng.random() < .6 else 'rock', None)); occ[y - 1:y + 3, x - 1:x + 3] = True
    placed.sort(key=lambda t: t[0])
    for (ab, ax, be, cat, fn) in placed:
        if cat == 'tree': tree(a, ax, ab - 4, rng.choice([3, 4, 4, 5]), ax * 7 + ab)
        elif cat == 'bush': bush(a, ax, ab, ax)
        elif cat == 'rock': rock(a, ax, ab, 1.6, ax)
        else: fx_all += fn(a, ax, ab, ax + ab) or []
    return a, bocc, fx_all


CROWD = {0: ['poor', 'poor', 'worker', 'soldier', 'scholar', 'rich'],
         1: ['poor', 'poor', 'worker', 'soldier', 'rich', 'scholar', 'worker']}


def populate(f, occ, era, stage, seed):
    rng = random.Random(seed * 3 + era)
    n = 9 if stage == 0 else 17
    spots = []
    tries = 0
    while len(spots) < n and tries < 2000:
        tries += 1
        x, y = rng.randint(4, SW - 6), rng.randint(6, SH - 6)
        if occ[max(y - 6, 0):y + 2, max(x - 2, 0):x + 3].any(): continue
        near = math.hypot(x - CXC, y - RY + 4) < 44
        if not near: continue
        if all(math.hypot(x - sx, y - sy) > 5 for sx, sy in spots): spots.append((x, y))
    sprites = []
    roles = CROWD[stage]
    for i, (x, y) in enumerate(spots):
        role = roles[i % len(roles)]
        pe = era if (stage == 1 or rng.random() < .35) else max(era - 1, 0)
        sprites.append((y, 'p', x, pe, role, i))
    # leader in front of seat
    sprites.append((RY - 1, 'p', CXC + 4, era if stage else max(era - 1, 0), 'chief', 99))
    # animals / vehicles
    an = {0: [deer, deer, wolf], 1: [camel, sheep, sheep], 2: [sheep, cow, horse, chicken], 3: [horse, chicken], 4: [], 5: [robodog]}[era]
    for k, fn in enumerate(an):
        x, y = rng.randint(6, 48), rng.randint(RY + 8, SH - 6)
        sprites.append((y, 'a', x, fn, k))
    sprites.sort(key=lambda t: t[0])
    for s in sprites:
        if s[1] == 'p':
            _, _, x, pe, role, i = s
            person(f, x * 2 - 4, s[0] * 2 - 13, pe, role, i % 2, seed=i + era)
        else:
            _, _, x, fn, k = s
            fn(f, x * 2, s[0] * 2 - 8, k % 2)
    # vehicles on roads
    if era == 3 and stage == 1:
        cart(f, 70 * 2, 52 * 2 + 1, C['coal'][1]) if False else None
    if era >= 4:
        for k, (cx, cy, col) in enumerate([(36, RY, R['K'][2]), (104, RY, K2['blue'][2]), (CXC - 1, RY + 16, hx('#e8eef6'))]):
            if stage == 0 and k > 0: break
            car(f, cx * 2, cy * 2 + 1, col, vertical=(cx == CXC - 1), future=era == 5)


def car(f, x, y, col, vertical=False, future=False):
    c = [lit(col, -.38), col, lit(col, .25)]
    if vertical:
        shadow_ell(f, x + 4, y + 11, 4, 2, .35)
        rect(f, x, y, 7, 10, c[1]); vline(f, x, y, 10, c[2]); vline(f, x + 6, y, 10, c[0])
        rect(f, x + 1, y + 2, 5, 2, hx('#2c3c4e')); rect(f, x + 1, y + 7, 5, 1, hx('#2c3c4e')); rect(f, x + 1, y + 4, 5, 3, c[2])
    else:
        shadow_ell(f, x + 6, y + 6, 6, 1.6, .35)
        rect(f, x, y, 11, 5, c[1]); hline(f, x, y, 11, c[2]); hline(f, x, y + 4, 11, c[0])
        rect(f, x + 2, y + 1, 2, 3, hx('#2c3c4e')); rect(f, x + 7, y + 1, 2, 3, hx('#2c3c4e')); rect(f, x + 4, y + 1, 3, 3, c[2])
        if not future:
            put(f, x + 1, y + 5, hx('#1e1e22')); put(f, x + 9, y + 5, hx('#1e1e22'))
    if future:
        blend_mask(f, ellipse_mask(f.shape[:2], x + 5, y + 6, 6, 2), C['cyan'], .4)


def city_label(f, x, y, name, era_name, stage_name):
    w = text_w(name) + 14
    panel(f, x, y, w + text_w(era_name) + 10, 9, .8)
    crest = ["..KKK..", ".KkkkK.", "KkLkLkK", "KkkLkkK", ".KkkkK.", "..KKK.."]
    cm = {'K': R['K'][0], 'k': R['K'][2], 'L': hx('#f3e6c8')}
    for j, row in enumerate(crest):
        for i, ch in enumerate(row):
            if ch != '.': put(f, x + 1 + i, y + 1 + j, cm[ch])
    ex = text(f, x + 10, y + 2, name, UI['txt'])
    text(f, ex + 4, y + 2, era_name, UI['acc'])


def render(era, stage):
    a, occ, fx = build_scene(era, stage, seed=3)
    f = upscale(a, 2)
    fine_fx(f, fx, 2)
    populate(f, occ, era, stage, seed=3)
    pop = [[18, 46], [120, 340], [400, 1300], [1500, 5200], [6000, 24000], [30000, 90000]][era][stage]
    city_label(f, 3, 3, 'QARNAH', str(pop), '')
    return vignette(Image.fromarray(f), .1)


STAGE_TXT = ['FOUNDING  (FIRST BREAKTHROUGH)', 'FLOURISHING  (ERA COMPLETE)']
CHANGE = ['nomad camp: tents, fire, first tools', 'COPPER FOUND -> foundry, first mud houses', 'IRON FOUND -> forge, iron mine, cottages',
          'COAL + STEAM -> coal mine, factory, terraces', 'OIL + ELECTRICITY -> oil field, labs, apartments', 'FUSION RESEARCH -> fusion core, pods']

if __name__ == '__main__':
    S = 3
    for part, eras in enumerate([(0, 1, 2), (3, 4, 5)]):
        tiles = [[render(e, st) for st in (0, 1)] for e in eras]
        tw, th = tiles[0][0].width * S, tiles[0][0].height * S
        TH, GAP, HH = 70, 14, 64
        out = Image.new('RGB', (2 * tw + 3 * GAP, TH + len(eras) * (th + HH + GAP)), (18, 22, 28))
        d = ImageDraw.Draw(out)
        fb = ImageFont.load_default(size=30); fm = ImageFont.load_default(size=21); fs = ImageFont.load_default(size=19)
        d.text((GAP, TH // 2), 'SAME CITY, ' + ('ERAS 1-3' if part == 0 else 'ERAS 4-6') + ': FOUNDING  vs  FLOURISHING', fill=(240, 228, 200), font=fb, anchor='lm')
        for r, e in enumerate(eras):
            y = TH + r * (th + HH + GAP)
            d.text((GAP, y + 20), f'{e + 1}. {ERAS[e]}', fill=(232, 180, 106), font=fm, anchor='lm')
            d.text((GAP + 260, y + 20), CHANGE[e], fill=(200, 205, 212), font=fs, anchor='lm')
            for c in range(2):
                x = GAP + c * (tw + GAP)
                d.text((x + 4, y + 48), STAGE_TXT[c], fill=(138, 148, 163), font=fs, anchor='lm')
                out.paste(tiles[r][c].resize((tw, th), Image.NEAREST), (x, y + HH))
        out.save(f'era_progression_{part + 1}.png'); print(out.size)
