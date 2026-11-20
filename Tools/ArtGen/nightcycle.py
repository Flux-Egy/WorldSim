"""Day vs night for the same city across eras: the light itself shows progress (fire -> torches -> street lamps -> neon)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from lib import *
from buildings import ERAS
from catalog import fine_fx
import scenes
from scenes import build_scene, populate, city_label

LIGHTS = [C['lit'], C['lit2'], C['fire'][0], C['fire'][1], C['fire'][2], C['cyan'], C['cyan2'], C['magenta']]


def lamps(f, era):
    """era-appropriate street lights along the main road (fine pixel coords)."""
    y = scenes.RY * 2 - 2
    pts = []
    step = {0: 52, 1: 0, 2: 46, 3: 30, 4: 22, 5: 22}[era]
    if not step: return pts
    for x in range(14, f.shape[1] - 10, step):
        if 2 * scenes.CXC - 8 < x < 2 * scenes.CXC + 12: continue
        if era == 0:   # torch stakes: wood + bound fire
            vline(f, x, y - 7, 7, C['wood'][1]); put(f, x - 1, y - 7, C['wood'][2]); put(f, x + 1, y - 7, C['wood'][2])
            put(f, x, y - 8, C['fire'][1]); put(f, x, y - 9, C['fire'][2]); put(f, x - 1, y - 8, C['fire'][0]); put(f, x + 1, y - 9, C['fire'][1])
        elif era == 2:   # torch on a pole
            vline(f, x, y - 6, 6, C['wood'][1]); put(f, x, y - 7, C['fire'][1]); put(f, x, y - 8, C['fire'][2])
        elif era == 3:  # gas lamp
            vline(f, x, y - 9, 9, hx('#2a2c30')); rect(f, x - 1, y - 12, 3, 3, C['lit']); hline(f, x - 1, y - 13, 3, hx('#2a2c30'))
        elif era == 4:  # sodium street light
            vline(f, x, y - 12, 12, hx('#5a5f66')); hline(f, x, y - 12, 4, hx('#5a5f66')); rect(f, x + 3, y - 11, 2, 1, C['lit'])
        else:          # holo pylons
            vline(f, x, y - 10, 10, hx('#d8e2ea')); rect(f, x - 1, y - 12, 3, 2, C['cyan2'])
        pts.append((x, y))
    return pts


def night(f, era, pools=()):
    a = f.astype(np.float32)
    m = np.zeros(f.shape[:2], bool)
    for c in LIGHTS: m |= np.all(f == np.array(c, np.uint8), axis=2)
    tint = {0: np.array([.20, .23, .40]), 2: np.array([.25, .28, .47]), 4: np.array([.30, .33, .52]), 5: np.array([.26, .28, .50])}[era]
    base = a * tint + np.array([6, 9, 22])
    mimg = Image.fromarray((m * 255).astype(np.uint8))
    g1 = np.asarray(mimg.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    g2 = np.asarray(mimg.filter(ImageFilter.GaussianBlur(9)), np.float32) / 255
    warm = np.array([255, 178, 92]) if era < 5 else np.array([120, 220, 255])
    glow = np.clip(g1 * 2.2 + g2 * 3.0, 0, 1.4)[..., None]
    k = .42 if era == 5 else .6
    out = base + glow * warm * k + glow * a * .5
    if pools:
        pm = np.zeros(f.shape[:2], np.float32)
        for (x, y) in pools: pm[ellipse_mask(f.shape[:2], x + 2, y + 1, 9, 4)] = 1
        pm = np.asarray(Image.fromarray((pm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] / 255
        out = out + pm * (warm * .25 + a * .55)
    for (fx_, fy_) in FIRES:
        fm = ellipse_mask(f.shape[:2], fx_, fy_, 26, 16).astype(np.float32)
        fm = np.asarray(Image.fromarray((fm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8)), np.float32)[..., None] / 255
        out = out + fm * (np.array([255, 130, 50]) * .16 + a * .32)
    out[m] = a[m]
    # moonlit rim: brighten roof tops slightly
    return np.clip(out, 0, 255).astype(np.uint8)


FIRES = []


def scene(era):
    a, occ, fx = build_scene(era, 1, seed=3)
    f = upscale(a, 2); fine_fx(f, fx, 2)
    FIRES[:] = [(e[1] * 2 + 1, e[2] * 2 - 2) for e in fx if e[0] == 'fire']
    pools = lamps(f, era)
    populate(f, occ, era, 1, seed=3)
    if era == 0:   # a few people carrying torches on the paths
        import random as _r
        rr = _r.Random(4)
        for _ in range(7):
            x, y = rr.randint(20, f.shape[1] - 20), rr.choice([scenes.RY * 2 - 1, scenes.RY * 2 + 9, rr.randint(30, f.shape[0] - 20)])
            from chars import person
            person(f, x - 4, y - 13, 0, 'poor', rr.randint(0, 1), seed=rr.randint(0, 99))
            vline(f, x + 4, y - 9, 5, C['wood'][1]); put(f, x + 4, y - 10, C['fire'][1]); put(f, x + 4, y - 11, C['fire'][2]); put(f, x + 5, y - 10, C['fire'][0])
            pools.append((x + 2, y - 4))
    city_label(f, 3, 3, 'QARNAH', ERAS[era].upper(), '')
    return f, pools


ROWS = [0, 2, 4, 5]
TXT = {0: 'campfires, torch stakes & torch-bearers', 2: 'torch poles + candle-lit windows', 4: 'sodium street lights, full windows', 5: 'holo pylons, cyan city glow'}
if __name__ == '__main__':
    S = 2
    tiles = []
    for e in ROWS:
        f, pools = scene(e)
        tiles.append((vignette(Image.fromarray(f), .1), vignette(Image.fromarray(night(f, e, pools)), .25)))
    tw, th = tiles[0][0].width * S, tiles[0][0].height * S
    TH, GAP, HH = 74, 14, 46
    out = Image.new('RGB', (2 * tw + 3 * GAP, TH + len(ROWS) * (th + HH + GAP)), (18, 22, 28))
    d = ImageDraw.Draw(out)
    fb = ImageFont.load_default(size=30); fm = ImageFont.load_default(size=22); fs = ImageFont.load_default(size=18)
    d.text((GAP, TH // 2), 'DAY / NIGHT  -  THE LIGHTS SHOW HOW FAR A NATION HAS COME', fill=(240, 228, 200), font=fb, anchor='lm')
    for r, e in enumerate(ROWS):
        y = TH + r * (th + HH + GAP)
        d.text((GAP, y + 22), f'{ERAS[e].upper()}', fill=(232, 180, 106), font=fm, anchor='lm')
        d.text((GAP + 200, y + 22), TXT[e], fill=(200, 205, 212), font=fs, anchor='lm')
        for c in range(2):
            out.paste(tiles[r][c].resize((tw, th), Image.NEAREST), (GAP + c * (tw + GAP), y + HH))
    out.save('day_night_eras.png'); print(out.size)
