"""Phase 1 creature / magic export: fauna (land, birds, small critters), sea life, biome creatures, magic beasts,
supernatural beings, titans and spells.  Every animation gets event markers (hit / spawn / sfx) for gameplay sync.
Post-processed states shared by everything that can die: hurt, dead, remains (eaten), burnt, frozen, dissolve."""
import os, math, random
import numpy as np
from PIL import Image
from lib import *
from xcore import Atlas
import animals as AN
import bestiary as BS
import beings as BE
import spells as SPL

OUT = None   # set by export_all
DONE = None

# ------------------------------------------------------------------ post-process states
def _bbox(rgba, thr=200):
    ys, xs = np.nonzero(rgba[..., 3] > thr)
    if not len(xs): ys, xs = np.nonzero(rgba[..., 3] > 0)
    return xs.min(), xs.max(), ys.min(), ys.max()


def hurt(rgba):
    o = np.zeros_like(rgba); o[:, :-1] = rgba[:, 1:]          # recoil 1 px back
    op = o[..., 3] > 0
    o[op, :3] = (o[op, :3] * .6 + np.array([230, 60, 50]) * .4).astype(np.uint8)
    return o


def dead_flip(rgba):
    o = rgba[::-1].copy(); op = o[..., 3] > 0
    o[op, :3] = (o[op, :3] * .82).astype(np.uint8)
    return o


def remains(rgba, seed=0):
    """eaten remains, cartoon-clean (STYLE_GUIDE no gore): pale bone silhouette with gaps, a little dust; no red."""
    r = random.Random(seed)
    o = dead_flip(rgba)
    op = o[..., 3] > 200
    x0, x1, y0, y1 = _bbox(o)
    meat, dark, bone = np.array([200, 190, 168]), np.array([170, 160, 140]), np.array([236, 228, 210])
    for y in range(o.shape[0]):
        for x in range(o.shape[1]):
            if not op[y, x]: continue
            if r.random() < .22: o[y, x] = 0; continue
            if (x - x0) % 3 == 0 and y < (y0 + y1) / 2 + 1: o[y, x, :3] = bone
            else: o[y, x, :3] = meat if (x + y) % 4 else dark
    for _ in range(4):
        x, y = r.randint(x0, x1), y1 + 1
        if y < o.shape[0]: o[y, x] = (200, 184, 150, 200)
    return o


def burnt(rgba):
    o = dead_flip(rgba); op = o[..., 3] > 0
    l = o[op, :3].mean(axis=1, keepdims=True)
    o[op, :3] = np.clip(l * .35 + np.array([18, 14, 12]), 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(o[..., 3] > 200)
    rr = random.Random(len(xs))
    for i in rr.sample(range(len(xs)), max(1, len(xs) // 25)): o[ys[i], xs[i], :3] = (240, 120, 40)
    return o


def frozen(rgba):
    o = rgba.copy(); op = o[..., 3] > 0
    l = o[op, :3].mean(axis=1, keepdims=True)
    o[op, :3] = np.clip(l * .55 + np.array([110, 170, 210]) * .5, 0, 255).astype(np.uint8)
    x0, x1, y0, y1 = _bbox(o)
    for x in range(x0, x1 + 1, 3):
        if o[y0 + 1, x, 3] > 0: o[y0 + 1, x, :3] = (240, 250, 255)
    return o


def dissolve(rgba, t, col=(200, 160, 240), seed=0):
    o = rgba.copy(); op = np.argwhere(o[..., 3] > 0)
    rr = np.random.default_rng(seed)
    kill = rr.random(len(op)) < t
    for (y, x), k in zip(op, kill):
        if k: o[y, x] = 0
        elif rr.random() < t * .6: o[y, x, :3] = col
    return o


def fall(rgba, pivot, ang):
    """rotate around the feet (pivot) towards the back (ccw) - used for biped deaths."""
    rgba = rgba.copy(); rgba[rgba[..., 3] < 200] = 0          # drop shadow / ground glow before rotating
    H, W = rgba.shape[:2]
    pad = max(H, W)
    big = np.zeros((H + pad * 2, W + pad * 2, 4), np.uint8); big[pad:pad + H, pad:pad + W] = rgba
    im = Image.fromarray(big, 'RGBA').rotate(ang, resample=Image.NEAREST, center=(pivot[0] + pad, pivot[1] + pad))
    a = np.array(im)
    ys, xs = np.nonzero(a[..., 3] > 0)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return a


def _pivot_bottom(rgba):
    x0, x1, y0, y1 = _bbox(rgba)
    return ((x0 + x1) // 2, y1)


def add_dead_set(at, base, rgba, tags, seed, flip=True):
    """dead / remains / burnt / frozen for anything that dies lying down."""
    d = dead_flip(rgba) if flip else rgba
    for st, img in (('dead', d), ('remains', remains(rgba, seed)), ('burnt', burnt(rgba)), ('frozen', frozen(rgba if not flip else d))):
        at.add_array(f'{base}_{st}', img, _pivot_bottom(img), dict(tags, state=st))


def _crop_pivot(at, key, pv_fn=None):
    """after at.add: recentre pivot x on the opaque body, add 'hit' anchor at body centre."""
    k, r2, m2, pv, tg, an = at.items[-1]
    x0, x1, y0, y1 = _bbox(r2)
    pv = pv if pv_fn is None else pv_fn(r2, pv)
    an = dict(an); an['hit'] = ((x0 + x1) // 2, (y0 + y1) // 2); an['top'] = ((x0 + x1) // 2, y0)
    at.items[-1] = (k, r2, m2, ((x0 + x1) // 2, pv[1]), tg, an)
    return r2


EV = {   # animation events for gameplay / audio sync
    'walk': [(0, 'step'), (2, 'step')], 'run': [(0, 'step'), (2, 'step')], 'attack': [(2, 'hit'), (1, 'sfx:attack')], 'eat': [(1, 'sfx:eat')],
    'idle': [], 'sleep': [], 'fly': [(0, 'sfx:flap')], 'swim': [], 'move': [(0, 'step'), (2, 'step')], 'cast': [(2, 'spawn_spell'), (0, 'sfx:cast')],
    'grab': [(1, 'grab_victim'), (3, 'hold_victim')], 'stomp': [(2, 'hit_area'), (2, 'sfx:quake'), (2, 'camera_shake')], 'roar': [(0, 'sfx:roar'), (1, 'fear_area')],
    'breath': [(1, 'spawn_breath'), (0, 'sfx:breath')], 'possess': [(3, 'possess_victim')],
}


# ------------------------------------------------------------------ land fauna (quad rig)
QUAD_NAMES = None


def ex_fauna():
    BS.install(); BS.install_magic()
    at = Atlas('fauna_land', os.path.join(OUT, 'Characters', 'Fauna'))
    names = [n for n in AN.SP if not n.startswith('_')]
    for n in names:
        cat = 'magic' if n in BS.MAGIC_SP else 'biome' if n in BS.BIOME_SP else 'animal'
        for young in (False, True):
            ag = 'young' if young else 'adult'
            first = None
            for pose, nf in BS.POSES.items():
                keys = []
                for fr in range(nf):
                    key = f'a_{n}_{ag}_{pose}_{fr}'
                    probe = np.zeros((96, 110, 3), np.uint8)
                    g = AN.quad(probe, 18, 18, n, fr, young, 3, pose=pose)
                    at.add(key, lambda a, ctx, n=n, young=young, fr=fr, pose=pose: AN.quad(a, 18, 18, n, fr, young, 3, pose=pose), 110, 96, (0, g),
                           tags={'species': n, 'age': ag, 'pose': pose, 'frame': fr, 'group': cat, 'biome': BS.BIOME_SP.get(n, ('',))[0]})
                    r2 = _crop_pivot(at, key); keys.append(key)
                    if first is None and pose == 'idle': first = r2
                at.anim(f'{n}_{ag}_{pose}', keys, {'walk': 6, 'run': 10, 'idle': 3, 'eat': 3, 'attack': 8, 'sleep': 2}[pose], pose not in ('attack',), EV.get(pose))
            at.add_array(f'a_{n}_{ag}_hurt', hurt(first), _pivot_bottom(first), {'species': n, 'age': ag, 'pose': 'hurt'})
            add_dead_set(at, f'a_{n}_{ag}', first, {'species': n, 'age': ag}, hash(n) % 97)
    DONE('fauna_land', at)


def ex_critters():
    """birds (flying + ground), snakes, frogs, crabs, insects, scorpions, spiders, worms - incl. biome specials & magic birds."""
    BS.install(); BS.install_magic()
    at = Atlas('fauna_critters', os.path.join(OUT, 'Characters', 'Fauna'))
    jobs = []
    for n, s in BS.BIRDS.items(): jobs.append((n, BS.bird, s, BS.BIRD_POSES, 'magic' if n in BS.MAGIC_BIRDS else 'bird', ''))
    for n, s in BS.GROUND_BIRDS.items(): jobs.append((n, BS.bird, s, {k: v for k, v in BS.BIRD_POSES.items() if k != 'fly'}, 'bird', ''))
    for n, (f, s) in BS.SPECIAL.items():
        ps = {'walk': 4, 'idle': 2, 'attack': 2, 'sleep': 1} if f is not BS.insect or not s.get('fly') else {'walk': 4, 'idle': 2}
        jobs.append((n, f, s, ps, 'critter', ''))
    for n, (bi, f, s) in BS.BIOME_SPECIAL.items():
        ps = {'walk': 4, 'idle': 2, 'run': 4, 'attack': 3, 'eat': 2, 'sleep': 2} if f is BS.worm else {'walk': 4, 'idle': 2, 'attack': 2, 'sleep': 1}
        jobs.append((n, f, s, ps, 'biome', bi))
    for (n, f, s, ps, grp, biome) in jobs:
        big = f is BS.worm or s.get('size', 1) > 1.5
        W, H = (80, 80) if big else (56, 48)
        for young in (False, True):
            ag = 'young' if young else 'adult'
            first = None
            for pose, nf in ps.items():
                keys = []
                for fr in range(nf):
                    key = f'c_{n}_{ag}_{pose}_{fr}'
                    at.add(key, lambda a, ctx, f=f, s=s, pose=pose, fr=fr, young=young: f(a, 6, 6, s, pose, fr, young), W, H, (0, 0),
                           tags={'species': n, 'age': ag, 'pose': pose, 'frame': fr, 'group': grp, 'biome': biome, 'flying': pose == 'fly' or bool(s.get('fly'))})
                    r2 = _crop_pivot(at, key, lambda r, pv: (0, _bbox(r)[3] if not (pose == 'fly' or s.get('fly')) else (_bbox(r)[2] + _bbox(r)[3]) // 2))
                    keys.append(key)
                    if first is None: first = r2
                at.anim(f'{n}_{ag}_{pose}', keys, {'fly': 10, 'walk': 6, 'run': 10, 'idle': 3, 'attack': 8, 'sleep': 2, 'eat': 3}[pose], pose != 'attack', EV.get(pose))
            at.add_array(f'c_{n}_{ag}_hurt', hurt(first), _pivot_bottom(first), {'species': n, 'age': ag, 'pose': 'hurt'})
            add_dead_set(at, f'c_{n}_{ag}', first, {'species': n, 'age': ag}, hash(n) % 89)
    DONE('fauna_critters', at)


def ex_sea():
    at = Atlas('fauna_sea', os.path.join(OUT, 'Characters', 'Fauna'))
    for n, (rp, L, Hh, fin, pat, kind) in BS.SEA.items():
        W = int(L + 30); H = int(Hh * 2 + 30)
        for young in (False, True):
            ag = 'young' if young else 'adult'
            first = None
            for pose, nf in BS.SEA_POSES.items():
                keys = []
                for fr in range(nf):
                    key = f's_{n}_{ag}_{pose}_{fr}'
                    at.add(key, lambda a, ctx, n=n, pose=pose, fr=fr, young=young: BS.sea(a, 2, 4, n, pose, fr, young), W + 10, H + 10, (0, 0),
                           tags={'species': n, 'age': ag, 'pose': pose, 'frame': fr, 'group': 'sea', 'kind': kind})
                    r2 = _crop_pivot(at, key, lambda r, pv: (0, (_bbox(r)[2] + _bbox(r)[3]) // 2)); keys.append(key)
                    if first is None: first = r2
                at.anim(f'{n}_{ag}_{pose}', keys, {'swim': 6, 'idle': 3, 'attack': 8}[pose], pose != 'attack', EV.get(pose))
            at.add_array(f's_{n}_{ag}_hurt', hurt(first), _pivot_bottom(first), {'species': n, 'age': ag, 'pose': 'hurt'})
            d = dead_flip(first)
            at.add_array(f's_{n}_{ag}_dead', d, ((_bbox(d)[0] + _bbox(d)[1]) // 2, (_bbox(d)[2] + _bbox(d)[3]) // 2), {'species': n, 'age': ag, 'state': 'dead', 'note': 'floats belly-up'})
            rm = remains(first, hash(n) % 71)
            at.add_array(f's_{n}_{ag}_remains', rm, _pivot_bottom(rm), {'species': n, 'age': ag, 'state': 'remains'})
    DONE('fauna_sea', at)


# ------------------------------------------------------------------ supernatural beings
SPIRIT = {'jinn', 'marid', 'afreet', 'sand_djinn', 'wraith', 'shade', 'fire_elemental', 'water_elemental', 'air_elemental', 'wisp'}
DISSOLVE_COL = {'jinn': (90, 140, 220), 'marid': (120, 210, 230), 'afreet': (255, 170, 60), 'sand_djinn': (230, 200, 140), 'wraith': (150, 190, 230),
                'shade': (120, 70, 160), 'fire_elemental': (255, 200, 90), 'water_elemental': (150, 210, 250), 'air_elemental': (240, 248, 255)}


def ex_beings():
    at = Atlas('beings', os.path.join(OUT, 'Characters', 'Magic'))
    poses = {'idle': 2, 'move': 4, 'attack': 3, 'cast': 3}
    for n, s in BE.B.items():
        big = s['h'] > 38
        W, H = (110, 96) if big else (84, 72)
        idle0 = None; pv0 = None
        for pose, nf in poses.items():
            keys = []
            for fr in range(nf):
                key = f'm_{n}_{pose}_{fr}'
                g = BE.being(np.zeros((H, W, 3), np.uint8), 14, 10, n, pose, fr)
                at.add(key, lambda a, ctx, n=n, pose=pose, fr=fr: BE.being(a, 14, 10, n, pose, fr), W, H, (0, 0),
                       tags={'being': n, 'pose': pose, 'frame': fr, 'spirit': n in SPIRIT},
                       anchors={'hand': (int(g['hand'][0]), int(g['hand'][1])), 'head': (int(g['head'][0]), int(g['head'][1]))})
                gy_ = _ground(at.items[-1][1])
                r2 = _crop_pivot(at, key, lambda r, p: (0, gy_))
                keys.append(key)
                if idle0 is None: idle0 = r2; pv0 = at.items[-1][3]
            at.anim(f'{n}_{pose}', keys, {'idle': 3, 'move': 7, 'attack': 9, 'cast': 7}[pose], pose in ('idle', 'move'), EV.get(pose))
        at.add_array(f'm_{n}_hurt', hurt(idle0), pv0, {'being': n, 'pose': 'hurt'})
        keys = []
        if n in SPIRIT:
            for i, t in enumerate((.2, .45, .7, .92)):
                img = dissolve(idle0, t, DISSOLVE_COL.get(n, (200, 160, 240)), i)
                at.add_array(f'm_{n}_death_{i}', img, pv0, {'being': n, 'pose': 'death', 'frame': i, 'death': 'dissolve'}); keys.append(f'm_{n}_death_{i}')
        else:
            for i, ang in enumerate((20, 50, 80, 90)):
                img = fall(idle0, pv0, ang)
                if i == 3:
                    img = img.copy(); op = img[..., 3] > 0; img[op, :3] = (img[op, :3] * .8).astype(np.uint8)
                at.add_array(f'm_{n}_death_{i}', img, _pivot_bottom(img), {'being': n, 'pose': 'death', 'frame': i, 'death': 'fall'}); keys.append(f'm_{n}_death_{i}')
        at.anim(f'{n}_death', keys, 7, False, [(0, 'sfx:death'), (3, 'corpse')])
    # interaction specials
    keys = []
    for fr in range(4):
        key = f'm_jinn_possess_{fr}'
        at.add(key, lambda a, ctx, fr=fr: BE.possess(a, 4, 6, fr), 90, 72, (0, 0), tags={'being': 'jinn', 'pose': 'possess', 'frame': fr, 'note': 'jinn + victim human in one sprite'})
        _crop_pivot(at, key, lambda r, p: (0, _bbox(r)[3])); keys.append(key)
    at.anim('jinn_possess', keys, 5, False, EV['possess'])
    keys = []
    for fr in range(4):
        key = f'ov_possessed_{fr}'
        at.add(key, lambda a, ctx, fr=fr: BE.possessed_overlay(a, fr), 20, 36, (9, 31), keep_canvas=True, tags={'overlay': 'possessed', 'frame': fr, 'note': 'draw on top of a 20x36 person frame'})
        keys.append(key)
    at.anim('possessed_overlay', keys, 6, True)
    DONE('beings', at)


def _ground(r2):
    x0, x1, y0, y1 = _bbox(r2)
    return y1


# ------------------------------------------------------------------ titans
def ex_titans():
    at = Atlas('titans', os.path.join(OUT, 'Characters', 'Titans'))
    jobs = [(n, (lambda a, pose, fr, n=n: BE.titan(a, 6, 6, n, pose, fr)), (150, 170), BE.TITAN_POSES) for n in BE.TITANS]
    jobs += [(n, (lambda a, pose, fr, fn=fn: fn(a, 0, 0, pose, fr)), size, poses) for n, (fn, size, poses) in BE.SPECIAL_TITANS.items()]
    for n, fn, (W, H), poses in jobs:
        idle0 = pv0 = None
        aquatic = n in ('sea_serpent', 'kraken')
        for pose, nf in poses.items():
            keys = []
            for fr in range(nf):
                key = f't_{n}_{pose}_{fr}'
                at.add(key, lambda a, ctx, fn=fn, pose=pose, fr=fr: fn(a, pose, fr), W, H, (0, 0), tags={'titan': n, 'pose': pose, 'frame': fr, 'aquatic': aquatic})
                r2 = _crop_pivot(at, key, lambda r, p: (0, _bbox(r)[3]))
                keys.append(key)
                if idle0 is None: idle0 = r2; pv0 = at.items[-1][3]
            at.anim(f'{n}_{pose}', keys, {'idle': 3, 'move': 5, 'walk': 5, 'attack': 6, 'grab': 5, 'stomp': 6, 'roar': 4, 'breath': 8}[pose], pose in ('idle', 'move', 'walk', 'breath'), EV.get(pose))
        at.add_array(f't_{n}_hurt', hurt(idle0), pv0, {'titan': n, 'pose': 'hurt'})
        keys = []
        if aquatic:
            for i, t in enumerate((.15, .35, .6, .85, 1.0)):
                img = idle0.copy(); Hh = img.shape[0]; cut = int(Hh * t)       # sinks below the water line
                img = np.vstack([np.zeros((cut, img.shape[1], 4), np.uint8), img[:Hh - cut]]) if cut < Hh else np.zeros((2, img.shape[1], 4), np.uint8)
                at.add_array(f't_{n}_death_{i}', img, pv0, {'titan': n, 'pose': 'death', 'frame': i, 'death': 'sink'}); keys.append(f't_{n}_death_{i}')
        else:
            for i, ang in enumerate((8, 25, 50, 80, 90)):
                img = fall(idle0, pv0, ang) if n not in ('sand_titan',) else np.vstack([np.zeros((int(idle0.shape[0] * i / 5), idle0.shape[1], 4), np.uint8), idle0[:idle0.shape[0] - int(idle0.shape[0] * i / 5)]])
                at.add_array(f't_{n}_death_{i}', img, _pivot_bottom(img), {'titan': n, 'pose': 'death', 'frame': i}); keys.append(f't_{n}_death_{i}')
        at.anim(f'{n}_death', keys, 5, False, [(0, 'sfx:titan_death'), (3, 'camera_shake'), (4, 'corpse')])
        # titan corpse decals: remains + burnt
        d = fall(idle0, pv0, 90) if not aquatic else idle0
        for st, img in (('remains', remains(d[::-1] if not aquatic else d, 5)), ('burnt', burnt(d[::-1]))):
            at.add_array(f't_{n}_{st}', img, _pivot_bottom(img), {'titan': n, 'state': st})
    # titan-scale FX shared: stomp crack decal, arrows stuck in hide (when humans attack)
    for i in range(3):
        at.add(f't_fx_crack_{i}', lambda a, ctx, i=i: _crack(a, i), 64, 24, (32, 12), tags={'fx': 'stomp_crack', 'frame': i})
    for i in range(3):
        at.add(f't_fx_stuck_arrows_{i}', lambda a, ctx, i=i: _arrows(a, i), 32, 24, (16, 12), tags={'fx': 'stuck_projectiles', 'variant': i, 'note': 'overlay on a titan hit anchor when humans shoot it'})
    DONE('titans', at)


def _crack(a, i):
    r = random.Random(i)
    for k in range(6 + i * 3):
        x, y = 32, 12
        ang = r.uniform(0, math.tau)
        for s in range(r.randint(6, 12 + i * 4)):
            x += math.cos(ang); y += math.sin(ang) * .5; ang += r.uniform(-.5, .5)
            put(a, int(x), int(y), hx('#2a1e14')); put(a, int(x) + 1, int(y), hx('#4a3424'))
    blend_mask(a, ellipse_mask(a.shape[:2], 32, 12, 14 + i * 5, 4 + i * 2), hx('#4a3424'), .35)


def _arrows(a, i):
    r = random.Random(i + 3)
    for k in range(3 + i * 2):
        x, y = r.randint(6, 26), r.randint(8, 20)
        for s in range(5): put(a, x - s, y - s // 2, hx('#8c6844'))
        put(a, x - 5, y - 3, hx('#f6f2ea')); put(a, x - 6, y - 3, hx('#d84a3a'))


# ------------------------------------------------------------------ spells
def ex_spells():
    at = Atlas('spells', os.path.join(OUT, 'FX', 'Spells'))
    for n, (el, shape) in SPL.SPELLS.items():
        for part, nf, W, H, pv, fn in SPL.parts_for(n):
            keys = []
            for f in range(nf):
                key = f'sp_{n}_{part}_{f}'
                at.add(key, lambda a, ctx, fn=fn, f=f: fn(a, f), W, H, pv, keep_canvas=part.startswith('beam'), tags={'spell': n, 'element': el, 'shape': shape, 'part': part, 'frame': f})
                keys.append(key)
            loop = part in ('storm', 'zone', 'aura_back', 'aura_front', 'beam_seg', 'beam_start', 'beam_end', 'cast', 'mark') or part.startswith('proj')
            ev = {'impact': [(0, 'hit_area'), (0, 'sfx:impact')], 'nova': [(1, 'hit_area'), (0, 'sfx:nova')], 'circle': [(6, 'summon'), (0, 'sfx:summon')], 'wall': [(2, 'block_on')]}.get(part, [])
            at.anim(f'spell_{n}_{part}', keys, 10 if part != 'circle' else 8, loop, ev)
        for sz in (16, 32):
            at.add(f'icon_spell_{n}_{sz}', lambda a, ctx, n=n, sz=sz: SPL.spell_icon(a, n, sz), sz, sz, (sz // 2, sz // 2), keep_canvas=True, tags={'icon': 'spell', 'spell': n, 'size': sz})
    DONE('spells', at)


CATS = {'fauna': ex_fauna, 'critters': ex_critters, 'sea': ex_sea, 'beings': ex_beings, 'titans': ex_titans, 'spells': ex_spells}
