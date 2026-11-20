"""Strategic weapons (modern / future eras): ballistic missiles, launch vehicles, silos, missile defence and the nuclear strike sequence.
Everything on the fine 2x grid, light from top-left, no outlines, TEAM ramp = kingdom colour (R['K']).
Hazard marks are an original WorldSim design (yellow/black chevron diamond), not a real-world symbol."""
import math, random
import numpy as np
from lib import *
import air

INKC = hx('#14110e')
STEEL = [hx('#4a4e56'), hx('#6a7078'), hx('#8b939a'), hx('#b4bcc4'), hx('#dfe4e8')]
WHITE = [hx('#8a929a'), hx('#b4bcc4'), hx('#d4dade'), hx('#eef1f3'), hx('#ffffff')]
OLIVE = [hx('#2e3626'), hx('#3e4832'), hx('#566244'), hx('#6e7c58'), hx('#8a9870')]
CONC = [hx('#6a6a66'), hx('#86867f'), hx('#a2a29a'), hx('#bdbdb4'), hx('#d4d4cc')]
FIRE = [hx('#d5452d'), hx('#f49a3c'), hx('#ffd34a'), hx('#fff2b0'), hx('#ffffff')]
SMOKE = [hx('#5a5650'), hx('#7a766e'), hx('#9a968c'), hx('#bab6ac'), hx('#dad6cc')]


def team(): return R['K']


# ------------------------------------------------------------------ missiles in flight (top-down like aircraft, 16 directions)
air.PLANES.update({
    'srbm': dict(cam='white', parts=[(0, [(-6, -1), (-10, -3.6), (-11, -3.6), (-10, -1)], True), (1, [(10, 0), (8, -1.4), (-10, -1.4), (-10, 1.4), (8, 1.4)], False),
                                       (5, [(10, 0), (7.5, -1.4), (7.5, 1.4)], False), (3, [(4, -1.4), (2.5, -1.4), (2.5, 1.4), (4, 1.4)], False)]),
    'icbm': dict(cam='white', parts=[(0, [(-11, -2), (-16, -5), (-17, -5), (-16, -2)], True), (1, [(17, 0), (13, -2.3), (-16, -2.3), (-16, 2.3), (13, 2.3)], False),
                                       (5, [(17, 0), (12.5, -2.3), (12.5, 2.3)], False), (3, [(6, -2.3), (3.5, -2.3), (3.5, 2.3), (6, 2.3)], False),
                                       (5, [(-3, -2.3), (-4, -2.3), (-4, 2.3), (-3, 2.3)], False)]),
    'cruise': dict(cam='grey', parts=[(0, [(1, -1), (-1, -6), (-3, -6), (-2, -1)], True), (0, [(-8, -1), (-10, -3), (-11, -3), (-10, -1)], True),
                                        (1, [(10, 0), (8, -1.1), (-10, -1.1), (-10, 1.1), (8, 1.1)], False), (3, [(5, -1.1), (4, -1.1), (4, 1.1), (5, 1.1)], False)]),
    'abm': dict(cam='white', parts=[(0, [(-5, -.8), (-8, -2.6), (-9, -2.6), (-8, -.8)], True), (1, [(9, 0), (6, -1), (-9, -1), (-9, 1), (6, 1)], False),
                                      (5, [(9, 0), (6, -1), (6, 1)], False), (4, [(1, -1), (0, -1), (0, 1), (1, 1)], False)]),
    'hgv': dict(cam='dark', parts=[(1, [(11, 0), (-8, -5), (-10, -5), (-9, 0), (-10, 5), (-8, 5)], False), (2, [(8, 0), (3, -1), (3, 1)], False),
                                     (3, [(-6, -4), (-8, -4.6), (-8, -3.6)], True)]),
})
MISSILES = {'srbm': ('TACTICAL BALLISTIC MISSILE', 1.6), 'icbm': ('NUCLEAR ICBM', 1.25), 'cruise': ('CRUISE MISSILE', 1.6), 'abm': ('INTERCEPTOR (ABM)', 1.6),
            'hgv': ('HYPERSONIC GLIDER', 1.5)}


def exhaust(a, cx, cy, ang, length, frame, big=False):
    """flame + smoke trail behind a missile flying at ang (deg) whose tail is at (cx,cy)."""
    t = math.radians(ang)
    dx, dy = -math.cos(t), -math.sin(t)
    r = random.Random(frame * 7 + int(ang))
    for i in range(length):
        u = i / max(1, length - 1)
        w = (1.6 if big else 1.0) * (1 - u * .4)
        x, y = cx + dx * i, cy + dy * i
        col = FIRE[4] if u < .15 else FIRE[3] if u < .3 else FIRE[2] if u < .5 else FIRE[1] if u < .75 else FIRE[0]
        for k in (-1, 0, 1):
            if abs(k) <= w and r.random() < .95 - u * .5:
                put(a, int(round(x - dy * k)), int(round(y + dx * k)), col)
    blend_mask(a, ellipse_mask(a.shape[:2], cx + dx * 3, cy + dy * 3, 4 if big else 3, 4 if big else 3), FIRE[2], .3)
    for i in range(4 if big else 3):
        d = length + 2 + i * (4 if big else 3) + frame
        blend_mask(a, ellipse_mask(a.shape[:2], cx + dx * d, cy + dy * d, 1.5 + i * .8, 1.5 + i * .8), SMOKE[3], .6 - i * .1)


def missile_flight(a, kind, ang, frame=0, cx=40, cy=40):
    name, sc = MISSILES[kind]
    s = air.plane(kind, ang, scale=sc, size=72)
    h, w = s[1].shape
    t = math.radians(ang)
    L = {'srbm': 10, 'icbm': 16, 'cruise': 10, 'abm': 9, 'hgv': 10}[kind] * sc
    tail = (cx - math.cos(t) * L, cy - math.sin(t) * L)
    if kind == 'hgv':
        for i in range(10):
            blend_mask(a, ellipse_mask(a.shape[:2], tail[0] - math.cos(t) * i * 2, tail[1] - math.sin(t) * i * 2, 2.4 - i * .2, 2.4 - i * .2), C['cyan'], .45 - i * .04)
    else:
        exhaust(a, tail[0], tail[1], ang, {'icbm': 14, 'srbm': 10, 'cruise': 5, 'abm': 9}[kind] + frame * 2, frame, kind == 'icbm')
    air.paste(a, s, int(cx - w / 2), int(cy - h / 2))


def reentry(a, frame=0, cx=20, cy=26):
    """warhead coming down at ~70 deg with plasma glow."""
    for i in range(16):
        blend_mask(a, ellipse_mask(a.shape[:2], cx - i * .5, cy - i * 1.4, 3.2 - i * .17, 3.2 - i * .17), FIRE[1] if i < 6 else FIRE[0], .55 - i * .03)
    dome(a, cx, cy, 2.6, 3.2, [hx('#3a3430'), hx('#5a524a'), hx('#7a7268'), hx('#a29a8e'), hx('#c8c0b4')], 3)
    blend_mask(a, ellipse_mask(a.shape[:2], cx + .5, cy + 2.5, 4 + frame, 2.4 + frame * .5), FIRE[3], .7)
    put(a, int(cx), int(cy + 3), FIRE[4]); put(a, int(cx + 1), int(cy + 3), FIRE[4])


# ------------------------------------------------------------------ ground: launch vehicle (TEL), silo, missile defence
def missile_body(a, px, py, ang, L=34, W=5, nuke=True):
    """side-view missile lying on an erector; (px,py) = tail, ang = elevation in degrees."""
    t = math.radians(ang)
    ux, uy = math.cos(t), -math.sin(t)
    nx, ny = -uy, ux
    tm = team()
    for i in range(L):
        for j in range(W):
            u = i / (L - 1)
            if u > .86 and abs(j - (W - 1) / 2) > (1 - u) / .14 * (W / 2): continue
            col = WHITE[3] if j == 0 else WHITE[2] if j < W - 1 else WHITE[1]
            if u > .86: col = STEEL[1] if j else STEEL[2]
            if .62 < u < .7: col = tm[2] if j else tm[3]
            if nuke and .74 < u < .78: col = hx('#e8c84a') if (i + j) % 2 else INKC     # original hazard band
            if i < 2: col = STEEL[0]
            put(a, int(round(px + ux * i + nx * (j - W // 2))), int(round(py + uy * i + ny * (j - W // 2))), col)
    for s in (-1, 1):  # fins
        for k in range(4):
            put(a, int(round(px + ux * (k + 1) + nx * s * (W // 2 + 1 + k // 2))), int(round(py + uy * (k + 1) + ny * s * (W // 2 + 1 + k // 2))), STEEL[1])


def tel(a, x, b, frame=0, nuke=True):
    """8-wheel transporter-erector-launcher. frames: 0 travel, 1 erect 35, 2 erect 65, 3 vertical, 4 ignition, 5 lift-off."""
    tm = team()
    shadow_ell(a, x + 24, b + 1, 26, 2, .35)
    rect(a, x, b - 9, 48, 6, OLIVE[2]); hline(a, x, b - 9, 48, OLIVE[3]); hline(a, x, b - 4, 48, OLIVE[0])
    rect(a, x + 40, b - 15, 10, 8, OLIVE[2]); hline(a, x + 40, b - 15, 10, OLIVE[4]); vline(a, x + 49, b - 15, 8, OLIVE[0])
    rect(a, x + 44, b - 13, 5, 3, hx('#8ad0e0')); put(a, x + 44, b - 13, hx('#d8f0ff'))
    rect(a, x + 41, b - 9, 3, 3, tm[2]); put(a, x + 41, b - 9, tm[3])
    for wx in range(x + 4, x + 46, 6):
        dome(a, wx, b - 1, 2.4, 2.4, [INKC, INKC, hx('#2a2c30'), hx('#3a3e44'), hx('#4a4e56')], wx); put(a, wx, b - 1, hx('#6a6e76'))
    ang = [0, 35, 65, 90, 90, 90][frame]
    px, py = x + 4, b - 11
    # erector arm
    t = math.radians(ang)
    for i in range(30): put(a, int(round(px + math.cos(t) * i + math.sin(t) * 3)), int(round(py - math.sin(t) * i + math.cos(t) * 3)), INKC if i % 6 else OLIVE[1])
    if frame == 5:
        missile_body(a, px, py - 16, 90, nuke=nuke)
        exhaust(a, px, py - 15, -90, 14, 1, True)
    else:
        missile_body(a, px, py, ang, nuke=nuke)
    if frame >= 4:
        blend_mask(a, ellipse_mask(a.shape[:2], px, b - 4, 16 + (frame - 4) * 6, 5 + (frame - 4) * 2), SMOKE[3], .75)
        blend_mask(a, ellipse_mask(a.shape[:2], px - 8, b - 8, 8, 5), SMOKE[4], .6)
        if frame == 4: exhaust(a, px, py + 1, -90, 6, 0, True)


def silo(a, x, b, frame=0, nuke=True):
    """missile silo, top-front view. frames: 0 closed, 1 opening, 2 open (missile visible), 3 launch."""
    tm = team()
    shadow_rect(a, x + 2, b - 18, 46, 20, .3)
    rect(a, x, b - 20, 46, 20, CONC[2]); hline(a, x, b - 20, 46, CONC[3]); hline(a, x, b - 1, 46, CONC[0]); vline(a, x, b - 20, 20, CONC[3]); vline(a, x + 45, b - 20, 20, CONC[1])
    for i in range(0, 46, 6): vline(a, x + i, b - 19, 18, CONC[1])
    for i in range(0, 46, 4): put(a, x + i, b - 21, hx('#e8c84a') if (i // 4) % 2 else INKC)        # hazard edge (original)
    cx, cy = x + 23, b - 10
    hole = ellipse_mask(a.shape[:2], cx, cy, 10, 6)
    a[hole] = hx('#1e1c1a')
    a[ellipse_mask(a.shape[:2], cx, cy, 11, 7) & ~hole] = CONC[0]
    if frame >= 2:
        dome(a, cx, cy - 1, 3.2, 3.4, [STEEL[0], STEEL[1], WHITE[2], WHITE[3], WHITE[4]], 3)
        hline(a, cx - 3, cy + 2, 7, tm[2]); put(a, cx - 1, cy + 3, hx('#e8c84a')); put(a, cx + 1, cy + 3, INKC)
    slide = [0, 6, 13, 13][frame]
    for s in (-1, 1):
        hx0 = cx + (0 if s > 0 else -12) + s * slide
        rect(a, hx0, cy - 7, 12, 14, CONC[3]); hline(a, hx0, cy - 7, 12, CONC[4]); hline(a, hx0, cy + 6, 12, CONC[1])
        for k in range(2, 12, 3): put(a, hx0 + k, cy - 1, CONC[1])
    # bunker + mast
    rect(a, x + 2, b - 30, 12, 10, CONC[2]); hline(a, x + 2, b - 30, 12, CONC[4]); rect(a, x + 5, b - 25, 4, 5, INKC); put(a, x + 10, b - 27, hx('#e05a5a'))
    vline(a, x + 40, b - 36, 16, STEEL[1]); hline(a, x + 37, b - 36, 7, STEEL[2]); put(a, x + 40, b - 37, hx('#e05a5a'))
    put(a, x + 12, b - 29, tm[2]); put(a, x + 13, b - 29, tm[3])
    if frame == 3:
        blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 24, 10), SMOKE[3], .8)
        blend_mask(a, ellipse_mask(a.shape[:2], cx - 6, cy - 6, 12, 7), SMOKE[4], .7)
        missile_body(a, cx - 2, cy - 14, 90, L=30, nuke=nuke)
        exhaust(a, cx - 2, cy - 12, -90, 10, 1, True)


def abm_battery(a, x, b, frame=0):
    """vertical-launch interceptor battery. frames: 0 closed, 1 firing."""
    shadow_rect(a, x + 2, b - 12, 30, 13, .3)
    rect(a, x, b - 12, 30, 12, STEEL[1]); hline(a, x, b - 12, 30, STEEL[3]); hline(a, x, b - 1, 30, STEEL[0])
    for i in range(4):
        for j in range(2):
            cx_, cy_ = x + 3 + i * 7, b - 10 + j * 5
            rect(a, cx_, cy_, 5, 4, STEEL[0] if (frame and i == 2 and j == 0) else STEEL[2]); hline(a, cx_, cy_, 5, STEEL[3])
    rect(a, x + 31, b - 9, 8, 9, OLIVE[2]); hline(a, x + 31, b - 9, 8, OLIVE[4]); rect(a, x + 33, b - 7, 3, 2, hx('#8ad0e0'))
    put(a, x + 1, b - 11, team()[2]); put(a, x + 2, b - 11, team()[3])
    if frame:
        cx_ = x + 19
        blend_mask(a, ellipse_mask(a.shape[:2], cx_, b - 12, 12, 4), SMOKE[4], .75)
        for i in range(16): put(a, cx_, b - 14 - i, WHITE[3] if i > 12 else SMOKE[3 + (i % 2)])
        put(a, cx_, b - 31, hx('#e05a5a')); exhaust(a, cx_, b - 16, -90, 6, 0)


def hazard_sign(a, x, y, s=1):
    """original WorldSim hazard marker: yellow diamond, black border, three bars (no real-world symbol)."""
    for j in range(-6, 7):
        w = 6 - abs(j)
        for i in range(-w, w + 1):
            c = INKC if abs(i) == w or abs(j) == 6 else hx('#ffd34a')
            rect(a, x + (i + 6) * s, y + (j + 6) * s, s, s, c)
    for k in (-2, 0, 2): rect(a, x + (6 + k) * s, y + 4 * s, s, 4 * s if k == 0 else 3 * s, INKC)


# ------------------------------------------------------------------ nuclear detonation sequence (big FX, pivot = ground zero)
def _puffs(a, cx, cy, rx, ry, n, cols, seed, alpha=1.0):
    r = random.Random(seed)
    for _ in range(n):
        ang = r.uniform(0, 2 * math.pi); d = r.uniform(0, 1) ** .6
        px, py = cx + math.cos(ang) * rx * d, cy + math.sin(ang) * ry * d
        rr = r.uniform(2.2, 4.4) * (rx / 22) ** .5
        shade = 3 if py < cy - ry * .2 else 2 if py < cy + ry * .3 else 1
        if alpha >= 1: dome(a, px, py, rr, rr * .9, cols, int(px * 7 + py), rough=.3)
        else: blend_mask(a, ellipse_mask(a.shape[:2], px, py, rr, rr * .9), cols[shade], alpha)


def nuke(a, frame, gx=80, gy=150):
    """frames: 0-1 flash, 2-4 fireball, 5-10 mushroom rising, 11-12 dissipating."""
    if frame <= 1:
        k = [1.0, .6][frame]
        for r_, al in ((70, .35), (48, .55), (30, .8), (16, 1)):
            blend_mask(a, ellipse_mask(a.shape[:2], gx, gy - 10, r_ * (1 + frame * .2), r_ * .8 * (1 + frame * .2)), hx('#fffbe6'), al * k)
        return
    if frame <= 4:
        rr = [10, 16, 22][frame - 2]
        blend_mask(a, ellipse_mask(a.shape[:2], gx, gy - rr * .6, rr * 2.2, rr * 1.4), FIRE[2], .35)
        dome(a, gx, gy - rr * .8, rr, rr * .9, [FIRE[0], FIRE[1], FIRE[2], FIRE[3], FIRE[4]], 5, rough=.35)
        blend_mask(a, ellipse_mask(a.shape[:2], gx, gy, rr * 2.4, rr * .5), SMOKE[2], .6)
        return
    k = frame - 5           # 0..7
    rise = min(1.0, k / 5)
    top = gy - 40 - rise * 68
    capr = 16 + rise * 20
    fade = 1.0 if k < 6 else [0.62, 0.34][k - 6]
    r = random.Random(40 + k)
    layer = a.copy()
    # base surge: dense rolling ring of dust
    skirt_r = 22 + k * 6
    blend_mask(layer, ellipse_mask(a.shape[:2], gx, gy - 2, skirt_r, 5 + k * .8), SMOKE[1], .8)
    for i in range(18 + k * 3):
        t = r.uniform(0, 2 * math.pi); d = r.uniform(.55, 1.0)
        px, py = gx + math.cos(t) * skirt_r * d, gy - 3 + math.sin(t) * (4 + k * .7) * d
        rr = r.uniform(2.6, 4.6)
        dome(layer, px, py - rr * .4, rr, rr * .8, [hx('#5a4a3a'), hx('#7a6650'), hx('#9a8468'), hx('#b8a284'), hx('#d0bc9c')], int(px * 3 + py), rough=.25)
    # stem: tapered rough column, brown at the root, grey above, lit from the left
    y0, y1 = int(top + capr * .35), int(gy - 4)
    for y in range(y0, y1):
        u = (y - y0) / max(1, y1 - y0)             # 0 top .. 1 bottom
        w = 4.5 + rise * 2.5 + u * u * 6 + math.sin(y * .7 + k) * .8
        warm = min(1, max(0, (u - .45) / .55))
        base = [tuple(int(c0 * (1 - warm) + c1 * warm) for c0, c1 in zip(cg, cb)) for cg, cb in
                zip(SMOKE, [hx('#4a3226'), hx('#6a4430'), hx('#8a5e3e'), hx('#a87a50'), hx('#c49a68')])]
        for xx in range(int(gx - w), int(gx + w) + 1):
            v = (xx - (gx - w)) / max(1, 2 * w)
            c = base[4] if v < .18 else base[3] if v < .45 else base[2] if v < .78 else base[1]
            put(layer, xx, y, c)
    for i in range(5):      # billows climbing the stem
        yy = y0 + (i * 13 + k * 3) % max(1, y1 - y0)
        dome(layer, gx + r.uniform(-4, 4), yy, 3.4, 2.8, SMOKE, i + k, rough=.2)
    # condensation ring
    if 1 <= k <= 4:
        ry_ = top + capr * .9 + 6
        for t in np.linspace(0, 2 * math.pi, 90):
            xx, yy = gx + (capr + 6 + k * 3) * math.cos(t), ry_ + (2.5 + k * .6) * math.sin(t)
            put(layer, int(xx), int(yy), WHITE[3] if math.sin(t) > 0 else WHITE[2])
    # cap: one big banded dome, then a lumpy rim and surface billows, fiery underside early on
    capcols = [SMOKE[0], SMOKE[1], SMOKE[2], SMOKE[3], WHITE[3]]
    dome(layer, gx, top, capr, capr * .58, capcols, 23 + k, rough=.25)
    for i in range(30):
        t = i / 30 * 2 * math.pi
        px, py = gx + math.cos(t) * capr * .92, top + math.sin(t) * capr * .52
        rr = r.uniform(3.4, 5.6) * (capr / 30) ** .5 + 1
        dome(layer, px, py, rr, rr * .85, capcols, i * 13 + k, rough=.25)
    for i in range(14):
        px, py = gx + r.uniform(-.6, .6) * capr, top - capr * .25 + r.uniform(-.2, .25) * capr
        rr = r.uniform(3, 5)
        dome(layer, px, py, rr, rr * .8, capcols, i * 7 + k * 3, rough=.25)
    glow = max(0.0, 1 - k / 6)
    if glow > 0:
        band = ellipse_mask(a.shape[:2], gx, top + capr * .32, capr * .95, capr * .2) & ~ellipse_mask(a.shape[:2], gx, top + capr * .18, capr * .95, capr * .2)
        blend_mask(layer, band, FIRE[1], .85 * glow)
        blend_mask(layer, ellipse_mask(a.shape[:2], gx, top + capr * .3, capr * .55, capr * .14), FIRE[2], .8 * glow)
        blend_mask(layer, ellipse_mask(a.shape[:2], gx, y0 + 4, 6, 4), FIRE[1], .5 * glow)
    if fade >= 1:
        a[:] = layer
    else:
        diff = np.any(layer != a, axis=2)
        a[diff] = (a[diff] * (1 - fade) + layer[diff] * fade).astype(np.uint8)


def shockwave(a, frame, gx=80, gy=40):
    r = 14 + frame * 18
    m = ellipse_mask(a.shape[:2], gx, gy, r, r * .35) & ~ellipse_mask(a.shape[:2], gx, gy, r - 4, r * .35 - 2)
    blend_mask(a, m, hx('#c8b88a'), .75 - frame * .15)
    m2 = ellipse_mask(a.shape[:2], gx, gy, r - 4, r * .35 - 2) & ~ellipse_mask(a.shape[:2], gx, gy, r - 7, r * .35 - 3)
    blend_mask(a, m2, hx('#ffffff'), .35 - frame * .07)


def crater(a, cx=40, cy=20, s=1.0):
    blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 36 * s, 16 * s), hx('#1e1a16'), .55)
    blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 26 * s, 11 * s), hx('#2a2420'), .85)
    m = ellipse_mask(a.shape[:2], cx, cy, 16 * s, 7 * s); a[m] = hx('#3a3430')
    a[ellipse_mask(a.shape[:2], cx, cy + 1, 12 * s, 5 * s)] = hx('#24201c')
    rim = ellipse_mask(a.shape[:2], cx, cy - 1, 17 * s, 7.6 * s) & ~ellipse_mask(a.shape[:2], cx, cy, 16 * s, 7 * s)
    a[rim] = hx('#5a524a')
    r = random.Random(3)
    for _ in range(int(14 * s)):
        x, y = cx + r.uniform(-20, 20) * s, cy + r.uniform(-8, 8) * s
        put(a, int(x), int(y), FIRE[r.randint(0, 1)])


def fallout(a, frame, cx=40, cy=24):
    r = random.Random(frame)
    m = ellipse_mask(a.shape[:2], cx + frame * 3, cy, 34, 14)
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if (x + y + frame) % 3 == 0 or r.random() < .1:
            a[y, x] = (np.array(a[y, x]) * .4 + np.array(hx('#b8e04a')) * .6).astype(np.uint8)


def fallout_overlay(a, frame):
    """standalone fallout cloud (transparent sprite): pale-green dither drifting."""
    m = ellipse_mask(a.shape[:2], 40 + frame * 2, 17, 38, 14)
    ys, xs = np.nonzero(m)
    r = random.Random(frame)
    for y, x in zip(ys, xs):
        if (x + y + frame) % 3 == 0 or r.random() < .08: a[y, x] = hx('#b8e04a') if (x * 7 + y) % 5 else hx('#e0ff8a')


def radiation_glow(a, cx=24, cy=12):
    blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 22, 10), hx('#9ae04a'), .28)
    blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 12, 5), hx('#d8ff8a'), .22)


# ------------------------------------------------------------------ UI power icons (11x11) added to the shared kit
def add_icons():
    import ui2kit as K
    K.PI.update({
        'nuke': (["...ggggg...", "..gGGGGGg..", ".gGGGGGGGg.", ".ggooooogg.", "...ggggg...", "....ggg....", "....ggg....", "...ggggg...", ".ggggggggg.", "ggggggggggg", "..........."],
                 {'g': '#9a968c', 'G': '#dad6cc', 'o': '#f49a3c'}),
        'missile': (["..........r", ".........ww", "........ww.", ".......ww..", "......ww...", ".....kw....", "..y.kk.....", ".yokk......", "yoo........", ".y.........", "..........."],
                    {'w': '#eef1f3', 'k': '#c4563d', 'r': '#6a7078', 'y': '#ffd34a', 'o': '#f49a3c'}),
        'launch_alert': (["....rrr....", "...rrrrr...", "...rrwrr...", "..rrrwrrr..", "..rrrwrrr..", ".rrrrwrrrr.", ".rrrrrrrrr.", "rrrrrwrrrrr", "rrrrrrrrrrr", "...........", "..........."],
                         {'r': '#e05a5a', 'w': '#ffffff'}),
        'hazard': ([".....k.....", "....kyk....", "...kyyyk...", "..kykykyk..", ".kyykykyyk.", "kyyykykyyyk", ".kyyyyyyyk.", "..kyyyyyk..", "...kyyyk...", "....kyk....", ".....k....."],
                   {'k': '#14110e', 'y': '#ffd34a'}),
        'shield_dome': (["...ccccc...", "..c.....c..", ".c.......c.", "c.........c", "c....k....c", "c...kkk...c", "gggggggggggg"[:11], "...........", "...........", "...........", "..........."],
                        {'c': '#5fe0e8', 'k': '#6a7078', 'g': '#4a4e56'}),
    })
