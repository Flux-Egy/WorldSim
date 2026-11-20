"""(v3.1) Only the COLLAPSE sequence is baked per building now (owner decision after review: memory).
Burning / burnt / frozen / overgrown / hit are done by the WorldSim/RecolorSprite shader (_Burn, _Frost, _Overgrown, _Flash)
plus small generic overlays (ov_fire_<cls>, ov_smoke_column, ov_flood_<cls>) placed on the 'roof' / base anchors.
Original description of all states, kept for reference - disaster states for EVERY building sprite (era buildings, culture houses, walls/keeps/wonders/sanctums...):
  __hit            explosion next to it: shake + flash on the blast side
  __burning_0..2   on fire (flames from roof + windows, smoke column)       loop
  __burnt          charred shell after the fire
  __flooded_0..1   water up to the windows (ripple)                         loop
  __collapse_0..3  cracks -> sinking -> half fallen + dust -> rubble heap  (bomb / missile / quake / titan stomp)
  __frozen         snow cap + icicles (blizzard, ice spells)
  __overgrown      vines + moss (abandoned / extinct kingdom ruins)
Derived from the exported atlases so they always match the base sprite; recolour masks follow geometric changes."""
import os, json, random
import numpy as np
from PIL import Image
from xcore import Atlas

FLAME = [(255, 226, 122), (244, 154, 60), (213, 69, 45), (150, 40, 30)]
SMOKE = [(60, 58, 56), (84, 80, 76), (110, 106, 100), (140, 136, 130)]


def load(art, rel):
    meta = json.load(open(os.path.join(art, rel + '.json')))
    d = os.path.dirname(rel)
    pages = [np.array(Image.open(os.path.join(art, d, p['image'])).convert('RGBA')) for p in meta['pageList']]
    masks = [np.array(Image.open(os.path.join(art, d, p['mask'])).convert('RGBA')) if p.get('mask') else None for p in meta['pageList']]
    return meta, pages, masks


def cut(meta, pages, masks, fr):
    p = pages[fr['page']]; m = masks[fr['page']]
    r = p[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']].copy()
    mk = m[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']].copy() if m is not None and fr.get('recolor') else np.zeros_like(r)
    piv = (int(round(fr['pivotX'] * fr['w'])), int(round((1 - fr['pivotY']) * fr['h'])))
    return r, mk, piv


def pad_top(r, mk, piv, n):
    z = np.zeros((n, r.shape[1], 4), np.uint8)
    return np.vstack([z, r]), np.vstack([z, mk]), (piv[0], piv[1] + n)


def pad_sides(r, mk, piv, n):
    z = np.zeros((r.shape[0], n, 4), np.uint8)
    return np.hstack([z, r, z]), np.hstack([z, mk, z]), (piv[0] + n, piv[1])


def top_profile(r):
    """first opaque row per column (or -1)."""
    op = r[..., 3] > 200
    top = np.where(op.any(axis=0), op.argmax(axis=0), -1)
    return top


def windows(r):
    """bright warm pixels = lit windows; dark pixels inside the body = door/openings."""
    c = r[..., :3].astype(int); op = r[..., 3] > 200
    lit = op & (c[..., 0] > 200) & (c[..., 1] > 150) & (c[..., 2] < 140)
    return lit


def blob(img, cx, cy, rad, col, al=1.0):
    H, W = img.shape[:2]
    for y in range(int(cy - rad), int(cy + rad) + 1):
        for x in range(int(cx - rad), int(cx + rad) + 1):
            if 0 <= x < W and 0 <= y < H and (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad:
                a0 = img[y, x, 3] / 255.
                na = al + a0 * (1 - al)
                if na <= 0: continue
                img[y, x, :3] = ((np.array(col) * al + img[y, x, :3] * a0 * (1 - al)) / na).astype(np.uint8)
                img[y, x, 3] = int(na * 255)


# ------------------------------------------------------------------ states
def st_hit(r, mk, piv, seed):
    r, mk, piv = pad_sides(r, mk, piv, 2)
    o = np.roll(r, 1, axis=1); m = np.roll(mk, 1, axis=1)
    op = o[..., 3] > 0
    W = o.shape[1]
    ramp = np.clip(1 - np.arange(W) / (W * .55), 0, 1)[None, :] * op
    o[..., :3] = np.clip(o[..., :3] + (ramp[..., None] * np.array([120, 100, 70])), 0, 255).astype(np.uint8)
    rr = random.Random(seed)
    for _ in range(10):
        x, y = rr.randint(0, W // 3), rr.randint(0, o.shape[0] - 1)
        if 0 <= y < o.shape[0]: o[y, x] = (255, 240, 200, 255)
    return o, m, piv


def char(r, k=.6):
    o = r.copy(); op = o[..., 3] > 0
    c = o[op, :3].astype(float)
    l = c.mean(axis=1, keepdims=True)
    o[op, :3] = np.clip(c * (1 - k) + (l * .35 + 10) * k, 0, 255).astype(np.uint8)
    return o


def st_burning(r, mk, piv, f, seed):
    r, mk, piv = pad_top(r, mk, piv, 22)
    o = char(r, .35)
    top = top_profile(r)
    rr = random.Random(seed * 7 + f)
    H, W = o.shape[:2]
    lit = windows(r)
    ys, xs = np.nonzero(lit)
    for y, x in zip(ys, xs):           # windows glow orange-red
        o[y, x, :3] = FLAME[(x + y + f) % 3]
    cols = [x for x in range(W) if top[x] >= 0]
    for x in cols[::2]:
        if rr.random() < .55:
            h = rr.randint(3, 9)
            for k in range(h):
                c = FLAME[0] if k > h - 3 else FLAME[1] if k > h // 2 else FLAME[2]
                y = top[x] - k + (1 if k == 0 else 0)
                xx = x + (1 if (k + f + x) % 4 == 0 else 0)
                if 0 <= y < H and 0 <= xx < W: o[y, xx] = (*c, 255)
    for i in range(5):                    # smoke column, drifting with the frame
        cx = (cols[len(cols) // 2] if cols else W // 2) + i * 1.2 + f
        cy = min(top[top >= 0]) - 6 - i * 4 - f * 1.5 if (top >= 0).any() else 8
        blob(o, cx, cy, 3 + i * .6, SMOKE[i % 4], .75 - i * .1)
    m = mk.copy(); m[...] = 0
    return o, m, piv


def st_burnt(r, mk, piv, seed):
    o = char(r, .85)
    rr = random.Random(seed)
    op = np.argwhere(o[..., 3] > 200)
    top = top_profile(r)
    for _ in range(len(op) // 14):     # holes in roof / walls
        y, x = op[rr.randrange(len(op))]
        if top[x] >= 0 and y < top[x] + (r.shape[0] - top[x]) * .45: o[y, x, 3] = 0
    for _ in range(len(op) // 60):
        y, x = op[rr.randrange(len(op))]
        o[y, x, :3] = FLAME[1] if rr.random() < .3 else (40, 38, 36)
    m = mk.copy(); m[...] = 0
    return o, m, piv


def st_flooded(r, mk, piv, f, seed):
    o = r.copy(); m = mk.copy()
    H, W = o.shape[:2]
    by = piv[1]
    level = int(by - max(5, (by - top_profile(r)[top_profile(r) >= 0].min()) * .33))
    water = np.array([50, 110, 170]); foam = np.array([220, 240, 248])
    for y in range(level, H):
        for x in range(W):
            if o[y, x, 3] > 0:
                o[y, x, :3] = (o[y, x, :3] * .35 + water * .65).astype(np.uint8)
                m[y, x] = 0
            elif y <= by + 3:
                o[y, x] = (*water, 200)
    for x in range(W):
        yy = level + (1 if (x // 3 + f) % 2 else 0)
        if 0 <= yy < H: o[yy, x] = (*foam, 255)
    rr = random.Random(seed + f)
    for _ in range(4):
        x = rr.randint(0, W - 3); y = rr.randint(level + 2, min(H - 1, by + 2))
        o[y, x:x + 2] = (*foam, 220)
    return o, m, piv


def st_collapse(r, mk, piv, stage, seed, ruined=None):
    rr = random.Random(seed)
    H, W = r.shape[:2]
    if stage == 0:                           # cracks + shake
        o = np.roll(r, rr.choice((-1, 1)), axis=1); m = np.roll(mk, 0, axis=1)
        op = np.argwhere(o[..., 3] > 200)
        for _ in range(6):
            y, x = op[rr.randrange(len(op))]
            for k in range(rr.randint(4, 9)):
                y += 1; x += rr.choice((-1, 0, 1))
                if 0 <= y < H and 0 <= x < W and o[y, x, 3] > 200: o[y, x, :3] = (30, 26, 22)
        return o, m, piv
    by = piv[1]
    keep = {1: .8, 2: .5, 3: .25}[stage]
    top = top_profile(r); tmin = top[top >= 0].min()
    h0 = by - tmin
    nh = max(4, int(h0 * keep))
    # squash the body vertically towards the base and tilt it
    body = Image.fromarray(r[tmin:by + 1]); mbody = Image.fromarray(mk[tmin:by + 1])
    bw = body.size[0]
    sq = np.array(body.resize((bw, nh), Image.NEAREST)); msq = np.array(mbody.resize((bw, nh), Image.NEAREST))
    o = np.zeros_like(r); m = np.zeros_like(mk)
    tilt = {1: 1, 2: 3, 3: 0}[stage] * rr.choice((-1, 1))
    for i in range(nh):
        y = by - nh + 1 + i
        sh = int(round(tilt * (nh - i) / nh))
        o[y] = np.roll(sq[i], sh, axis=0); m[y] = np.roll(msq[i], sh, axis=0)
    if stage >= 2:                           # break edges, rubble + dust
        op = np.argwhere(o[..., 3] > 0)
        for _ in range(len(op) // (5 if stage == 2 else 3)):
            y, x = op[rr.randrange(len(op))]
            o[y, x, 3] = 0; m[y, x] = 0
        for _ in range(W // 2):
            x = rr.randint(1, W - 2); y = by - rr.randint(0, 3 if stage == 2 else 6)
            c = rr.choice([(120, 112, 100), (90, 84, 76), (150, 140, 124), (110, 80, 56)])
            o[y, x] = (*c, 255); o[y, x + 1] = (*c, 255)
        o2 = o
        if stage == 2:
            o2, m, piv2 = pad_top(o, m, piv, 10)
            for i in range(6): blob(o2, W * (.2 + i * .13), piv2[1] - 6 - (i % 2) * 4, 4 + i % 3, (190, 176, 150), .55)
            return o2, m, piv2
        for i in range(5): blob(o2, W * (.2 + i * .15), by - 3, 3, (170, 158, 136), .35)
        return o2, m, piv
    return o, m, piv


def st_frozen(r, mk, piv, seed):
    o = r.copy(); m = mk.copy()
    top = top_profile(r)
    H, W = o.shape[:2]
    rr = random.Random(seed)
    for x in range(W):
        if top[x] < 0: continue
        for k in range(rr.choice((1, 2, 2, 3))):
            y = top[x] + k
            if y < H: o[y, x] = (240, 248, 252, 255); m[y, x] = 0
    op = o[..., 3] > 0
    o[op, :3] = (o[op, :3] * .8 + np.array([170, 200, 225]) * .2).astype(np.uint8)
    # icicles under the roof edge: look for horizontal overhangs
    for x in range(1, W - 1, 3):
        for y in range(1, H - 4):
            if o[y, x, 3] > 200 and o[y + 1, x, 3] == 0 and y > top[x] if top[x] >= 0 else False:
                for k in range(rr.randint(1, 3)):
                    if y + 1 + k < H: o[y + 1 + k, x] = (200, 230, 250, 255)
                break
    return o, m, piv


def st_overgrown(r, mk, piv, seed):
    o = char(r, .25); m = mk.copy()
    rr = random.Random(seed)
    H, W = o.shape[:2]
    greens = [(58, 100, 44), (78, 128, 52), (106, 154, 68)]
    for _ in range(W // 2):                  # vines climbing from the base
        x = rr.randint(0, W - 1); y = piv[1]
        for k in range(rr.randint(4, int(H * .7))):
            y -= 1; x += rr.choice((-1, 0, 0, 1))
            if 0 <= x < W and 0 <= y < H and o[y, x, 3] > 200:
                o[y, x, :3] = greens[(k + x) % 3]; m[y, x] = 0
    op = np.argwhere(o[..., 3] > 200)
    for _ in range(len(op) // 25):
        y, x = op[rr.randrange(len(op))]; o[y, x, :3] = greens[rr.randrange(3)]; m[y, x] = 0
    return o, m, piv


STATES = ['hit', 'burning', 'burnt', 'flooded', 'collapse', 'frozen', 'overgrown']


def bake(art, rel, out_name, folder, filt=lambda n: True, DONE=None):
    meta, pages, masks = load(art, rel)
    at = Atlas(out_name, folder)
    for i, fr in enumerate(meta['frameList']):
        n = fr['name']
        if '__' in n or not filt(n): continue
        r, mk, piv = cut(meta, pages, masks, fr)
        seed = i * 13 + 5
        def add(key, res, tags):
            o, m, pv = res
            at.add_array(key, o, pv, dict(tags, base=n), mask=m)
        keys = []
        for s in range(4):
            add(f'{n}__collapse_{s}', st_collapse(r, mk, piv, s, seed), {'state': 'collapse', 'frame': s}); keys.append(f'{n}__collapse_{s}')
        at.anim(f'{n}__collapse', keys, 6, False, [(0, 'sfx:building_crack'), (1, 'sfx:building_collapse'), (2, 'dust'), (3, 'rubble')])
    DONE(out_name, at)
    return at


# ------------------------------------------------------------------ decals & particles (things left behind)
def decals(folder, DONE):
    from lib import hx, blend_mask, ellipse_mask, put, smooth_noise
    at = Atlas('decals_particles', folder)
    def arr(W, H): return np.zeros((H, W, 4), np.uint8)
    def paint(img, mask, col, al):
        img[mask, :3] = col; img[mask, 3] = np.maximum(img[mask, 3], int(al * 255))
    for size, R in (('s', 6), ('m', 11), ('l', 18), ('xl', 28)):
        for v in range(3):
            W = R * 2 + 6; H = R + 6
            img = arr(W, H); yy, xx = np.mgrid[0:H, 0:W]
            n = smooth_noise(W, H, 4, v + R) * .5
            d = ((xx - W / 2) / R) ** 2 + ((yy - H / 2) / (R * .5)) ** 2
            paint(img, d + n * .6 < 1.0, (24, 20, 18), .85)
            paint(img, d + n * .6 < .55, (40, 34, 28), .9)
            paint(img, (d + n * .6 > .9) & (d + n * .6 < 1.25) & (n > .25), (60, 52, 44), .6)
            at.add_array(f'decal_scorch_{size}_{v}', img, (W // 2, H // 2), {'decal': 'scorch', 'size': size})
            img = arr(W, H)
            paint(img, d + n * .4 < 1.0, (70, 54, 40), 1)
            paint(img, d + n * .4 < .7, (48, 36, 28), 1)
            paint(img, d < .35, (30, 24, 20), 1)
            paint(img, (d > .8) & (d < 1.05), (110, 92, 70), 1)
            at.add_array(f'decal_crater_{size}_{v}', img, (W // 2, H // 2), {'decal': 'crater', 'size': size})
    for v in range(4):
        rr = random.Random(v)
        img = arr(16, 8)
        for _ in range(12):
            x, y = rr.randint(1, 14), rr.randint(1, 6); img[y, x] = (*[(120, 112, 100), (90, 84, 76), (150, 140, 124), (110, 80, 56)][rr.randrange(4)], 255)
        at.add_array(f'decal_rubble_{v}', img, (8, 4), {'decal': 'rubble'})
        img = arr(16, 8); yy, xx = np.mgrid[0:8, 0:16]
        paint(img, ((xx - 8) / 7) ** 2 + ((yy - 4) / 3) ** 2 < 1, (90, 86, 80), .8)
        for _ in range(4): img[rr.randint(2, 5), rr.randint(3, 12)] = (244, 154, 60, 255)
        at.add_array(f'decal_ash_{v}', img, (8, 4), {'decal': 'ash'})
        img = arr(18, 8); yy, xx = np.mgrid[0:8, 0:18]
        paint(img, ((xx - 9) / 8) ** 2 + ((yy - 4) / 3) ** 2 + smooth_noise(18, 8, 3, v) * .4 < 1.1, (60, 120, 170), .7)
        at.add_array(f'decal_puddle_{v}', img, (9, 4), {'decal': 'puddle'})
        img = arr(10, 6)
        for k in range(2): img[2 + k * 2, 1 + k * 5:4 + k * 5] = (80, 64, 48, 160)
        at.add_array(f'decal_footprints_{v}', img, (5, 3), {'decal': 'footprints'})
    # particles: smoke puffs, dust, embers, sparks, shrapnel, wood splinters, stone chips, glass, water drops, leaves, feathers, bones
    P = {'smoke': [(84, 80, 76), (110, 106, 100), (140, 136, 130)], 'dust': [(170, 158, 136), (190, 176, 150), (150, 138, 118)], 'ember': [(255, 226, 122), (244, 154, 60), (213, 69, 45)],
         'spark': [(255, 255, 220), (255, 226, 122)], 'shrapnel': [(70, 72, 78), (120, 124, 130)], 'splinter': [(140, 104, 68), (100, 74, 50)], 'stone': [(150, 146, 140), (100, 98, 94)],
         'glass': [(200, 230, 245), (150, 200, 230)], 'drop': [(120, 180, 230), (200, 230, 250)], 'leaf': [(80, 130, 52), (200, 120, 40)], 'feather': [(236, 232, 224), (200, 196, 188)],
         'bone': [(226, 214, 190), (180, 170, 150)], 'snow': [(255, 255, 255), (220, 236, 246)], 'ash_flake': [(70, 68, 64), (120, 116, 110)]}
    for kind, cols in P.items():
        for s in range(4):
            img = arr(8, 8); c = cols[s % len(cols)]
            if kind in ('smoke', 'dust'):
                yy, xx = np.mgrid[0:8, 0:8]; r = 1.5 + s
                paint(img, (xx - 3.5) ** 2 + (yy - 3.5) ** 2 <= r * r, c, .8 - s * .12)
            elif kind in ('splinter', 'shrapnel', 'glass', 'bone', 'feather', 'leaf'):
                for k in range(2 + s % 2): img[3 + (k if s % 2 else 0), 2 + k] = (*c, 255)
            else:
                img[3:3 + 1 + s // 2, 3:3 + 1 + s // 2] = (*c, 255)
            at.add_array(f'pt_{kind}_{s}', img, (4, 4), {'particle': kind, 'size': s})
    # blast-zone ring telegraph (for UI preview of bomb radius), 4 zones
    for zi, col in enumerate(((255, 246, 192), (255, 160, 60), (220, 80, 50), (140, 140, 150))):
        img = arr(64, 32)
        for t in np.linspace(0, 2 * np.pi, 160):
            x, y = int(32 + 30 * np.cos(t)), int(16 + 14 * np.sin(t))
            if int(t * 12) % 2 == 0: img[y, x] = (*col, 230)
        at.add_array(f'ui_blast_zone_{zi}', img, (32, 16), {'ui': 'blast_zone', 'zone': zi, 'note': 'scale to the weapon radius for that zone'})
    DONE('decals_particles', at)


# ------------------------------------------------------------------ generic overlays + annotations (v3.1)
CLASSES = {'s': 40, 'm': 64, 'l': 96, 'xl': 128}


def width_class(w):
    for k, v in CLASSES.items():
        if w <= v: return k
    return 'xl'


def overlays(folder, DONE):
    at = Atlas('building_overlays', folder)
    for cls, W in CLASSES.items():
        keys = []
        for f in range(3):
            img = np.zeros((18, W, 4), np.uint8); rr = random.Random(f * 7 + W)
            for x in range(1, W - 1, 2):
                if rr.random() < .6:
                    h = rr.randint(4, 12)
                    for k in range(h):
                        c = FLAME[0] if k > h - 3 else FLAME[1] if k > h // 2 else FLAME[2]
                        xx = x + (1 if (k + f + x) % 4 == 0 else 0)
                        if xx < W: img[17 - k, xx] = (*c, 255)
            at.add_array(f'ov_fire_{cls}_{f}', img, (W // 2, 17), {'overlay': 'fire', 'class': cls, 'frame': f, 'place': "anchor 'roof' (bottom-centre on the roof line)"})
            keys.append(f'ov_fire_{cls}_{f}')
        at.anim(f'ov_fire_{cls}', keys, 8, True, [(0, 'sfx:house_fire')])
        keys = []
        for f in range(2):
            img = np.zeros((10, W + 6, 4), np.uint8)
            img[3:, :] = (50, 110, 170, 170)
            for x in range(W + 6): img[3 + ((x // 3 + f) % 2), x] = (220, 240, 248, 255)
            at.add_array(f'ov_flood_{cls}_{f}', img, ((W + 6) // 2, 9), {'overlay': 'flood', 'class': cls, 'frame': f, 'place': 'building pivot (base); draw on top'})
            keys.append(f'ov_flood_{cls}_{f}')
        at.anim(f'ov_flood_{cls}', keys, 3, True)
    keys = []
    for f in range(4):
        img = np.zeros((40, 20, 4), np.uint8)
        for i in range(6): blob(img, 10 + i * .6 + f * .5, 36 - i * 6 - f * 1.5, 3 + i * .5, SMOKE[i % 4], .8 - i * .1)
        at.add_array(f'ov_smoke_column_{f}', img, (10, 39), {'overlay': 'smoke', 'frame': f, 'place': "anchor 'roof'"})
        keys.append(f'ov_smoke_column_{f}')
    at.anim('ov_smoke_column', keys, 5, True)
    DONE('building_overlays', at)


def annotate(art, rels):
    """add a 'roof' anchor (top of the silhouette, centred) and a 'w_class' tag to every building frame, in place."""
    for rel in rels:
        p = os.path.join(art, rel + '.json')
        meta, pages, masks = load(art, rel)
        for fr in meta['frameList']:
            r = pages[fr['page']][fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
            op = r[..., 3] > 200
            if not op.any(): continue
            ys, xs = np.nonzero(op)
            cx = int((xs.min() + xs.max()) // 2)
            top = int(ys[xs == cx].min()) if (xs == cx).any() else int(ys.min())
            anchors = [a for a in fr.get('anchors', []) if a['name'] != 'roof'] + [{'name': 'roof', 'x': cx, 'y': top}]
            fr['anchors'] = anchors
            tags = json.loads(fr.get('tagsJson') or '{}'); tags['w_class'] = width_class(int(xs.max() - xs.min() + 1)); fr['tagsJson'] = json.dumps(tags)
        json.dump(meta, open(p, 'w'), separators=(',', ':'))
