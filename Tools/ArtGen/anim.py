"""Life & death animation beats (2x fine grid): hunting, predators, injury, disease stages, contagion.
Readable, cartoon-clean (no gore): hit flash, damage numbers, legs-up animals, lying bodies, graves."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from animals import draw as adraw
from people import person2

SENT = np.array((1, 254, 3), np.uint8)
PW_, PH_ = 64, 38
RED = hx('#e0503c'); GRN = hx('#8ac04a'); GRN2 = hx('#5e8a2e'); WHITE = hx('#f6f2ea'); GOLDC = hx('#ecc25c'); INKC = hx('#14110e')


def spr(fn, w=40, h=40):
    a = np.zeros((h, w, 3), np.uint8); a[:] = SENT
    fn(a)
    ai = a.astype(int)
    m = np.any(a != SENT, axis=2) & ~((ai[..., 1] > 120) & (ai[..., 0] < 70) & (ai[..., 2] < 70))
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return a[y0:y1, x0:x1].copy(), m[y0:y1, x0:x1].copy()


def paste(f, s, x, y, tint=None, k=0.):
    img, m = s
    h, w = m.shape
    for j in range(h):
        for i in range(w):
            if m[j, i] and 0 <= y + j < f.shape[0] and 0 <= x + i < f.shape[1]:
                c = img[j, i]
                if tint is not None: c = (np.array(c, float) * (1 - k) + np.array(tint) * k).astype(np.uint8)
                f[y + j, x + i] = c


def flipud(s): return (s[0][::-1].copy(), s[1][::-1].copy())
def rot(s, k=1): return (np.rot90(s[0], k).copy(), np.rot90(s[1], k).copy())


def ground(seed, tint='#74a753'):
    return grass_ground(PW_, PH_, seed, tint=(hx(tint), .25))


def hp(f, x, y, frac, col=None):
    rect(f, x, y, 12, 3, INKC); rect(f, x + 1, y + 1, 10, 1, hx('#3a1a16'))
    rect(f, x + 1, y + 1, max(0, int(10 * frac)), 1, col or (GRN if frac > .5 else RED if frac < .3 else GOLDC))


def num(f, x, y, s, col):
    text(f, x + 1, y + 1, s, INKC); text(f, x, y, s, col)


def cloud(f, x, y, r, col, a=.55):
    blend_mask(f, ellipse_mask(f.shape[:2], x, y, r, r * .8), col, a)


def bubble(f, x, y, kind):
    """status icon above a head."""
    rect(f, x, y, 7, 7, INKC); rect(f, x + 1, y + 1, 5, 5, hx('#1d2530'))
    if kind == 'infected':
        for (dx, dy) in [(2, 1), (1, 2), (3, 2), (2, 3), (2, 2), (1, 4), (3, 4)]: put(f, x + 1 + dx - 1, y + 1 + dy - 1, GRN)
    elif kind == 'sick':
        rect(f, x + 2, y + 2, 3, 3, GRN); put(f, x + 2, y + 3, INKC); put(f, x + 4, y + 3, INKC)
    elif kind == 'immune':
        rect(f, x + 2, y + 2, 3, 2, GOLDC); put(f, x + 3, y + 4, GOLDC); put(f, x + 3, y + 2, WHITE)
    elif kind == 'alert':
        vline(f, x + 3, y + 1, 3, RED); put(f, x + 3, y + 5, RED)
    elif kind == 'food':
        rect(f, x + 2, y + 2, 3, 2, hx('#c86a4a')); put(f, x + 4, y + 4, WHITE)
    elif kind == 'heal':
        hline(f, x + 1, y + 3, 5, GRN); vline(f, x + 3, y + 1, 5, GRN)


def grave(f, x, b):
    """plain rounded headstone (no symbols) with a mound."""
    rect(f, x + 1, b - 9, 6, 9, hx('#8a8780')); hline(f, x + 2, b - 10, 4, hx('#a29d92')); put(f, x + 1, b - 9, hx('#a29d92')); put(f, x + 6, b - 9, hx('#6e6b65'))
    vline(f, x + 1, b - 8, 8, hx('#a29d92')); vline(f, x + 6, b - 8, 8, hx('#6e6b65'))
    hline(f, x + 3, b - 6, 2, hx('#5f5b55')); hline(f, x + 2, b - 4, 4, hx('#6e6b65'))


def man(seed=3, frame=0, state=None, cls='poor', culture='northern', age='adult', g='m'):
    return spr(lambda a: person2(a, 2, 4, culture, cls, age, g, frame, seed=seed, shadow=False, state=state), 24, 36)


def bandage(f, x, y):  # x,y = sprite top-left of person (16x28 box offset 2,4 inside spr crop ~ head at row 0..)
    hline(f, x + 3, y + 3, 7, WHITE); put(f, x + 4, y + 3, RED)


def shadow(f, x, y, rx=4):
    shadow_ell(f, x, y, rx, 1.2, .3)


# ------------------------------------------------------------------ rows
def row_hunt():
    frames = []
    hunter = [man(5, f, cls='poor', culture='highland') for f in range(4)]
    deer = [spr(lambda a, f=f: adraw(a, 2, 2, 'deer', f, False, 3), 40, 40) for f in range(4)]
    for k in range(5):
        f = ground(10 + k)
        dx = 38
        dy = PH_ - 2 - deer[0][1].shape[0]
        hx_, hy_ = 6, PH_ - 2 - hunter[0][1].shape[0]
        if k == 0:
            shadow(f, hx_ + 6, PH_ - 2); paste(f, hunter[0], hx_, hy_)
            shadow(f, dx + 9, PH_ - 2, 7); paste(f, deer[0], dx, dy); bubble(f, hx_ + 3, hy_ - 9, 'alert')
            vline(f, hx_ + 12, hy_ - 4, 14, C['wood'][2])
        elif k == 1:
            shadow(f, hx_ + 6, PH_ - 2); paste(f, hunter[1], hx_, hy_)
            for i in range(10): put(f, hx_ + 14 + i, hy_ + 6 - i // 4, C['wood'][2])
            put(f, hx_ + 24, hy_ + 3, hx('#c8c2b6'))
            shadow(f, dx + 9, PH_ - 2, 7); paste(f, deer[1], dx, dy)
        elif k == 2:
            shadow(f, hx_ + 6, PH_ - 2); paste(f, hunter[2], hx_, hy_)
            shadow(f, dx + 9, PH_ - 2, 7); paste(f, deer[2], dx, dy, WHITE, .65)
            line_ = [(dx + 2 - i, dy + 4 - i // 3) for i in range(8)]
            for (x, y) in line_: put(f, x, y, C['wood'][2])
            for (ox, oy) in [(-2, -2), (2, -3), (3, 1), (-3, 1)]: put(f, dx + 10 + ox, dy + 4 + oy, WHITE)
            num(f, dx + 2, max(1, dy - 1), '-40', RED)
        elif k == 3:
            shadow(f, hx_ + 6, PH_ - 2); paste(f, hunter[3], hx_ + 6, hy_)
            d = flipud(deer[0]); paste(f, d, dx, PH_ - 3 - d[1].shape[0] // 2 - 4)
            put(f, dx + 14, PH_ - 9, INKC); put(f, dx + 15, PH_ - 8, INKC)
            shadow(f, dx + 9, PH_ - 2, 8)
        else:
            shadow(f, hx_ + 20, PH_ - 2); paste(f, hunter[0], hx_ + 14, hy_)
            rect(f, hx_ + 27, hy_ + 10, 6, 4, hx('#b05a42')); hline(f, hx_ + 27, hy_ + 10, 6, hx('#d47a5a')); put(f, hx_ + 32, hy_ + 13, WHITE)
            num(f, hx_ + 6, hy_ - 9, '+FOOD', GRN)
        frames.append(f)
    return frames


def row_predator():
    frames = []
    wolf = [spr(lambda a, f=f: adraw(a, 2, 2, 'wolf', f, False, 4), 40, 40) for f in range(4)]
    v = [man(8, f, cls='poor', culture='riverland', g='f') for f in range(4)]
    for k in range(5):
        f = ground(20 + k, '#8a9a5a')
        vx, vy = 40, PH_ - 2 - v[0][1].shape[0]
        wy = PH_ - 2 - wolf[0][1].shape[0]
        if k == 0:
            shadow(f, vx + 6, PH_ - 2); paste(f, v[0], vx, vy); bubble(f, vx + 3, vy - 9, 'alert')
            shadow(f, 12, PH_ - 2, 7); paste(f, wolf[0], 2, wy)
            for i in range(3): put(f, 1 - i, wy + 6 + i, hx('#c8c2b6'))
        elif k == 1:
            shadow(f, vx + 6, PH_ - 2); paste(f, v[1], vx + 3, vy)
            shadow(f, 26, PH_ - 2, 7); paste(f, wolf[2], 16, wy - 2)
        elif k == 2:
            shadow(f, vx + 6, PH_ - 2); paste(f, v[0], vx + 3, vy, RED, .55); hp(f, vx + 2, vy - 6, .35)
            paste(f, wolf[1], 28, wy - 3)
            num(f, vx - 14, vy - 2, '-25', RED)
            for (ox, oy) in [(0, 0), (2, -2), (-2, 2)]: put(f, vx + 2 + ox, vy + 10 + oy, WHITE)
        elif k == 3:
            p = rot(v[0], 1); paste(f, p, vx - 2, PH_ - 3 - p[1].shape[0]); shadow(f, vx + 10, PH_ - 2, 9)
            paste(f, wolf[0], 18, wy); hp(f, vx + 2, PH_ - 16, 0.0)
        else:
            # remains + wolf eating, crows: readable but not gory
            for (x, y) in [(vx + 2, PH_ - 5), (vx + 6, PH_ - 4), (vx + 9, PH_ - 5)]: hline(f, x, y, 3, WHITE); put(f, x, y + 1, hx('#c8c2b6'))
            paste(f, wolf[3], 22, wy + 1); bubble(f, 30, wy - 8, 'food')
            for (x, y) in [(50, 6), (56, 9)]: hline(f, x, y, 3, INKC); put(f, x + 1, y - 1, INKC)
        frames.append(f)
    return frames


def row_injury():
    frames = []
    for k in range(5):
        f = ground(30 + k, '#9aa070')
        x, y0 = 22, PH_ - 2
        if k < 3:
            p = man(11, [0, 1, 0][k], cls='middle', culture='northern')
            y = y0 - p[1].shape[0] + (1 if k == 1 else 0)
            shadow(f, x + 6, y0); paste(f, p, x + k * 4, y)
            bandage(f, x + k * 4, y)
            put(f, x + k * 4 + 1, y + 13, WHITE); put(f, x + k * 4 + 2, y + 14, WHITE)  # sling
            vline(f, x + k * 4 + 14, y + 10, 16, C['wood'][2])  # crutch
            hp(f, x + k * 4 + 1, y - 6, .4)
            if k == 1: num(f, x + 20, y - 2, 'LIMP', GOLDC)
        else:
            p = man(11, 0, cls='middle', culture='northern')
            h = man(17, 0, cls='rich', culture='highland', g='f')
            y = y0 - p[1].shape[0]
            shadow(f, x + 6, y0); paste(f, p, x, y)
            if k == 3:
                bandage(f, x, y); hp(f, x + 1, y - 6, .7); shadow(f, x + 22, y0); paste(f, h, x + 16, y - 0)
                bubble(f, x + 20, y - 9, 'heal')
                for (ox, oy) in [(12, 6), (14, 3), (11, 1)]: put(f, x + ox, y + oy, GRN)
            else:
                hp(f, x + 1, y - 6, 1.0)
                for (ox, oy) in [(-2, 4), (14, 2), (13, 12), (-1, 14), (6, -3)]: put(f, x + ox, y + oy, GOLDC)
                num(f, x + 16, y + 4, 'HEALED', GRN)
        frames.append(f)
    return frames


def row_disease():
    frames = []
    labels = ['HEALTHY', 'INFECTED', 'SICK', 'SEVERE', 'RECOVERED / DIED']
    for k in range(5):
        f = ground(40 + k, '#7a9a58')
        x, y0 = 24, PH_ - 2
        if k == 0:
            p = man(21, 0, cls='middle', culture='riverland'); y = y0 - p[1].shape[0]
            shadow(f, x + 6, y0); paste(f, p, x, y); hp(f, x + 1, y - 6, 1.0)
        elif k == 1:
            p = man(21, 0, cls='middle', culture='riverland'); y = y0 - p[1].shape[0]
            shadow(f, x + 6, y0); paste(f, p, x, y); bubble(f, x + 3, y - 9, 'infected'); hp(f, x + 12, y - 4, .9)
        elif k == 2:
            p = man(21, 0, cls='middle', culture='riverland', state='sick'); y = y0 - p[1].shape[0] + 1
            shadow(f, x + 6, y0); paste(f, p, x, y); bubble(f, x + 3, y - 9, 'sick'); hp(f, x + 12, y - 4, .55)
            put(f, x + 3, y + 3, hx('#9ad0f0')); put(f, x + 3, y + 4, hx('#9ad0f0'))
            for i, (ox, r) in enumerate([(13, 1.6), (17, 2.2), (22, 2.8)]): cloud(f, x + ox, y + 6 - i, r, GRN, .5 - i * .1)
        elif k == 3:
            rect(f, 10, y0 - 6, 40, 5, hx('#8a6a46')); hline(f, 10, y0 - 6, 40, hx('#b08a5e'))  # mat
            p = rot(man(21, 0, cls='middle', culture='riverland', state='sick'), 1)
            paste(f, p, 14, y0 - 6 - p[1].shape[0] + 3)
            rect(f, 26, y0 - 9, 22, 5, hx('#c8b88a')); hline(f, 26, y0 - 9, 22, hx('#e2d4a8'))  # blanket
            hp(f, 22, y0 - 22, .15)
            for (ox, oy) in [(12, -16), (20, -19), (40, -15), (34, -20)]: put(f, ox, y0 + oy, INKC)
        else:
            # split: left recovered (immune), right grave
            p = man(21, 0, cls='middle', culture='riverland'); y = y0 - p[1].shape[0]
            shadow(f, 12, y0); paste(f, p, 6, y); bubble(f, 9, y - 9, 'immune')
            gx = 42
            rect(f, gx - 2, y0 - 3, 14, 3, hx('#6a5038')); hline(f, gx - 2, y0 - 3, 14, hx('#8a6a4a'))
            grave(f, gx + 1, y0 - 3)
            for (ox, c) in [(-1, hx('#e8c84a')), (11, hx('#d5452d'))]: put(f, gx + ox, y0 - 4, c); put(f, gx + ox, y0 - 3, GRN2)
            vline(f, 32, 4, PH_ - 8, hx('#2a3240'))
        frames.append(f)
    return frames, labels


def row_contagion():
    frames = []
    xs = [4, 16, 28, 40, 52]
    order = {0: [0], 1: [0], 2: [0, 1], 3: [0, 1, 3], 4: [0, 1, 2, 3]}
    for k in range(5):
        f = ground(50 + k, '#8a9a6a')
        for i, x in enumerate(xs):
            sick = i in order[k]
            p = man(30 + i, (k + i) % 2 * (0 if sick else 1), cls=['poor', 'middle', 'poor', 'rich', 'middle'][i], culture=['riverland', 'northern', 'highland', 'riverland', 'northern'][i],
                    g='mf'[i % 2], state='sick' if (sick and k - (order[k].index(i) if i in order[k] else 0) >= 1 and i == 0) or (i == 0) else None)
            y = PH_ - 2 - p[1].shape[0]
            shadow(f, x + 5, PH_ - 2, 3.4); paste(f, p, x - 2, y)
            if sick: bubble(f, x + 1, y - 9, 'sick' if i == 0 else 'infected')
        # cough cloud travels from patient zero
        cx = 10 + k * 9
        if k < 4:
            for j, r in enumerate([2.2, 3.0, 3.8]): cloud(f, cx + j * 4, 13 + j, r, GRN, .6 - j * .1)
        # rat carrier
        rx, ry = 58 - k * 6, PH_ - 4
        rect(f, rx, ry, 4, 2, hx('#5a5048')); put(f, rx - 1, ry, hx('#5a5048')); put(f, rx + 4, ry + 1, hx('#3a3430')); put(f, rx + 5, ry + 1, hx('#3a3430')); put(f, rx - 1, ry - 1, INKC)
        if k == 4:
            vline(f, 60, 6, 16, C['wood'][1]); rect(f, 61, 6, 3, 4, GOLDC); put(f, 62, 7, INKC)
        frames.append(f)
    return frames


ROWS = [('HUNT', 'hunter spots, throws, hits (flash + damage), deer falls legs-up, meat -> food', row_hunt),
        ('PREDATOR', 'wolf stalks, lunges, villager hurt (red flash, hp), falls; wolf feeds, crows arrive', row_predator),
        ('INJURED', 'bandage + sling + crutch, limp walk, healer treats, healed sparkle', row_injury),
        ('DISEASE', 'healthy -> infected (no symptoms) -> sick (pale-green skin, sweat, cough) -> bedridden -> immune or grave', None),
        ('CONTAGION', 'patient zero coughs, cloud drifts, neighbours infected one by one; rat carrier; quarantine flag', row_contagion)]

if __name__ == '__main__':
    S = 4
    data = []
    for (n, d, fn) in ROWS:
        if n == 'DISEASE': fr, _ = row_disease()
        else: fr = fn()
        data.append((n, d, fr))
    G, LW, TH = 12, 0, 92
    pw, ph = PW_ * S, PH_ * S
    W_ = 5 * (pw + G) + G
    H_ = TH + len(data) * (ph + 50 + G)
    out = Image.new('RGB', (W_, H_), (18, 22, 28)); dr = ImageDraw.Draw(out)
    dr.text((G, 30), 'LIFE & DEATH ANIMATIONS  -  5 KEY BEATS PER ACTION (2x DETAIL)', fill=(240, 228, 200), font=ImageFont.load_default(size=32), anchor='lm')
    dr.text((G, 66), 'clean & readable on a phone: hit flash, damage numbers, status bubbles, hp bars. no gore.', fill=(150, 160, 175), font=ImageFont.load_default(size=20), anchor='lm')
    gif_frames = []
    for r, (n, d, fr) in enumerate(data):
        y = TH + r * (ph + 50 + G)
        dr.text((G, y + 14), n, fill=(232, 180, 106), font=ImageFont.load_default(size=24), anchor='lm')
        dr.text((G + 150, y + 14), d, fill=(200, 205, 212), font=ImageFont.load_default(size=18), anchor='lm')
        for k, fimg in enumerate(fr):
            out.paste(Image.fromarray(fimg).resize((pw, ph), Image.NEAREST), (G + k * (pw + G), y + 36))
    out.save('anim_life_death.png'); print(out.size)
    # animated gif: all 5 actions playing at once (2 columns grid)
    S2 = 4
    cols = 2
    gw, gh = PW_ * S2, PH_ * S2
    for k in range(5):
        im = Image.new('RGB', (cols * (gw + 8) + 8, 3 * (gh + 30) + 8), (18, 22, 28)); dd = ImageDraw.Draw(im)
        for r, (n, d, fr) in enumerate(data):
            x = 8 + (r % cols) * (gw + 8); y = 8 + (r // cols) * (gh + 30)
            dd.text((x, y + 10), n, fill=(232, 180, 106), font=ImageFont.load_default(size=18), anchor='lm')
            im.paste(Image.fromarray(fr[k]).resize((gw, gh), Image.NEAREST), (x, y + 22))
        gif_frames.append(im)
    pal = gif_frames[2].quantize(colors=255, method=Image.Quantize.MAXCOVERAGE)
    q = [g.quantize(palette=pal, dither=Image.Dither.NONE) for g in gif_frames]
    q[0].save('anim_life_death.gif', save_all=True, append_images=q[1:], duration=[700, 600, 600, 700, 1100], loop=0)
    print('gif ok')
