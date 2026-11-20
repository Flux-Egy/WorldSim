"""Feature wishlist board: what players ask competitors for, illustrated as pixel vignettes (2x fine grid)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from people import person2, T
from animals import draw as adraw
from weapons import soldier, helmet, cannon, fx_smoke, fx_flash, fx_boom, line, outfit
from army2 import rider
import air, culturegen as cg
from terrain import pine, cactus, fern, deadtree, lavapool
from buildings import BUILD

F = lambda s: ImageFont.load_default(size=s)
VW, VH = 96, 56
INKC = hx('#14110e')
RED, BLUE = R['K'], K2['blue']


def grass(seed, tint='#74a753'): return grass_ground(VW, VH, seed, tint=(hx(tint), .2))


def water(seed, deep=False):
    a = np.zeros((VH, VW, 3), np.uint8); a[:] = C['water'][1 if deep else 2]
    r = np.random.default_rng(seed)
    for _ in range(90):
        x, y = r.integers(0, VW - 3), r.integers(0, VH)
        hline(a, x, y, 3, C['water'][3])
    return a


def ship(a, x, b, rp, pirate=False, sails=2, firing=False):
    hull = hx('#5a3a22') if not pirate else hx('#2a2420')
    for i in range(24):
        d = 4 if 3 < i < 20 else 3 if 1 < i < 22 else 2
        vline(a, x + i, b - d, d + 1, hull if i % 5 else lit(hull, .15))
    hline(a, x + 2, b - 4, 20, lit(hull, .3)); hline(a, x, b + 1, 24, C['water'][4])
    for k in range(sails):
        mx = x + 7 + k * 9
        vline(a, mx, b - 18, 15, hx('#3a2a1e'))
        for j in range(10):
            hline(a, mx - 4 + j // 4, b - 17 + j, 8 - j // 3, hx('#e8e2d4') if not pirate else hx('#3a3a40'))
        if not pirate: put(a, mx - 2, b - 14, rp[2]); put(a, mx - 1, b - 14, rp[2])
    put(a, x + 16, b - 20, rp[2] if not pirate else INKC); put(a, x + 17, b - 20, rp[3] if not pirate else hx('#f0ece0'))
    for i in range(3): put(a, x + 6 + i * 6, b - 2, INKC)
    if firing:
        for i in range(3): fx_flash(a, x + 24, b - 3 - i); fx_smoke(a, x + 26, b - 5, 2, .8)


def wallseg(a, x, b, w, h=10):
    rect(a, x, b - h, w, h, W['fort'][1]); hline(a, x, b - h, w, W['fort'][2])
    for i in range(0, w, 2): put(a, x + i, b - h - 1, W['fort'][2])
    for yy in range(b - h + 2, b, 3):
        for xx in range(x + (yy % 2) * 2, x + w, 4): put(a, xx, yy, W['fort'][0])


def towerk(a, x, b, rp):
    rect(a, x, b - 16, 7, 16, W['fort'][1]); vline(a, x, b - 16, 16, W['fort'][2]); vline(a, x + 6, b - 16, 16, W['fort'][0])
    for i in range(0, 8, 2): put(a, x + i - 1 if i else x, b - 17, W['fort'][2])
    rect(a, x + 2, b - 12, 2, 3, INKC); put(a, x + 3, b - 22, rp[2]); vline(a, x + 3, b - 22, 5, hx('#c4bfb3'))


def P(a, x, y, cls='poor', cul='riverland', g='m', fr=0, seed=1, **kw):
    person2(a, x, y, cul, cls, 'adult', g, fr, seed=seed, **kw)


# ---------------------------------------------------------------- vignettes
def v_walls():
    a = grass(1)
    wallseg(a, 30, 40, 50, 12); towerk(a, 26, 42, RED); towerk(a, 80, 42, RED)
    rect(a, 50, 33, 8, 8, hx('#2a1d14')); hline(a, 49, 32, 10, W['fort'][2])
    blend_mask(a, ellipse_mask(a.shape[:2], 66, 34, 5, 4), hx('#1e1a16'), .7); fx_smoke(a, 64, 26, 3)
    cannon(a, 4, 52); fx_flash(a, 21, 43)
    soldier(a, 40, 6, 'xbow', 0); return a


def v_sea():
    a = water(2)
    ship(a, 6, 40, RED, firing=True); ship(a, 60, 36, BLUE, pirate=True)
    fx_boom(a, 66, 30, .7)
    for i in range(5): put(a, 40 + i * 3, 50 + (i % 2), hx('#3a2a1e'))   # wreck planks
    rect(a, 44, 51, 6, 2, hx('#5a3a22'))
    for t in range(12): put(a, 80 + t // 2, 50 - int(3 * math.sin(t)), hx('#3a6a5a'))
    return a


def v_cav():
    a = grass(3, '#c8b480'); rider(a, 2, 'horse', 'knight', 1, 'knight', lance=True)
    from army2 import B as AB
    return a


def v_cav2():
    a = grass_ground(VW, VH, 3, tint=(hx('#c8b480'), .25))
    y0 = VH - 3
    adraw(a, 4, y0 - 28, 'horse', 1, False, 3); soldier(a, 9, y0 - 36, 'knight', 0); helmet(a, 9, y0 - 36, 'knight')
    adraw(a, 46, y0 - 30, 'camel', 2, False, 4); soldier(a, 51, y0 - 39, 'archer', 0, seed=5)
    return a


def v_bridge():
    a = grass(4)
    for y in range(VH):
        for x in range(36, 60): a[y, x] = C['water'][2] if (x * 3 + y * 7) % 13 else C['water'][3]
        a[y, 35] = hx('#c8b07a'); a[y, 60] = hx('#c8b07a')
    for x in range(30, 66):
        rect(a, x, 26, 1, 6, W['stone'][2] if x % 4 else W['stone'][1])
    hline(a, 30, 25, 36, W['stone'][2]); hline(a, 30, 32, 36, W['stone'][0])
    for ax in (40, 52):
        for t in range(-4, 5): put(a, ax + t, 32 + int(math.sqrt(max(0, 16 - t * t)) * .7), C['water'][1])
    for x in range(0, 30): hline(a, x, 28, 1, C['dirt'][1]); put(a, x, 29, C['dirt'][0])
    for x in range(66, VW): hline(a, x, 28, 1, C['dirt'][1]); put(a, x, 29, C['dirt'][0])
    adraw(a, 40, 6, 'donkey', 1, False, 2); P(a, 26, 4, 'poor', 'riverland', 'm', 1, 3)
    return a


def v_heroes():
    a = grass(5)
    P(a, 40, 10, 'ruler', 'northern', 'm', 0, 4)
    blend_mask(a, ellipse_mask(a.shape[:2], 48, 24, 14, 16), hx('#ecc25c'), .15)
    for (gx, f_) in ((22, 0), (60, 0), (30, 2), (52, 2)):
        soldier(a, gx, 14 + (f_ == 2) * 12 if False else 12 + (gx in (30, 52)) * 10, 'knight', 0, seed=gx)
    for (dx, dy) in [(44, 6), (52, 4), (48, 2)]: put(a, dx, dy, hx('#fff2b0'))
    return a


def v_form():
    a = grass(6, '#8a9a5a')
    for bx, by, k, rp in ((6, 8, 'xbow', RED), (6, 26, 'xbow', RED)):
        for i in range(3):
            for j in range(2): soldier(a, bx + i * 7, by + j * 3 - 6, k, 0, seed=i + j)
    vline(a, 30, 2, 14, hx('#c4bfb3')); rect(a, 31, 2, 6, 4, RED[2]); put(a, 33, 3, C['gold'])
    for i in range(4):
        for t in range(6): put(a, 40 + i * 9 + t, 26 + (t if t < 3 else 6 - t) - 3, RED[3])
    rect(a, 78, 22, 14, 12, W['plaster'][1]); roof = [hx('#c4563d')] * 5; hline(a, 77, 21, 16, roof[0])
    for t in np.linspace(0, 2 * math.pi, 30): put(a, int(85 + 12 * math.cos(t)), int(28 + 9 * math.sin(t)), hx('#ffd34a'))
    t_ = 'GOAL'
    text(a, 76, 44, t_, hx('#ffd34a'))
    return a


def v_peace():
    a = grass(7)
    rect(a, 22, 22, 52, 14, hx('#6a4a2e')); hline(a, 22, 22, 52, hx('#8a6a46'))
    rect(a, 36, 24, 24, 9, hx('#ece4d2')); hline(a, 38, 27, 20, hx('#8a7a5e')); hline(a, 38, 30, 14, hx('#8a7a5e'))
    put(a, 56, 31, hx('#c83a3a')); put(a, 57, 31, hx('#c83a3a'))
    P(a, 4, 12, 'ruler', 'riverland', 'm', 0, 3); P(a, 76, 12, 'ruler', 'northern', 'm', 0, 7)
    for i, rp in enumerate((RED, BLUE)):
        c = np.zeros((15, 13, 3), np.uint8); c[:] = hx('#6a4a2e')
        cg.crest(c, 1, 1, dict(acc=rp, acc2=K2['gold'], seed=i, gold=True, symbol=['sun', 'wave'][i]), 1, rp, ['sun', 'wave'][i])
        a[38:53, 24 + i * 36:37 + i * 36] = c
    return a


def v_bigmap():
    import ui
    m, land = ui.world_map(seed=9)
    sm = np.asarray(Image.fromarray(m).resize((VW, VH * 2), Image.NEAREST))[30:30 + VH]
    a = sm.copy()
    for x in range(0, VW, 16): vline(a, x, 0, VH, lit(a[0, x], -.3))
    for y in range(0, VH, 16): hline(a, 0, y, VW, lit(a[y, 0], -.3))
    rect(a, 48, 16, 16, 16, a[16, 48])
    for k in range(16): put(a, 48 + k, 16, hx('#ffd34a')); put(a, 48 + k, 31, hx('#ffd34a')); put(a, 48, 16 + k, hx('#ffd34a')); put(a, 63, 16 + k, hx('#ffd34a'))
    text(a, 2, 2, '64 CHUNKS', TXTC)
    return a


def v_farm():
    a = grass(9)
    for x in range(8, 88, 2): put(a, x, 14, C['wood'][2]); put(a, x, 50, C['wood'][2])
    for y in range(14, 51, 2): put(a, 8, y, C['wood'][2]); put(a, 87, y, C['wood'][2])
    hline(a, 8, 15, 80, C['wood'][1]); hline(a, 8, 49, 80, C['wood'][1])
    adraw(a, 14, 18, 'sheep', 0, False, 1); adraw(a, 40, 16, 'cow', 1, False, 2); adraw(a, 14, 32, 'sheep', 1, True, 3)
    adraw(a, 66, 32, 'chicken', 0, False, 4); adraw(a, 74, 38, 'chicken', 1, True, 5); adraw(a, 60, 40, 'pig', 2, True, 6)
    rect(a, 50, 40, 4, 5, hx('#8a8a90')); hline(a, 50, 40, 4, hx('#ffffff'))
    for i in range(3): rect(a, 80 - i * 3, 46, 2, 2, hx('#f4ecdc'))
    return a


def v_rebels():
    a = grass(10, '#8a8a70')
    for i in range(4):
        P(a, 4 + i * 9, 18 + (i % 2) * 4, 'poor', ['riverland', 'highland', 'northern', 'riverland'][i], 'mf'[i % 2], i % 2, 20 + i)
        x = 15 + i * 9
        vline(a, x, 14 + (i % 2) * 4, 12, C['wood'][1])
        if i % 2: put(a, x, 13 + (i % 2) * 4, C['fire'][1]); put(a, x, 12 + (i % 2) * 4, C['fire'][2])
        else: put(a, x - 1, 14, hx('#8b939a')); put(a, x + 1, 14, hx('#8b939a'))
    for i in range(2): soldier(a, 64 + i * 12, 20, 'knight', 0, seed=i + 3)
    P(a, 50, 0, 'poor', 'highland', 'm', 1, 33); rect(a, 60, 12, 4, 3, hx('#8a6a3a')); put(a, 61, 11, C['gold'])
    return a


def v_caravan():
    a = grass_ground(VW, VH, 11, tint=(hx('#d9c08a'), .5))
    for t in range(0, VW, 3): put(a, t, 46 - int(6 * math.sin(t / 30)), hx('#c9a35a'))
    adraw(a, 4, 18, 'camel', 1, False, 1); adraw(a, 30, 16, 'camel', 3, False, 2)
    P(a, 56, 18, 'middle', 'riverland', 'm', 1, 5)
    for i in range(2): rect(a, 14 + i * 26, 18, 6, 4, [hx('#c83a3a'), hx('#3a62a0')][i])
    cactus(a, 82, 10); cactus(a, 88, 30)
    return a


def v_gov():
    a = np.zeros((VH, VW, 3), np.uint8); a[:] = hx('#1e2633')
    items = [('crown', 'MONARCHY', RED), ('know', 'REPUBLIC', BLUE), ('sword', 'MILITARY', R['K']), ('flask', 'TECHNOCRACY', K2['violet'])]
    for i, (ic, n, rp) in enumerate(items):
        x = 4 + (i % 2) * 46; y = 4 + (i // 2) * 26
        rect(a, x, y, 42, 22, hx('#28323f')); hline(a, x, y, 42, rp[3])
        icon(a, x + 3, y + 4, ic); text(a, x + 3, y + 14, n[:10], hx('#f3e6c8'))
    return a


def v_prof():
    a = grass(13)
    jobs = [('worker', 'northern', 'hammer'), ('poor', 'riverland', 'fish'), ('poor', 'highland', 'hoe'), ('rich', 'riverland', 'bag'), ('middle', 'northern', 'book')]
    for i, (c, cul, it) in enumerate(jobs):
        x = 2 + i * 19
        o = outfit('archer') if False else None
        P(a, x, 20, c if c != 'worker' else 'poor', cul, 'mf'[i % 2], 0, 40 + i)
        hx_, hy_ = x + 11, 39
        if it == 'hammer': line(a, hx_, hy_, hx_ + 3, hy_ - 6, C['wood'][1]); rect(a, hx_ + 2, hy_ - 8, 4, 2, hx('#8b939a')); rect(a, x + 4, 32, 7, 6, hx('#3a2a1e'))
        if it == 'fish': line(a, hx_, hy_, hx_ + 6, hy_ - 14, C['wood'][2]); vline(a, hx_ + 6, hy_ - 14, 10, hx('#e8e2d4')); rect(a, hx_ + 5, hy_ - 4, 3, 2, hx('#7098ae'))
        if it == 'hoe': line(a, hx_, hy_ + 2, hx_ + 2, hy_ - 12, C['wood'][2]); hline(a, hx_ + 1, hy_ - 12, 4, hx('#8b939a'))
        if it == 'bag': rect(a, hx_, hy_, 4, 4, hx('#b08a4a')); put(a, hx_ + 1, hy_ + 1, C['gold'])
        if it == 'book': rect(a, hx_, hy_ - 2, 4, 3, hx('#8a3a30')); hline(a, hx_, hy_ - 2, 4, hx('#f3e6c8'))
    return a


def v_fest():
    a = grass(14, '#6a7a7a'); a = (a * .45).astype(np.uint8)
    for k, (fx_, fy, col) in enumerate(((20, 12, '#e87ab8'), (50, 8, '#ffd34a'), (76, 14, '#5fe0e8'))):
        for t in range(12):
            ang = t / 12 * 2 * math.pi
            for r_ in (3, 6, 8): put(a, int(fx_ + r_ * math.cos(ang)), int(fy + r_ * math.sin(ang)), lit(hx(col), .2 if r_ < 6 else -.1))
        blend_mask(a, ellipse_mask(a.shape[:2], fx_, fy, 10, 9), hx(col), .15)
    for x in range(4, 92, 6): put(a, x, 30 + (x % 12 == 4), hx('#f49a3c')); put(a, x, 31 + (x % 12 == 4), hx('#ffd34a'))
    hline(a, 4, 29, 88, hx('#3a2a1e'))
    for i in range(5): P(a, 6 + i * 18, 28, 'middle', ['riverland', 'northern', 'highland', 'riverland', 'northern'][i], 'mf'[i % 2], i % 2, 50 + i, shadow=False)
    return a


def v_modern():
    import scenes
    a_, occ, fx = scenes.build_scene(4, 1, seed=3)
    f = upscale(a_, 2)
    return np.asarray(Image.fromarray(f[60:60 + VH * 2, 60:60 + VW * 2]).resize((VW, VH), Image.NEAREST)).copy()


def v_fog():
    import ui
    m, land = ui.world_map(seed=4)
    a = np.asarray(Image.fromarray(m[140:140 + VH * 2, 20:20 + VW * 2]).resize((VW, VH), Image.NEAREST)).copy()
    yy, xx = np.mgrid[0:VH, 0:VW]
    d = np.hypot(xx - 30, (yy - 30) * 1.2)
    fog = d > 22 + (smooth_noise(VW, VH, 6, 3) - .5) * 10
    a[fog] = (a[fog] * .25 + np.array(hx('#1e2633')) * .75).astype(np.uint8)
    edge = fog & ~(np.roll(fog, 1, 0) & np.roll(fog, -1, 0) & np.roll(fog, 1, 1) & np.roll(fog, -1, 1))
    a[edge] = hx('#3a4656')
    P(a, 24, 12, 'poor', 'northern', 'm', 1, 3); vline(a, 36, 18, 8, C['wood'][1]); put(a, 36, 17, C['fire'][2])
    text(a, 60, 44, '???', hx('#8f99a8'))
    return a


def v_editor():
    a = grass(16)
    for t in np.linspace(0, 2 * math.pi, 40): put(a, int(40 + 12 * math.cos(t)), int(28 + 9 * math.sin(t)), hx('#ffffff'))
    m = ellipse_mask(a.shape[:2], 40, 28, 10, 7); a[m] = (a[m] * .4 + np.array(hx('#87837a')) * .6).astype(np.uint8)
    rock(a, 38, 28, 2.4, 3); rock(a, 44, 30, 1.8, 4)
    rect(a, 66, 4, 26, 48, hx('#1e2633'))
    for i, c in enumerate(('#74a753', '#d9c08a', '#87837a', '#3277b0', '#e8eef2')):
        rect(a, 70, 8 + i * 8, 8, 6, hx(c));
    rect(a, 69, 23, 10, 8, hx('#ffd34a')); rect(a, 70, 24, 8, 6, hx('#87837a'))
    for (dx, dy) in [(0, 2), (1, 1), (2, 0), (1, 3), (2, 4), (3, 2), (4, 2), (5, 2), (6, 3)]: put(a, 81 + dx, 10 + dy, hx('#f3e6c8'))
    text(a, 81, 18, 'UNDO', hx('#f3e6c8'))
    return a


def v_share():
    a = np.zeros((VH, VW, 3), np.uint8); a[:] = hx('#1e2633')
    rect(a, 6, 4, 34, 48, hx('#0b0e13')); rect(a, 8, 7, 30, 42, hx('#28323f'))
    g = cg.make_culture(37)
    c = np.zeros((15, 13, 3), np.uint8); c[:] = hx('#28323f'); cg.crest(c, 1, 1, g, 1)
    a[10:25, 16:29] = c
    text(a, 10, 28, g['name'][:6], hx('#f3e6c8'))
    r = random.Random(3)
    for y in range(36, 46, 2):
        for x in range(12, 34, 2):
            if r.random() < .5: rect(a, x, y, 2, 2, hx('#f3e6c8'))
    for i in range(3):
        rect(a, 54, 8 + i * 16, 36, 12, hx('#28323f')); hline(a, 54, 8 + i * 16, 36, hx('#e8b46a'))
        text(a, 57, 12 + i * 16, ['PLAYER2', 'WORLD#', 'CULTURE'][i], hx('#8f99a8'))
    for t in range(8): put(a, 42 + t, 26, hx('#e8b46a'))
    put(a, 49, 25, hx('#e8b46a')); put(a, 49, 27, hx('#e8b46a'))
    return a


def v_seasons():
    a = np.zeros((VH, VW, 3), np.uint8)
    tints = [('#7cb05a', None), ('#74a753', None), ('#b8904a', '#d8803a'), ('#e8eef2', '#ffffff')]
    for k, (tc, leaf) in enumerate(tints):
        s = grass_ground(24, VH, k, tint=(hx(tc), .55 if k >= 2 else .2))
        if k == 0:
            for i in range(10): put(s, (i * 7) % 24, (i * 13) % VH, hx('#e87ab8'))
        tree(s, 10, 18, 4, k, rp=None if k < 2 else ramp('#8a3a1e', '#b0502a', '#d8803a', '#e8a04a', '#f0c060') if k == 2 else ramp('#a8b4bc', '#c8d0d8', '#e0e6ea', '#f0f4f6', '#ffffff'))
        if k == 3:
            for i in range(14): put(s, (i * 5) % 24, (i * 11) % VH, hx('#ffffff'))
        if k == 1:
            for i in range(8): vline(s, (i * 7) % 24, (i * 9) % 40, 3, hx('#9ad0f0'))
        a[:, k * 24:(k + 1) * 24] = s
    return a


def v_disaster():
    a = grass(18, '#8a8a70')
    for i in range(30):
        hh = int(22 - abs(i - 15) * 1.4)
        vline(a, 4 + i, VH - hh - 6, hh, W['stone'][1] if i < 15 else W['stone'][0])
    lavapool(a, 19, VH - 28, 4, 2, 1)
    for i in range(6): put(a, 19 + (i % 3) - 1, VH - 30 - i * 3, C['fire'][2 - i % 3])
    fx_smoke(a, 16, 14, 4, 1.5)
    for x in range(40, VW):
        h = int(14 + 10 * math.sin((x - 40) / 12))
        for y in range(VH - h, VH): a[y, x] = C['water'][2] if y > VH - h + 2 else C['water'][4]
    for i in range(8): put(a, 50 + i * 5, VH - 26 + (i % 2), hx('#ffffff'))
    return a


def v_titan():
    a = water(19)
    for k, x0 in enumerate((10, 34, 58)):
        for t in range(14):
            y = 40 - int(10 * math.sin(t / 13 * math.pi))
            for o in range(3): put(a, x0 + t, y + o, [hx('#2a5a4a'), hx('#3a7a62'), hx('#1e4a3a')][o])
            if t % 3 == 0: put(a, x0 + t, y - 1, hx('#e8c84a'))
    dome(a, 82, 26, 6, 5, [hx('#1e4a3a'), hx('#2a5a4a'), hx('#3a7a62'), hx('#5a9a80'), hx('#8ac0a8')], 3)
    put(a, 85, 24, hx('#ffe27a')); rect(a, 86, 28, 5, 1, hx('#f0ece0'))
    ship(a, 2, 54, BLUE, sails=1)
    return a


def v_replay():
    a = np.zeros((VH, VW, 3), np.uint8); a[:] = hx('#1e2633')
    series = [(RED[3], [2, 3, 5, 8, 9, 14, 18, 20, 19, 24]), (BLUE[3], [4, 5, 6, 6, 10, 15, 22, 30, 32, 31]), (K2['violet'][3], [6, 7, 9, 10, 9, 8, 6, 4, 2, 0])]
    for col, d in series:
        pts = [(4 + i * 9, 40 - v) for i, v in enumerate(d)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]): line(a, x0, y0, x1, y1, col)
    hline(a, 4, 40, 86, hx('#3a4656'))
    rect(a, 4, 46, 86, 4, hx('#0b0e13')); rect(a, 4, 46, 58, 4, hx('#e8b46a')); rect(a, 60, 44, 4, 8, hx('#f3e6c8'))
    text(a, 4, 2, 'Y0', hx('#8f99a8')); text(a, 74, 2, 'Y1342', hx('#8f99a8'))
    return a


def v_prehist():
    a = grass(21, '#4e8a3c')
    for i in range(7): fern(a, 6 + i * 13, 48 - (i % 2) * 6)
    # original long-neck grazer
    dome(a, 50, 34, 14, 7, [hx('#3a5a3a'), hx('#4a6e44'), hx('#5e8650'), hx('#7aa066'), hx('#9aba82')], 4)
    for t in range(14): put(a, 62 + t, 30 - t + t * t // 22, hx('#5e8650')); put(a, 62 + t, 31 - t + t * t // 22, hx('#4a6e44'))
    dome(a, 77, 18, 3, 2, [hx('#3a5a3a'), hx('#4a6e44'), hx('#5e8650'), hx('#7aa066'), hx('#9aba82')], 5); put(a, 78, 17, INKC)
    for lx in (40, 46, 54, 60): rect(a, lx, 39, 3, 7, hx('#3a5a3a'))
    for t in range(12): put(a, 37 - t, 34 + t // 2, hx('#4a6e44'))
    return a


def v_migrate():
    a = grass(22, '#8a8a70')
    rect(a, 70, 8, 22, 14, W['plaster'][1]); hline(a, 70, 7, 22, R['K'][1])
    fx_boom(a, 80, 8, .7); fx_smoke(a, 74, 2, 3, 1.1)
    for i in range(4): P(a, 52 - i * 13, 24 + (i % 2) * 2, 'poor', 'highland', 'mf'[i % 2], i % 2, 60 + i)
    rect(a, 2, 38, 12, 6, C['wood'][1]); hline(a, 2, 38, 12, C['wood'][2]); rect(a, 4, 34, 8, 4, hx('#c8b88a'))
    dome(a, 4, 45, 1.6, 1.6, [INKC] * 5, 1); dome(a, 12, 45, 1.6, 1.6, [INKC] * 5, 2)
    return a


TXTC = hx('#f3e6c8')

B1 = [(v_walls, 'KINGDOM WALLS & CASTLES', 'TOP REQUEST', 97, 'walls with gates & towers; cannons breach them; castles hold sieges'),
      (v_sea, 'SHIPS, PIRATES & NAVAL WAR', 'TOP REQUEST', 85, 'fleets, sea battles, pirate raids, wrecks you can find later'),
      (v_cav2, 'CAVALRY & MOUNTS', 'TOP REQUEST', 81, 'horses, camels & beasts for travel and battle (already drawn)'),
      (v_bridge, 'BRIDGES', 'TOP REQUEST', 62, 'nations build bridges over rivers & straits to reach new land'),
      (v_heroes, 'HEROES & ROYAL GUARDS', 'TOP REQUEST', 59, 'legends with abilities; elite guards protect the ruler'),
      (v_form, 'FORMATIONS & WAR GOALS', 'REQUESTED', 35, 'blocks & lines, banners, officers; wars fought for a target'),
      (v_peace, 'PEACE DEALS & VASSALS', 'REQUESTED', 14, 'treaties split land; losers become vassals or puppet states'),
      (v_bigmap, 'BIGGER MAPS', 'REQUESTED', 56, 'chunked worlds stream in pieces, phone keeps 30 fps'),
      (v_farm, 'FARM ANIMALS', 'REQUESTED', 26, 'pens, milk, eggs & wool; herders move flocks'),
      (v_rebels, 'REBELLIONS & CRIME', 'REQUESTED', 22, 'mobs with torches, thieves, rebel towns switch sides'),
      (v_caravan, 'NOMADS & TRADE ROUTES', 'REQUESTED', 19, 'caravans walk real roads; trade spreads ideas & disease'),
      (v_gov, 'GOVERNMENTS & LAWS', 'REQUESTED', 26, 'monarchy, republic, junta...; laws change daily life')]
B2 = [(v_prof, 'PROFESSIONS CHANGE LOOKS', 'REQUESTED', 10, 'smith, fisher, farmer, merchant, scholar each look different'),
      (v_fest, 'FESTIVALS & FIREWORKS', 'REQUESTED', 6, 'every culture invents its own holidays & lanterns'),
      (v_modern, 'MODERN ERA', 'NOT PLANNED THERE', 69, 'their most-wanted "no": we ship modern + future eras'),
      (v_fog, 'FOG OF WAR & EXPLORERS', 'REQUESTED', 11, 'nations only know what they explored; no wars on strangers'),
      (v_editor, 'WORLD EDITOR + UNDO', 'REQUESTED', 23, 'paint height & biomes with brushes; undo any mistake'),
      (v_share, 'SHARE WORLDS & CULTURES', 'REQUESTED', 17, 'export a world or a culture as a code; play friends\' worlds'),
      (v_seasons, 'SEASONS & WEATHER', 'LIKELY NEXT ASK', 0, 'spring bloom, rain, autumn leaves, snow winters & famine'),
      (v_disaster, 'VOLCANOES & TSUNAMIS', 'LIKELY NEXT ASK', 0, 'natural disasters with warnings nations can learn to read'),
      (v_titan, 'TITANS & SEA SERPENTS', 'REQUESTED', 43, 'rare giant beasts that grow, hunt and become legends'),
      (v_replay, 'TIMELAPSE REPLAY & GRAPHS', 'LIKELY NEXT ASK', 0, 'rewind centuries, compare nations, export a clip'),
      (v_prehist, 'PREHISTORIC BIOME', 'REQUESTED', 16, 'fern jungles & giant grazers before the stone age'),
      (v_migrate, 'MIGRATION & REFUGEES', 'LIKELY NEXT ASK', 0, 'war & famine push families to walk to safer lands')]


def board(cards, title, sub, path):
    S, G, cols = 3, 14, 4
    cw, ch = VW * S, VH * S
    CH = ch + 110
    rows = (len(cards) + cols - 1) // cols
    out = Image.new('RGB', (cols * (cw + G) + G, 110 + rows * (CH + G)), (18, 22, 28)); d = ImageDraw.Draw(out)
    d.text((G, 36), title, fill=(240, 228, 200), font=F(30), anchor='lm')
    d.text((G, 76), sub, fill=(150, 160, 175), font=F(18), anchor='lm')
    for i, (fn, name, tag, votes, desc) in enumerate(cards):
        x = G + (i % cols) * (cw + G); y = 110 + (i // cols) * (CH + G)
        d.rectangle([x - 4, y - 4, x + cw + 3, y + CH - 4], fill=(26, 31, 39), outline=(52, 62, 76), width=2)
        out.paste(Image.fromarray(fn()).resize((cw, ch), Image.NEAREST), (x, y))
        d.text((x + 4, y + ch + 18), name, fill=(240, 228, 200), font=F(18), anchor='lm')
        col = {'TOP REQUEST': (232, 180, 106), 'REQUESTED': (124, 196, 106), 'NOT PLANNED THERE': (224, 106, 85), 'LIKELY NEXT ASK': (95, 224, 232)}[tag]
        lab = tag + (f'  ·  {votes} comments' if votes else '')
        d.rounded_rectangle([x + 4, y + ch + 34, x + 14 + 8 * len(lab), y + ch + 56], 5, fill=tuple(int(v * .25) for v in col), outline=col)
        d.text((x + 10, y + ch + 45), lab, fill=col, font=F(14), anchor='lm')
        # wrap desc
        words, line_, ly = desc.split(), '', y + ch + 74
        for w in words:
            if len(line_ + ' ' + w) > 38: d.text((x + 4, ly), line_.strip(), fill=(170, 178, 190), font=F(15), anchor='lm'); line_, ly = '', ly + 20
            line_ += ' ' + w
        d.text((x + 4, ly), line_.strip(), fill=(170, 178, 190), font=F(15), anchor='lm')
    out.save(path); print(path, out.size)


if __name__ == '__main__':
    board(B1, 'WHAT PLAYERS ASK COMPETITORS FOR  (1/2)', 'from the public WorldBox idea board (comment counts) - all planned for WorldSim', 'features_wishlist_1.png')
    board(B2, 'WHAT PLAYERS ASK COMPETITORS FOR  (2/2)', 'requested ideas + what we expect players to ask next', 'features_wishlist_2.png')
