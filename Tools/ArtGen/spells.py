"""40 spells. Every spell = element palette + shape.  Parts (all facing right / top-down ground ellipses squashed 0.5):
  bolt   -> proj_<dir 0..7>_<f0..3> + impact_<f0..5>
  nova   -> nova_<f0..7>                (expanding ring on the ground)
  storm  -> storm_<f0..7> (loop) + mark_<f0..3>  (falling particles over an area)
  beam   -> beam_seg_<f0..3> (tileable 16 px) + beam_start_<f> + beam_end_<f>
  aura   -> aura_back_<f0..5> + aura_front_<f0..5> (draw behind / in front of a unit)
  zone   -> zone_<f0..5> (loop ground pool)
  summon -> circle_<f0..9> (rune circle forming, then a light pillar)
  wall   -> wall_<f0..5> (rising, loop)
Every spell also gets cast_<f0..3> (circle under the caster) and an icon.  Rune circles are original geometry (rings, ticks, dots) - no real symbols."""
import math, random
import numpy as np
from lib import *
from animals import R5

EL = {   # element: (ramp dark->light, particle colour, core)
    'fire': (R5('#5a140a', '#a82a10', '#e8521a', '#ff9a3a', '#ffe27a'), hx('#ffb84a'), hx('#fff6c0')),
    'ice': (R5('#1e4a6a', '#3a7aa8', '#6aaed6', '#a8d8f0', '#e8f8ff'), hx('#cfefff'), hx('#ffffff')),
    'lightning': (R5('#2a2a6a', '#4a4ab8', '#7a8af0', '#b4c8ff', '#f0f6ff'), hx('#d8e4ff'), hx('#ffffff')),
    'poison': (R5('#1e3a10', '#3a6a1a', '#5ea02a', '#9ad84a', '#d8ff9a'), hx('#9ae04a'), hx('#e8ffc0')),
    'arcane': (R5('#2a104a', '#4a1e7a', '#7a3ab8', '#b07ae8', '#e8c8ff'), hx('#c87ae8'), hx('#fff0ff')),
    'life': (R5('#0e4a2a', '#1e7a3a', '#3ab45a', '#7ae08a', '#d0ffd8'), hx('#9af0a8'), hx('#ffffff')),
    'earth': (R5('#3a2a1a', '#5a4428', '#7e623c', '#a08458', '#c8ac80'), hx('#a88a5a'), hx('#e8d8b8')),
    'wind': (R5('#5a6a74', '#8094a0', '#a8bcc6', '#d0e0e8', '#f4fbff'), hx('#e0eef4'), hx('#ffffff')),
    'shadow': (R5('#0a060e', '#1e1028', '#3a1e4a', '#5e3474', '#8a5aa0'), hx('#7a4a9a'), hx('#d8b8f0')),
    'water': (R5('#0e2a5a', '#1a4a8a', '#2a72b8', '#5aa4e0', '#b4e0ff'), hx('#8ac8f0'), hx('#ffffff')),
    'sand': (R5('#6a502a', '#9a7a44', '#c4a066', '#e0c48e', '#fff0c8'), hx('#e0c48e'), hx('#fff8e0')),
    'light': (R5('#6a5a1e', '#b4962a', '#e8c840', '#fff08a', '#ffffe8'), hx('#fff08a'), hx('#ffffff')),
    'smoke': (R5('#2a2a2e', '#46464c', '#66666e', '#8c8c94', '#b8b8c0'), hx('#9a9aa4'), hx('#e0e0e8')),
}

SPELLS = {
    'fireball': ('fire', 'bolt'), 'flame_wave': ('fire', 'nova'), 'meteor_rain': ('fire', 'storm'), 'fire_wall': ('fire', 'wall'), 'inferno_ray': ('fire', 'beam'),
    'ice_shard': ('ice', 'bolt'), 'frost_nova': ('ice', 'nova'), 'blizzard': ('ice', 'storm'), 'ice_wall': ('ice', 'wall'),
    'lightning_bolt': ('lightning', 'bolt'), 'chain_lightning': ('lightning', 'beam'), 'thunder_storm': ('lightning', 'storm'), 'static_field': ('lightning', 'zone'),
    'poison_dart': ('poison', 'bolt'), 'plague_cloud': ('poison', 'zone'), 'acid_rain': ('poison', 'storm'),
    'arcane_missile': ('arcane', 'bolt'), 'arcane_ray': ('arcane', 'beam'), 'mana_shield': ('arcane', 'aura'), 'warp_gate': ('arcane', 'summon'),
    'heal': ('life', 'aura'), 'mass_heal': ('life', 'nova'), 'regrowth': ('life', 'zone'), 'bless_harvest': ('life', 'storm'),
    'earth_spike': ('earth', 'wall'), 'quake': ('earth', 'nova'), 'stone_skin': ('earth', 'aura'), 'boulder_throw': ('earth', 'bolt'),
    'wind_blade': ('wind', 'bolt'), 'cyclone': ('wind', 'zone'), 'haste': ('wind', 'aura'),
    'shadow_bolt': ('shadow', 'bolt'), 'life_drain': ('shadow', 'beam'), 'curse': ('shadow', 'aura'), 'raise_dead': ('shadow', 'summon'),
    'tidal_wave': ('water', 'nova'), 'water_jet': ('water', 'beam'), 'summon_rain': ('water', 'storm'),
    'sandstorm_call': ('sand', 'zone'), 'jinn_binding': ('smoke', 'summon'), 'demon_gate': ('fire', 'summon'), 'sun_flare': ('light', 'nova'),
    'smoke_veil': ('smoke', 'zone'), 'possession': ('smoke', 'aura'),
}
FRAMES = {'proj': 4, 'impact': 6, 'nova': 8, 'storm': 8, 'mark': 4, 'beam_seg': 4, 'beam_start': 4, 'beam_end': 4, 'aura_back': 6, 'aura_front': 6,
          'zone': 6, 'circle': 10, 'wall': 6, 'cast': 4}


def glow(a, cx, cy, r, col, al=.35):
    blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, r, r), col, al)


def ring(a, cx, cy, r, col, sq=.5, step=None, dash=0, rot=0.0, th=1):
    n = max(12, int(r * 7))
    for i in range(n):
        if dash and (i // dash) % 2: continue
        t = i / n * math.tau + rot
        for q in range(th): put(a, int(round(cx + math.cos(t) * (r - q))), int(round(cy + math.sin(t) * (r - q) * sq)), col)


def rune_circle(a, cx, cy, r, rp, f, seed=0):
    """original geometric rune circle: 2 rings, rotating ticks, orbiting dots, inner polygon outline."""
    rr = random.Random(seed)
    ring(a, cx, cy, r, rp[3]); ring(a, cx, cy, r - 3, rp[2], dash=3, rot=f * .15)
    n = 6 + seed % 3 * 2
    for i in range(n):
        t = i / n * math.tau + f * .2
        x0, y0 = cx + math.cos(t) * (r - 1.5), cy + math.sin(t) * (r - 1.5) * .5
        put(a, int(x0), int(y0), rp[4])
    sides = 3 + seed % 4
    pts = [(cx + math.cos(i / sides * math.tau - f * .12) * (r - 6), cy + math.sin(i / sides * math.tau - f * .12) * (r - 6) * .5) for i in range(sides)]
    for i in range(sides):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % sides]
        for s in range(20): put(a, int(x0 + (x1 - x0) * s / 19), int(y0 + (y1 - y0) * s / 19), rp[2])
    ring(a, cx, cy, max(2, r * .3), rp[3])


# --------------------------------------------------------------- parts
def proj(a, el, d, f, heavy=False):
    rp, pc, core = EL[el]
    ang = d / 8 * math.tau
    cx, cy = 16, 16
    dx, dy = math.cos(ang), math.sin(ang)
    for i in range(10):     # trail
        r = (3 - i * .25) * (1.3 if heavy else 1)
        if r <= .3: break
        x, y = cx - dx * i * 1.3 + math.sin(i + f) * .5 * (el in ('fire', 'smoke', 'poison', 'shadow')), cy - dy * i * 1.3
        blend_mask(a, ellipse_mask(a.shape[:2], x, y, r, r), rp[3 - min(i // 3, 3)] if i < 9 else rp[0], .9 - i * .08)
    if el == 'lightning':
        x, y = cx, cy
        for i in range(8):
            nx, ny = x - dx * 1.6 + (random.Random(f * 9 + i).random() - .5) * 2.4 * -dy, y - dy * 1.6 + (random.Random(f * 7 + i).random() - .5) * 2.4 * dx
            put(a, int(nx), int(ny), rp[4]); x, y = nx, ny
    if el == 'ice' or el == 'earth':
        for i in range(5):
            put(a, int(cx + dx * (2 - i)), int(cy + dy * (2 - i)), rp[4 if i < 2 else 3])
            put(a, int(cx + dx * (2 - i) - dy), int(cy + dy * (2 - i) + dx), rp[2])
    if el == 'wind':
        for i in range(-3, 4): put(a, int(cx + dx * (-abs(i) * .7) - dy * i), int(cy + dy * (-abs(i) * .7) + dx * i), rp[4] if abs(i) < 2 else rp[3])
        return
    rad = 2.6 * (1.4 if heavy else 1) + (f % 2) * .4
    glow(a, cx, cy, rad + 3, pc, .3)
    dome(a, cx, cy, rad, rad, rp[1:] + [core], 1)
    put(a, cx, cy - 1, core)


def impact(a, el, f):
    rp, pc, core = EL[el]
    cx, cy = 20, 22
    t = f / 5
    r = 3 + t * 12
    if f < 3: glow(a, cx, cy - 2, 10 - f * 2, core, .6 - f * .15)
    ring(a, cx, cy, r, rp[3] if f < 4 else rp[2], sq=.55, th=2 if f < 3 else 1)
    rr = random.Random(f + hash(el) % 99)
    for i in range(14):
        ang = rr.uniform(0, math.tau)
        d = r * rr.uniform(.4, 1.1)
        y = cy + math.sin(ang) * d * .55 - (1 - t) * rr.uniform(2, 8)
        put(a, int(cx + math.cos(ang) * d), int(y), [pc, rp[4], rp[3]][i % 3] if f < 5 else rp[1])
    if f < 4: dome(a, cx, cy - 3 + f, 5 - f, 4 - f, rp[1:] + [core], 2)
    if el in ('fire', 'smoke', 'earth', 'sand', 'poison') and f >= 2:
        for i in range(3): blend_mask(a, ellipse_mask(a.shape[:2], cx - 4 + i * 4, cy - 4 - f * 1.5, 3 + f * .4, 2.5), EL['smoke'][0][2 + (i % 2)], .55 - f * .06)


def nova(a, el, f):
    rp, pc, core = EL[el]
    cx, cy = 32, 20
    r = 4 + f * 3.6
    al = 1 - f / 9
    blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, r, r * .5) & ~ellipse_mask(a.shape[:2], cx, cy, max(r - 5, 0), max(r - 5, 0) * .5), rp[3], .7 * al)
    ring(a, cx, cy, r, rp[4] if f < 6 else rp[2], th=2)
    rr = random.Random(f)
    for i in range(16):
        t = i / 16 * math.tau + rr.uniform(-.1, .1)
        x, y = cx + math.cos(t) * r, cy + math.sin(t) * r * .5
        put(a, int(x), int(y - 1 - (i % 3)), pc)
        if el == 'ice': put(a, int(x), int(y - 2), core); put(a, int(x), int(y - 3), rp[4])
        if el == 'earth': rect(a, int(x), int(y - 2), 2, 2, rp[2])
        if el == 'water': put(a, int(x), int(y - 3), rp[4]); put(a, int(x + 1), int(y - 2), rp[3])
    if f < 2: glow(a, cx, cy, 8, core, .5)


def storm(a, el, f):
    rp, pc, core = EL[el]
    cx, cy = 32, 40
    rr = random.Random(7)
    if el in ('lightning', 'water', 'poison', 'ice', 'life'):
        blend_mask(a, ellipse_mask(a.shape[:2], cx, 10, 26, 7), rp[0] if el != 'life' else rp[2], .55)
        blend_mask(a, ellipse_mask(a.shape[:2], cx - 8, 8, 14, 5), rp[1], .45)
    for i in range(28):
        x0 = cx + rr.uniform(-24, 24); sp = rr.uniform(.7, 1.3); ph = rr.uniform(0, 40)
        y = 12 + (ph + f * 5 * sp) % 34
        x = x0 - (y - 12) * (.4 if el in ('fire', 'earth') else .15)
        if el == 'fire':
            if i % 4 == 0: dome(a, x, y, 1.6, 1.6, rp[1:] + [core], i); put(a, int(x + 1), int(y - 2), rp[3]); put(a, int(x + 2), int(y - 4), rp[2])
        elif el == 'ice': put(a, int(x), int(y), core if i % 2 else rp[3])
        elif el == 'lightning' and i < 2 and f % 3 == i:
            xx = x0
            for yy in range(12, 46):
                xx += rr.choice((-1, 0, 1)); put(a, int(xx), yy, core); put(a, int(xx) + 1, yy, rp[3])
            glow(a, xx, 46, 6, rp[4], .5)
        else:
            vline(a, int(x), int(y), 2 + (el in ('water', 'poison')), rp[3] if i % 2 else rp[2])
    ring(a, cx, cy + 4, 24, rp[2], dash=2, rot=f * .1)


def mark(a, el, f):
    rp, pc, core = EL[el]
    ring(a, 24, 12, 20, rp[3] if f % 2 else rp[2], dash=2, rot=f * .2); ring(a, 24, 12, 4, rp[4])


def beam_seg(a, el, f):
    rp, pc, core = EL[el]
    W = 16
    for x in range(W):
        w = 2.4 + math.sin(x / W * math.tau * 2 + f * 1.4) * .9
        for y in range(-3, 4):
            if abs(y) <= w: put(a, x, 8 + y, rp[4] if abs(y) < w * .35 else rp[3] if abs(y) < w * .7 else rp[2])
        if el == 'lightning':
            put(a, x, int(8 + 3.5 * math.sin(x * 1.7 + f * 3)), core)
    for x in range(0, W, 4): put(a, (x + f * 2) % W, 8 + ((x // 4 + f) % 3) - 1, core)


def beam_end(a, el, f, start=False):
    rp, pc, core = EL[el]
    glow(a, 8, 8, 6 + f % 2, pc, .45); dome(a, 8, 8, 3 + (f % 2) * .5, 3 + (f % 2) * .5, rp[1:] + [core], f)
    if not start:
        for i in range(6):
            t = i / 6 * math.tau + f
            put(a, int(8 + math.cos(t) * (4 + f % 3)), int(8 + math.sin(t) * (4 + f % 3)), rp[4])


def aura(a, el, f, front):
    rp, pc, core = EL[el]
    cx, cy = 16, 30
    if not front:
        blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 10, 4), rp[2], .45)
        ring(a, cx, cy, 10, rp[3], sq=.4, dash=2, rot=f * .3)
        if el in ('arcane', 'earth'):
            blend_mask(a, ellipse_mask(a.shape[:2], cx, cy - 13, 11, 16), rp[3], .18)
    else:
        rr = random.Random(3)
        for i in range(9):
            x = cx + rr.uniform(-9, 9); y = cy - ((rr.uniform(0, 26) + f * 4) % 28)
            c = pc if i % 2 else rp[4]
            if el == 'life':
                put(a, int(x), int(y), c); put(a, int(x) - 1, int(y) + 1, rp[3]); put(a, int(x) + 1, int(y) + 1, rp[3])
            elif el == 'shadow' or el == 'smoke':
                blend_mask(a, ellipse_mask(a.shape[:2], x, y, 2, 1.5), rp[2], .6)
            else: put(a, int(x), int(y), c)
        if el in ('arcane', 'earth'):
            ring(a, cx, cy - 13, 11, rp[4] if f % 3 == 0 else rp[3], sq=1.45, dash=4, rot=f * .25)


def zone(a, el, f):
    rp, pc, core = EL[el]
    cx, cy = 28, 22
    if el in ('poison', 'smoke', 'sand', 'shadow'):
        for i in range(7):
            t = i / 7 * math.tau + f * .25
            blend_mask(a, ellipse_mask(a.shape[:2], cx + math.cos(t) * 12, cy - 4 + math.sin(t) * 5, 8, 5), rp[2 + i % 2], .45)
        blend_mask(a, ellipse_mask(a.shape[:2], cx, cy - 6, 14, 7), rp[3], .35)
    elif el == 'wind':
        for j in range(5):
            r = 4 + j * 3
            for s in range(int(r * 4)):
                t = s / (r * 4) * math.tau * .75 + f * .6 + j
                put(a, int(cx + math.cos(t) * r * .7), int(cy - j * 5 + math.sin(t) * r * .25), rp[3 + (j % 2)])
    else:
        blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 20, 9), rp[1], .55)
        ring(a, cx, cy, 20, rp[3], sq=.45, dash=3, rot=f * .2)
        rr = random.Random(f)
        for i in range(10):
            x, y = cx + rr.uniform(-16, 16), cy + rr.uniform(-6, 6)
            if el == 'lightning':
                for k in range(3): put(a, int(x + rr.choice((-1, 0, 1))), int(y - k), core)
            elif el == 'life':
                put(a, int(x), int(y), rp[4]); put(a, int(x), int(y) - 1, rp[3]); put(a, int(x) + 1, int(y) - 2, rp[3])
            else: put(a, int(x), int(y), pc)


def circle(a, el, f, seed):
    rp, pc, core = EL[el]
    cx, cy = 32, 52
    grow = min(f / 4, 1)
    rune_circle(a, cx, cy, 6 + 16 * grow, rp, f, seed)
    if f >= 5:
        h = [16, 34, 46, 46, 30][f - 5]
        for y in range(int(cy - h), int(cy)):
            w = 8 - (cy - y) / max(h, 1) * 3
            blend_rect(a, int(cx - w), y, int(w * 2), 1, rp[4], .35)
            put(a, int(cx), y, core)
        glow(a, cx, cy - h, 6, core, .5)


def wall(a, el, f):
    rp, pc, core = EL[el]
    h = [3, 8, 13, 15, 14, 15][f]
    for i in range(7):
        x = 6 + i * 6
        hh = h - (i % 2) * 2
        if el == 'fire':
            for y in range(hh):
                c = rp[4] if y < hh * .3 else rp[3] if y < hh * .7 else rp[2]
                w = 2 + (y // 4)
                hline(a, x - w // 2 + int(math.sin(y + f + i) * .8), 22 - y, w, c)
        else:   # ice / earth spikes
            for y in range(hh):
                w = max(1, int((hh - y) / hh * 4))
                hline(a, x - w // 2, 22 - y, w, rp[3] if y > hh * .5 else rp[2]); put(a, x - w // 2, 22 - y, rp[4])
    blend_mask(a, ellipse_mask(a.shape[:2], 25, 23, 22, 2.5), rp[0], .5)


def cast(a, el, f):
    rp, pc, core = EL[el]
    rune_circle(a, 16, 8, 12, rp, f, hash(el) % 7)
    for i in range(4):
        t = i / 4 * math.tau + f * .4
        put(a, int(16 + math.cos(t) * 7), int(8 + math.sin(t) * 3.5 - f), pc)


def spell_icon(a, name, size=16):
    el, shape = SPELLS[name]
    rp, pc, core = EL[el]
    s = size / 16
    rect(a, 0, 0, size, size, rp[0])
    blend_mask(a, ellipse_mask(a.shape[:2], size / 2, size / 2, size * .45, size * .45), rp[1], .9)
    c = size / 2 - .5
    if shape == 'bolt':
        for i in range(int(6 * s)): put(a, int(c - 4 * s + i), int(c + 4 * s - i), rp[3])
        dome(a, c + 2 * s, c - 2 * s, 2.4 * s, 2.4 * s, rp[1:] + [core], 1)
    elif shape == 'nova':
        ring(a, c, c, 5.5 * s, rp[4], sq=1, th=max(1, int(s))); ring(a, c, c, 3 * s, rp[3], sq=1); put(a, int(c), int(c), core)
    elif shape == 'storm':
        blend_mask(a, ellipse_mask(a.shape[:2], c, c - 3 * s, 6 * s, 2.5 * s), rp[3], .9)
        for i in range(4): vline(a, int(c - 4 * s + i * 2.6 * s), int(c), int(3 * s) + 1, rp[4])
    elif shape == 'beam':
        for i in range(size - 2): put(a, i + 1, int(c), rp[4]); put(a, i + 1, int(c) + 1, rp[3]); put(a, i + 1, int(c) - 1, rp[3])
        dome(a, 3 * s, c, 2 * s, 2 * s, rp[1:] + [core], 1)
    elif shape == 'aura':
        ring(a, c, c, 5.5 * s, rp[3], sq=1.0, dash=2); dome(a, c, c + 1, 2 * s, 3 * s, rp[1:] + [core], 2)
    elif shape == 'zone':
        blend_mask(a, ellipse_mask(a.shape[:2], c, c + 2 * s, 6 * s, 3 * s), rp[3], .9)
        for i in range(3): put(a, int(c - 3 * s + i * 3 * s), int(c - 1 * s - i % 2), pc)
    elif shape == 'summon':
        rune_circle(a, c, c + s, 6.5 * s, rp, 0, 3)
    elif shape == 'wall':
        for i in range(4): vline(a, int(c - 5 * s + i * 3.3 * s), int(c - 3 * s + (i % 2) * s), int(7 * s), rp[3 + (i % 2)])
    for x in range(size): put(a, x, 0, rp[3]); put(a, x, size - 1, rp[0])
    for y in range(size): put(a, 0, y, rp[3]); put(a, size - 1, y, rp[0])


def parts_for(name):
    """yields (part, frames, W, H, pivot, drawer(a, f)) for the exporter."""
    el, shape = SPELLS[name]
    seed = sum(map(ord, name))
    out = [('cast', 4, 32, 18, (16, 9), lambda a, f: cast(a, el, f))]
    if shape == 'bolt':
        heavy = name in ('boulder_throw', 'fireball')
        for d in range(8):
            out.append((f'proj_{d}', 4, 32, 32, (16, 16), lambda a, f, d=d: proj(a, el, d, f, heavy)))
        out.append(('impact', 6, 40, 30, (20, 22), lambda a, f: impact(a, el, f)))
    elif shape == 'nova': out.append(('nova', 8, 64, 40, (32, 20), lambda a, f: nova(a, el, f)))
    elif shape == 'storm':
        out.append(('storm', 8, 64, 52, (32, 44), lambda a, f: storm(a, el, f))); out.append(('mark', 4, 48, 24, (24, 12), lambda a, f: mark(a, el, f)))
    elif shape == 'beam':
        out += [('beam_seg', 4, 16, 16, (0, 8), lambda a, f: beam_seg(a, el, f)), ('beam_start', 4, 16, 16, (8, 8), lambda a, f: beam_end(a, el, f, True)),
                ('beam_end', 4, 16, 16, (8, 8), lambda a, f: beam_end(a, el, f))]
    elif shape == 'aura':
        out += [('aura_back', 6, 32, 36, (16, 30), lambda a, f: aura(a, el, f, False)), ('aura_front', 6, 32, 36, (16, 30), lambda a, f: aura(a, el, f, True))]
    elif shape == 'zone': out.append(('zone', 6, 56, 34, (28, 22), lambda a, f: zone(a, el, f)))
    elif shape == 'summon': out.append(('circle', 10, 64, 64, (32, 52), lambda a, f: circle(a, el, f, seed)))
    elif shape == 'wall': out.append(('wall', 6, 50, 26, (25, 23), lambda a, f: wall(a, el, f)))
    return out
