"""4 extra biomes the simulation has but the pack did not: LAVA (animated liquid), BIRCH FOREST, GLIMMERWOOD, EMBER WASTES.
Tiles: 64 px tileable x4 variants (fine grid). Props: birch / glimmer trees (sway, seasons), ember vents, charred stumps, lava & ember rocks."""
import os, math, random
import numpy as np
from lib import *
from animals import R5
from xcore import Atlas, up2
import terrain as T_
from export_world import seamless, season_tint, sway, SEASONS

TILES = {
    'birch_forest': (['#6e9a4e', '#76a356', '#7fac5e'], '#e8e0c8,#d8c870', 10),
    'glimmerwood': (['#2f4e5a', '#365864', '#3e626e'], '#7ff0f0,#b8f8ff,#9a7af0', 12),
    'ember_wastes': (['#3a302a', '#433730', '#4c3e36'], '#f4602a,#ffb84a,#5a504a', 10),
}
LAVA = R5('#6a140a', '#b0280e', '#e8521a', '#ff9a3a', '#ffe27a')


def tile(name, v):
    cols, speck, n = TILES[name]
    g = T_.ground(32, 32, cols, hash(name) % 97 * 10 + v, cell=8, speck=speck.split(','), nspeck=n)
    return seamless(g)


def lava_tile(v, f):
    yy, xx = np.mgrid[0:64, 0:64]
    n = np.zeros((64, 64))
    for k, (fx, fy, ph) in enumerate(((1, 1, 0), (2, 1, 1.7), (1, 2, 3.1), (3, 2, .6))):
        n += np.sin(2 * np.pi * (fx * xx / 64 + fy * yy / 64) + ph + v * 1.3 + f * math.pi / 2 * (1 if k % 2 else -1)) / (k + 1)
    n = (n - n.min()) / (n.max() - n.min())
    q = np.clip((n * 4.99).astype(int), 0, 4)
    img = np.array(LAVA, np.uint8)[q]
    crust = (n < .22)
    img[crust] = hx('#2a1a14'); img[crust & ((xx + yy + v) % 5 == 0)] = hx('#4a2a1a')
    return img


def birch(w, x, y, s, seed):
    rr = random.Random(seed)
    shadow_ell(w, x + 1, y + s * 2 + 4, s + 1, max(2, s // 2))
    h = s * 2 + 4
    vline(w, x, y + 2, h, hx('#ece8e0')); vline(w, x + 1, y + 2, h, hx('#c8c2b6'))
    for k in range(3, h, 3): put(w, x + (k % 2), y + 2 + k, hx('#2a2622'))
    for (dx, dy, r) in ((0, 0, s * .8), (-s * .6, s * .5, s * .6), (s * .6, s * .5, s * .6), (0, -s * .4, s * .55)):
        dome(w, x + .5 + dx, y + dy, r, r * .9, R5('#4a7a2a', '#5e9434', '#78ae44', '#98c85a', '#c0e07a'), rr.randint(0, 99), rough=.35)


def glimmer(w, x, y, s, seed, f=0):
    rr = random.Random(seed)
    shadow_ell(w, x + 1, y + s * 2 + 4, s + 1, max(2, s // 2))
    h = s * 2 + 3
    vline(w, x, y + 2, h, hx('#3a2a4a')); vline(w, x + 1, y + 2, h, hx('#2a1e36'))
    for (dx, dy, r) in ((0, 0, s), (-s * .7, s * .4, s * .6), (s * .7, s * .4, s * .6)):
        dome(w, x + .5 + dx, y + dy, r, r * .9, R5('#1e4a5a', '#2a6a7a', '#3a8a9a', '#5ab8c4', '#9af0f0'), rr.randint(0, 99), rough=.3)
    for i in range(5):
        px, py = x + rr.randint(-s, s), y + rr.randint(-s, s)
        put(w, px, py, hx('#e8ffff') if (i + f) % 2 else hx('#9af0f0'))
    blend_mask(w, ellipse_mask(w.shape[:2], x, y + 1, s * 1.6, s * 1.4), hx('#7ff0f0'), .10 + .05 * (f % 2))


def vent(w, f):
    dome(w, 10, 15, 6, 3, R5('#1e1814', '#2e2620', '#3e342c', '#504438', '#665648'), 2)
    blend_mask(w, ellipse_mask(w.shape[:2], 10, 14, 3, 1.4), hx('#ff6a1e'), 1)
    for i in range(3):
        blend_mask(w, ellipse_mask(w.shape[:2], 10 + i * .6 + f * .4, 10 - i * 3 - f, 2 + i * .6, 1.6 + i * .4), hx('#5a554e'), .6 - i * .15)
    put(w, 9 + f % 2, 12, hx('#ffe27a'))


def stump(w, v):
    shadow_ell(w, 8, 15, 5, 1.5)
    rect(w, 5, 9, 6, 6, hx('#1e1814')); vline(w, 5, 9, 6, hx('#3a2e26'))
    hline(w, 5, 9, 6, hx('#2a201a')); put(w, 7 + v % 2, 9, hx('#f4602a'))
    if v == 1: vline(w, 9, 5, 4, hx('#1e1814')); put(w, 10, 5, hx('#1e1814'))


def rock(w, v, ember):
    rp = R5('#1e1a18', '#2e2824', '#423a34', '#5a5048', '#746a60') if ember else R5('#2a1e1a', '#3e2a22', '#56382a', '#704a36', '#8a5e44')
    dome(w, 9, 12, 6 - v, 4 - v * .5, rp, v + 5)
    for i in range(3 - v % 2): put(w, 6 + i * 3, 11 + (i % 2), hx('#f4602a') if ember else hx('#ffb84a'))


def export(out, done):
    at = Atlas('biomes_extra', os.path.join(out, 'Terrain'))
    for name in TILES:
        for v in range(4):
            f = upscale(tile(name, v), 2)
            at.add_array(f't_{name}_{v}', np.dstack([f, np.full(f.shape[:2], 255, np.uint8)]), (0, 0), {'biome': name.upper().replace('_', ' '), 'variant': v, 'tile_px': 64, 'tileable': True})
            if name == 'birch_forest':
                for season in ('spring', 'autumn', 'winter'):
                    rgba = np.dstack([f, np.full(f.shape[:2], 255, np.uint8)])
                    if season == 'winter':
                        sn = smooth_noise(64, 64, 10, v + 5) > .35
                        rgba[sn, :3] = (rgba[sn, :3] * .15 + np.array([232, 240, 246]) * .85).astype(np.uint8)
                    else: rgba = season_tint(rgba, season, v, strength=.4)
                    at.add_array(f't_{name}_{season}_{v}', rgba, (0, 0), {'biome': 'BIRCH FOREST', 'season': season, 'variant': v, 'tile_px': 64, 'tileable': True})
    for v in range(4):
        keys = []
        for f in range(4):
            img = lava_tile(v, f)
            at.add_array(f't_lava_{v}_{f}', np.dstack([img, np.full((64, 64), 255, np.uint8)]), (0, 0), {'biome': 'LAVA', 'variant': v, 'frame': f, 'tile_px': 64, 'tileable': True, 'emissive': True})
            keys.append(f't_lava_{v}_{f}')
        at.anim(f't_lava_{v}', keys, 4, True)
    # props
    for s in (3, 4, 5):
        for v in range(2):
            at.add(f'birch_{s}_{v}_base', up2(lambda w, ctx, s=s, v=v: birch(w, 12, 24 - s * 2, s, v * 11 + s)), 52, 64, (24, 60), regions=())
            base = at.items.pop(); rgba, piv = base[1], base[3]
            for season in SEASONS:
                sr = season_tint(rgba, season, s * 7 + v) if season != 'summer' else rgba
                keys = []
                for i, k in enumerate((0, 1, 0, -1)):
                    key = f'birch_{s}_{v}_{season}_sway_{i}'; at.add_array(key, sway(sr, k * 2), piv, {'prop': 'birch', 'biome': 'BIRCH FOREST', 'season': season, 'frame': i}); keys.append(key)
                at.anim(f'birch_{s}_{v}_{season}_sway', keys, 3, True)
            keys = []
            for f in range(4):
                key = f'glimmer_{s}_{v}_{f}'
                at.add(key, up2(lambda w, ctx, s=s, v=v, f=f: glimmer(w, 12, 24 - s * 2, s, v * 13 + s, f)), 52, 64, (24, 60), regions=(), tags={'prop': 'glimmer_tree', 'biome': 'GLIMMERWOOD', 'frame': f, 'emissive': True})
                keys.append(key)
            at.anim(f'glimmer_{s}_{v}', keys, 3, True)
    keys = []
    for f in range(4):
        at.add(f'ember_vent_{f}', up2(lambda w, ctx, f=f: vent(w, f)), 40, 40, (20, 36), regions=(), tags={'prop': 'ember_vent', 'biome': 'EMBER WASTES', 'frame': f}); keys.append(f'ember_vent_{f}')
    at.anim('ember_vent', keys, 5, True)
    for v in range(2):
        at.add(f'charred_stump_{v}', up2(lambda w, ctx, v=v: stump(w, v)), 32, 34, (16, 30), regions=(), tags={'prop': 'charred_stump', 'biome': 'EMBER WASTES'})
        at.add(f'ember_rock_{v}', up2(lambda w, ctx, v=v: rock(w, v, True)), 36, 32, (18, 28), regions=(), tags={'prop': 'ember_rock', 'biome': 'EMBER WASTES'})
        at.add(f'lava_rock_{v}', up2(lambda w, ctx, v=v: rock(w, v, False)), 36, 32, (18, 28), regions=(), tags={'prop': 'lava_rock', 'biome': 'LAVA'})
    done('biomes_extra', at)
