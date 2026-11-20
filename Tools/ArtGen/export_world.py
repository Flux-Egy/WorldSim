"""Phase 3 export: walls/castles/bridges/docks/farms/pens/civic props/wonders/sanctums/roads, ships & vehicles (8 dirs),
seasonal + swaying + choppable + burning trees, seasonal terrain, blend masks and shore autotiles."""
import os, math, random
import numpy as np
from PIL import Image
from lib import *
from xcore import Atlas, up2
import structures as SR
from culturegen import SYMBOLS

OUT = None
DONE = None
ADD_STATES = None
SEASONS = ['spring', 'summer', 'autumn', 'winter']


def _w(at, key, fn, W, H, gy, regions=('TEAM',), tags=None, center=True):
    at.add(key, up2(lambda w, ctx: fn(w)), W * 2, H * 2, (W, gy * 2), regions=regions, tags=tags or {})
    if center:
        k, r2, m2, pv, tg, an = at.items[-1]
        ys, xs = np.nonzero(r2[..., 3] > 200)
        if len(xs): at.items[-1] = (k, r2, m2, ((xs.min() + xs.max()) // 2, pv[1]), tg, an)


def ex_structures():
    at = Atlas('world_structures', os.path.join(OUT, 'Buildings'))
    for e in range(6):
        for p in ('h', 'v', 'corner', 'gate_closed', 'gate_open', 'tower'):
            _w(at, f'wall_{e}_{p}', lambda w, e=e, p=p: SR.wall_piece(w, 6, 34, e, p), 30, 40, 34, tags={'era': e, 'wall': p, 'cell_px': 32})
        for big in (False, True):
            _w(at, f'keep_{e}_{"big" if big else "small"}', lambda w, e=e, big=big: SR.keep(w, 6, 52, e, big), 44, 56, 52, tags={'era': e, 'keep': big})
        _w(at, f'dock_{e}', lambda w, e=e: SR.dock(w, 4, 22, e), 34, 28, 22, tags={'era': e, 'prop': 'dock'})
        _w(at, f'well_{e}', lambda w, e=e: SR.well(w, 4, 18, e), 18, 20, 18, regions=(), tags={'era': e, 'prop': 'well'})
        _w(at, f'barn_{e}', lambda w, e=e: SR.barn(w, 3, 22, e), 26, 26, 22, regions=(), tags={'era': e, 'prop': 'barn'})
        for v in range(3):
            _w(at, f'market_{e}_{v}', lambda w, e=e, v=v: SR.market(w, 3, 18, e, v * 5 + e), 24, 22, 18, regions=(), tags={'era': e, 'prop': 'market'})
        for on in (False, True):
            _w(at, f'lamp_{e}_{"on" if on else "off"}', lambda w, e=e, on=on: SR.lamp(w, 3, 16, e, on), 10, 18, 16, regions=(), tags={'era': e, 'prop': 'lamp', 'lit': on})
    for kind in SR.BRIDGE:
        for p in ('h', 'h_end', 'v'):
            _w(at, f'bridge_{kind}_{p}', lambda w, kind=kind, p=p: SR.bridge(w, 4, 22, kind, p), 24, 26, 22, regions=(), tags={'bridge': kind, 'piece': p, 'cell_px': 32})
    for s in range(3): _w(at, f'pen_{s}', lambda w, s=s: SR.pen(w, 3, 24, s), 42, 28, 24, regions=(), tags={'prop': 'pen', 'size': s})
    for style in ('figure', 'beast', 'obelisk', 'orb', 'rider', 'abstract'):
        for mat in ('stone', 'bronze', 'gold', 'marble'):
            _w(at, f'statue_{style}_{mat}', lambda w, style=style, mat=mat: SR.statue(w, 3, 22, style, mat), 18, 26, 22, regions=(), tags={'prop': 'statue', 'style': style, 'material': mat})
    keys = []
    for f in range(4):
        _w(at, f'fountain_{f}', lambda w, f=f: SR.fountain(w, 3, 16, f), 24, 20, 16, regions=(), tags={'prop': 'fountain', 'frame': f}); keys.append(f'fountain_{f}')
    at.anim('fountain', keys, 6)
    for name in SR.WONDERS:
        _w(at, f'wonder_{name}', lambda w, name=name: SR.wonder(w, 6, 96, name), 60, 100, 96, regions=(), tags={'wonder': name})
    for sym in SYMBOLS:
        for tier in range(3):
            _w(at, f'sanctum_{sym}_{tier}', lambda w, ctx=None, sym=sym, tier=tier: SR.sanctum(w, 3, 34, sym, tier, R['K']), 46, 40, 34, tags={'sanctum': sym, 'tier': tier,
               'note': 'fictional creed sanctum; emblem = culture crest symbol'})
    ADD_STATES(at)
    DONE('world_structures', at)


def ex_farms_roads():
    at = Atlas('farms_roads', os.path.join(OUT, 'Terrain'))
    for crop in SR.CROPS:
        for st in SR.STAGES:
            g = np.zeros((16, 32, 3), np.uint8); SR.farm_tile(g, crop, st, hash(crop) % 50)
            f = upscale(g, 2)
            at.add_array(f'farm_{crop}_{st}', np.dstack([f, np.full(f.shape[:2], 255, np.uint8)]), (32, 32), {'crop': crop, 'stage': st, 'tile_px': [64, 32]})
    for kind in SR.ROADS:
        for m in range(16):
            g = np.zeros((16, 16, 3), np.uint8); g[:] = (255, 0, 255); SR.road_tile(g, kind, m)
            f = upscale(g, 2); al = np.where(np.all(f == (255, 0, 255), axis=2), 0, 255).astype(np.uint8); f[al == 0] = 0
            at.add_array(f'road_{kind}_{m}', np.dstack([f, al]), (0, 0), {'road': kind, 'mask': m, 'bits': 'N1 E2 S4 W8', 'tile_px': 32})
    for m in range(16):
        g = np.zeros((16, 16, 3), np.uint8); g[:] = (255, 0, 255); SR.rail_tile(g, m)
        f = upscale(g, 2); al = np.where(np.all(f == (255, 0, 255), axis=2), 0, 255).astype(np.uint8); f[al == 0] = 0
        at.add_array(f'rail_{m}', np.dstack([f, al]), (0, 0), {'rail': True, 'mask': m, 'tile_px': 32})
    DONE('farms_roads', at)


def ex_ships_vehicles():
    at = Atlas('ships_vehicles', os.path.join(OUT, 'Units'))
    for era, (trade, war) in SR.SHIPS.items():
        for wi, name in enumerate((trade, war)):
            for d in range(8):
                keys = []
                for f in range(2):
                    key = f'ship_{name}_{d * 45}_{f}'
                    _w(at, key, lambda w, era=era, wi=wi, d=d, f=f: SR.ship(w, 20, 22, era, wi == 1, d, f), 40, 36, 22, tags={'ship': name, 'era': era, 'war': wi == 1, 'dir': d * 45, 'frame': f}, center=False)
                    k, r2, m2, pv, tg, an = at.items[-1]; at.items[-1] = (k, r2, m2, pv, tg, an)
                    keys.append(key)
                at.anim(f'ship_{name}_{d * 45}', keys, 3)
            # sinking: tilt + submerge using the east-facing frame
            base = [it for it in at.items if it[0] == f'ship_{name}_0_0'][0]
            for i in range(4):
                r2 = base[1].copy(); H = r2.shape[0]
                cut = int(H * (i + 1) / 5)
                r2 = np.vstack([np.zeros((cut, r2.shape[1], 4), np.uint8), r2[:H - cut]])
                r2[..., :3] = (r2[..., :3] * (1 - .12 * i)).astype(np.uint8)
                at.add_array(f'ship_{name}_sink_{i}', r2, base[3], {'ship': name, 'state': 'sinking', 'frame': i})
            at.anim(f'ship_{name}_sink', [f'ship_{name}_sink_{i}' for i in range(4)], 4, False, [(0, 'sfx:ship_sink'), (3, 'remove')])
    for kind in SR.VEHICLES:
        for d in range(8):
            keys = []
            for f in range(2):
                key = f'veh_{kind}_{d * 45}_{f}'
                _w(at, key, lambda w, kind=kind, d=d, f=f: SR.vehicle(w, 16, 16, kind, d, f), 32, 28, 16, tags={'vehicle': kind, 'dir': d * 45, 'frame': f}, center=False)
                keys.append(key)
            at.anim(f'veh_{kind}_{d * 45}', keys, 6)
        base = [it for it in at.items if it[0] == f'veh_{kind}_0_0'][0]
        wr = base[1].copy(); op = wr[..., 3] > 0
        wr[op, :3] = (wr[op, :3].mean(axis=1, keepdims=True) * .35 + 10).astype(np.uint8)
        at.add_array(f'veh_{kind}_wreck', wr, base[3], {'vehicle': kind, 'state': 'wreck'})
    DONE('ships_vehicles', at)


# ------------------------------------------------------------------ seasonal nature (sway / chop / burn)
def season_tint(rgba, season, seed=0, strength=1.0, keep_leaves=False):
    o = rgba.copy(); op = o[..., 3] > 0
    c = o[..., :3].astype(int)
    green = (c[..., 1] > c[..., 0] + 6) & (c[..., 1] > c[..., 2]) & op
    r = np.random.default_rng(seed)
    if season == 'autumn':
        l = c[green].mean(axis=1, keepdims=True)
        pal = np.array([[200, 110, 40], [220, 150, 50], [170, 70, 40]])
        pick = pal[r.integers(0, 3, green.sum())]
        c[green] = (c[green] * (1 - strength) + (l / 140 * pick * .9 + pick * .1) * strength).astype(int)
    elif season == 'winter':
        ys, xs = np.nonzero(green)
        keep = r.random(len(ys)) < (.35 if not keep_leaves else .7)
        for y, x, k in zip(ys, xs, keep):
            if k == (not keep_leaves): c[y, x] = (236, 244, 250) if (y + x) % 3 else (200, 214, 226)
            elif not keep_leaves: o[y, x, 3] = 0
        # snow on top rows
    elif season == 'spring':
        ys, xs = np.nonzero(green)
        for i in r.choice(len(ys), max(1, len(ys) // 18), replace=False) if len(ys) else []:
            c[ys[i], xs[i]] = (244, 170, 200) if i % 2 else (255, 230, 240)
    o[..., :3] = np.clip(c, 0, 255).astype(np.uint8)
    return o


def sway(rgba, k):
    """shift rows above the trunk sideways: top moves most."""
    o = np.zeros_like(rgba); H = rgba.shape[0]
    for y in range(H):
        s = int(round(k * max(0, (H * .65 - y)) / (H * .65)))
        o[y] = np.roll(rgba[y], s, axis=0)
    return o


def ex_nature_seasons():
    from lib import tree, palm, bush
    from culturecity import pine
    at = Atlas('nature_seasonal', os.path.join(OUT, 'Nature'))
    kinds = [('tree', s, v) for s in (3, 4, 5) for v in range(3)] + [('pine', s, 0) for s in (3, 4, 5)] + [('palm', 0, v) for v in range(2)] + [('bush', 0, v) for v in range(3)]
    for (kind, s, v) in kinds:
        def draw(w, kind=kind, s=s, v=v):
            if kind == 'tree': tree(w, 12, 22 - s, s, v * 13 + s)
            elif kind == 'pine': pine(w, 12, 26 - s * 2, s, s, False)
            elif kind == 'palm': palm(w, 12, 14, v)
            else: bush(w, 12, 26, v)
        name = f'{kind}_{s}_{v}'
        _w(at, f'{name}_base', draw, 26, 32, 30, regions=(), tags={})
        base = at.items.pop()
        rgba, piv = base[1], base[3]
        for season in SEASONS:
            if kind == 'palm' and season == 'winter': continue
            sr = season_tint(rgba, season, hash(name) % 99) if not (kind == 'pine' and season != 'winter') else (season_tint(rgba, 'winter', 3, keep_leaves=True) if season == 'winter' else rgba)
            keys = []
            for i, k in enumerate((0, 1, 0, -1)):
                key = f'{name}_{season}_sway_{i}'
                at.add_array(key, sway(sr, k * (2 if kind != 'bush' else 1)), piv, {'prop': kind, 'size': s, 'variant': v, 'season': season, 'frame': i}); keys.append(key)
            at.anim(f'{name}_{season}_sway', keys, 3, True)
        if kind in ('tree', 'pine', 'palm'):
            # chopped: falling sequence + stump + log
            keys = []
            for i, ang in enumerate((0, 15, 40, 70, 90)):
                from export_creatures import fall
                r2 = fall(rgba, piv, -ang) if ang else rgba
                key = f'{name}_fall_{i}'; at.add_array(key, r2, (r2.shape[1] // 4 if ang > 40 else r2.shape[1] // 2, r2.shape[0] - 1), {'prop': kind, 'state': 'falling', 'frame': i}); keys.append(key)
            at.anim(f'{name}_fall', keys, 6, False, [(4, 'sfx:tree_fall'), (4, 'spawn_logs')])
            stump = np.zeros((10, 12, 4), np.uint8)
            for y in range(4, 10):
                for x in range(3, 9): stump[y, x] = (*lit(hx('#6b4c34'), .1 if x < 5 else -.1), 255)
            stump[4, 3:9] = (*hx('#c8a46a'), 255)
            at.add_array(f'{name}_stump', stump, (6, 9), {'prop': kind, 'state': 'stump'})
            # burning (3 frames) and burnt
            keys = []
            for i in range(3):
                b = rgba.copy(); op = b[..., 3] > 0
                b[op, :3] = (b[op, :3] * .55).astype(np.uint8)
                ys, xs = np.nonzero(op); rr = np.random.default_rng(i + hash(name) % 9)
                for j in rr.choice(len(ys), len(ys) // 6, replace=False):
                    b[ys[j], xs[j], :3] = [(255, 210, 90), (245, 150, 50), (213, 69, 45)][(j + i) % 3]
                key = f'{name}_burning_{i}'; at.add_array(key, b, piv, {'prop': kind, 'state': 'burning', 'frame': i}); keys.append(key)
            at.anim(f'{name}_burning', keys, 8, True)
            bt = rgba.copy(); op = bt[..., 3] > 0
            gr = (bt[..., 1].astype(int) > bt[..., 0].astype(int) + 6) & op
            bt[gr, 3] = 0
            bt[op & ~gr, :3] = (bt[op & ~gr, :3] * .25).astype(np.uint8)
            at.add_array(f'{name}_burnt', bt, piv, {'prop': kind, 'state': 'burnt'})
    # logs pile, ore rocks (mineable) with depletion stages
    for i in range(3):
        _w(at, f'logs_{i}', lambda w, i=i: [hline(w, 3, 14 - k, 10 - k * 2 + i, WOOD) for k in range(3)] if False else _logs(w, i), 18, 18, 16, regions=(), tags={'prop': 'logs', 'amount': i})
    for ore, col in (('stone', '#9a958c'), ('iron', '#a8705a'), ('gold', '#e8c040'), ('crystal', '#5fe0e8'), ('coal', '#2a2a2e')):
        for st in range(4):
            _w(at, f'ore_{ore}_{st}', lambda w, col=col, st=st: _ore(w, hx(col), st), 20, 18, 16, regions=(), tags={'prop': 'ore', 'ore': ore, 'depletion': st})
    DONE('nature_seasonal', at)


WOOD = None


def seamless(t):
    n = t.shape[0]
    w = (np.sin(np.linspace(0, np.pi, n, endpoint=False)) ** 2)
    A = t.astype(float)
    X = A * w[None, :, None] + np.roll(A, n // 2, axis=1) * (1 - w[None, :, None])
    Y = X * w[:, None, None] + np.roll(X, n // 2, axis=0) * (1 - w[:, None, None])
    return Y.astype(np.uint8)


def _logs(w, n):
    for k in range(n + 1):
        for j in range(3 - k):
            x, y = 3 + j * 4 + k * 2, 14 - k * 3
            rect(w, x, y, 4, 3, hx('#7a5434')); put(w, x, y + 1, hx('#c8a46a')); put(w, x + 1, y + 1, hx('#a8844e'))


def _ore(w, col, st):
    size = [6, 5, 3.5, 2][st]
    dome(w, 10, 14, size + 1, size * .8, R['stone'], 3)
    for i in range(max(0, 5 - st)):
        put(w, int(10 - size + i * 2.2), int(13 - (i % 2) * 2), col); put(w, int(10 - size + i * 2.2) + 1, int(13 - (i % 2) * 2), lit(col, .25))


def ex_terrain_seasons():
    import terrain as T_
    at = Atlas('terrain_seasonal', os.path.join(OUT, 'Terrain'))
    green = [n for (n, cols, props, speck) in T_.BIOMES if n in ('MEADOW', 'FOREST', 'PLAINS', 'GRASSLAND', 'FARMLAND', 'STEPPE', 'SAVANNA', 'JUNGLE', 'SWAMP', 'FLOWER FIELD', 'HILLS', 'PINE TAIGA')]
    for i, (name, cols, props, speck) in enumerate(T_.BIOMES):
        if name not in green: continue
        for v in range(4):
            g = T_.ground(32, 32, cols, i * 31 + v, cell=8, speck=speck.split(',') if speck else None, nspeck=14 if speck else 0)
            g = seamless(g)
            for season in ('spring', 'autumn', 'winter'):
                f = upscale(g, 2)
                rgba = np.dstack([f, np.full(f.shape[:2], 255, np.uint8)])
                if season == 'winter':
                    rr = np.random.default_rng(v)
                    sn = smooth_noise(64, 64, 10, v + i) > .35
                    rgba[sn, :3] = (rgba[sn, :3] * .15 + np.array([232, 240, 246]) * .85).astype(np.uint8)
                    rgba[~sn, :3] = (rgba[~sn, :3] * .7 + np.array([200, 210, 220]) * .3).astype(np.uint8)
                else:
                    rgba = season_tint(rgba, season, v, strength=.4)
                at.add_array(f't_{name.lower().replace(" ", "_")}_{season}_{v}', rgba, (0, 0), {'biome': name, 'season': season, 'variant': v, 'tile_px': 64, 'tileable': True})
    # 47-blob style reduced to 16 corner/edge blend masks (alpha) used by the terrain shader to blend any two biomes
    for m in range(16):
        f = np.zeros((64, 64), float)
        yy, xx = np.mgrid[0:64, 0:64] / 63.
        if m & 1: f = np.maximum(f, 1 - yy * 2.2)
        if m & 2: f = np.maximum(f, xx * 2.2 - 1.2)
        if m & 4: f = np.maximum(f, yy * 2.2 - 1.2)
        if m & 8: f = np.maximum(f, 1 - xx * 2.2)
        n = smooth_noise(64, 64, 8, m) * .35
        al = np.clip((f + n - .3) * 3, 0, 1)
        al = (np.round(al * 3) / 3 * 255).astype(np.uint8)
        img = np.dstack([np.full((64, 64, 3), 255, np.uint8), al])
        at.add_array(f'blend_mask_{m}', img, (0, 0), {'blend_mask': m, 'bits': 'N1 E2 S4 W8', 'note': 'alpha = how much of the neighbour biome shows'})
    # shoreline autotile (sand over water) 16 masks
    for m in range(16):
        g = np.zeros((64, 64, 4), np.uint8)
        yy, xx = np.mgrid[0:64, 0:64] / 63.
        f = np.zeros((64, 64))
        if m & 1: f = np.maximum(f, 1 - yy * 3)
        if m & 2: f = np.maximum(f, xx * 3 - 2)
        if m & 4: f = np.maximum(f, yy * 3 - 2)
        if m & 8: f = np.maximum(f, 1 - xx * 3)
        f = f + smooth_noise(64, 64, 6, m + 30) * .3
        sand = f > .45; foam = (f > .3) & ~sand
        g[sand] = (*hx('#dcc896'), 255); g[foam] = (*hx('#e8f6fa'), 200)
        at.add_array(f'shore_{m}', g, (0, 0), {'shore_mask': m, 'bits': 'N1 E2 S4 W8 = land side'})
    DONE('terrain_seasonal', at)


CATS = {'structures': ex_structures, 'farms_roads': ex_farms_roads, 'ships': ex_ships_vehicles, 'nature_seasons': ex_nature_seasons, 'terrain_seasons': ex_terrain_seasons}
