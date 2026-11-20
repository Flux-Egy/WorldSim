"""Supernatural beings and titans.  Fine grid, facing right, light top-left.
being(a, x, y, kind, pose, frame)  poses: idle(2) move(4) attack(3) cast(3) + special (possess / grab / stomp / breath)
Hurt and death frames are produced by the exporter from these (recoil + tint, fall / dissolve).
Names demon / jinn / afreet / marid are used as the owner asked; no real-world religious symbols anywhere."""
import math, random
import numpy as np
from lib import *
from animals import R5, DARK, line
import people

GLOW = {'fire': hx('#ffb84a'), 'ember': hx('#f4602a'), 'cyan': hx('#5fe0e8'), 'toxic': hx('#9ae04a'), 'violet': hx('#c87ae8'),
        'ice': hx('#cfefff'), 'gold': hx('#ffd34a'), 'red': hx('#ff4a3a'), 'white': hx('#f6f6ff'), 'green': hx('#6af08a')}


def person_tiny(a, x, y, frame=0, seed=7, flail=False):
    """a 20x36-frame human (same as the people atlas) - used inside titan grab / possess sprites."""
    g = dict(acc=R5('#2a4a6a', '#3a6086', '#5a7ea0', '#7a9cbc', '#a0bcd6'), acc2=R5('#6a2a5a', '#8a3a76', '#a85a94', '#c87ab4', '#e8a8d8'),
             garment='pants', head=None, fhead=None, crown=None, gold=False, values=['TRADITION'], nomad=False, skins=['#c89a74'], hairs=['#3a2618'], paint=False)
    people.person2(a, x, y, None, 'poor', 'adult', 'm', frame, seed=seed, og=g, shadow=False)
    if flail:   # arms thrown up
        sk = hx('#c89a74')
        for i in range(4):
            put(a, x + 3 - (frame % 2), y + 15 - i, sk); put(a, x + 14 + (frame % 2), y + 15 - i, sk)


# ------------------------------------------------------------------ specs
# body: ramp, h (height px at k=1 ~ person 27), build (shoulder width), lower: legs|smoke|float|hooves, extra flags
B = {
    'demon': dict(rp=R5('#3a0e0e', '#5a1814', '#7a241c', '#9a3424', '#b84a30'), h=34, w=8, lower='hooves', horns='ram', wings='bat', tail=True, eye=GLOW['fire'], claws=True, aura=None),
    'demon_lord': dict(rp=R5('#1e0a0e', '#3a1018', '#561a22', '#74262c', '#923436'), h=46, w=11, lower='hooves', horns='great', wings='bat', tail=True, eye=GLOW['fire'],
                       weapon='blade', aura=GLOW['ember'], crown_spikes=True),
    'imp': dict(rp=R5('#5a1a14', '#7a2a1c', '#9a3c26', '#b85232', '#d06c44'), h=18, w=5, lower='legs', horns='small', wings='bat', tail=True, eye=GLOW['gold'], claws=True),
    'afreet': dict(rp=R5('#4a1a0a', '#7a2a0e', '#a84014', '#d0601e', '#f08a34'), h=40, w=10, lower='smoke', smoke=R5('#3a1a10', '#6a2a14', '#a8461c', '#e0742a', '#ffb84a'),
                   horns='great', eye=GLOW['gold'], aura=GLOW['fire'], flames=True, bracers=hx('#ffd34a')),
    'jinn': dict(rp=R5('#1e2a5a', '#2a3c7a', '#3a529a', '#5a72b8', '#84a0d6'), h=36, w=9, lower='smoke', smoke=R5('#1e2a5a', '#2a3c7a', '#4a64a8', '#7a98d0', '#b4ccf0'),
                 eye=GLOW['cyan'], aura=GLOW['cyan'], topknot=True, bracers=hx('#ffd34a')),
    'marid': dict(rp=R5('#0e3a4a', '#145a6a', '#1e7a8a', '#3a9aa8', '#6abcc8'), h=44, w=11, lower='smoke', smoke=R5('#0e3a4a', '#1e6a7a', '#3a9aaa', '#7ac8d4', '#c0eef2'),
                  eye=GLOW['white'], aura=GLOW['cyan'], topknot=True, bracers=hx('#d8e8f0'), drips=True),
    'ghoul': dict(rp=R5('#3a3a2a', '#4e4e38', '#666648', '#7e7e5c', '#9a9a74'), h=26, w=6, lower='legs', hunch=3, eye=GLOW['toxic'], claws=True, rags=hx('#3a3228')),
    'wraith': dict(rp=R5('#1a1a24', '#262634', '#363648', '#4a4a60', '#62627c'), h=32, w=8, lower='float', hood=True, eye=GLOW['cyan'], aura=hx('#8ab4d8'), claws=True, ghost=True),
    'skeleton': dict(rp=R5('#8a8474', '#a8a290', '#c4beac', '#dcd6c4', '#f2ecdc'), h=27, w=6, lower='legs', bones=True, eye=GLOW['red'], weapon='sword'),
    'zombie': dict(rp=R5('#3a4a3a', '#4e624a', '#667c5e', '#7e9674', '#9ab08c'), h=27, w=7, lower='legs', hunch=1, eye=hx('#e8e0a0'), rags=hx('#4a4038'), arms_fwd=True),
    'lich': dict(rp=R5('#8a8474', '#a8a290', '#c4beac', '#dcd6c4', '#f2ecdc'), h=32, w=7, lower='robe', robe=R5('#1e1428', '#2e1e3e', '#402a56', '#563a70', '#6e4e8c'),
                 bones=True, eye=GLOW['green'], aura=GLOW['green'], weapon='staff', crown_spikes=True),
    'werewolf': dict(rp=R5('#2a2420', '#3e342e', '#544640', '#6c5a52', '#867064'), h=36, w=10, lower='legs', snout=True, ears=True, eye=GLOW['gold'], claws=True, hunch=2, fur=True),
    'vampire': dict(rp=R5('#a89a98', '#c4b6b4', '#dccecc', '#ece2e0', '#f8f2f0'), h=29, w=7, lower='robe', robe=R5('#140a10', '#24121c', '#3a1a2a', '#541e34', '#7a2440'),
                    cape=hx('#7a1a2a'), eye=GLOW['red'], hair=hx('#141418')),
    'troll': dict(rp=R5('#3a4a3a', '#4a604a', '#5e7a5c', '#789670', '#94b088'), h=40, w=12, lower='legs', hunch=3, eye=GLOW['gold'], weapon='club', nose=True, moss=True),
    'ogre': dict(rp=R5('#6a5a3a', '#86744a', '#a08e5e', '#b8a674', '#d0be8e'), h=40, w=13, lower='legs', belly=True, eye=hx('#ffe27a'), weapon='club', rags=hx('#5a4430')),
    'minotaur': dict(rp=R5('#3a2418', '#54341e', '#6e4628', '#885a34', '#a27044'), h=40, w=12, lower='hooves', horns='bull', snout=True, eye=GLOW['red'], weapon='axe'),
    'cyclops': dict(rp=R5('#7a6a5a', '#94826e', '#ae9a84', '#c6b29c', '#dccab4'), h=48, w=13, lower='legs', one_eye=True, eye=hx('#f6f2ea'), weapon='club', rags=hx('#6a5440')),
    'naga': dict(rp=R5('#1e4a3a', '#2a644e', '#3a8064', '#529c7c', '#70b896'), h=34, w=8, lower='serpent', eye=GLOW['gold'], weapon='spear', crest=hx('#c8a040')),
    'harpy': dict(rp=R5('#6a4a3a', '#86604a', '#a07a5e', '#b89474', '#d0ae8e'), h=26, w=6, lower='talons', wings='feather', wcol=R5('#3a2a2a', '#4e3a36', '#664c44', '#7e6054', '#987666'), eye=GLOW['gold'], hair=hx('#2a1a14')),
    'stone_golem': dict(rp=R5('#4a4844', '#64605a', '#7e7a72', '#98938a', '#b2aca2'), h=40, w=13, lower='legs', blocky=True, eye=GLOW['cyan'], runes=GLOW['cyan']),
    'iron_golem': dict(rp=R5('#3a3e44', '#525860', '#6c727c', '#8a919a', '#aab0b8'), h=42, w=12, lower='legs', blocky=True, eye=GLOW['fire'], runes=GLOW['fire'], rivets=True),
    'gargoyle': dict(rp=R5('#3a3a40', '#504f56', '#68676e', '#828088', '#9c9aa2'), h=28, w=8, lower='legs', horns='small', wings='bat', tail=True, eye=GLOW['red'], hunch=2, claws=True),
    'fire_elemental': dict(rp=R5('#8a1e0e', '#c43a14', '#f0661e', '#ffa040', '#ffe27a'), h=36, w=9, lower='smoke', smoke=R5('#5a140a', '#a82a10', '#e8521a', '#ff9a3a', '#ffe27a'), elemental='fire', eye=hx('#fff6c0'), aura=GLOW['fire']),
    'water_elemental': dict(rp=R5('#0e3a6a', '#1a548a', '#2a72aa', '#4a94c8', '#7ab8e0'), h=36, w=9, lower='smoke', smoke=R5('#0e3a6a', '#1e5a92', '#3a7eb8', '#6aa8d8', '#a8d4f0'), elemental='water', eye=GLOW['white'], aura=hx('#7ab8e0')),
    'earth_elemental': dict(rp=R5('#3a2a1a', '#54402a', '#6e583a', '#88724e', '#a28c66'), h=40, w=13, lower='legs', blocky=True, elemental='earth', eye=GLOW['toxic'], moss=True),
    'air_elemental': dict(rp=R5('#8a9aa8', '#a6b4c0', '#c0ccd6', '#d8e2ea', '#eef4f8'), h=36, w=9, lower='smoke', smoke=R5('#8a9aa8', '#a6b4c0', '#c8d4de', '#e2eaf0', '#f8fbfd'), elemental='air', eye=GLOW['white'], ghost=True),
    'shade': dict(rp=R5('#08080c', '#101016', '#181822', '#22222e', '#2e2e3c'), h=30, w=7, lower='float', eye=GLOW['violet'], aura=hx('#4a2a6a'), ghost=True, claws=True),
    'treant': dict(rp=R5('#3a2618', '#54381e', '#6e4c28', '#886234', '#a27a44'), h=48, w=12, lower='roots', leaves=R5('#1e4a1e', '#2a6428', '#3a8034', '#529c44', '#70b85a'), eye=GLOW['gold']),
    'sand_djinn': dict(rp=R5('#8a6a3a', '#a8844a', '#c49e5e', '#d8b878', '#ecd29a'), h=36, w=9, lower='smoke', smoke=R5('#6a502a', '#a8844a', '#d0aa6a', '#ecd29a', '#fff0d0'), eye=GLOW['gold'], topknot=True, bracers=hx('#ffd34a')),
    'frost_wight': dict(rp=R5('#4a6a8a', '#6488a8', '#82a6c4', '#a4c4dc', '#cae2f2'), h=30, w=7, lower='legs', bones=True, eye=GLOW['ice'], aura=GLOW['ice'], weapon='sword', frost=True),
}
# beasts built from other rigs (exported by the bestiary path): dragon, wyvern, griffin, unicorn, hellhound, nightmare, phoenix, thunderbird
MAGIC_QUADS = {}


def capsule(a, x0, y0, x1, y1, w, rp, seed=0):
    """thick shaded limb from (x0,y0) to (x1,y1); w = thickness in px."""
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    r = max(w / 2, .6)
    pts = [(x0 + (x1 - x0) * i / max(n - 1, 1), y0 + (y1 - y0) * i / max(n - 1, 1)) for i in range(n)]
    for px, py in pts:
        for dy in range(-int(r) - 1, int(r) + 2):
            for dx in range(-int(r) - 1, int(r) + 2):
                if dx * dx + dy * dy <= r * r + .3: put(a, int(round(px + dx)), int(round(py + dy)), rp[2])
    for px, py in pts:
        put(a, int(round(px - r * .6)), int(round(py - r * .6)), rp[3])
        if r >= 1.4: put(a, int(round(px + r * .7)), int(round(py + r * .5)), rp[1])


def _wing(a, x, y, span, up, rp, kind, side=1, frame=0):
    """bat or feather wing from shoulder (x,y). up in [-1..1]"""
    tipx, tipy = x - span * .8 * side, y - span * (.25 + .55 * up)
    for i in range(int(span) + 1):
        u = i / max(span, 1)
        px, py = x + (tipx - x) * u, y + (tipy - y) * u
        put(a, int(px), int(py), rp[1])
        drop = int((1 - u) * span * .45 + 1) if kind == 'bat' else int((1 - u * .6) * span * .5 + 1)
        for j in range(1, drop):
            c = rp[2] if j < drop * .5 else rp[1]
            if kind == 'bat' and (i % max(int(span / 3), 2) == 0): c = rp[0]
            if kind == 'feather' and j % 3 == 0: c = rp[3]
            put(a, int(px), int(py + j), c)


def being(a, x, y, kind, pose='idle', frame=0, k=1.0, ground=None):
    s = B[kind]
    rp = s['rp']
    H = s['h'] * k; W = s['w'] * k
    gy = ground if ground is not None else y + int(H) + 6
    cx = x + int(W) + 10 * k
    bob = [0, -1][frame % 2] if pose == 'idle' else [0, -1, 0, -1][frame % 4] if pose == 'move' else 0
    lean = {'attack': [0, 2, 3][frame % 3], 'cast': [0, -1, -1][frame % 3]}.get(pose, 0) * k
    floaty = s['lower'] in ('smoke', 'float')
    if floaty: bob = [0, -1, -2, -1][frame % 4]
    hunch = s.get('hunch', 0) * k
    hip = gy - H * .42 + bob
    sh = gy - H * .78 + bob + hunch * .5
    head_c = (cx + lean + hunch, sh - H * .1 - 2 * k)
    hr = max(2.4, H * .1)
    shadow_ell(a, cx, gy + 1, W * .9 + 2, 1.5 * k, .3 if not floaty else .18)
    # aura
    if s.get('aura'):
        blend_mask(a, ellipse_mask(a.shape[:2], cx, gy, W * 1.3 + 3, 2.2 * k + 1), s['aura'], .35)
        rr_ = random.Random(len(kind))
        for i in range(int(6 * k)):
            mx, my = cx + rr_.uniform(-W * 1.2, W * 1.2), gy - ((rr_.uniform(0, H) + frame * 3 * k) % (H * .9))
            put(a, int(mx), int(my), s['aura'])
    # wings behind
    if s.get('wings'):
        wr = s.get('wcol', [lit(c, -.1) for c in rp])
        up = {'idle': [.2, .4], 'move': [1, .3, -.3, .3], 'attack': [.8, 1, -.2], 'cast': [1, 1, 1]}.get(pose, [.3])
        u = up[frame % len(up)]
        span = H * (.75 if kind != 'imp' else .9)
        _wing(a, cx - W * .2, sh + 1, span, u, wr, s['wings'], 1, frame)
    # tail
    if s.get('tail'):
        sw = [0, 1, 0, -1][frame % 4]
        pts = [(cx - W * .5 - i * k, hip + 2 + i * .3 - (i * i) * .02 * (1 + sw * .5)) for i in range(int(8 * k))]
        for j in range(len(pts) - 1): capsule(a, pts[j][0], pts[j][1], pts[j + 1][0], pts[j + 1][1], max(1, 1.6 * k * (1 - j / len(pts))), rp)
        put(a, int(pts[-1][0] - 1), int(pts[-1][1] - 1), rp[0]); put(a, int(pts[-1][0] - 1), int(pts[-1][1]), rp[0])
    # cape behind
    if s.get('cape'):
        for yy in range(int(sh), int(gy)):
            fl = int((yy - sh) * .25 * (1 if pose == 'move' else .4)) + (frame % 2 if pose == 'move' else 0)
            hline(a, int(cx - W * .6 - fl), yy, int(W * 1.1) + fl, s['cape'] if yy % 5 else lit(s['cape'], -.2))
    # lower body
    lw = max(1, int(W * .28))
    low = s['lower']
    if low in ('legs', 'hooves', 'talons'):
        sw = {'move': [2, 0, -2, 0], 'attack': [1, 2, 2], 'cast': [0, 0, 0], 'idle': [0, 0]}.get(pose, [0])[frame % len({'move': 4, 'attack': 3, 'cast': 3, 'idle': 2}.get(pose, 1) * [0])] * k
        lw = max(2, W * .34)
        for side, d in ((-1, sw), (1, -sw)):
            lx = cx + side * W * .26
            fx = lx + d
            kx, ky = (lx + fx) / 2 + (1 if low == 'hooves' else .5) * k, (hip + gy) / 2
            lr = rp if side > 0 else [lit(c, -.12) for c in rp]
            capsule(a, lx, hip, kx, ky, lw * 1.1, lr); capsule(a, kx, ky, fx, gy - lw * .4, lw * .9, lr)
            if low == 'hooves': rect(a, int(fx - lw * .5), int(gy) - 1, int(lw) + 1, 2, DARK)
            elif low == 'talons': put(a, int(fx + lw), int(gy), hx('#e8b030')); put(a, int(fx - 1), int(gy), hx('#e8b030'))
            else: rect(a, int(fx - lw * .4), int(gy) - 1, int(lw) + 2, 1, rp[0])
    elif low == 'smoke':
        sm = s['smoke']
        n = int(gy - hip)
        for i in range(n):
            u = i / max(n, 1)
            w_ = W * (.55 - .45 * u)
            wob = math.sin(i * .5 + frame * 1.3) * 1.5 * k * u
            for xx in range(int(cx - w_ + wob), int(cx + w_ + wob) + 1):
                rr = (xx - (cx + wob)) / max(w_, 1)
                put(a, xx, int(hip + i), sm[3 if rr < -.3 else 2 if rr < .4 else 1])
        put(a, int(cx + math.sin(frame) * 2), int(gy - 2), sm[4]); put(a, int(cx - 2 + math.sin(frame) * 2), int(gy - 1), sm[3])
    elif low == 'float':
        n = int(gy - hip - 3 * k)
        for i in range(n):
            u = i / max(n, 1)
            w_ = W * (.6 - .2 * u)
            for xx in range(int(cx - w_), int(cx + w_) + 1):
                if i > n * .6 and (xx + i + frame) % 3 == 0: continue
                put(a, xx, int(hip + i), rp[2] if xx < cx else rp[1])
    elif low == 'robe':
        rb = s['robe']
        for yy in range(int(hip - H * .12), int(gy)):
            u = (yy - hip) / max(gy - hip, 1)
            w_ = W * (.5 + .25 * max(u, 0))
            for xx in range(int(cx - w_), int(cx + w_) + 1):
                rr = (xx - cx) / max(w_, 1)
                put(a, xx, yy, rb[3 if rr < -.4 else 2 if rr < .3 else 1])
        hline(a, int(cx - W * .7), int(gy) - 1, int(W * 1.4), rb[0])
    elif low == 'serpent':
        n = int(16 * k)
        for i in range(n):
            px = cx - i * .9 * k
            py = gy - 2 + math.sin(i * .45 + frame) * 1.5 * k
            for t in range(-int(2 * k), int(2 * k) + 1): put(a, int(px), int(py + t * .6), rp[2] if t < 0 else rp[1])
        for i in range(int(gy - hip)): hline(a, int(cx - W * .45), int(hip + i), int(W * .9), rp[2] if i % 3 else rp[3])
    elif low == 'roots':
        sw = {'move': [2, 0, -2, 0]}.get(pose, [0])[frame % 4 if pose == 'move' else 0] * k
        for side in (-1, 1):
            kx, ky = cx + side * W * .45 + sw * side, (hip + gy) / 2
            capsule(a, cx + side * W * .2, hip, kx, ky, W * .38, rp if side > 0 else [lit(c, -.12) for c in rp])
            capsule(a, kx, ky, kx + side * W * .25, gy - 1, W * .3, rp if side > 0 else [lit(c, -.12) for c in rp])
            for r_ in range(3): line(a, kx + side * W * .25, gy - 1, kx + side * W * (.25 + .2 * r_) + (r_ - 1) * 2 * k, gy, rp[0])
    # torso
    tw, th = W * .55, (hip - sh) * .62 + 1
    tcy = (sh + hip) / 2
    if s.get('blocky'):
        rect(a, int(cx - W * .6 + lean), int(sh), int(W * 1.2), int(hip - sh) + 1, rp[2])
        rect(a, int(cx - W * .6 + lean), int(sh), int(W * .45), int(hip - sh) + 1, rp[3])
        hline(a, int(cx - W * .6 + lean), int(sh), int(W * 1.2), rp[4]); hline(a, int(cx - W * .6 + lean), int(hip), int(W * 1.2), rp[0])
        if s.get('runes'):
            for i in range(3): put(a, int(cx - 2 + i * 2 + lean), int(tcy - 1 + (i % 2) * 2), s['runes'])
        if s.get('rivets'):
            for i in range(4): put(a, int(cx - W * .5 + 1 + i * W * .3 + lean), int(sh + 1), hx('#cfd4da'))
        if s.get('moss'):
            for i in range(int(W)): put(a, int(cx - W * .6 + i * 1.2 + lean), int(sh - (i % 2)), hx('#5a8a3a'))
    else:
        dome(a, cx + lean * .6, tcy, W * .62, (hip - sh) * .62 + 1, rp, 3)
        for side in (-1, 1): dome(a, cx + lean * .7 + side * W * .5, sh + 1.5 * k, max(1.6, W * .26), max(1.4, W * .22), rp if side > 0 else [lit(c, -.1) for c in rp], 4 + side)
        if s.get('belly'): dome(a, cx + 1 + lean * .6, tcy + th * .4, tw * .8, th * .6, [lit(c, .05) for c in rp], 4)
        if s.get('bones'):
            for i in range(3): hline(a, int(cx - tw * .6 + lean * .6), int(tcy - th * .4 + i * 2), int(tw * 1.2), rp[0] if i % 2 == 0 else rp[3])
            vline(a, int(cx + lean * .6), int(tcy - th * .6), int(th * 1.6), rp[1])
        if s.get('rags'):
            for i in range(int(tw * 2)): vline(a, int(cx - tw + i + lean * .6), int(tcy + th * .2), 2 + (i % 3), s['rags'])
        if s.get('fur'):
            for i in range(int(tw * 2)): put(a, int(cx - tw + i + lean * .6), int(tcy - th + (i % 2)), rp[4])
        if s.get('drips'):
            for i in range(3): put(a, int(cx - 2 + i * 2), int(tcy + th + (frame + i) % 3), hx('#a8d4f0'))
    if s.get('flames') or s.get('elemental') == 'fire':
        for i in range(5):
            fx = cx - W * .5 + i * W * .25 + lean
            fl = (frame + i) % 3
            put(a, int(fx), int(sh - 1 - fl), hx('#ffd34a')); put(a, int(fx), int(sh - fl), hx('#f49a3c'))
    if s.get('elemental') == 'earth':
        for i in range(3): dome(a, cx - W * .4 + i * W * .4 + lean, sh, 2 * k, 1.6 * k, R5('#4a4844', '#64605a', '#7e7a72', '#98938a', '#b2aca2'), i)
    # arms
    arm_col = rp[2]
    shx = cx + lean
    ay = sh + 1
    ap = {'idle': [(W * .55, H * .33), (W * .55, H * .31)], 'move': [(W * .3, H * .32), (W * .6, H * .3), (W * .85, H * .28), (W * .6, H * .3)],
          'attack': [(-W * .1, -H * .05), (W * .45, -H * .2), (W * 1.15, H * .08)], 'cast': [(W * .5, -H * .16), (W * .65, -H * .24), (W * 1.05, -H * .08)]}.get(pose, [(W * .7, H * .35)])
    hdx, hdy = ap[frame % len(ap)]
    if s.get('arms_fwd') and pose in ('idle', 'move'): hdx, hdy = W * 1.0, H * .02
    hand = (shx + hdx, ay + hdy)
    back = (shx - W * .55, ay + H * .3 + (2 if pose == 'move' and frame % 2 else 0))
    if pose == 'cast': back = (shx - W * .2, ay - H * .22)
    aw = max(1.8, W * .26)
    sx_f, sx_b = shx + W * .45, shx - W * .45
    for (sx_, tgt, rr) in ((sx_b, back, [lit(c, -.14) for c in rp]), (sx_f, hand, rp)):
        ex_ = (sx_ + tgt[0]) / 2 + (-.5 if tgt[1] > ay else .5) * k
        ey_ = (ay + tgt[1]) / 2 + 1 * k
        capsule(a, sx_, ay + 1, ex_, ey_, aw * 1.05, rr); capsule(a, ex_, ey_, tgt[0], tgt[1], aw * .9, rr)
        dome(a, tgt[0], tgt[1], aw * .62, aw * .62, rr, 2)
    if s.get('bracers'): put(a, int(hand[0]), int(hand[1]), s['bracers']); put(a, int(hand[0] - 1), int(hand[1]), s['bracers'])
    if s.get('claws'):
        for i in range(2): put(a, int(hand[0] + 1 + i), int(hand[1] + 1 - i), hx('#f2ece0'))
    wp = s.get('weapon')
    if wp:
        hx_, hy_ = hand
        if wp in ('sword', 'blade'):
            L = int((7 if wp == 'sword' else 11) * k)
            ang = {'attack': [-2.3, -1.2, .1]}.get(pose, [-1.1, -1.1, -1.1, -1.1])[frame % (3 if pose == 'attack' else 4)]
            for i in range(L):
                put(a, int(hx_ + math.cos(ang) * i), int(hy_ + math.sin(ang) * i), hx('#eef2f6') if wp == 'sword' else hx('#ff7a3a'))
                put(a, int(hx_ + math.cos(ang) * i + 1), int(hy_ + math.sin(ang) * i), hx('#9aa4ae') if wp == 'sword' else hx('#3a1010'))
            put(a, int(hx_ - 1), int(hy_), hx('#6b4c34')); put(a, int(hx_ + 1), int(hy_), hx('#6b4c34'))
        elif wp in ('club', 'axe'):
            ang = {'attack': [-2.4, -1.6, .2]}.get(pose, [-1.3] * 4)[frame % (3 if pose == 'attack' else 4)]
            L = int(9 * k)
            for i in range(L): put(a, int(hx_ + math.cos(ang) * i), int(hy_ + math.sin(ang) * i), hx('#6b4c34')); put(a, int(hx_ + math.cos(ang) * i + 1), int(hy_ + math.sin(ang) * i), hx('#4a3424'))
            ex, ey = hx_ + math.cos(ang) * L, hy_ + math.sin(ang) * L
            if wp == 'club': dome(a, ex, ey, 2.8 * k, 2.8 * k, R5('#4a3424', '#64462e', '#7e5a3a', '#987048', '#b08860'), 1)
            else:
                for j in range(-3, 4):
                    for q in range(3): put(a, int(ex + j * -math.sin(ang) - q * math.cos(ang)), int(ey + j * math.cos(ang) - q * math.sin(ang)), hx('#d8dde2') if q == 0 else hx('#9aa4ae'))
        elif wp in ('staff', 'spear'):
            L = int(18 * k)
            if pose == 'attack' and wp == 'spear':
                for i in range(L): put(a, int(hx_ - L * .4 + i), int(hy_), hx('#8c6844'))
                put(a, int(hx_ + L * .6), int(hy_), hx('#d8dde2')); put(a, int(hx_ + L * .6 + 1), int(hy_), hx('#d8dde2'))
            else:
                vline(a, int(hx_), int(hy_ - L * .5), L, hx('#5a4430') if wp == 'staff' else hx('#8c6844'))
                if wp == 'staff':
                    dome(a, hx_, hy_ - L * .5 - 1, 1.6, 1.6, R5('#1e5a2a', '#2a8a3a', '#4ac460', '#8af0a0', '#d0ffd8'), 2)
                    blend_mask(a, ellipse_mask(a.shape[:2], hx_, hy_ - L * .5 - 1, 4, 4), s.get('eye', GLOW['green']), .3)
                else: put(a, int(hx_), int(hy_ - L * .5 - 1), hx('#d8dde2')); put(a, int(hx_), int(hy_ - L * .5 - 2), hx('#d8dde2'))
    if pose == 'cast':
        orb = s.get('aura') or s.get('eye') or GLOW['violet']
        r_ = [1.5, 2.5, 3.5][frame % 3] * k
        blend_mask(a, ellipse_mask(a.shape[:2], hand[0] + 1, hand[1] - 1, r_ + 2, r_ + 2), orb, .35)
        blend_mask(a, ellipse_mask(a.shape[:2], hand[0] + 1, hand[1] - 1, r_, r_), orb, .85)
        put(a, int(hand[0] + 1), int(hand[1] - 1), hx('#ffffff'))
    # head
    hcx, hcy = head_c
    if s.get('hood'):
        dome(a, hcx - .5, hcy, hr * 1.25, hr * 1.3, [lit(c, -.05) for c in rp], 5)
        blend_mask(a, ellipse_mask(a.shape[:2], hcx + 1, hcy + .5, hr * .8, hr * .8), hx('#000000'), .85)
    elif s.get('snout'):
        dome(a, hcx, hcy, hr * 1.05, hr, rp, 5)
        dome(a, hcx + hr, hcy + hr * .3, hr * .7, hr * .5, rp, 6)
        put(a, int(hcx + hr * 1.6), int(hcy + hr * .1), DARK)
        if pose == 'attack': hline(a, int(hcx + hr * .7), int(hcy + hr * .7), int(hr), hx('#f2ece0'))
    else:
        dome(a, hcx, hcy, hr, hr * 1.05, rp if not s.get('bones') else rp, 5)
        if s.get('nose'): put(a, int(hcx + hr + 1), int(hcy + 1), rp[1]); put(a, int(hcx + hr), int(hcy + 1), rp[1])
    if s.get('hair'):
        for i in range(int(hr * 2)): put(a, int(hcx - hr + i), int(hcy - hr), s['hair']); put(a, int(hcx - hr), int(hcy - hr + 1 + i // 2), s['hair'])
    if s.get('ears'):
        for side in (-1, 1): put(a, int(hcx + side * hr * .5), int(hcy - hr - 1), rp[1]); put(a, int(hcx + side * hr * .5), int(hcy - hr - 2), rp[0])
    if s.get('topknot'):
        for i in range(int(hr * 2.2)):
            put(a, int(hcx - hr * .6 - i * .5), int(hcy - hr + i * .7 + math.sin(i * .6 + frame) * .8), hx('#141418'))
            put(a, int(hcx - hr * .6 - i * .5) + 1, int(hcy - hr + i * .7 + math.sin(i * .6 + frame) * .8), hx('#2a2a34'))
        rect(a, int(hcx - hr * .7), int(hcy - hr - 1), 2, 2, s.get('bracers', hx('#ffd34a')))
    hn = s.get('horns')
    if hn:
        hc, hd = (hx('#3a2a26'), hx('#1e1614')) if kind in ('demon', 'demon_lord', 'imp', 'gargoyle', '_t', 'afreet') else (hx('#e2d8c2'), hx('#9a8c74'))
        q = max(1.0, hr / 2.6)
        def horn(pts, c, oy=0.0):
            P = [(hcx + dx * q, hcy - hr + oy * hr + dy * q) for dx, dy in pts]
            for j in range(len(P) - 1):
                w_ = max(1.2, q * 1.5 * (1 - j / len(P)))
                capsule(a, P[j][0], P[j][1], P[j + 1][0], P[j + 1][1], w_, [c, c, c, lit(c, .25), lit(c, .4)])
        if hn == 'small':
            horn([(.5, 0), (1, -1)], hc); horn([(-1.5, 0), (-1.5, -1)], hd)
        elif hn == 'ram':
            horn([(-.5, 0), (-1.5, -.6), (-2.6, -.4), (-3.2, .5), (-3, 1.6), (-2.2, 2.2)], hc, .45)
        elif hn == 'great':
            horn([(0, .4), (1, -.6), (1.6, -1.8), (2.4, -2.8), (3.4, -3.3)], hc, .3); horn([(-1.6, .4), (-2.4, -.8), (-2.8, -2), (-2.6, -3.2)], hd, .3)
        elif hn == 'bull':
            horn([(1.5, .5), (2.4, 0), (3.2, -.8), (3.4, -1.8)], hc); horn([(-1.5, .5), (-2.4, 0), (-3, -.8), (-3.2, -1.8)], hd)
    if s.get('crown_spikes'):
        for i in range(3): vline(a, int(hcx - 2 + i * 2), int(hcy - hr - 2 - (i == 1)), 2 + (i == 1), hx('#3a3a40') if kind != 'lich' else hx('#c8a040'))
    if s.get('crest'):
        for i in range(4): put(a, int(hcx - i), int(hcy - hr - 1 + i // 2), s['crest'])
    if s.get('elemental') == 'fire':
        for i in range(4): put(a, int(hcx - 2 + i), int(hcy - hr - 1 - (frame + i) % 3), hx('#ffd34a'))
    # eyes
    ec = s.get('eye', DARK)
    ex_ = hcx + hr * .45; ey_ = hcy - hr * .15
    if s.get('one_eye'):
        dome(a, ex_ - .5, ey_, 1.6, 1.3, R5('#c8c4bc', '#dcd8d0', '#ece8e0', '#f6f4ee', '#ffffff'), 1); put(a, int(ex_), int(ey_), DARK)
    else:
        put(a, int(ex_), int(ey_), ec)
        if hr > 3: put(a, int(ex_ - 2), int(ey_), lit(ec, -.15))
        if ec in GLOW.values(): blend_mask(a, ellipse_mask(a.shape[:2], ex_, ey_, 2, 1.5), ec, .3)
    if hr >= 4.5 and not s.get('hood') and not s.get('one_eye'):
        q = hr / 4
        hline(a, int(ex_ - 2 * q), int(ey_ - 1.2 * q), int(3 * q) + 1, lit(rp[0], -.2))          # brow
        rect(a, int(ex_ - q * .5), int(ey_), int(q) + 1, int(q * .8) + 1, ec)                       # eye
        hline(a, int(hcx + hr * .1), int(hcy + hr * .55), int(hr * .75), lit(rp[0], -.25))         # mouth
        put(a, int(hcx + hr * .95), int(hcy + hr * .15), rp[1])                                    # nose
        if pose in ('attack', 'cast') or kind in ('demon', 'demon_lord', 'ogre', 'troll', 'abyss_lord'):
            for i in range(int(hr * .7)):
                if i % 2 == 0: put(a, int(hcx + hr * .15 + i), int(hcy + hr * .55) + 1, hx('#f2ece0'))
    if k >= 2:   # muscle / plate lines for titans
        for i in range(3): hline(a, int(cx - W * .3 + lean * .6), int(sh + (hip - sh) * (.3 + i * .2)), int(W * .5), lit(rp[1], -.1))
    if s.get('leaves'):
        dome(a, hcx - 1, hcy - hr * .8, hr * 2.2, hr * 1.4, s['leaves'], 7, rough=.4)
        dome(a, cx - W * .6, sh + 2, hr * 1.4, hr, s['leaves'], 8, rough=.4)
    if s.get('frost'):
        for i in range(4): put(a, int(cx - W * .5 + i * W * .3), int(sh - 1), hx('#e8f6ff'))
    if s.get('ghost'):
        pass
    return dict(hand=hand, head=(hcx, hcy), gy=gy, cx=cx)


# ------------------------------------------------------------------ special interaction sprites
def possess(a, x, y, frame):
    """jinn entering a human: smoke ribbon flowing into the human's head, eyes glow, human tilts."""
    being(a, x, y, 'jinn', 'cast', min(frame, 2))
    hx_, hy_ = x + 46, y + 14
    person_tiny(a, hx_, hy_, 0, flail=frame < 2)
    sm = B['jinn']['smoke']
    t = (frame + 1) / 4
    for i in range(int(22 * t)):
        u = i / 22
        px = x + 30 + u * 24; py = y + 14 + math.sin(u * 6 + frame) * 3 - u * 4
        put(a, int(px), int(py), sm[3]); put(a, int(px), int(py + 1), sm[2])
    if frame >= 2:
        put(a, hx_ + 11, hy_ + 11, GLOW['cyan']); blend_mask(a, ellipse_mask(a.shape[:2], hx_ + 9, hy_ + 13, 7, 9), GLOW['cyan'], .2 + .1 * (frame - 2))


def possessed_overlay(a, frame):
    """overlay for a possessed human (20x36 people frame): glowing eyes + swirl."""
    put(a, 11, 11, GLOW['cyan']); put(a, 9, 11, GLOW['cyan'])
    for i in range(6):
        t = i / 6 * math.tau + frame * .8
        put(a, int(9 + math.cos(t) * 7), int(14 + math.sin(t) * 3), B['jinn']['smoke'][3])


# ------------------------------------------------------------------ titans  (big canvases; humans are 27 px tall)
TITANS = {
    'colossus': dict(base='stone_golem', k=3.2),
    'hill_giant': dict(base='ogre', k=2.6),
    'frost_giant': dict(base='frost_wight', k=3.4, over=dict(bones=False, rp=R5('#4a6a8a', '#6488a8', '#82a6c4', '#a4c4dc', '#cae2f2'), weapon='club', hair=hx('#e8f6ff'))),
    'flame_titan': dict(base='afreet', k=3.0),
    'abyss_lord': dict(base='demon_lord', k=2.6),
    'elder_treant': dict(base='treant', k=2.4),
}
TITAN_POSES = {'idle': 2, 'move': 4, 'attack': 3, 'grab': 4, 'stomp': 3, 'roar': 2}


def titan(a, x, y, name, pose='idle', frame=0):
    t = TITANS[name]
    spec = dict(B[t['base']]); spec.update(t.get('over', {}))
    B['_t'] = spec
    try:
        bp = {'grab': 'attack', 'stomp': 'move', 'roar': 'cast'}.get(pose, pose)
        bf = frame if pose not in ('grab', 'stomp') else (2 if pose == 'grab' and frame > 0 else frame % 3)
        g = being(a, x, y, '_t', bp, bf, k=t['k'])
    finally:
        B.pop('_t', None)
    spec = spec
    if pose == 'grab':
        hx_, hy_ = g['hand']
        lift = [0, 6, 14, 20][frame % 4]
        rpb = spec['rp']
        person_tiny(a, int(hx_ - 9), int(hy_ - 22 - lift), frame % 2, flail=True)
        capsule(a, hx_, hy_, hx_, hy_ - lift - 2, max(2, spec['w'] * t['k'] * .22), rpb)
        dome(a, hx_, hy_ - lift - 2, 4.5, 3.8, rpb, 9)
        for i in range(3): put(a, int(hx_ - 2 + i * 2), int(hy_ - lift - 4), rpb[0])
    if pose == 'stomp':
        if frame == 2:
            for i in range(10):
                ang = math.pi + i / 9 * math.pi
                put(a, int(g['cx'] + 18 + math.cos(ang) * 14), int(g['gy'] + math.sin(ang) * 4), hx('#a88a5a'))
            blend_mask(a, ellipse_mask(a.shape[:2], g['cx'] + 18, g['gy'], 16, 3), hx('#8a6a4a'), .5)
    if pose == 'roar':
        hx_, hy_ = g['head']
        for i in range(3):
            r_ = 4 + i * 4 + frame * 2
            for t_ in np.linspace(-.6, .6, 9): put(a, int(hx_ + 6 + math.cos(t_) * r_), int(hy_ + math.sin(t_) * r_), hx('#f6f2ea'))
    return g


def sea_serpent(a, x, y, pose='idle', frame=0):
    """humps rising from the water; head strikes on attack, coils a human on grab."""
    rp = R5('#0e3a3a', '#145a54', '#1e7a6e', '#3a9a88', '#6abca8')
    wl = y + 96
    for hump in range(3):
        bx = x + 30 + hump * 40 + (frame % 2) * 2
        rr = 18 - hump * 3
        for i in range(40):
            ang = math.pi * i / 39
            px, py = bx - math.cos(ang) * rr, wl - math.sin(ang) * rr
            for t in range(8): put(a, int(px), int(py + t), rp[4 if t < 1 else 3 if t < 3 else 2 if t < 6 else 1])
            if i % 5 == 0: put(a, int(px), int(py + 7), hx('#c8a070'))
        for i in range(4): put(a, int(bx - 9 + i * 6), int(wl - rr - 1), hx('#c8a040')); put(a, int(bx - 9 + i * 6), int(wl - rr - 2), hx('#e8c860'))
        blend_mask(a, ellipse_mask(a.shape[:2], bx - rr, wl + 2, 6, 2), hx('#e8f6ff'), .6); blend_mask(a, ellipse_mask(a.shape[:2], bx + rr, wl + 2, 6, 2), hx('#e8f6ff'), .6)
    strike = {'attack': [0, 12, 22], 'grab': [6, 12, 14, 14], 'roar': [-4, -6]}.get(pose, [0, 2])[frame % {'attack': 3, 'grab': 4, 'roar': 2}.get(pose, 2)]
    hx_, hy_ = x + 150 + strike, wl - 56 + strike * .6
    for i in range(30):
        u = i / 29
        px, py = x + 138 + (hx_ - x - 138) * u, wl - u * (wl - hy_)
        for t in range(9): put(a, int(px + t * .5), int(py + t * .45), rp[4 if t < 1 else 3 if t < 3 else 2 if t < 6 else 1])
    blend_mask(a, ellipse_mask(a.shape[:2], x + 140, wl + 2, 9, 2), hx('#e8f6ff'), .6)
    dome(a, hx_ + 5, hy_, 10, 6.5, rp, 3); dome(a, hx_ + 14, hy_ + 2, 6, 4, rp, 4)
    rect(a, int(hx_ + 8), int(hy_ - 3), 3, 2, GLOW['gold']); put(a, int(hx_ + 9), int(hy_ - 3), hx('#141418'))
    if pose in ('attack', 'grab', 'roar'):
        hline(a, int(hx_ + 6), int(hy_ + 4), 14, hx('#3a1a1a')); hline(a, int(hx_ + 6), int(hy_ + 5), 13, hx('#5a2020'))
        for i in range(5): put(a, int(hx_ + 7 + i * 3), int(hy_ + 3), hx('#f2ece0')); put(a, int(hx_ + 8 + i * 3), int(hy_ + 6), hx('#f2ece0'))
    for i in range(9): vline(a, int(hx_ - 4 - i), int(hy_ - 6 - (i % 3)), 2, hx('#c8a040'))
    if pose == 'grab': person_tiny(a, int(hx_ + 6), int(hy_ - 6 - frame * 3), frame % 2, flail=True)


def kraken(a, x, y, pose='idle', frame=0):
    rp = R5('#3a1a2a', '#5a2440', '#7a3256', '#9a4a70', '#ba6a8c')
    wl = y + 100
    reach = {'attack': [0, 10, 22], 'grab': [8, 14, 20, 20], 'move': [0, 3, 6, 3]}.get(pose, [0, 3])[frame % {'attack': 3, 'grab': 4, 'move': 4}.get(pose, 2)]
    for ti, (bx, h, ph) in enumerate([(x + 14, 38, 0), (x + 34, 48, 1.2), (x + 96, 46, 2.1), (x + 116, 34, .6)]):
        tip = None
        for i in range(int(h + (reach if ti >= 2 else reach * .4))):
            u = i / h
            px = bx + math.sin(u * 3 + frame * .7 + ph) * 6 * u + (reach * u * (1 if ti >= 2 else -.3))
            py = wl - i
            w = max(1, int(4 * (1 - u * .7)))
            for t in range(-w, w + 1): put(a, int(px + t), int(py), rp[3 if t < 0 else 2 if t < w * .5 else 1])
            if i % 4 == 0 and w > 1: put(a, int(px + w), int(py), hx('#e8c8d4'))
            tip = (px, py)
        if pose == 'grab' and ti == 2: person_tiny(a, int(tip[0] - 8), int(tip[1] - 26), frame % 2, flail=True)
        blend_mask(a, ellipse_mask(a.shape[:2], bx, wl + 1, 8, 2), hx('#e8f6ff'), .5)
    tmp = a.copy(); dome(tmp, x + 65, wl - 2, 24, 18, rp, 4); a[:wl - 1] = tmp[:wl - 1]
    blend_mask(a, ellipse_mask(a.shape[:2], x + 65, wl, 26, 3), hx('#e8f6ff'), .55)
    for side in (-1, 1):
        rect(a, int(x + 64 + side * 9), int(wl - 9), 3, 2, GLOW['gold']); put(a, int(x + 65 + side * 9), int(wl - 8), hx('#141418'))


def elder_wyrm(a, x, y, pose='idle', frame=0):
    """giant dragon side view: body, two legs visible, big wings, long neck; breath pose spits fire."""
    rp = R5('#3a0e14', '#5a1820', '#7a2a2c', '#9a4038', '#ba5a48')
    wp = R5('#2a0a10', '#4a1418', '#6a2424', '#8a3a30', '#a8543e')
    gy = y + 92
    cx, cy = x + 70, gy - 26 + [0, -1, 0, -1][frame % 4]
    shadow_ell(a, cx, gy + 1, 40, 4, .3)
    up = {'idle': [.2, .4], 'move': [1, .3, -.4, .3], 'attack': [.6, .9, .2], 'breath': [.8, .8, .8], 'grab': [1, .8, .6, .4], 'roar': [1, 1]}.get(pose, [.3])
    _wing(a, cx - 4, cy - 12, 56, up[frame % len(up)], wp, 'bat')
    for i in range(36):   # tail
        u = i / 35
        px, py = cx - 22 - i * 1.3, cy + 4 - u * 10 + math.sin(u * 4 + frame) * 3
        w = int(6 * (1 - u)) + 1
        for t in range(w): put(a, int(px), int(py + t), rp[3 if t < w * .3 else 2 if t < w * .7 else 1])
    sw = {'move': [4, 0, -4, 0]}.get(pose, [0])[frame % 4 if pose == 'move' else 0]
    for side, d in ((-1, sw), (1, -sw)):
        lx = cx + side * 14
        for t in range(6): line(a, lx + t, cy + 4, lx + t + d, gy, rp[1] if side < 0 else rp[2])
        for c_ in range(3): put(a, int(lx + d + 6 + c_), int(gy), hx('#e2d8c2'))
    dome(a, cx, cy, 26, 14, rp, 3)
    for i in range(10): put(a, int(cx - 20 + i * 4), int(cy - 14 + (i % 2)), hx('#e2d8c2'))
    hline(a, int(cx - 18), int(cy + 8), 36, hx('#c8a070'))
    neck = {'attack': [0, 6, 12], 'breath': [4, 4, 4], 'grab': [0, 8, 4, -4], 'roar': [-4, -6]}.get(pose, [0, 0, 0, 0])
    nk = neck[frame % len(neck)]
    hx_, hy_ = cx + 40 + nk, cy - 30 + nk * .8
    for i in range(20):
        u = i / 19
        px, py = cx + 20 + (hx_ - cx - 20) * u, cy - 6 - (cy - 6 - hy_) * u
        for t in range(7): put(a, int(px + t * .3), int(py + t * .6), rp[3 if t < 2 else 2 if t < 5 else 1])
    dome(a, hx_ + 4, hy_, 9, 5.5, rp, 5)
    dome(a, hx_ + 12, hy_ + 1.5, 6, 3.2, rp, 6)
    for i in range(5): put(a, int(hx_ - 2 - i), int(hy_ - 5 - i * .8), hx('#e2d8c2'))
    put(a, int(hx_ + 6), int(hy_ - 2), GLOW['gold']); put(a, int(hx_ + 7), int(hy_ - 2), GLOW['gold'])
    if pose in ('breath', 'attack', 'roar', 'grab'):
        hline(a, int(hx_ + 8), int(hy_ + 3), 9, hx('#3a1010'))
        for i in range(4): put(a, int(hx_ + 9 + i * 2), int(hy_ + 2), hx('#f2ece0'))
    if pose == 'breath':
        L = [30, 46, 60][frame % 3]
        for i in range(L):
            u = i / 60
            w = 2 + u * 12
            for j in range(-int(w), int(w) + 1):
                if random.Random(i * 31 + j + frame).random() < .75:
                    c = hx('#fff6c0') if abs(j) < w * .3 else hx('#ffb84a') if abs(j) < w * .6 else hx('#e8521a')
                    put(a, int(hx_ + 17 + i), int(hy_ + 3 + j * .6 + i * .25), c)
    if pose == 'grab':
        person_tiny(a, int(hx_ + 10), int(hy_ - 4 + (frame % 2)), frame % 2, flail=True)


def behemoth(a, x, y, pose='idle', frame=0):
    import animals as AN
    from bestiary import ex_spikes, ex_horn_nose
    AN.SP['_behemoth'] = dict(rx=34, ry=20, rp=R5('#2a2420', '#3e342c', '#54463a', '#6a5a4a', '#806e5c'), fur='bristle', head=(12, 10), neck=(0, 0), snout=8,
                              ears='tiny', horns='curl', legs=(16, 9), lcol=hx('#3e342c'), hoof=DARK, tail='stub',
                              extras=(ex_spikes(hx('#c8bca0')), ex_horn_nose), eyec=GLOW['red'])
    try:
        p = {'stomp': 'attack', 'roar': 'attack', 'grab': 'eat'}.get(pose, pose)
        if p not in ('walk', 'idle', 'run', 'eat', 'attack', 'sleep'): p = 'walk' if pose == 'move' else 'idle'
        g = AN.quad(a, x + 6, y + 10, '_behemoth', frame, False, 5, pose=p)
    finally:
        AN.SP.pop('_behemoth', None)
    if pose == 'stomp' and frame % 3 == 2:
        blend_mask(a, ellipse_mask(a.shape[:2], x + 100, y + 104, 26, 4), hx('#8a6a4a'), .55)
    if pose == 'grab':
        person_tiny(a, x + 128, y + 54 + frame % 2 * 2, frame % 2, flail=True)


def sand_titan(a, x, y, pose='idle', frame=0):
    from bestiary import worm
    spec = dict(rp=R5('#6a4a2a', '#8a6a42', '#a8885a', '#c4a676', '#dcc296'), size=3.2)
    p = {'move': 'walk', 'grab': 'attack', 'stomp': 'attack', 'roar': 'eat', 'breath': 'attack'}.get(pose, pose)
    if p not in ('walk', 'idle', 'attack', 'sleep', 'run', 'eat'): p = 'idle'
    worm(a, x + 30, y + 40, spec, p, frame)
    if pose == 'grab': person_tiny(a, x + 76, y + 6 + frame * 3, frame % 2, flail=True)


SPECIAL_TITANS = {'sea_serpent': (sea_serpent, (220, 130), {'idle': 2, 'attack': 3, 'grab': 4, 'roar': 2}),
                  'kraken': (kraken, (150, 140), {'idle': 2, 'move': 4, 'attack': 3, 'grab': 4}),
                  'elder_wyrm': (elder_wyrm, (200, 120), {'idle': 2, 'move': 4, 'attack': 3, 'breath': 3, 'grab': 4, 'roar': 2}),
                  'behemoth': (behemoth, (170, 120), {'idle': 2, 'walk': 4, 'attack': 3, 'stomp': 3, 'grab': 2}),
                  'sand_titan': (sand_titan, (140, 170), {'idle': 2, 'move': 4, 'attack': 3, 'grab': 4, 'roar': 2})}
