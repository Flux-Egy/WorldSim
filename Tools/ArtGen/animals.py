"""2x-detail creatures: one parametric quadruped rig + birds, fish, crocodile.
Every species: adult + young, 4-frame walk. Facing right, light top-left, no outlines."""
import math, random
import numpy as np
from lib import *

DARK = hx('#16120e')


def R5(*c): return ramp(*c)


def line(a, x0, y0, x1, y1, col, t=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n):
        u = i / max(1, n - 1)
        x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        for k in range(t): put(a, int(round(x)) + k, int(round(y)), col)


def mask_of(a, cx, cy, rx, ry):
    return ellipse_mask(a.shape[:2], cx, cy, rx, ry)


def fur(a, m, kind, rp, seed, extra=None):
    r = random.Random(seed)
    ys, xs = np.nonzero(m)
    if not len(xs): return
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    if kind == 'wool':
        for y, x in zip(ys, xs):
            if (x + (y // 2) * 2) % 3 == 0 and y % 2 == 0:
                a[y, x] = lit(tuple(a[y, x]), .18)
                if y + 1 <= y1 and m[y + 1, x]: a[y + 1, x] = lit(tuple(a[y + 1, x]), -.14)
    elif kind == 'short':
        for _ in range(len(xs) // 14):
            i = r.randrange(len(xs)); y, x = ys[i], xs[i]
            if y > (y0 + y1) / 2: a[y, x] = lit(tuple(a[y, x]), -.1)
    elif kind == 'shaggy':
        for y, x in zip(ys, xs):
            if (x * 5 + y * 3) % 7 == 0: a[y, x] = lit(tuple(a[y, x]), -.15)
            elif (x * 5 + y * 3) % 7 == 3 and y < (y0 + y1) / 2: a[y, x] = lit(tuple(a[y, x]), .12)
        for x in range(x0 + 1, x1, 2):
            col = [yy for yy in range(y0, y1 + 1) if m[yy, x]]
            if col and r.random() < .7: put(a, x, col[-1] + 1, rp[1])
    elif kind == 'spots':
        for _ in range(extra.get('n', 4)):
            cx, cy = r.uniform(x0 + 1, x1 - 1), r.uniform(y0, y1)
            sm = mask_of(a, cx, cy, r.uniform(1.4, 2.6), r.uniform(1, 2)) & m
            a[sm] = extra['col']
            # keep top-light on spots
            for y, x in zip(*np.nonzero(sm)):
                if y > 0 and not sm[y - 1, x]: a[y, x] = lit(extra['col'], .25)
    elif kind == 'stripes':
        for y, x in zip(ys, xs):
            if (x + y // 3) % extra.get('p', 3) == 0 and y < y1 - extra.get('skip', 0): a[y, x] = lit(tuple(a[y, x]), -.28) if 'col' not in extra else extra['col']
    elif kind == 'dapple':
        for _ in range(extra.get('n', 7)):
            i = r.randrange(len(xs)); y, x = ys[i], xs[i]
            if y < (y0 + y1) / 2 + 1: put(a, x, y, extra['col'])
    elif kind == 'bristle':
        for y, x in zip(ys, xs):
            if (x * 7 + y * 5) % 5 == 0: a[y, x] = lit(tuple(a[y, x]), -.18)
        for x in range(x0 + 2, x1 - 1):
            col = [yy for yy in range(y0, y1 + 1) if m[yy, x]]
            if col and x % 2 == 0: put(a, x, col[0] - 1, rp[0])


def belly(a, m, col, frac=.35, front=None):
    ys, xs = np.nonzero(m)
    if not len(ys): return
    yt = ys.max() - (ys.max() - ys.min()) * frac
    for y, x in zip(ys, xs):
        if y >= yt and (front is None or x >= front): a[y, x] = col if (x + y) % 5 else lit(col, -.08)


# ------------------------------------------------------------------ species specs
SP = {
    'sheep': dict(rx=7, ry=5, rp=R5('#a9a397', '#cdc8bb', '#e4e0d4', '#f3f1ea', '#ffffff'), fur='wool', rough=.35,
                  head=(2.6, 2.3), hrp=R5('#211c18', '#2e2721', '#3e352c', '#54493d', '#6a5d4e'), neck=(1, -1), snout=1.2,
                  ears='droop', legs=(4, 1), lcol=hx('#2e2721'), tail='stub',
                  young=dict(rp=R5('#c9c3b5', '#e2ddd0', '#f1eee5', '#faf8f2', '#ffffff'))),
    'goat': dict(rx=6, ry=3.8, rp=R5('#5e4632', '#7b5c40', '#98754f', '#b38f66', '#cfae84'), fur='short', head=(2.3, 2), neck=(2.5, 3), snout=2,
                 ears='side', horns='curl', beard=True, legs=(5, 1), lcol=hx('#3f3024'), hoof=DARK, tail='up', marks=('face', hx('#ece4d2')),
                 young=dict(horns=None, beard=False)),
    'cow': dict(rx=8.5, ry=4.6, rp=R5('#bdb6a8', '#d8d2c4', '#ece7db', '#f8f5ee', '#ffffff'), fur='spots', furx=dict(col=hx('#2a2a2e'), n=5),
                head=(2.8, 2.3), neck=(1.5, 1), snout=2, scol=hx('#e2a5a0'), ears='side', horns='small', legs=(5, 2), lcol=hx('#d8d2c4'), hoof=hx('#3a3530'),
                tail='tuft', udder=True, young=dict(horns=None, udder=False)),
    'pig': dict(rx=7, ry=4.4, rp=R5('#b8706a', '#d48b84', '#e8a6a0', '#f4c2bc', '#fcdcd8'), fur='short', head=(3, 2.6), neck=(0, 0), snout=1.8,
                scol=hx('#c27a74'), disc=True, ears='flop', legs=(3, 2), lcol=hx('#d48b84'), hoof=hx('#7a4a46'), tail='curl'),
    'horse': dict(rx=8, ry=4, rp=R5('#4a2c18', '#653d22', '#83532f', '#a06a3e', '#bb8552'), fur='short', head=(2.4, 2), neck=(4, 6), snout=3.2,
                  ears='point', mane=hx('#1e1510'), legs=(7, 2), lcol=hx('#653d22'), hoof=DARK, sock=hx('#ece4d2'), tail='long', tcol=hx('#1e1510'),
                  marks=('blaze', hx('#ece4d2'))),
    'donkey': dict(rx=7, ry=3.8, rp=R5('#5a5652', '#75706a', '#8f8a82', '#a8a39b', '#c2bdb4'), fur='short', head=(2.4, 2.1), neck=(3, 4), snout=2.6,
                   scol=hx('#d8d2c8'), ears='long', mane=hx('#2e2b28'), legs=(6, 2), lcol=hx('#75706a'), hoof=DARK, tail='tuft', bellyc=hx('#d2cdc4')),
    'camel': dict(rx=8, ry=4, rp=R5('#8a6a3e', '#a8844f', '#c39e64', '#d8b77d', '#ead09a'), fur='short', head=(2.2, 1.8), neck=(6, 7), snout=3,
                  ears='tiny', hump=True, legs=(9, 2), lcol=hx('#a8844f'), hoof=hx('#5a4430'), tail='tuft'),
    'dog': dict(rx=5, ry=3, rp=R5('#6a4426', '#8a5a34', '#a87444', '#c49058', '#dcae74'), fur='short', head=(2.3, 2), neck=(2, 2.5), snout=2.4,
                ears='droop', legs=(4, 1), lcol=hx('#8a5a34'), tail='up', bellyc=hx('#ecdcc0'), front_belly=True),
    'cat': dict(rx=4.5, ry=2.6, rp=R5('#9a5a20', '#bc7430', '#d68f44', '#eaa95e', '#f6c47e'), fur='stripes', furx=dict(p=3, skip=1), head=(2.2, 1.9), neck=(1.5, 2),
                snout=.8, ears='point', legs=(3, 1), lcol=hx('#bc7430'), tail='cat', bellyc=hx('#f4e6d0')),
    'deer': dict(rx=6.5, ry=3.6, rp=R5('#6e3e22', '#8c522e', '#a8683c', '#c2804e', '#d69a66'), fur='short', head=(2.2, 1.9), neck=(3.5, 5), snout=2.4,
                 ears='side', antler=True, legs=(7, 1), lcol=hx('#8c522e'), hoof=DARK, tail='white', bellyc=hx('#ecdcc6'),
                 young=dict(antler=False, fur='dapple', furx=dict(col=hx('#f6ead2'), n=9))),
    'rabbit': dict(rx=3.6, ry=3, rp=R5('#6e6052', '#8a7a68', '#a39380', '#bcad98', '#d4c6b0'), fur='short', head=(2, 1.8), neck=(1.5, 1.8), snout=.6,
                   ears='rabbit', legs=(1, 2), lcol=hx('#8a7a68'), tail='puff', hop=True, bellyc=hx('#e8dece')),
    'wolf': dict(rx=6.5, ry=3.4, rp=R5('#4a4c52', '#64666c', '#7e8086', '#999ba0', '#b6b8bc'), fur='shaggy', head=(2.3, 2), neck=(2.5, 2.5), snout=3,
                 ears='point', legs=(5, 1), lcol=hx('#64666c'), tail='bushy', bellyc=hx('#d2d0cc'), front_belly=True),
    'bear': dict(rx=8, ry=5.4, rp=R5('#2e1e14', '#43301f', '#5a412a', '#715336', '#8a6744'), fur='shaggy', head=(3, 2.7), neck=(1.5, 1), snout=1.8,
                 scol=hx('#9a7a58'), ears='round', legs=(4, 3), lcol=hx('#43301f'), tail='stub'),
    'boar': dict(rx=6.5, ry=4.2, rp=R5('#2a2018', '#3b2d22', '#4e3c2d', '#634d3a', '#7a6048'), fur='bristle', head=(2.8, 2.4), neck=(0, 0), snout=2,
                 scol=hx('#5e4838'), disc=True, tusk=True, ears='point', legs=(3, 1), lcol=hx('#3b2d22'), hoof=DARK, tail='stub',
                 young=dict(tusk=False, rp=R5('#5e4632', '#7b5c40', '#98754f', '#b38f66', '#cfae84'), fur='stripes', furx=dict(p=3, col=hx('#e2cca4')))),
    'fox': dict(rx=5.2, ry=2.8, rp=R5('#9a3c14', '#bc5020', '#d86a30', '#ec8644', '#f8a660'), fur='short', head=(2.2, 1.9), neck=(2, 2.5), snout=2.8,
                ears='point', etip=DARK, legs=(4, 1), lcol=hx('#2a1e18'), tail='fox', bellyc=hx('#f4ece0'), front_belly=True),
}
SPECIES = list(SP.keys())


def quad(a, x, y, name, frame=0, young=False, seed=1, pose='walk'):
    """x,y = top-left of an approx (2rx+10) x (2ry+legs+8) box. pose: walk(0-3) idle(0-1) run(0-3) eat(0-1) attack(0-2) sleep(0-1)"""
    s = dict(SP[name])
    if young:
        s.update(s.get('young', {}))
        k = .66
        s['rx'] *= k; s['ry'] *= k; s['head'] = (s['head'][0] * .86, s['head'][1] * .86)
        s['neck'] = (s['neck'][0] * .7, s['neck'][1] * .7); s['snout'] *= .7
        s['legs'] = (max(1, round(s['legs'][0] * .8)), max(1, s['legs'][1] - 1 if s['legs'][1] > 1 else 1))
        s['rp'] = [lit(c, .06) for c in s['rp']]
    G = 1.25
    s['rx'] *= G; s['ry'] *= G; s['head'] = (s['head'][0] * G, s['head'][1] * G)
    s['neck'] = (s['neck'][0] * G, s['neck'][1] * G); s['snout'] *= G
    s['legs'] = (int(round(s['legs'][0] * G)), s['legs'][1])
    rx, ry = s['rx'], s['ry']
    L, T = s['legs']
    frame4 = frame % 4
    bob = 1 if frame4 in (1, 3) else 0
    if pose in ('idle', 'eat', 'sleep'): bob = frame % 2 if pose == 'idle' else 0
    if pose == 'attack': bob = 0
    if s.get('hop') and pose in ('walk', 'run'):
        bob = [0, -2, -3, -1][frame4] * (2 if pose == 'run' else 1)
    adx = [-1, 2, 1][frame % 3] if pose == 'attack' else 0
    sleep_drop = int(L * .8) if pose == 'sleep' else 0
    cx, cy = x + rx + 4 + adx, y + ry + 3 + (s['neck'][1] if s['neck'][1] > ry else 0) - bob
    ground = int(cy + bob + ry * .7 + L)
    cy += sleep_drop
    rp = s['rp']; hrp = s.get('hrp', rp)
    shadow_ell(a, cx + 1, ground + .5, rx + .5, 1.2, .24)
    # legs: diagonal pairs A (near-front, far-back) and B
    swing = [1, 0, -1, 0][frame4] if pose == 'walk' else [2, 0, -2, 0][frame4] if pose == 'run' else 0
    if pose == 'attack': swing = [0, 1, 1][frame % 3]
    hipb, hipf = cx - rx * .55, cx + rx * .5
    legy = cy + ry * .55
    lc = s['lcol']; lcd = lit(lc, -.25)

    def leg(hx_, sw, col, far):
        if pose == 'sleep':
            put(a, int(hx_ + 1), ground - 1, col); put(a, int(hx_ + 2), ground - 1, col); return
        fx = hx_ + sw * (1.5 if L > 3 else 1)
        lift = 1 if sw == 0 and frame in (1, 3) and ((frame == 1) ^ far) else 0
        if s.get('hop'): lift = 0 if frame in (0, 3) else -1
        fy = ground - lift
        for t in range(T): line(a, hx_ + t, legy, fx + t, fy, col)
        if s.get('sock') and not far:
            for t in range(T): put(a, int(round(fx)) + t, fy - 1, s['sock'])
        if s.get('hoof'):
            for t in range(T): put(a, int(round(fx)) + t, fy, s['hoof'])
    leg(hipb + 1, swing, lcd, True); leg(hipf + 1, -swing, lcd, True)
    # tail behind body
    tx, ty = cx - rx + .5, cy - ry * .35
    tail = s['tail']; tc = s.get('tcol', rp[1])
    if tail == 'long':
        for i in range(8): put(a, int(tx - 1 - i * .35 + (i % 3 == 0)), int(ty + i), tc); put(a, int(tx - i * .35), int(ty + i), lit(tc, .15))
    elif tail == 'tuft':
        tl = ry * .5 + L * .55
        line(a, tx, ty, tx - 1.5, ty + tl, lit(rp[1], -.22)); rect(a, int(tx - 2), int(ty + tl), 2, 2, s.get('mane', DARK))
    elif tail == 'bushy':
        dome(a, tx - 2, ty + 3, 2.2, 4, [lit(c, -.05) for c in rp], seed, rough=.3)
    elif tail == 'fox':
        dome(a, tx - 3, ty + 2, 4.2, 2.4, rp, seed); put(a, int(tx - 7), int(ty + 2), hx('#f4ece0')); put(a, int(tx - 6), int(ty + 3), hx('#f4ece0')); put(a, int(tx - 7), int(ty + 3), hx('#f4ece0'))
    elif tail == 'cat':
        pts = [(0, 0), (-1, -1), (-2, -2), (-2, -3), (-2, -4), (-1, -5), (0, -6)]
        sw = [0, 1, 0, -1][frame]
        for i, (dx, dy) in enumerate(pts): put(a, int(tx + dx + (sw if i > 3 else 0)), int(ty + dy), rp[2] if i % 2 else rp[1])
    elif tail == 'up':
        line(a, tx, ty, tx - 2, ty - 3, rp[2], 1); put(a, int(tx - 1), int(ty - 1), rp[3])
    elif tail == 'curl':
        for (dx, dy) in [(0, 0), (-1, 0), (-2, -1), (-1, -2), (-2, -2)]: put(a, int(tx + dx), int(ty + dy), rp[2])
    elif tail == 'white':
        rect(a, int(tx - 1), int(ty), 2, 2, hx('#f6f2ea'))
    elif tail == 'puff':
        dome(a, tx - .5, ty + 1, 1.6, 1.5, R5('#cfc8bc', '#e2ddd4', '#f2eee8', '#fbf9f6', '#ffffff'), seed)
    else:
        put(a, int(tx), int(ty), rp[2]); put(a, int(tx - 1), int(ty + 1), rp[1])
    # body
    dome(a, cx, cy, rx, ry, rp, seed, rough=s.get('rough', 0))
    if s.get('hump'):
        dome(a, cx - rx * .1, cy - ry * .8, rx * .45, ry * .7, rp, seed + 1)
    m = mask_of(a, cx, cy, rx, ry)
    if s.get('hump'): m |= mask_of(a, cx - rx * .1, cy - ry * .8, rx * .45, ry * .7)
    if s.get('bellyc'): belly(a, m, s['bellyc'], .3, cx + rx * .2 if s.get('front_belly') else None)
    fur(a, m, s['fur'], rp, seed, s.get('furx'))
    if s.get('udder'):
        rect(a, int(cx - rx * .3), int(cy + ry - 1), 3, 2, hx('#e8a8a2')); put(a, int(cx - rx * .3), int(cy + ry + 1), hx('#d08a84'))
    # near legs
    leg(hipb, -swing, lc, False); leg(hipf, swing, lc, False)
    # neck + head
    nx, ny = s['neck']
    hrx, hry = s['head']
    hcx, hcy = cx + rx * .78 + nx * .45, cy - ry * .25 - ny
    if pose == 'eat': hcx += 1 + frame % 2; hcy = ground - hry - 1 - (frame % 2)
    if pose == 'attack': hcx += [0, 2, 1][frame % 3]; hcy += [-1, 1, 0][frame % 3]
    if pose == 'sleep': hcx -= 1; hcy = min(hcy + ny * .6 + 2, ground - hry - 1)
    if nx or ny:
        steps = 6
        for i in range(steps + 1):
            u = i / steps
            px_, py_ = cx + rx * .6 + (hcx - cx - rx * .6) * u, cy - ry * .2 + (hcy - cy + ry * .2) * u
            dome(a, px_, py_, max(1.4, ry * .5 - u * .6), max(1.4, ry * .5 - u * .6), rp, seed + i)
        if s.get('mane'):
            for i in range(steps + 2):
                u = i / steps
                put(a, int(cx + rx * .45 + (hcx - cx - rx * .45) * u - 1), int(cy - ry * .6 + (hcy - cy + ry * .6) * u - 1), s['mane'])
                put(a, int(cx + rx * .45 + (hcx - cx - rx * .45) * u), int(cy - ry * .6 + (hcy - cy + ry * .6) * u - 1), lit(s['mane'], .12))
    # snout
    sn = s['snout']; scol = s.get('scol')
    if sn > 0:
        sx0 = hcx + hrx * .3
        for i in range(int(round(sn)) + 1):
            hh = max(1, int(hry * 1.1 - i * .25))
            for j in range(hh):
                c = scol or hrp[2]
                if j == 0: c = lit(c, .15)
                if j == hh - 1: c = lit(c, -.15)
                put(a, int(sx0 + i + hrx * .5), int(hcy - hry * .1 + j), c)
    dome(a, hcx, hcy, hrx, hry, hrp, seed + 3)
    if s.get('marks'):
        kind, mc = s['marks']
        if kind == 'face':
            for i in range(int(sn) + 2): put(a, int(hcx + hrx * .5 + i), int(hcy - hry * .2), mc)
        if kind == 'blaze':
            for i in range(int(sn) + 1): put(a, int(hcx + hrx * .4 + i), int(hcy - hry * .4 + (i > sn / 2)), mc)
    tipx, tipy = int(sx0 + hrx * .5 + sn) if sn > 0 else int(hcx + hrx), int(hcy - hry * .1)
    if s.get('disc'):
        rect(a, tipx, tipy, 1, max(2, int(hry)), lit(scol or hrp[2], -.2)); put(a, tipx, tipy, lit(scol or hrp[2], .1))
        put(a, tipx, tipy + 1, DARK)
    elif sn > 0:
        put(a, tipx, tipy, DARK)
    if s.get('tusk'): put(a, tipx - 1, tipy + 2, hx('#f2ece0')); put(a, tipx - 1, tipy + 1, hx('#f2ece0'))
    if pose == 'attack' and frame % 3 >= 1:
        for i in range(max(2, int(sn) + 1)): put(a, int(hcx + hrx * .5 + i), int(hcy + hry * .55), DARK)
        put(a, int(hcx + hrx * .5 + 1), int(hcy + hry * .55 + 1), hx('#f2ece0'))
    # eye
    ex, ey = int(hcx + hrx * .3), int(hcy - hry * .3)
    if pose == 'sleep': put(a, ex, ey, lit(hrp[1], -.3)); put(a, ex - 1, ey, lit(hrp[1], -.3))
    else: put(a, ex, ey, s.get('eyec', DARK))
    if young: put(a, ex, ey + 1, DARK); put(a, ex, ey - 1, lit(hrp[3], .1))
    if hrx >= 2.6: put(a, ex - 1, ey - 1, lit(hrp[3], .1))
    # ears / horns
    et = int(hcy - hry) ; ebx = int(hcx - hrx * .3)
    ear = s['ears']; ec = hrp[1]
    if ear == 'point':
        for i in range(3 if not young else 2): put(a, ebx + (i == 2), et - i, ec if i else hrp[2])
        if s.get('etip'): put(a, ebx + (not young), et - (2 if not young else 1), s['etip'])
        put(a, ebx + 1, et, hrp[2])
    elif ear == 'droop':
        put(a, ebx - 1, et + 1, ec); put(a, ebx - 1, et + 2, ec); put(a, ebx - 2, et + 2, lit(ec, -.2)); put(a, ebx - 1, et + 3, lit(ec, -.2))
    elif ear == 'side':
        put(a, ebx - 1, et + 1, ec); put(a, ebx - 2, et + 1, ec); put(a, ebx - 2, et, hrp[2])
    elif ear == 'flop':
        put(a, ebx + 1, et, ec); put(a, ebx + 2, et, ec); put(a, ebx + 2, et + 1, lit(ec, -.2)); put(a, ebx + 3, et + 1, lit(ec, -.2))
    elif ear == 'long':
        for i in range(5 if not young else 3): put(a, ebx, et - i, ec); put(a, ebx + 1, et - i - 1, hrp[3] if i < 3 else ec)
    elif ear == 'rabbit':
        n = 6 if not young else 4
        for i in range(n): put(a, ebx - (i > n // 2), et - i, ec); put(a, ebx + 1 - (i > n // 2), et - i, hx('#d8a8a0') if 0 < i < n - 1 else ec)
    elif ear == 'round':
        dome(a, ebx, et, 1.4, 1.3, hrp, seed); put(a, ebx, et, lit(hrp[1], -.1))
    elif ear == 'tiny':
        put(a, ebx, et, ec)
    if s.get('horns') == 'curl':
        for (dx, dy) in [(0, -1), (-1, -2), (-2, -2), (-3, -1), (-3, 0)]: put(a, ebx + 1 + dx, et + dy, hx('#8a7a62') if dx > -2 else hx('#6a5c48'))
    elif s.get('horns') == 'small':
        put(a, ebx + 1, et - 1, hx('#e2d8c2')); put(a, ebx + 1, et - 2, hx('#bfb39a'))
    if s.get('antler'):
        ac = hx('#c9b48a'); ad = hx('#9a845e')
        for (dx, dy) in [(0, -1), (0, -2), (-1, -3), (-1, -4), (-2, -5), (1, -3), (2, -4), (-2, -3), (-3, -4), (0, -5), (1, -6)]:
            put(a, ebx + 1 + dx, et + dy, ac if dx >= 0 else ad)
    if s.get('beard'):
        put(a, int(hcx + hrx * .3), int(hcy + hry), hx('#ece4d2')); put(a, int(hcx + hrx * .3), int(hcy + hry + 1), hx('#d2c8b2'))
    for fn in s.get('extras', ()): fn(a, dict(cx=cx, cy=cy, rx=rx, ry=ry, hcx=hcx, hcy=hcy, hrx=hrx, hry=hry, ground=ground, frame=frame, pose=pose, young=young, rp=rp, hrp=hrp, sn=sn, et=et, ebx=ebx, seed=seed))
    return ground


# ------------------------------------------------------------------ non-quadrupeds
def chicken(a, x, y, frame=0, young=False, seed=1):
    if young:
        g = y + 9
        shadow_ell(a, x + 5, g + 1, 3, 1, .3)
        dome(a, x + 5, y + 6 - (frame % 2), 3, 2.6, R5('#c99a22', '#e0b636', '#f0cc4c', '#f8de6c', '#fff09a'), seed)
        dome(a, x + 7, y + 3 - (frame % 2), 1.9, 1.7, R5('#c99a22', '#e0b636', '#f0cc4c', '#f8de6c', '#fff09a'), seed + 1)
        put(a, x + 9, y + 3 - (frame % 2), hx('#e07a2a')); put(a, x + 8, y + 2 - (frame % 2), DARK)
        for i, lx in enumerate((4, 6)): vline(a, x + lx + ([0, 1, 0, -1][frame] * (1 if i else -1)), g - 1, 1, hx('#e07a2a'))
        return g
    g = y + 14
    rp = R5('#a87a4a', '#c8955a', '#dcae72', '#ecc890', '#f8e2b4')
    shadow_ell(a, x + 6, g + 1, 4.5, 1.2, .3)
    sw = [1, 0, -1, 0][frame]
    for (lx, s_) in ((5, sw), (7, -sw)):
        line(a, x + lx, g - 3, x + lx + s_, g, hx('#e0a030')); put(a, x + lx + s_ + 1, g, hx('#e0a030'))
    for (dx, dy) in [(0, 0), (-1, -1), (-1, -2), (0, -3), (1, -2), (-2, -1)]: put(a, x + 2 + dx, y + 6 + dy, hx('#3a2a1e') if dy < -1 else rp[1])
    dome(a, x + 6, y + 8, 4.4, 3.4, rp, seed)
    for i in range(3): put(a, x + 4 + i * 2, y + 9, lit(rp[1], -.1))  # wing feathers
    hline(a, x + 4, y + 8, 4, rp[3])
    dome(a, x + 9.5, y + 4, 2, 2, rp, seed + 1)
    put(a, x + 9, y + 1, hx('#d23a2a')); put(a, x + 10, y + 1, hx('#e84a36')); put(a, x + 10, y + 2, hx('#d23a2a')); put(a, x + 11, y + 2, hx('#d23a2a'))
    put(a, x + 12, y + 4, hx('#e8b030')); put(a, x + 11, y + 6, hx('#d23a2a')); put(a, x + 10, y + 3, DARK)
    return g


def duck(a, x, y, frame=0, young=False, seed=1):
    bob = frame % 2
    if young:
        g = y + 9
        shadow_ell(a, x + 5, g + 1, 3, 1, .3)
        dome(a, x + 5, y + 6 - bob, 3.2, 2.4, R5('#a08a2a', '#c0aa3c', '#d8c454', '#ead872', '#f8ec9a'), seed)
        dome(a, x + 8, y + 3 - bob, 1.8, 1.7, R5('#7a6a2a', '#9a8a3c', '#b8a654', '#d4c272', '#e8d890'), seed + 1)
        put(a, x + 10, y + 3 - bob, hx('#e0902a')); put(a, x + 8, y + 2 - bob, DARK)
        for i, lx in enumerate((4, 6)): put(a, x + lx + ([0, 1, 0, -1][frame] * (1 if i else -1)), g - 1, hx('#e0902a'))
        return g
    g = y + 13
    rp = R5('#b4ada0', '#cdc7ba', '#e0dbd0', '#efebe3', '#fbf9f5')
    shadow_ell(a, x + 6, g + 1, 5, 1.2, .3)
    sw = [1, 0, -1, 0][frame]
    for (lx, s_) in ((5, sw), (8, -sw)): line(a, x + lx, g - 2, x + lx + s_, g, hx('#e0902a')); put(a, x + lx + s_ + 1, g, hx('#e0902a'))
    dome(a, x + 6, y + 8, 5, 3, rp, seed); put(a, x + 1, y + 6, rp[2]); put(a, x, y + 5, rp[3])
    hline(a, x + 3, y + 8, 5, rp[1]); hline(a, x + 4, y + 7, 3, R5('#2f6aa8', '#2f6aa8', '#2f6aa8', '#2f6aa8', '#2f6aa8')[0])
    hm = R5('#123a22', '#1a5030', '#24683e', '#32844e', '#4aa064')
    dome(a, x + 10, y + 4, 2.1, 2.1, hm, seed + 1); hline(a, x + 9, y + 6, 3, hx('#f2f0ea'))
    put(a, x + 12, y + 4, hx('#e8b030')); put(a, x + 13, y + 4, hx('#e8b030')); put(a, x + 13, y + 5, hx('#c89020')); put(a, x + 10, y + 3, DARK)
    return g


def fish(a, x, y, frame=0, young=False, seed=1):
    k = .55 if young else 1
    rx, ry = 6 * k, 2.6 * k
    cx, cy = x + rx + 5, y + 5
    rp = R5('#3a5a70', '#527890', '#7098ae', '#98bccc', '#d0e6ee') if not young else R5('#6a7a5a', '#8a9a70', '#a8b88a', '#c4d4a4', '#e0ecc4')
    fl = [0, 1, 0, -1][frame]
    for i in range(int(4 * k) + 1):
        put(a, int(cx - rx - i), int(cy - i * .8 + fl * (i > 1)), rp[1]); put(a, int(cx - rx - i), int(cy + i * .8 + fl * (i > 1)), rp[0])
    dome(a, cx, cy, rx, ry, rp, seed)
    for i in range(int(rx * 1.2)): put(a, int(cx - rx * .6 + i), int(cy), rp[3] if i % 2 else rp[2])
    put(a, int(cx - 1), int(cy - ry), rp[1]); put(a, int(cx), int(cy - ry - 1 + (not young)), rp[1])
    put(a, int(cx + rx * .6), int(cy - ry * .3), DARK)
    return y + 9


def croc(a, x, y, frame=0, young=False, seed=1):
    k = .55 if young else 1
    rp = R5('#1e3218', '#2b4422', '#3c5a2e', '#507440', '#6a8e54') if not young else R5('#3a4a22', '#4e6430', '#667e40', '#829a54', '#a2b86e')
    L = int(30 * k); g = y + int(10 * k) + 3
    shadow_ell(a, x + L / 2, g + 1, L / 2, 1.6, .3)
    sw = [1, 0, -1, 0][frame]
    for (lx, s_) in ((int(L * .35), sw), (int(L * .62), -sw)):
        line(a, x + lx, g - 2, x + lx + s_ + 1, g, rp[1]); put(a, x + lx + s_ + 2, g, rp[0])
    # tail tapering (left), body, head/snout (right)
    for i in range(int(L * .45)):
        h = max(1, int(1 + i * .16 * (1 / k if young else 1) * k))
        for j in range(h): put(a, x + i, g - 2 - j + (i % 6 == 0 and frame % 2), rp[2] if j == h - 1 else rp[1])
    dome(a, x + L * .55, g - 3.2 * k - 1, L * .2, 2.6 * k + .6, rp, seed)
    for i in range(int(L * .3)):
        hh = 2 if i < L * .2 else 1
        for j in range(hh + 1): put(a, int(x + L * .7 + i), g - 2 - j, rp[3] if j == hh else rp[2])
    for xx in range(x + 2, int(x + L * .72), 2): put(a, xx, a.shape[0] and int(g - 2 - max(1, int(1 + (xx - x) * .16 * k)) - (xx > x + L * .4)), rp[0])
    ex = int(x + L * .76); put(a, ex, g - 5, hx('#d8c040')); put(a, ex + 1, g - 5, DARK)
    for i in (2, 5): put(a, int(x + L * .78 + i * k), g - 2, hx('#f0eada'))
    if young:
        for xx in range(x + 3, int(x + L * .7), 4): vline(a, xx, g - 4, 2, hx('#2a3818'))
    return g


EXTRA = {'chicken': chicken, 'duck': duck, 'fish': fish, 'crocodile': croc}
ALL = SPECIES + list(EXTRA.keys())


def draw(a, x, y, name, frame=0, young=False, seed=1):
    if name in EXTRA: return EXTRA[name](a, x, y, frame, young, seed)
    return quad(a, x, y, name, frame, young, seed)
