"""Modern/future air war: top-down aircraft (8 directions), air defence ground units (frames), FX, airbase. 2x fine grid.
Altitude is shown by drawing the aircraft above its ground shadow (shadow offset = altitude)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *

INKC = hx('#14110e')
TEAM = R['K']
CAMO = {'grey': [hx('#4a525c'), hx('#66707a'), hx('#8a949e'), hx('#b4bcc4')], 'dark': [hx('#262b33'), hx('#343a44'), hx('#474f5b'), hx('#6a7488')],
        'olive': [hx('#3e4832'), hx('#566244'), hx('#6e7c58'), hx('#8a9870')], 'white': [hx('#9aa4ae'), hx('#c8ced4'), hx('#e4e8ec'), hx('#ffffff')],
        'sand': [hx('#8a7454'), hx('#a8906a'), hx('#c4ac84'), hx('#ddc8a0')]}

# parts: (layer, polygon, mirror?) ; layer 0 = wings/tail (dark), 1 = fuselage, 2 = canopy, 3 = team mark, 4 = engine glow
PLANES = {
    'fighter': dict(cam='grey', parts=[(0, [(3, -1), (-3, -8), (-6, -8), (-4, -1)], True), (0, [(-7, -1), (-10, -4), (-12, -4), (-11, -1)], True),
                                         (1, [(11, 0), (7, -1.6), (-10, -1.6), (-12, 0), (-10, 1.6), (7, 1.6)], False), (2, [(7, 0), (5, -1), (2, -1), (2, 1), (5, 1)], False),
                                         (3, [(-4, -6), (-5, -7), (-5.5, -6)], True), (4, [(-12, -1), (-14, 0), (-12, 1)], False)]),
    'stealth': dict(cam='dark', parts=[(0, [(2, -3), (-3, -9), (-8, -8), (-7, -3)], True), (0, [(-7, -2), (-11, -6), (-12, -5), (-10, -2)], True),
                                        (1, [(11, 0), (3, -3), (-11, -2.5), (-11, 2.5), (3, 3)], False), (2, [(7, 0), (5, -1.2), (1, -1), (1, 1), (5, 1.2)], False),
                                        (3, [(-5, -7), (-6, -7.5), (-6, -6)], True)]),
    'interceptor': dict(cam='white', parts=[(0, [(4, -1), (-7, -10), (-10, -10), (-7, -1)], True), (1, [(12, 0), (6, -1.6), (-9, -1.6), (-11, 0), (-9, 1.6), (6, 1.6)], False),
                                             (2, [(8, 0), (6, -1), (3, -1), (3, 1), (6, 1)], False), (3, [(-8, -9), (-9, -9.5), (-9.5, -8)], True), (4, [(-11, -1), (-14, 0), (-11, 1)], False)]),
    'bomber': dict(cam='olive', parts=[(0, [(5, -2), (1, -19), (-4, -19), (-3, -2)], True), (0, [(-13, -1), (-15, -7), (-18, -7), (-17, -1)], True),
                                        (1, [(19, 0), (16, -2.4), (-16, -2.4), (-19, 0), (-16, 2.4), (16, 2.4)], False),
                                        (5, [(3, -7), (5, -7), (5, -5.5), (3, -5.5)], True), (5, [(1.5, -13), (3.5, -13), (3.5, -11.5), (1.5, -11.5)], True),
                                        (2, [(17, 0), (15, -1), (13, -1), (13, 1), (15, 1)], False), (3, [(-14, -5), (-16, -6), (-16, -4)], True)]),
    'wing': dict(cam='dark', parts=[(1, [(11, 0), (-6, -20), (-9, -18), (-5, -8), (-8, -5), (-6, 0), (-8, 5), (-5, 8), (-9, 18), (-6, 20)], False),
                                     (2, [(8, 0), (5, -1.5), (3, -1.5), (3, 1.5), (5, 1.5)], False), (3, [(-5, -16), (-6, -17), (-7, -15)], True)]),
    'transport': dict(cam='grey', parts=[(0, [(2, -3), (0, -18), (-4, -18), (-3, -3)], True), (0, [(-13, -1), (-14, -7), (-16, -7), (-16, -1)], True),
                                          (1, [(15, 0), (13, -3.2), (-14, -3), (-17, 0), (-14, 3), (13, 3.2)], False),
                                          (5, [(1, -8), (3, -8), (3, -6.5), (1, -6.5)], True), (2, [(14, 0), (12, -1.5), (11, -1.5), (11, 1.5), (12, 1.5)], False)]),
    'recon': dict(cam='white', parts=[(0, [(1, -1), (0, -13), (-2, -13), (-1, -1)], True), (0, [(-7, 0), (-9, -4), (-10, -4), (-9, 0)], True),
                                       (1, [(7, 0), (5, -1.2), (-8, -0.8), (-9, 0), (-8, 0.8), (5, 1.2)], False), (3, [(-1, -11), (-2, -12), (-2, -10)], True)]),
    'loiter': dict(cam='sand', parts=[(1, [(7, 0), (-5, -7), (-6, -6), (-4, 0), (-6, 6), (-5, 7)], False), (3, [(-3, -4), (-4, -5), (-4, -3)], True),
                                       (4, [(-4, -1), (-7, 0), (-4, 1)], False)]),
}


def plane(name, ang, team=TEAM, scale=1.0, size=48):
    """returns (rgb, mask) top-down sprite rotated to ang degrees (0 = right, 90 = down)."""
    spec = PLANES[name]
    cam = CAMO[spec['cam']]
    lay = Image.new('L', (size, size), 0); d = ImageDraw.Draw(lay)
    cx = cy = size / 2
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    def tr(p): return (cx + (p[0] * ca - p[1] * sa) * scale, cy + (p[0] * sa + p[1] * ca) * scale)
    order = sorted(spec['parts'], key=lambda t: {0: 0, 5: 1, 1: 2, 4: 3, 2: 4, 3: 5}[t[0]])
    for (L, poly, mir) in order:
        polys = [poly] + ([[(x, -y) for (x, y) in poly]] if mir else [])
        for pp in polys: d.polygon([tr(p) for p in pp], fill=L + 1)
    m = np.asarray(lay)
    rgb = np.zeros((size, size, 3), np.uint8)
    col = {1: cam[1], 6: lit(cam[1], -.15), 2: cam[2], 3: hx('#2a4a6a'), 4: team[2], 5: hx('#ffb84a')}
    for k, c in col.items(): rgb[m == k] = c
    mask = m > 0
    # bevel: light from top-left
    up = np.zeros_like(mask); up[1:] = mask[:-1]; lf = np.zeros_like(mask); lf[:, 1:] = mask[:, :-1]
    dn = np.zeros_like(mask); dn[:-1] = mask[1:]; rt = np.zeros_like(mask); rt[:, :-1] = mask[:, 1:]
    hi = mask & (~up | ~lf) & (m != 3); lo = mask & (~dn | ~rt) & (m != 3)
    rgb[hi] = np.clip(rgb[hi].astype(int) + 38, 0, 255); rgb[lo] = np.clip(rgb[lo].astype(int) - 40, 0, 255)
    rgb[m == 3] = hx('#7ab8e0');
    cnp = (m == 3); cnp_hi = cnp & ~up
    rgb[cnp_hi] = hx('#d8f0ff')
    ys, xs = np.nonzero(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return rgb[y0:y1, x0:x1].copy(), mask[y0:y1, x0:x1].copy()


def paste(f, s, x, y, alpha=1.0):
    img, m = s
    h, w = m.shape
    for j in range(h):
        for i in range(w):
            if m[j, i] and 0 <= y + j < f.shape[0] and 0 <= x + i < f.shape[1]:
                f[y + j, x + i] = img[j, i] if alpha >= 1 else (np.array(f[y + j, x + i]) * (1 - alpha) + img[j, i] * alpha).astype(np.uint8)


def shadow_of(f, s, x, y, a=.35):
    _, m = s
    h, w = m.shape
    mm = np.zeros(f.shape[:2], bool)
    for j in range(h):
        for i in range(w):
            if m[j, i] and 0 <= y + j < f.shape[0] and 0 <= x + i < f.shape[1]: mm[y + j, x + i] = True
    blend_mask(f, mm, SHADOW, a)


def fly(f, name, gx, gy, alt, ang, team=TEAM, scale=1.0, outline=False):
    """gx,gy = ground point; aircraft drawn alt px above, shadow on ground."""
    s = plane(name, ang, team, scale)
    h, w = s[1].shape
    shadow_of(f, s, gx - w // 2 + alt // 3, gy - h // 2, .28 if alt > 10 else .38)
    if outline:
        m = s[1]; d = m.copy()
        d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
        paste(f, (np.zeros(s[0].shape, np.uint8) + np.array(INKC, np.uint8), d), gx - w // 2, gy - h // 2 - alt, .55)
    paste(f, s, gx - w // 2, gy - h // 2 - alt)
    return gx, gy - alt


def heli_top(f, gx, gy, alt, ang, frame=0, team=TEAM):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    cx, cy = gx, gy - alt
    blend_mask(f, ellipse_mask(f.shape[:2], gx + alt // 3, gy, 6, 3), SHADOW, .3)
    for t in range(18):
        for o in (-1, 0, 1) if t < 6 else (0,):
            put(f, int(cx - (t - 2) * ca - o * sa), int(cy - (t - 2) * sa + o * ca), CAMO['olive'][1 if t < 12 else 0])
    for o in range(-3, 4): put(f, int(cx - 15 * ca - o * sa), int(cy - 15 * sa + o * ca), CAMO['olive'][0])
    dome(f, cx + 2 * ca, cy + 2 * sa, 5.5, 4, [CAMO['olive'][0]] + CAMO['olive'], 3)
    for o in (-1, 0, 1): put(f, int(cx + 5 * ca - o * sa), int(cy + 5 * sa + o * ca), hx('#8ad0e0'))
    for o in (-4, 4): put(f, int(cx - o * sa), int(cy + o * ca), INKC); put(f, int(cx + ca - o * sa), int(cy + sa + o * ca), INKC)
    put(f, int(cx - 13 * ca), int(cy - 13 * sa), team[2])
    r = 13
    for k in range(2):
        b = a + frame * math.pi / 4 + k * math.pi / 2
        for t in range(-r, r + 1):
            put(f, int(cx + t * math.cos(b)), int(cy + t * math.sin(b)), hx('#c8ced4') if abs(t) > 2 else INKC)
    blend_mask(f, ellipse_mask(f.shape[:2], cx, cy, r, r), hx('#c8ced4'), .12)


# ------------------------------------------------------------------ ground air defence (3/4 view like other ground units)
def truck(f, x, b, cam='olive'):
    c = CAMO[cam]
    shadow_ell(f, x + 13, b + 1, 14, 1.6, .35)
    rect(f, x, b - 7, 26, 5, c[1]); hline(f, x, b - 7, 26, c[2]); hline(f, x, b - 3, 26, c[0])
    rect(f, x + 20, b - 11, 7, 5, c[1]); hline(f, x + 20, b - 11, 7, c[3]); rect(f, x + 23, b - 10, 3, 2, hx('#8ad0e0'))
    for wx in (x + 4, x + 10, x + 21): dome(f, wx, b - 1, 2.2, 2.2, [INKC, INKC, hx('#2a2c30'), hx('#3a3e44'), hx('#4a4e56')], wx); put(f, wx, b - 1, hx('#6a6e76'))


def sam(f, x, b, frame=0, team=TEAM):
    truck(f, x, b)
    c = CAMO['olive']
    ang = [0, 25, 45, 45][frame]
    a = math.radians(ang)
    px, py = x + 4, b - 8
    L, H = 15, 7
    for t in range(L):
        for h in range(H):
            xx = px + t * math.cos(a) - h * math.sin(a); yy = py - t * math.sin(a) - h * math.cos(a)
            col = c[2] if h == H - 1 else c[1] if h > 1 else c[0]
            if t == L - 1: col = INKC if h % 2 == 0 else c[0]
            put(f, int(round(xx)), int(round(yy)), col)
    put(f, px + 2, py - 2, team[2]); put(f, px + 3, py - 2, team[3])
    if frame == 3:
        ex, ey = px + L * math.cos(a), py - L * math.sin(a) - 4
        missile(f, ex + 8, ey - 8, 45)
        for i in range(5): blend_mask(f, ellipse_mask(f.shape[:2], ex - i * 2, ey + i * 2, 2 + i * .7, 1.6 + i * .5), hx('#e8e4dc'), .7 - i * .1)
        blend_mask(f, ellipse_mask(f.shape[:2], px - 2, b - 4, 8, 3), hx('#e8e4dc'), .5)


def radar(f, x, b, frame=0):
    truck(f, x, b, 'grey')
    c = CAMO['grey']
    vline(f, x + 9, b - 16, 9, c[0])
    w = [11, 7, 2, 7][frame]
    for i in range(w):
        yy = b - 18 - int(2 * math.sin(i / max(1, w - 1) * math.pi)) if w > 2 else b - 19 + i
        put(f, x + 10 - w // 2 + i, yy, c[3] if frame != 2 else c[2]); put(f, x + 10 - w // 2 + i, yy + 1, c[1])
    if frame in (0, 1):
        for k in range(1, 3):
            for t in np.linspace(-.6, .6, 9): put(f, int(x + 10 + (6 + k * 5) * math.cos(t - 1.57 + .3 * frame)), int(b - 18 + (6 + k * 5) * math.sin(t - 1.57 + .3 * frame)), hx('#7cc46a'))


def flak(f, x, b, frame=0):
    shadow_ell(f, x + 8, b + 1, 9, 1.4)
    rect(f, x + 1, b - 4, 14, 4, CAMO['olive'][1]); hline(f, x + 1, b - 4, 14, CAMO['olive'][2])
    rect(f, x + 5, b - 8, 6, 4, CAMO['olive'][1]); hline(f, x + 5, b - 8, 6, CAMO['olive'][3])
    for k in range(2):
        for t in range(10): put(f, x + 9 + k * 2 + t // 2, b - 9 - t, INKC if t % 3 else hx('#4a4e56'))
    if frame % 2:
        for k in range(2): put(f, x + 15 + k * 2, b - 20, hx('#fff2b0')); put(f, x + 16 + k * 2, b - 21, hx('#ffd34a'))
        for i in range(3): blend_mask(f, ellipse_mask(f.shape[:2], x + 22 + i * 6, b - 30 - i * 6, 2.6, 2.4), hx('#3a3a40'), .7)


def ciws(f, x, b, frame=0):
    shadow_ell(f, x + 6, b + 1, 7, 1.4)
    rect(f, x + 1, b - 4, 10, 4, CAMO['white'][1]); hline(f, x + 1, b - 4, 10, CAMO['white'][3])
    dome(f, x + 6, b - 9, 4, 4.4, [CAMO['white'][0]] + CAMO['white'], 3)
    rect(f, x + 9, b - 8, 6, 2, hx('#3a3e44'))
    if frame % 2:
        for i in range(4): hline(f, x + 18 + i * 7, b - 10 - i * 3, 3, hx('#ffe27a'))


def laser_ad(f, x, b, frame=0):
    shadow_ell(f, x + 6, b + 1, 7, 1.4)
    rect(f, x + 3, b - 14, 6, 14, CAMO['white'][1]); vline(f, x + 3, b - 14, 14, CAMO['white'][3]); vline(f, x + 8, b - 14, 14, CAMO['white'][0])
    dome(f, x + 6, b - 16, 4, 3, [CAMO['white'][0]] + CAMO['white'], 1); put(f, x + 7, b - 17, C['cyan'])
    if frame % 2:
        for t in range(26):
            put(f, x + 8 + t, b - 18 - t, C['cyan2']); put(f, x + 9 + t, b - 18 - t, C['cyan'])
        blend_mask(f, ellipse_mask(f.shape[:2], x + 34, b - 44, 4, 4), C['cyan2'], .7)


def missile(f, x, y, ang, trail=0, big=False):
    a = math.radians(ang)
    if big:
        blend_mask(f, ellipse_mask(f.shape[:2], x, y, 3, 3), hx('#ffd34a'), .35)
    for t in range(5): put(f, int(x - t * math.cos(a)), int(y + t * math.sin(a)), hx('#e8eef2') if t else hx('#e05a5a'))
    put(f, int(x - 5 * math.cos(a)), int(y + 5 * math.sin(a)), hx('#ffd34a'))
    for i in range(trail):
        blend_mask(f, ellipse_mask(f.shape[:2], x - (6 + i * 3) * math.cos(a), y + (6 + i * 3) * math.sin(a), 1.2 + i * .25, 1.2 + i * .25), hx('#e8e4dc'), .65 - i * .05)


def boom(f, x, y, s=1.0, k=0):
    """k = frame 0..3"""
    r = [3, 6, 7, 6][k] * s
    if k < 3:
        blend_mask(f, ellipse_mask(f.shape[:2], x, y, r * 1.8, r * 1.5), hx('#ffb35a'), .3)
        dome(f, x, y, r, r * .9, [hx('#d5452d'), hx('#f49a3c'), hx('#ffd34a'), hx('#fff2b0'), hx('#ffffff')], 5, rough=.4)
    for i in range(k):
        blend_mask(f, ellipse_mask(f.shape[:2], x - 2 + i * 2, y - r - i * 3, r * .6 + i, r * .5 + i), hx('#5a5650') if k == 3 else hx('#8a847a'), .7)
    if k >= 2:
        rr = random.Random(int(x * 7 + y))
        for _ in range(8): put(f, int(x + rr.uniform(-r * 2, r * 2)), int(y + rr.uniform(-r * 1.5, r)), hx('#3a3430'))


def bomb(f, x, y, size=2):
    rect(f, x, y, 2, size + 1, hx('#3a3e34')); put(f, x, y, hx('#6a6e64')); put(f, x - 1, y - 1, hx('#3a3e34')); put(f, x + 2, y - 1, hx('#3a3e34'))


def flares(f, x, y, k=0):
    for i in range(6):
        t = i * .9 + k * .4
        put(f, int(x - 3 - i * 3), int(y + (-1) ** i * (2 + i * 1.5) + k), hx('#fff2b0'))
        blend_mask(f, ellipse_mask(f.shape[:2], x - 3 - i * 3, y + (-1) ** i * (2 + i * 1.5) + k, 2, 2), hx('#ffb35a'), .3)


def airbase(f, x, y, team=TEAM):
    rect(f, x, y + 18, 120, 12, hx('#4a4c50')); hline(f, x, y + 18, 120, hx('#6a6c70'))
    for i in range(0, 120, 8): hline(f, x + i, y + 24, 4, hx('#e8e4da'))
    for i in (4, 112): rect(f, x + i, y + 20, 3, 8, hx('#e8e4da'))
    # hangar (rounded roof)
    shadow_rect(f, x + 3, y - 2, 34, 14)
    rect(f, x, y, 32, 12, CAMO['grey'][1])
    for i in range(32):
        hh = int(4 * math.sin(i / 31 * math.pi))
        vline(f, x + i, y - hh, hh + 1, CAMO['grey'][2] if i < 16 else CAMO['grey'][1])
    rect(f, x + 8, y + 4, 16, 8, hx('#1e2024')); put(f, x + 4, y + 2, team[2]); put(f, x + 5, y + 2, team[3])
    # control tower
    rect(f, x + 44, y - 6, 5, 18, CAMO['white'][1]); vline(f, x + 44, y - 6, 18, CAMO['white'][3])
    rect(f, x + 42, y - 10, 9, 4, hx('#2a4a6a')); hline(f, x + 42, y - 11, 9, CAMO['white'][2]); put(f, x + 46, y - 13, hx('#e05a5a'))
    # fuel tanks
    for k in range(2): dome(f, x + 60 + k * 9, y + 6, 4, 4, [CAMO['white'][0]] + CAMO['white'], k)
