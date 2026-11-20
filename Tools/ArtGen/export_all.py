"""Exports every WorldSim art asset into Unity-ready atlases (PNG + recolour mask PNG + JSON).
Run:  python export_all.py [category ...]      (no args = everything)   -> ../WorldSim_Assets/Art/"""
import sys, os, math, random, json, copy, time
import numpy as np
from PIL import Image
from lib import *
import xcore
from xcore import Atlas, up2

_HERE = os.path.dirname(os.path.abspath(__file__))
# default: the Unity project of the repo (Tools/ArtGen -> Assets/WorldSim/Resources/WorldSimArt); override with WORLDSIM_ART_OUT
OUT = os.environ.get('WORLDSIM_ART_OUT') or os.path.join(_HERE, '..', '..', 'Assets', 'WorldSim', 'Resources', 'WorldSimArt')
STATS = {}


def done(name, at):
    n, p = at.save(); STATS[name] = (n, p); print(f'{name:28s} {n:5d} sprites  {p} page(s)', flush=True)


# ================================================================ BUILDING STATES (post-process, keeps recolour mask)
def state_variants(at, key, rgba, mask, pivot, tags, seed):
    r = random.Random(seed)
    H, W = rgba.shape[:2]
    op = rgba[..., 3] > 0
    ys, xs = np.nonzero(op)
    top, bot = ys.min(), ys.max()
    out = {}
    # damaged: soot blobs, broken pixels, cracks
    d = rgba.copy(); dm = mask.copy()
    for _ in range(max(3, W * H // 500)):
        cx, cy = r.randint(0, W - 1), r.randint(top, bot)
        m = ellipse_mask((H, W), cx, cy, r.uniform(2, 5), r.uniform(1.5, 3.5)) & op
        d[m, :3] = (d[m, :3] * .45).astype(np.uint8)
    for _ in range(W // 6):
        x, y = r.randint(0, W - 1), r.randint(top, bot)
        for k in range(r.randint(3, 7)):
            if 0 <= y + k < H and 0 <= x + (k % 2) < W and op[y + k, x + (k % 2)]: d[y + k, x + (k % 2), :3] = (20, 17, 14)
    out['damaged'] = (d, dm)
    # ruined: keep the lower ~45 %, jagged top, rubble
    cut = int(bot - (bot - top) * .45)
    ru = rgba.copy(); rm = mask.copy()
    for x in range(W):
        cx_ = cut + int(3 * math.sin(x * .9 + seed)) + r.randint(-1, 1)
        ru[:max(cx_, 0), x] = 0; rm[:max(cx_, 0), x] = 0
    ru[..., :3] = (ru[..., :3] * .7).astype(np.uint8)
    for _ in range(W // 2):
        x, y = r.randint(1, W - 3), r.randint(max(cut, bot - 6), bot)
        c = [(110, 106, 98), (140, 134, 122), (84, 80, 74), (107, 76, 52)][r.randint(0, 3)]
        ru[y, x] = (*c, 255); ru[y, x + 1] = (*c, 255)
    out['ruined'] = (ru, rm)
    # construction: lower half + scaffold
    cu = rgba.copy(); cm = mask.copy()
    half = int(bot - (bot - top) * .5)
    cu[:half] = 0; cm[:half] = 0
    for x in range(xs.min(), xs.max() + 1, 5):
        for y in range(top + (bot - top) // 4, bot + 1): cu[y, x] = (140, 104, 68, 255)
    for y in range(top + (bot - top) // 4, bot, 5):
        for x in range(xs.min(), xs.max() + 1): cu[y, x] = (107, 76, 52, 255)
    out['construction'] = (cu, cm)
    for st, (img, m) in out.items():
        at.add_array(f'{key}__{st}', img, pivot, dict(tags, state=st), m)


def add_states(at):
    base = list(at.items)
    for i, (k, r2, m2, pv, tags, an) in enumerate(base):
        state_variants(at, k, r2, m2, pv, tags, i * 7 + 1)


# ================================================================ BUILDINGS (6 eras x 10 categories)
def ex_buildings():
    from buildings import BUILD, ERAS, CATS
    at = Atlas('buildings_eras', os.path.join(OUT, 'Buildings'))
    for e in range(6):
      for c in CATS:
        for sv, sd in enumerate((7, 31, 77)):
            fn = BUILD[e][c]
            probe = np.zeros((56, 64, 3), np.uint8)
            fx = fn(probe, 10, 46, sd) or []
            anchors = {f'fx_{i}_{f_[0]}': (f_[1] * 2, f_[2] * 2) for i, f_ in enumerate(fx)}
            key = f'b_{e}_{c}_v{sv}'
            at.add(key, up2(lambda w, ctx, fn=fn, sd=sd: fn(w, 10, 46, sd)), 128, 112, (0, 0), regions=('TEAM',),
                   tags={'era': e, 'era_name': ERAS[e], 'category': c, 'fx': [list(f_[:3]) + ([list(f_[3])] if len(f_) > 3 else []) for f_ in fx]}, anchors=anchors)
            # pivot: base centre of the footprint
            k, r2, m2, pv, tags, an = at.items[-1]
            ys, xs = np.nonzero(r2[..., 3] > 200)
            at.items[-1] = (k, r2, m2, ((xs.min() + xs.max()) // 2, pv[1] + 92), tags, an)
            for prev in at.items[-1 - sv:-1]:
                if prev[1].shape == r2.shape and np.array_equal(prev[1], r2):
                    at.items.pop(); break
    add_states(at)
    done('buildings_eras', at)


# ================================================================ CULTURE HOUSE KIT (genome-driven)
ROOFS = ['gable', 'hip', 'flat', 'dome', 'cone', 'tiered', 'thatch']
WALLS = ['mudw', 'adobe', 'whitew', 'plaster', 'planks', 'logs', 'stone', 'reedw']
ORN_SETS = [[], ['banner', 'spikes'], ['spire'], ['awning'], ['garden'], ['totem'], ['banner', 'spire'], ['garden', 'awning']]
TIERS = ['slum', 'poor', 'middle', 'rich', 'palace']


def ex_houses():
    import culturegen as cg
    from houses import R as HR
    at = Atlas('houses_culture_kit', os.path.join(OUT, 'Buildings'))
    combos = [(r, w) for r in ROOFS for w in WALLS] + [('yurt', 'hide')]
    for (roof, wall) in combos:
        nv = 3 if roof == 'yurt' else 2
        for t in range(5):
            for v in range(nv):
                rng = random.Random(hash((roof, wall, t, v)) & 0xffff)
                orn = ORN_SETS[rng.randrange(len(ORN_SETS))]
                tall = rng.random() < .4
                seed = rng.randrange(1, 10 ** 6)

                def fn(w, ctx, roof=roof, wall=wall, t=t, orn=orn, tall=tall, seed=seed):
                    rr = ctx.v['ROOF'] if roof in ('gable', 'hip', 'dome', 'cone', 'tiered', 'yurt') else (HR['straw'] if roof == 'thatch' else HR['mud'])
                    g = dict(acc=ctx.v['ACC'], acc2=ctx.v['ACC2'], wall=wall, roof=roof, rroof=rr, orn=orn, tall=tall, nomad=roof == 'yurt', seed=seed)
                    return cg.gen_house(w, 22, 62, g, t, seed)
                key = f'h_{roof}_{wall}_{TIERS[t]}_{v}'
                at.add(key, up2(fn), 176, 140, (0, 124), regions=('ACC', 'ACC2', 'ROOF'),
                       tags={'roof': roof, 'wall': wall, 'tier': t, 'tier_name': TIERS[t], 'ornaments': orn, 'tall': tall, 'nomad': roof == 'yurt'})
                k, r2, m2, pv, tg, an = at.items[-1]
                ys, xs = np.nonzero(r2[..., 3] > 200)
                at.items[-1] = (k, r2, m2, ((xs.min() + xs.max()) // 2, pv[1]), tg, an)
    add_states(at)
    done('houses_culture_kit', at)


# ================================================================ PEOPLE (paper-doll bakes)
M_HEADS = ['turban', 'skullcap', 'flatcap', 'band', 'feathers', 'hood', 'bonnet', 'furhat', None]
F_HEADS = ['scarf', 'veil', 'kerchief', 'band', None]
CROWNS = ['crown_river', 'crown_north', 'circlet', 'furhat']


def ex_people():
    from people import person2
    at = Atlas('people', os.path.join(OUT, 'Characters'))
    head_y = {'adult': 8, 'child': 15, 'elder': 9}
    jobs = []
    for age in ('adult', 'elder', 'child'):
        classes = ['poor', 'middle', 'rich', 'ruler'] if age != 'child' else ['poor', 'middle']
        for gender in 'mf':
            gars = ['robe', 'pants', 'kilt'] if gender == 'm' else ['dress', 'pants']
            for cls in classes:
                heads = (CROWNS if cls == 'ruler' else (M_HEADS if gender == 'm' else F_HEADS))
                for gar in gars:
                    for hd in heads:
                        jobs.append((age, gender, cls, gar, hd))
    for (age, gender, cls, gar, hd) in jobs:
        keys = []
        for fr in range(4):
            def fn(a, ctx, age=age, gender=gender, cls=cls, gar=gar, hd=hd, fr=fr):
                g = dict(acc=ctx.v['ACC'], acc2=ctx.v['ACC2'], garment='robe' if gar == 'robe' else ('kilt' if gar == 'kilt' else 'pants'),
                         head=hd if gender == 'm' else 'band', fhead=hd if gender == 'f' else None, crown=hd, gold=True, values=['TRADITION'],
                         nomad=(gar == 'pants' and gender == 'f'), skins=['#c89a74'], hairs=['#3a2618'], paint=False)
                if cls == 'ruler': g['crown'] = hd
                person2(a, 2, 4, None, cls, age, gender, fr, seed=7, og=g)
            key = f'p_{age}_{gender}_{cls}_{gar}_{hd or "bare"}_{fr}'
            hy = head_y[age] - (1 if fr in (1, 3) else 0)
            at.add(key, fn, 20, 36, (9, 31), regions=('ACC', 'ACC2', 'SKIN', 'HAIR'),
                   tags={'age': age, 'gender': gender, 'class': cls, 'garment': gar, 'head': hd or 'bare', 'frame': fr},
                   anchors={'head': (9, hy), 'hand_r': (13 - [1, 0, -1, 0][fr], 23), 'hand_l': (1 + [1, 0, -1, 0][fr], 23)})
            keys.append(key)
        at.anim(f'walk_{age}_{gender}_{cls}_{gar}_{hd or "bare"}', keys, 6)
    # overlays: status & condition layers drawn over any person
    ov = {'bandage': lambda a, c: (hline(a, 5, 10, 7, hx('#f6f2ea')), put(a, 6, 10, hx('#e0503c'))),
          'sling': lambda a, c: (put(a, 4, 18, hx('#f6f2ea')), put(a, 5, 19, hx('#f6f2ea')), put(a, 6, 19, hx('#f6f2ea'))),
          'crutch': lambda a, c: vline(a, 16, 14, 17, hx('#8c6844')),
          'facepaint': lambda a, c: (put(a, 6, 12, hx('#c83a3a')), put(a, 9, 12, hx('#c83a3a'))),
          'sweat': lambda a, c: (put(a, 5, 9, hx('#9ad0f0')), put(a, 5, 10, hx('#9ad0f0'))),
          'torch': lambda a, c: (vline(a, 14, 16, 8, hx('#6b4c34')), put(a, 14, 15, hx('#f49a3c')), put(a, 14, 14, hx('#ffe27a')), put(a, 15, 15, hx('#d5452d')))}
    for k, f_ in ov.items():
        at.add(f'ov_{k}', f_, 20, 36, (9, 31), keep_canvas=True, tags={'overlay': k, 'note': 'same 20x36 frame as a person; draw on top'})
    done('people', at)


# ================================================================ ANIMALS
def ex_animals():
    from animals import draw, ALL
    at = Atlas('animals', os.path.join(OUT, 'Characters'))
    for n in ALL:
        for young in (False, True):
            keys = []
            for fr in range(4):
                key = f'a_{n}_{"young" if young else "adult"}_{fr}'
                gy = {}
                def fn(a, ctx, n=n, young=young, fr=fr):
                    gy['g'] = draw(a, 8, 8, n, fr, young, 3)
                probe = np.zeros((60, 70, 3), np.uint8); g = draw(probe, 8, 8, n, fr, young, 3)
                at.add(key, fn, 70, 60, (0, g), tags={'species': n, 'young': young, 'frame': fr})
                k, r2, m2, pv, tg, an = at.items[-1]
                ys, xs = np.nonzero(r2[..., 3] > 200)
                at.items[-1] = (k, r2, m2, ((xs.min() + xs.max()) // 2, pv[1]), tg, an)
                keys.append(key)
            at.anim(f'walk_{n}_{"young" if young else "adult"}', keys, 6)
            # dead pose = legs-up flip of frame 0
            k0 = at.items[-4]
            r2 = k0[1][::-1].copy(); m2 = k0[2][::-1].copy()
            import animals as _AN
            dkey = f'a_{n}_{"young" if young else "adult"}_dead' + ('_classic' if n in _AN.SP else '')   # fauna_land owns the plain _dead name
            at.add_array(dkey, r2, (r2.shape[1] // 2, r2.shape[0] - 2), {'species': n, 'young': young, 'pose': 'dead'})
    done('animals', at)


# ================================================================ ARMY: soldiers, mounts, machines
SOLDIERS = ['club', 'sling', 'hoplite', 'archer', 'knight', 'xbow', 'musket', 'gunner', 'rifle', 'flame', 'laser', 'pilot']


def ex_army():
    import weapons as W_
    from weapons import soldier, helmet, line, catapult, cannon, tank, drone, mech
    import army2 as A2
    from people import person2
    at = Atlas('army', os.path.join(OUT, 'Units'))
    ERA = {'club': 0, 'sling': 0, 'hoplite': 1, 'archer': 1, 'knight': 2, 'xbow': 2, 'musket': 3, 'gunner': 3, 'rifle': 4, 'flame': 4, 'laser': 5, 'pilot': 5}
    extra = {
        'pikeman': (2, lambda a, fr: (soldier(a, 8, 14, 'xbow', fr), helmet(a, 8, 14, 'kettle'), line(a, 19, 30, 30, 2, hx('#8c6844')), put(a, 30, 1, hx('#c8ced4')))),
        'javelin': (1, lambda a, fr: (person2(a, 8, 14, 'riverland', 'middle', 'adult', 'm', fr, seed=7, o_over=W_.outfit('archer')), helmet(a, 8, 14, 'bronze'), line(a, 19, 33, 24, 18, hx('#8c6844')))),
        'chieftain': (0, lambda a, fr: person2(a, 8, 14, 'highland', 'middle', 'adult', 'm', fr, seed=4, o_over=dict(W_.outfit('club'), head='feathers', hcol=[hx('#6e2a22'), hx('#8a3a30'), hx('#a84a3a')], cape=[R['K'][0], R['K'][1], R['K'][2]]))),
        'grenadier': (3, lambda a, fr: (soldier(a, 8, 14, 'musket', fr, seed=8), helmet(a, 8, 14, 'shako'))),
        'hussar_foot': (3, lambda a, fr: (soldier(a, 8, 14, 'gunner', fr), helmet(a, 8, 14, 'shako'))),
        'sniper': (4, lambda a, fr: (soldier(a, 8, 14, 'rifle', fr, seed=6), line(a, 19, 31, 30, 28, hx('#14110e')), put(a, 23, 28, hx('#8ad0e0')))),
        'medic': (4, lambda a, fr: (person2(a, 8, 14, 'highland', 'middle', 'adult', 'f', fr, seed=4, o_over=dict(W_.outfit('rifle'), top=[hx('#c9cdd2'), hx('#e6e9ec'), hx('#ffffff')])), helmet(a, 8, 14, 'modern'),
                                    rect(a, 11, 26, 6, 5, hx('#ffffff')), [put(a, 12 + i, 27 + j, hx('#3e9a4e')) for (i, j) in [(0, 0), (1, 0), (3, 0), (4, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2), (2, 3)]])),
        'shield_bearer': (5, lambda a, fr: (soldier(a, 8, 14, 'laser', fr, seed=3), A2.hexshield(a, 24, 27))),
    }
    for kind in SOLDIERS:
        keys = []
        for fr in range(4):
            def fn(a, ctx, kind=kind, fr=fr):
                soldier(a, 8, 14, kind, fr)
                if kind == 'gunner': helmet(a, 8, 14, 'shako')
            key = f'u_{kind}_{fr}'
            at.add(key, fn, 40, 48, (15, 41), regions=('TEAM', 'SKIN', 'HAIR'), tags={'unit': kind, 'era': ERA[kind], 'frame': fr},
                   anchors={'muzzle': (30, 31), 'hand_r': (19, 33)})
            keys.append(key)
        at.anim(f'walk_{kind}', keys, 6)
    for kind, (era, f_) in extra.items():
        keys = []
        for fr in range(4):
            key = f'u_{kind}_{fr}'
            at.add(key, lambda a, ctx, f_=f_, fr=fr: f_(a, fr), 40, 48, (15, 41), regions=('TEAM', 'SKIN', 'HAIR'), tags={'unit': kind, 'era': era, 'frame': fr})
            keys.append(key)
        at.anim(f'walk_{kind}', keys, 6)
    # mounted
    mounts = [('knight_lancer', 'horse', 'knight', 'knight', True, False, 2), ('hussar', 'horse', 'gunner', 'shako', False, True, 3),
              ('camel_lancer', 'camel', 'archer', 'bronze', True, False, 1), ('horse_archer', 'horse', 'archer', 'kettle', False, False, 1)]
    for (name, mount, kind, helm, lance, sabre, era) in mounts:
        keys = []
        for fr in range(4):
            key = f'm_{name}_{fr}'
            at.add(key, lambda a, ctx, mount=mount, kind=kind, helm=helm, lance=lance, sabre=sabre, fr=fr: A2.rider(a, 4, mount, kind, fr, helm, lance, sabre),
                   72, 40, (20, 38), regions=('TEAM', 'SKIN', 'HAIR'), tags={'unit': name, 'mount': mount, 'era': era, 'frame': fr})
            keys.append(key)
        at.anim(f'walk_{name}', keys, 6)
    # machines (ground)
    B = 37
    machines = {
        'catapult_0': (2, lambda a: catapult(a, 4, B, 0)), 'catapult_1': (2, lambda a: catapult(a, 4, B, 1)), 'trebuchet': (2, lambda a: A2.trebuchet(a, 6)),
        'battering_ram': (1, lambda a: A2.ram(a, 8)), 'cannon': (3, lambda a: cannon(a, 6, B)), 'gatling': (3, lambda a: A2.gatling(a, 8)),
        'tank': (4, lambda a: tank(a, 2, B)), 'howitzer': (4, lambda a: A2.howitzer(a, 6)), 'hover_tank': (5, lambda a: A2.hovertank(a, 4)),
        'exo_mech': (5, lambda a: mech(a, 4, B)), 'drone_side_0': (5, lambda a: drone(a, 4, 4, 0)), 'drone_side_1': (5, lambda a: drone(a, 4, 4, 1)),
        'zeppelin': (3, lambda a: A2.zeppelin(a, 2, 2)), 'gunship_side_0': (4, lambda a: A2.heli(a, 18, 4, 0)), 'gunship_side_1': (4, lambda a: A2.heli(a, 18, 4, 1)),
    }
    for name, (era, f_) in machines.items():
        at.add(f'x_{name}', lambda a, ctx, f_=f_: f_(a), 72, 40, (36, 38), regions=('TEAM',), tags={'machine': name, 'era': era})
        k, r2, m2, pv, tg, an = at.items[-1]
        at.items[-1] = (k, r2, m2, (r2.shape[1] // 2, r2.shape[0] - 2), tg, an)
    at.anim('catapult_fire', ['x_catapult_0', 'x_catapult_1'], 3, False)
    at.anim('drone_hover', ['x_drone_side_0', 'x_drone_side_1'], 12)
    at.anim('gunship_side', ['x_gunship_side_0', 'x_gunship_side_1'], 12)
    done('army', at)


# ================================================================ AIR
def ex_air():
    import air
    at = Atlas('aircraft', os.path.join(OUT, 'Units'))
    sc = {'fighter': 1.5, 'stealth': 1.5, 'interceptor': 1.4, 'bomber': 1.05, 'wing': 1.05, 'transport': 1.1, 'recon': 1.5, 'loiter': 1.9}
    for n in air.PLANES:
        for d in range(8):
            def fn(a, ctx, n=n, d=d):
                s = air.plane(n, d * 45, scale=sc[n], size=64)
                h, w = s[1].shape
                air.paste(a, s, (64 - w) // 2, (64 - h) // 2)
            at.add(f'air_{n}_{d * 45}', fn, 64, 64, (32, 32), regions=('TEAM',), tags={'aircraft': n, 'angle': d * 45, 'note': 'top-down; draw shadow copy at +alt/3,+alt'})
            k, r2, m2, pv, tg, an = at.items[-1]
            at.items[-1] = (k, r2, m2, (r2.shape[1] // 2, r2.shape[0] // 2), tg, an)
    for d in range(8):
        keys = []
        for fr in range(4):
            key = f'air_heli_{d * 45}_{fr}'
            at.add(key, lambda a, ctx, d=d, fr=fr: air.heli_top(a, 32, 32, 0, d * 45, fr), 64, 64, (32, 32), regions=('TEAM',), tags={'aircraft': 'heli', 'angle': d * 45, 'frame': fr})
            k, r2, m2, pv, tg, an = at.items[-1]
            at.items[-1] = (k, r2, m2, (r2.shape[1] // 2, r2.shape[0] // 2), tg, an)
            keys.append(key)
        at.anim(f'heli_rotor_{d * 45}', keys, 16)
    done('aircraft', at)
    ad = Atlas('air_defence', os.path.join(OUT, 'Units'))
    for name, f_, n in (('sam', air.sam, 4), ('radar', air.radar, 4), ('flak', air.flak, 2), ('ciws', air.ciws, 2), ('laser_ad', air.laser_ad, 2)):
        keys = []
        for k in range(n):
            key = f'ad_{name}_{k}'
            ad.add(key, lambda a, ctx, f_=f_, k=k: f_(a, 8, 52, k), 72, 56, (24, 53), regions=('TEAM',), tags={'unit': name, 'frame': k})
            keys.append(key)
        ad.anim(name, keys, 4, name != 'sam')
    ad.add('airbase', lambda a, ctx: air.airbase(a, 4, 16), 132, 52, (66, 48), regions=('TEAM',), tags={'building': 'airbase', 'era': 4})
    done('air_defence', ad)


# ================================================================ FX
def ex_fx():
    import air
    from catalog import fine_fx
    import weapons as W_
    import anim as AN
    at = Atlas('fx', os.path.join(OUT, 'FX'))
    def put_fx(key, f_, W=40, H=40, piv=None, tags=None, anim=None):
        at.add(key, lambda a, ctx: f_(a), W, H, piv or (W // 2, H // 2), tags=tags or {})
    for s in range(3):
        for k in range(4): put_fx(f'boom_{s}_{k}', lambda a, s=s, k=k: air.boom(a, 20, 22, [.6, 1.0, 1.6][s], k), 48, 48, (24, 28), {'fx': 'explosion', 'size': s, 'frame': k})
        at.anim(f'explosion_{s}', [f'boom_{s}_{k}' for k in range(4)], 10, False)
    for d in range(8):
        put_fx(f'missile_{d * 45}', lambda a, d=d: air.missile(a, 20, 20, d * 45, 0), 40, 40, None, {'fx': 'missile', 'angle': d * 45})
        put_fx(f'arrow_{d * 45}', lambda a, d=d: AN.line_ang(a, 20, 20, d * 45) if hasattr(AN, 'line_ang') else _arrow(a, 20, 20, d * 45), 30, 30, None, {'fx': 'arrow', 'angle': d * 45})
    for i in range(6): put_fx(f'smoke_{i}', lambda a, i=i: blend_mask(a, ellipse_mask(a.shape[:2], 12, 12, 2 + i, 1.8 + i * .8), (200 - i * 8,) * 3, .7 - i * .08), 24, 24, None, {'fx': 'smoke', 'size': i})
    at.anim('smoke_rise', [f'smoke_{i}' for i in range(6)], 6, False)
    for k in range(3):
        def fire(a, k=k):
            pat = [["..y..", ".yoy.", "yoroy", "orrro", ".rrr."], [".y...", ".yoy.", "yoroy", "orrro", ".rrr."], ["...y.", ".yoy.", "yoroy", "orrro", ".rrr."]][k]
            cm = {'y': C['fire'][2], 'o': C['fire'][1], 'r': C['fire'][0]}
            blend_mask(a, ellipse_mask(a.shape[:2], 8, 9, 7, 5), hx('#ffb35a'), .25)
            for j, row in enumerate(pat):
                for i, ch in enumerate(row):
                    if ch != '.': put(a, 6 + i, 4 + j, cm[ch])
        put_fx(f'fire_{k}', fire, 16, 14, (8, 10), {'fx': 'fire', 'frame': k})
    at.anim('fire', [f'fire_{k}' for k in range(3)], 8)
    for k in range(3): put_fx(f'flame_jet_{k}', lambda a, k=k: W_.fx_flame(a, 2, 14, 40, k + 1), 50, 28, (2, 14), {'fx': 'flamethrower', 'frame': k})
    at.anim('flame_jet', [f'flame_jet_{k}' for k in range(3)], 12)
    put_fx('laser_segment', lambda a: W_.fx_laser(a, 0, 4, 16), 16, 9, (0, 4), {'fx': 'laser', 'note': 'tile horizontally, rotate in engine'})
    put_fx('muzzle_flash', lambda a: W_.fx_flash(a, 2, 3), 8, 7, (2, 3), {'fx': 'muzzle'})
    put_fx('tracer', lambda a: hline(a, 1, 2, 5, hx('#ffe27a')), 8, 5, (1, 2), {'fx': 'tracer'})
    for s in (1, 2, 3): put_fx(f'bomb_{s}', lambda a, s=s: air.bomb(a, 3, 2, s), 8, 8, (4, 2), {'fx': 'bomb', 'size': s})
    for k in range(2): put_fx(f'flares_{k}', lambda a, k=k: air.flares(a, 26, 14, k), 32, 28, (26, 14), {'fx': 'flares', 'frame': k})
    for kind in ('alert', 'infected', 'sick', 'immune', 'food', 'heal'): put_fx(f'status_{kind}', lambda a, kind=kind: AN.bubble(a, 1, 1, kind), 9, 9, (4, 8), {'fx': 'status', 'kind': kind})
    for i, r_ in enumerate((2.2, 3.0, 3.8)): put_fx(f'cough_{i}', lambda a, r_=r_: AN.cloud(a, 10, 8, r_, AN.GRN, .6), 20, 16, (10, 8), {'fx': 'cough', 'frame': i})
    at.anim('cough', ['cough_0', 'cough_1', 'cough_2'], 6, False)
    for k in range(2): put_fx(f'flies_{k}', lambda a, k=k: [put(a, 3 + ((i * 5 + k * 3) % 10), 2 + ((i * 3 + k) % 6), hx('#14110e')) for i in range(4)], 16, 10, (8, 9), {'fx': 'flies', 'frame': k})
    for k in range(2): put_fx(f'sparkle_{k}', lambda a, k=k: [put(a, x, y, hx('#ecc25c')) for (x, y) in ([(2, 4), (8, 1), (11, 7), (5, 9)] if k == 0 else [(4, 2), (10, 4), (7, 9), (1, 7)])], 14, 12, (7, 11), {'fx': 'sparkle', 'frame': k})
    for k in range(3): put_fx(f'hit_spark_{k}', lambda a, k=k: [put(a, 6 + int((2 + k * 2) * math.cos(t)), 6 + int((2 + k * 2) * math.sin(t)), hx('#ffffff')) for t in np.linspace(0, 6.28, 6, endpoint=False)], 13, 13, (6, 6), {'fx': 'hit', 'frame': k})
    for k in range(3): put_fx(f'dust_{k}', lambda a, k=k: blend_mask(a, ellipse_mask(a.shape[:2], 8, 6, 2 + k * 2, 1.5 + k), hx('#c8b88a'), .7 - k * .2), 16, 10, (8, 8), {'fx': 'dust', 'frame': k})
    for k in range(3): put_fx(f'splash_{k}', lambda a, k=k: [put(a, 7 + int((1 + k * 2) * math.cos(t)), 6 - int((2 + k) * abs(math.sin(t))), hx('#d6eef2')) for t in np.linspace(0, 3.14, 7)], 15, 10, (7, 8), {'fx': 'splash', 'frame': k})
    put_fx('raindrop', lambda a: vline(a, 1, 0, 3, hx('#9ad0f0')), 3, 4, (1, 3), {'fx': 'rain'})
    put_fx('snowflake', lambda a: (put(a, 1, 1, hx('#ffffff')), put(a, 0, 1, hx('#d8e4ec')), put(a, 2, 1, hx('#d8e4ec')), put(a, 1, 0, hx('#d8e4ec')), put(a, 1, 2, hx('#d8e4ec'))), 3, 3, (1, 1), {'fx': 'snow'})
    for k in range(3):
        def bolt(a, k=k):
            r = random.Random(k); x = 8
            for y in range(0, 40):
                x += r.choice([-1, 0, 1]) if y % 3 == 0 else 0
                put(a, x, y, hx('#fff2b0')); put(a, x + 1, y, hx('#ffd34a'))
            blend_mask(a, ellipse_mask(a.shape[:2], x, 38, 6, 3), hx('#fff2b0'), .5)
        put_fx(f'lightning_{k}', bolt, 18, 42, (9, 40), {'fx': 'lightning', 'frame': k})
    put_fx('meteor', lambda a: (dome(a, 20, 20, 5, 5, [hx('#3a2a20'), hx('#6a3a2a'), hx('#b8582e'), hx('#f49a3c'), hx('#ffe27a')], 2), [blend_mask(a, ellipse_mask(a.shape[:2], 20 - i * 3, 20 - i * 3, 4 - i * .4, 4 - i * .4), hx('#f49a3c'), .5 - i * .06) for i in range(6)]), 30, 30, (20, 20), {'fx': 'meteor'})
    done('fx', at)


def _arrow(a, x, y, ang):
    t = math.radians(ang)
    for i in range(8): put(a, int(x + (i - 4) * math.cos(t)), int(y + (i - 4) * math.sin(t)), hx('#8c6844'))
    put(a, int(x + 4 * math.cos(t)), int(y + 4 * math.sin(t)), hx('#c8ced4'))
    put(a, int(x - 4 * math.cos(t)), int(y - 4 * math.sin(t)), hx('#e8e2d4'))


# ================================================================ NATURE PROPS
def ex_nature():
    import terrain as T_
    from culturecity import pine
    from buildings import campfire
    at = Atlas('nature_props', os.path.join(OUT, 'Nature'))
    def addw(key, f_, W=24, H=28, gy=None, tags=None):
        at.add(key, up2(lambda w, ctx, f_=f_: f_(w)), W * 2, H * 2, (W, (gy or H - 2) * 2), tags=tags or {})
        k, r2, m2, pv, tg, an = at.items[-1]
        ys, xs = np.nonzero(r2[..., 3] > 200)
        at.items[-1] = (k, r2, m2, ((xs.min() + xs.max()) // 2, pv[1]), tg, an)
    for s in (2, 3, 4, 5):
        for v in range(3): addw(f'tree_{s}_{v}', lambda w, s=s, v=v: tree(w, 10, 18 - s, s, v * 13 + s), tags={'prop': 'tree', 'size': s})
    for v in range(3): addw(f'palm_{v}', lambda w, v=v: palm(w, 10, 12, v), tags={'prop': 'palm'})
    for s in (3, 4, 5):
        for snow in (False, True): addw(f'pine_{s}_{"snow" if snow else "green"}', lambda w, s=s, snow=snow: pine(w, 10, 22 - s * 2, s, s, snow), tags={'prop': 'pine', 'size': s, 'snow': snow})
    for v in range(3): addw(f'bush_{v}', lambda w, v=v: bush(w, 10, 22, v), tags={'prop': 'bush'})
    for s in (1.4, 1.8, 2.4):
        for v in range(2): addw(f'rock_{s}_{v}', lambda w, s=s, v=v: rock(w, 10, 22, s, v), tags={'prop': 'rock', 'size': s})
    for v in range(2): addw(f'cactus_{v}', lambda w, v=v: T_.cactus(w, 10 + v, 16), tags={'prop': 'cactus'})
    for v in range(2): addw(f'deadtree_{v}', lambda w, v=v: T_.deadtree(w, 10 + v, 15), tags={'prop': 'deadtree'})
    addw('reeds', lambda w: T_.reeds(w, 9, 20), tags={'prop': 'reeds'})
    for v in range(2): addw(f'fern_{v}', lambda w, v=v: T_.fern(w, 10 + v, 20), tags={'prop': 'fern'})
    for big in (False, True): addw(f'mushroom_{"big" if big else "small"}', lambda w, big=big: T_.mushroom(w, 10, 20, big), tags={'prop': 'mushroom'})
    for c in ('#5fe0e8', '#c45aa8', '#8a7ae8'): addw(f'crystal_{c[1:]}', lambda w, c=c: T_.crystal(w, 9, 18, hx(c)), tags={'prop': 'crystal'})
    for c in ('#e87a8a', '#f0a050', '#c45aa8', '#e8e070'): addw(f'coral_{c[1:]}', lambda w, c=c: T_.coral(w, 8, 20, hx(c)), tags={'prop': 'coral'})
    addw('iceblock', lambda w: T_.iceblock(w, 8, 20), tags={'prop': 'ice'})
    for v in range(2): addw(f'lava_pool_{v}', lambda w, v=v: T_.lavapool(w, 12, 18, 5 + v * 2, 3 + v, v), 24, 24, tags={'prop': 'lava'})
    addw('campfire', lambda w: campfire(w, 9, 20), tags={'prop': 'campfire', 'fx': 'fire'})
    for i, col in enumerate(('#e8c84a', '#d5452d', '#c45aa8')):
        addw(f'flowers_{i}', lambda w, col=col: [put(w, 6 + (k * 5) % 10, 16 + (k * 3) % 6, hx(col)) for k in range(7)], tags={'prop': 'flowers'})
    done('nature_props', at)


# ================================================================ TERRAIN TILES
def seamless(t):
    n = t.shape[0]
    w = (np.sin(np.linspace(0, np.pi, n, endpoint=False)) ** 2)
    A = t.astype(float)
    Bx = np.roll(A, n // 2, axis=1)
    X = A * w[None, :, None] + Bx * (1 - w[None, :, None])
    By = np.roll(X, n // 2, axis=0)
    Y = X * w[:, None, None] + By * (1 - w[:, None, None])
    return Y.astype(np.uint8)


def ex_terrain():
    import terrain as T_
    at = Atlas('terrain_tiles', os.path.join(OUT, 'Terrain'))
    for i, (name, cols, props, speck) in enumerate(T_.BIOMES):
        for v in range(4):
            g = T_.ground(32, 32, cols, i * 31 + v, cell=8, speck=speck.split(',') if speck else None, nspeck=14 if speck else 0)
            g = seamless(g)
            if name == 'FARMLAND':
                T_.crops(g, 0, 0, 32, 32, ['#c9a94e', '#6ea447', '#d8bb5e', '#8fae68'][v])
            f = upscale(g, 2)
            rgba = np.dstack([f, np.full(f.shape[:2], 255, np.uint8)])
            at.add_array(f't_{name.lower().replace(" ", "_")}_{v}', rgba, (0, 0), {'biome': name, 'variant': v, 'tile_px': 64, 'tileable': True})
    # water depth tiles + foam edges
    for d, c in enumerate(('#1d4a82', '#255c98', '#3277b0')):
        g = np.zeros((32, 32, 3), np.uint8); g[:] = hx(c)
        r = np.random.default_rng(d)
        for _ in range(16): x, y = r.integers(0, 29), r.integers(0, 32); hline(g, x, y, 3, lit(hx(c), .15))
        f = upscale(g, 2); at.add_array(f'water_depth_{d}', np.dstack([f, np.full(f.shape[:2], 255, np.uint8)]), (0, 0), {'water': d, 'tile_px': 64})
    for k in range(2):
        f = np.zeros((8, 64, 4), np.uint8)
        for x in range(64):
            h = 2 + int(1.5 * math.sin(x / 5 + k))
            for y in range(h): f[y, x] = (*hx('#d6eef2'), 255 if y < h - 1 else 150)
        at.add_array(f'shore_foam_{k}', f, (0, 0), {'edge': 'foam', 'frame': k, 'note': 'lay along water side of shore, rotate per edge'})
    # cliff faces: 1..4 level steps (6 fine px per level), 3 materials, rim highlight
    for mat, base in (('earth', '#6a5a46'), ('stone', '#5f5b55'), ('snow', '#c8d0d8')):
        for lv in range(1, 5):
            h = lv * 6
            f = np.zeros((h + 2, 64, 4), np.uint8)
            for y in range(h + 2):
                for x in range(64):
                    c = lit(hx(base), -.05 * ((x // 3 + y) % 3) - (.12 if y > 6 else 0))
                    if (x * 7 + y * 3) % 17 == 0: c = lit(c, -.15)
                    f[y, x] = (*c, 255)
            at.add_array(f'cliff_{mat}_{lv}', f, (0, 0), {'cliff': mat, 'levels': lv, 'px_per_level': 6, 'tileable_x': True})
    done('terrain_tiles', at)


# ================================================================ UI KIT
def ex_ui():
    import ui2kit as K
    import strategic as ST
    ST.add_icons()
    at = Atlas('ui_kit', os.path.join(OUT, 'UI'))
    def ui(key, f_, W, H, tags, regions=('TEAM',)):
        at.add(key, lambda a, ctx: f_(a), W, H, (0, 0), regions=regions, tags=tags, keep_canvas=True)
    # panels need a transparent background: draw on black and keep alpha from the frame only
    ui('frame_9slice', lambda a: K.frame(a, 0, 0, 48, 48, R['K'], alpha=1.0), 48, 48, {'ui': 'frame', 'slice': [8, 8, 8, 8], 'note': '9-slice borders 8 px; TEAM = kingdom colour'})
    ui('ribbon', lambda a: K.ribbon(a, 30, 5, 'X' * 0 + ' ', None, R['K'], 40), 60, 22, {'ui': 'ribbon', 'slice': [8, 0, 8, 0]})
    for st in ('ghost', 'primary', 'gold', 'on'):
        ui(f'button_{st}', lambda a, st=st: K.button(a, 0, 0, 32, 16, '', style=st, rp=R['K']), 34, 18, {'ui': 'button', 'style': st, 'slice': [3, 3, 3, 3]})
    ui('meter_frame', lambda a: K.meter(a, 0, 0, 40, 8, 0, hx('#7cc46a')), 40, 8, {'ui': 'meter', 'slice': [2, 2, 2, 2]}, ())
    ui('gem', lambda a: K.gem(a, 0, 0, R['K']), 7, 7, {'ui': 'gem'})
    for name in K.PI:
        at.add(f'picon_{name}', lambda a, ctx, name=name: K.picon(a, 0, 0, name), 11, 11, (0, 0), keep_canvas=True, tags={'ui': 'power_icon'})
        at.add(f'picon_{name}_x2', lambda a, ctx, name=name: K.picon(a, 0, 0, name, 2), 22, 22, (0, 0), keep_canvas=True, tags={'ui': 'power_icon', 'scale': 2})
    for name in ICONS:
        at.add(f'icon_{name}', lambda a, ctx, name=name: icon(a, 0, 0, name), 7, 7, (0, 0), keep_canvas=True, tags={'ui': 'icon'})
        at.add(f'icon_{name}_x2', lambda a, ctx, name=name: icon(a, 0, 0, name, 2), 14, 14, (0, 0), keep_canvas=True, tags={'ui': 'icon', 'scale': 2})
    # crest parts: shield (ACC/ACC2 recolour) + symbols
    import culturegen as cg
    for split in ('plain', 'pale', 'fess', 'chevron'):
        def sh(a, ctx, split=split):
            shape = ["###########"] * 8 + [".#########.", ".#########.", "..#######..", "...#####...", "....###...."]
            for j, row in enumerate(shape):
                for i, c in enumerate(row):
                    if c != '#': continue
                    cc = ctx.v['ACC'][2]
                    if split == 'pale' and i >= 6: cc = ctx.v['ACC'][1]
                    if split == 'fess' and j >= 6: cc = ctx.v['ACC'][1]
                    if split == 'chevron' and 4 + abs(i - 5) <= j < 7 + abs(i - 5): cc = ctx.v['ACC2'][2]
                    if j == 0 or i == 0: cc = lit(cc, .2)
                    put(a, i, j, cc)
        at.add(f'crest_shield_{split}', sh, 11, 13, (0, 0), regions=('ACC', 'ACC2'), keep_canvas=True, tags={'ui': 'crest_shield'})
    for sym, rows in cg.SYMBOLS.items():
        at.add(f'crest_symbol_{sym}', lambda a, ctx, rows=rows: [put(a, i, j, hx('#f3e6c8')) for j, row in enumerate(rows) for i, c in enumerate(row) if c == '#'], 5, 7, (0, 0), keep_canvas=True,
               tags={'ui': 'crest_symbol', 'offset_in_shield': [3, 2], 'note': 'tint gold for GREEDY/GRANDEUR cultures'})
    # reticle + selection ring
    at.add('reticle', lambda a, ctx: [put(a, int(24 + 22 * math.cos(t)), int(24 + 22 * math.sin(t)), hx('#ffd34a')) for t in np.linspace(0, 6.28, 80) if int(t * 8) % 2], 49, 49, (24, 24), keep_canvas=True, tags={'ui': 'reticle'})
    at.add('select_ring', lambda a, ctx: [put(a, int(10 + 9 * math.cos(t)), int(5 + 4 * math.sin(t)), K.GOLD[3]) for t in np.linspace(0, 6.28, 40)], 21, 11, (10, 5), keep_canvas=True, tags={'ui': 'selection'})
    done('ui_kit', at)
    # bitmap fonts (5x7 UI font + 3x5 world font) as glyph atlases
    fa = Atlas('font_5x7', os.path.join(OUT, 'UI'))
    for ch, g in K._F.items():
        w = len(g[0])
        name = {' ': 'space', '.': 'dot', ',': 'comma', ':': 'colon', '-': 'minus', '+': 'plus', '%': 'percent', '/': 'slash', '!': 'excl', '?': 'quest', "'": 'apos',
                '(': 'lparen', ')': 'rparen', '>': 'gt', '<': 'lt', '|': 'bar', '*': 'dotmid', '^': 'up', '#': 'hash'}.get(ch, ch)
        rgba = np.zeros((7, max(w, 1), 4), np.uint8)
        for j, row in enumerate(g):
            for i, c in enumerate(row):
                if c == '#': rgba[j, i] = (255, 255, 255, 255)
        fa.add_array(f'g_{name}', rgba, (0, 0), {'char': ch, 'advance': w + 1, 'note': 'white glyph; tint in engine; add 1px INK drop shadow at +1,+1'})
    done('font_5x7', fa)


# ================================================================ STRATEGIC (ballistic & nuclear)
def ex_strategic():
    import strategic as ST
    import anim as AN
    at = Atlas('strategic', os.path.join(OUT, 'Units'))
    keys = []
    for k in range(6):
        key = f'st_tel_{k}'
        at.add(key, lambda a, ctx, k=k: ST.tel(a, 10, 50, k), 88, 56, (34, 50), regions=('TEAM',), tags={'unit': 'tel', 'era': 4, 'frame': k,
               'note': '0 travel, 1-2 erect, 3 vertical, 4 ignition, 5 lift-off (then spawn a missile_flight sprite)'})
        keys.append(key)
    at.anim('tel_launch', keys, 3, False)
    keys = []
    for k in range(4):
        key = f'st_silo_{k}'
        at.add(key, lambda a, ctx, k=k: ST.silo(a, 18, 54, k), 88, 60, (41, 54), regions=('TEAM',), tags={'building': 'missile_silo', 'era': 4, 'frame': k})
        keys.append(key)
    at.anim('silo_launch', keys, 3, False)
    for k in range(2):
        at.add(f'st_abm_battery_{k}', lambda a, ctx, k=k: ST.abm_battery(a, 20, 50, k), 88, 56, (35, 50), regions=('TEAM',), tags={'unit': 'abm_battery', 'era': 4, 'frame': k})
    at.anim('abm_battery_fire', ['st_abm_battery_0', 'st_abm_battery_1', 'st_abm_battery_0'], 4, False)
    for kind in ST.MISSILES:
        for d in range(16):
            fk = []
            for fr in range(2):
                key = f'st_{kind}_{int(d * 22.5 * 10)}_{fr}'
                at.add(key, lambda a, ctx, kind=kind, d=d, fr=fr: ST.missile_flight(a, kind, d * 22.5, fr, 40, 40), 80, 80, (40, 40), regions=('TEAM',),
                       tags={'missile': kind, 'angle': d * 22.5, 'frame': fr, 'note': 'angle key = degrees x10; pivot = missile centre; flame included'})
                k_, r2, m2, pv, tg, an = at.items[-1]
                fk.append(key)
            at.anim(f'{kind}_{int(d * 22.5 * 10)}', fk, 12)
    for k in range(2):
        at.add(f'st_reentry_{k}', lambda a, ctx, k=k: ST.reentry(a, k), 40, 40, (20, 29), tags={'fx': 'reentry', 'frame': k})
    at.anim('reentry', ['st_reentry_0', 'st_reentry_1'], 10)
    nk = []
    for k in range(13):
        key = f'nuke_{k}'
        at.add(key, lambda a, ctx, k=k: ST.nuke(a, k, 80, 150), 160, 160, (80, 150), tags={'fx': 'nuclear_detonation', 'frame': k,
               'note': '0-1 flash (also flash the whole screen white), 2-4 fireball, 5-10 mushroom cloud, 11-12 dissipating'})
        nk.append(key)
    at.anim('nuclear_detonation', nk, 5, False)
    for k in range(4):
        at.add(f'shockwave_{k}', lambda a, ctx, k=k: ST.shockwave(a, k, 90, 40), 180, 80, (90, 40), tags={'fx': 'shockwave', 'frame': k, 'layer': 'ground decal'})
    at.anim('shockwave', [f'shockwave_{k}' for k in range(4)], 10, False)
    at.add('crater_nuclear', lambda a, ctx: ST.crater(a, 40, 20, 1.0), 84, 42, (40, 20), tags={'decal': 'crater', 'layer': 'ground decal'})
    for k in range(2):
        at.add(f'fallout_{k}', lambda a, ctx, k=k: ST.fallout_overlay(a, k), 84, 34, (42, 17), tags={'decal': 'fallout', 'frame': k, 'layer': 'overlay, drifts with wind'})
    at.anim('fallout', ['fallout_0', 'fallout_1'], 2)
    at.add('radiation_glow', lambda a, ctx: ST.radiation_glow(a, 24, 12), 48, 24, (24, 12), tags={'decal': 'radiation', 'layer': 'additive overlay'})
    at.add('hazard_marker', lambda a, ctx: ST.hazard_sign(a, 1, 1, 1), 16, 16, (7, 13), tags={'prop': 'hazard_marker', 'note': 'original WorldSim design, placed around irradiated zones'})
    at.add('grave_marker', lambda a, ctx: AN.grave(a, 2, 12), 12, 14, (5, 12), tags={'prop': 'grave', 'note': 'plain headstone, no symbols'})
    done('strategic', at)


def write_index():
    """atlas_index.json: every atlas JSON (path relative to WorldSimArt, no extension) for the runtime loader."""
    found = []
    for dp, dn, fn in os.walk(OUT):
        for f_ in fn:
            if f_.endswith('.json') and f_ not in ('atlas_index.json', 'export_stats.json'):
                found.append(os.path.relpath(os.path.join(dp, f_), OUT).replace(os.sep, '/')[:-5])
    json.dump({'atlases': sorted(found)}, open(os.path.join(OUT, 'atlas_index.json'), 'w'), indent=1)
    print('index', len(found), 'atlases')


import export_creatures as EC
EC.OUT = OUT; EC.DONE = done
CATS = {'buildings': ex_buildings, 'houses': ex_houses, 'people': ex_people, 'animals': ex_animals, 'army': ex_army, 'air': ex_air,
        'fx': ex_fx, 'nature': ex_nature, 'terrain': ex_terrain, 'ui': ex_ui, 'strategic': ex_strategic}
CATS.update(EC.CATS)
import export_humans as EH
EH.OUT = OUT; EH.DONE = done
CATS.update(EH.CATS)
import export_world as EW
EW.OUT = OUT; EW.DONE = done; EW.ADD_STATES = add_states
CATS.update(EW.CATS)
import phase4 as P4
P4.OUT = OUT; P4.DONE = done
CATS.update(P4.CATS)
import disaster_states as DS
def ex_disasters():
    DS.bake(OUT, 'Buildings/buildings_eras', 'disaster_buildings_eras', os.path.join(OUT, 'Buildings', 'Disaster'), DONE=done)
    DS.bake(OUT, 'Buildings/houses_culture_kit', 'disaster_houses', os.path.join(OUT, 'Buildings', 'Disaster'), DONE=done)
    DS.bake(OUT, 'Buildings/world_structures', 'disaster_structures', os.path.join(OUT, 'Buildings', 'Disaster'),
            filt=lambda n: n.split('_')[0] in ('wall', 'keep', 'dock', 'barn', 'market', 'well', 'wonder', 'sanctum', 'statue', 'fountain', 'bridge'), DONE=done)
    DS.decals(os.path.join(OUT, 'FX', 'Decals'), done)
    DS.overlays(os.path.join(OUT, 'Buildings', 'Disaster'), done)
    DS.annotate(OUT, ['Buildings/buildings_eras', 'Buildings/houses_culture_kit', 'Buildings/world_structures',
                      'Buildings/Disaster/disaster_buildings_eras', 'Buildings/Disaster/disaster_houses', 'Buildings/Disaster/disaster_structures'])
CATS['disasters'] = ex_disasters

if __name__ == '__main__':
    todo = sys.argv[1:] or list(CATS)
    t0 = time.time()
    for c in todo:
        t = time.time(); CATS[c](); print(f'   ({time.time() - t:.1f}s)', flush=True)
    stats_path = os.path.join(OUT, 'export_stats.json')
    old = json.load(open(stats_path)) if os.path.exists(stats_path) else {}
    old.update({k: {'sprites': v[0], 'pages': v[1]} for k, v in STATS.items()})
    json.dump(old, open(stats_path, 'w'), indent=1)
    write_index()
    print('total time', round(time.time() - t0, 1))
