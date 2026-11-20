import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
import strategic as ST, air, scenes
from catalog import fine_fx

F = lambda s: ImageFont.load_default(size=s)
BG = (18, 22, 28)


def g(w, h, s, tint='#8a8a70'): return grass_ground(w, h, s, tint=(hx(tint), .25))


def sheet():
    S, G, LW, TH = 3, 8, 330, 100
    rows = []
    rows.append(('BALLISTIC LAUNCHER (TEL)', 'travel / erect / vertical / ignition / lift-off', [(lambda a, k=k: ST.tel(a, 10, 50, k), 88, 56) for k in range(6)]))
    rows.append(('MISSILE SILO', 'closed / opening / armed / launch', [(lambda a, k=k: ST.silo(a, 18, 54, k), 88, 60) for k in range(4)]))
    rows.append(('MISSILE DEFENCE', 'interceptor battery idle / firing  +  hazard marker', [(lambda a: ST.abm_battery(a, 20, 50, 0), 88, 56), (lambda a: ST.abm_battery(a, 20, 50, 1), 88, 56),
                                                                                          (lambda a: ST.hazard_sign(a, 30, 16, 2), 88, 56)]))
    for kind, (name, sc) in ST.MISSILES.items():
        rows.append((name, '16 directions x 2 exhaust frames (8 shown)', [(lambda a, d=d, kind=kind: ST.missile_flight(a, kind, d * 45, d % 2, 40, 40), 80, 80) for d in range(8)]))
    rows.append(('RE-ENTRY WARHEAD', 'plasma glow, 2 frames', [(lambda a, k=k: ST.reentry(a, k), 40, 40) for k in range(2)]))
    rows.append(('AFTERMATH DECALS', 'shockwave x4  /  crater  /  fallout x2  /  radiation glow',
                 [(lambda a, k=k: ST.shockwave(a, k, 44, 22), 88, 44) for k in range(4)] + [(lambda a: ST.crater(a, 44, 22, .9), 88, 44)] +
                 [(lambda a, k=k: ST.fallout(a, k, 40, 22), 88, 44) for k in range(2)] + [(lambda a: ST.radiation_glow(a, 44, 22), 88, 44)]))
    maxw = max(sum(w * S + G for _, w, h in r[2]) for r in rows)
    H = TH + sum(max(h for _, w, h in r[2]) * S + 40 for r in rows)
    out = Image.new('RGB', (LW + maxw + G, H), BG); d = ImageDraw.Draw(out)
    d.text((14, 34), 'STRATEGIC WEAPONS  -  BALLISTIC & NUCLEAR MISSILES, SILOS, MISSILE DEFENCE', fill=(240, 228, 200), font=F(30), anchor='lm')
    d.text((14, 72), 'modern & future eras only. nuclear weapons need uranium + enrichment + rocketry, and every use is remembered by all nations.',
           fill=(150, 160, 175), font=F(18), anchor='lm')
    y = TH
    for (lab, sub, cells) in rows:
        hh = max(h for _, w, h in cells) * S
        d.text((14, y + hh // 2 - 10), lab, fill=(240, 228, 200), font=F(18), anchor='lm')
        d.text((14, y + hh // 2 + 14), sub[:44], fill=(150, 160, 175), font=F(13), anchor='lm')
        x = LW
        for i, (fn, w, h) in enumerate(cells):
            a = g(w, h, i + len(lab), '#7a8a6a' if 'MISSILE' not in lab and 'ICBM' not in lab and 'GLIDER' not in lab and 'INTERCEPTOR' not in lab else '#6a7a6a')
            fn(a)
            out.paste(Image.fromarray(a).resize((w * S, h * S), Image.NEAREST), (x, y))
            x += w * S + G
        y += hh + 40
    out.save('strategic_assets.png'); print('sheet', out.size)


def nuke_sequence():
    S, G = 2, 8
    frames = list(range(13))
    out = Image.new('RGB', (7 * (160 * S + G) + G, 2 * (160 * S + G) + 90), BG); d = ImageDraw.Draw(out)
    d.text((G, 34), 'NUCLEAR DETONATION  -  13 FRAMES (FLASH, FIREBALL, MUSHROOM CLOUD, DISSIPATION)', fill=(240, 228, 200), font=F(28), anchor='lm')
    d.text((G, 66), 'one 160x160 sprite strip, pivot = ground zero. shockwave, crater and fallout are separate ground decals.', fill=(150, 160, 175), font=F(17), anchor='lm')
    for i, k in enumerate(frames):
        a = g(160, 160, 5, '#7a8a6a')
        ST.nuke(a, k, 80, 150)
        x = G + (i % 7) * (160 * S + G); y = 90 + (i // 7) * (160 * S + G)
        out.paste(Image.fromarray(a).resize((160 * S, 160 * S), Image.NEAREST), (x, y))
        d.text((x + 8, y + 14), str(k), fill=(255, 255, 255), font=F(18), anchor='lm')
    out.save('nuke_sequence.png'); print('nuke seq', out.size)


def strike_gif():
    # shot A: silo launch on a remote base
    base = g(288, 192, 9, '#8a8a70')
    for x in range(20, 268, 3): put(base, x, 30, hx('#8b939a')); put(base, x, 176, hx('#8b939a'))
    for y in range(30, 177, 3): put(base, 20, y, hx('#8b939a')); put(base, 267, y, hx('#8b939a'))
    ST.abm_battery(base, 200, 160, 0)
    air.radar(base, 196, 120, 0)
    shots = []
    for k in range(4):
        f = base.copy(); ST.silo(f, 100, 140, k); shots.append((f, ['SILO HATCH OPENS', 'SILO HATCH OPENS', 'WARHEAD ARMED', 'LAUNCH'][k]))
    f = base.copy(); ST.silo(f, 100, 140, 2)
    for i in range(30): blend_mask(f, ellipse_mask(f.shape[:2], 121 + i * .3, 120 - i * 3, 2 + i * .2, 2 + i * .2), ST.SMOKE[3], .5)
    ST.missile_flight(f, 'icbm', -80, 1, 132, 22); shots.append((f, 'ICBM IN FLIGHT'))
    # shot B: target city
    a_, occ, fx = scenes.build_scene(4, 1, seed=3)
    city = upscale(a_, 2); fine_fx(city, fx, 2); scenes.populate(city, occ, 4, 1, seed=3)
    gx, gy = 150, 176
    def alert(f):
        rect(f, 6, 6, 120, 16, hx('#3a0e0e')); rect(f, 6, 6, 120, 2, hx('#e05a5a'))
        text(f, 12, 11, 'LAUNCH DETECTED', hx('#ffb0a0'))
        return f
    for k in range(2):
        f = alert(city.copy()); ST.reentry(f, k, gx + 30 - k * 12, 30 + k * 40); shots.append((f, 'INCOMING WARHEAD'))
    f = city.copy(); ST.reentry(f, 0, gx + 6, 120)
    for i in range(10): put(f, 250 - i * 9, 180 - i * 6, hx('#e8eef2'))
    shots.append((f, 'INTERCEPTOR MISSES'))
    for k in range(13):
        f = city.copy()
        if k >= 2:
            dark = np.zeros(f.shape[:2]); yy, xx = np.mgrid[0:f.shape[0], 0:f.shape[1]]
            dist = np.hypot(xx - gx, (yy - gy) * 1.5)
            burn = np.clip(1.25 - dist / (50 + min(k, 8) * 14), 0, 1) * .85
            f[:] = (f * (1 - burn[..., None]) + np.array(hx('#2a2018')) * burn[..., None]).astype(np.uint8)
        if 3 <= k <= 6: ST.shockwave(f, k - 3, gx, gy)
        ST.nuke(f, k, gx, gy)
        cap = ['DETONATION'] * 2 + ['FIREBALL'] * 3 + ['MUSHROOM CLOUD'] * 6 + ['FALLOUT DRIFTS'] * 2
        shots.append((f, cap[k]))
    # aftermath
    f = city.copy(); yy, xx = np.mgrid[0:f.shape[0], 0:f.shape[1]]
    dist = np.hypot(xx - gx, (yy - gy) * 1.5); burn = np.clip(1.3 - dist / 150, 0, 1) * .9
    f[:] = (f * (1 - burn[..., None]) + np.array(hx('#2a2018')) * burn[..., None]).astype(np.uint8)
    ST.crater(f, gx, gy, 1.0); ST.fallout(f, 1, gx - 30, gy - 30); ST.radiation_glow(f, gx, gy)
    rr = random.Random(5)
    for _ in range(26):
        x, y = gx + rr.randint(-110, 110), gy + rr.randint(-90, 10)
        if 0 < x < 286 and 4 < y < 190 and math.hypot(x - gx, (y - gy) * 1.5) < 140:
            put(f, x, y, ST.FIRE[1]); put(f, x, y - 1, ST.FIRE[2]); blend_mask(f, ellipse_mask(f.shape[:2], x + 1, y - 5, 2, 3), ST.SMOKE[1], .5)
    ST.hazard_sign(f, gx - 70, gy - 20, 1); ST.hazard_sign(f, gx + 56, gy - 24, 1)
    for _ in range(2): shots.append((f, 'AFTERMATH: IRRADIATED ZONE'))
    imgs = []
    Sx = 3
    for f, cap in shots:
        im = Image.fromarray(f).resize((f.shape[1] * Sx, f.shape[0] * Sx), Image.NEAREST)
        c = Image.new('RGB', (im.width, im.height + 56), BG); c.paste(im, (0, 56)); dd = ImageDraw.Draw(c)
        dd.text((16, 28), 'STRATEGIC STRIKE', fill=(240, 228, 200), font=F(26), anchor='lm')
        dd.text((im.width - 16, 28), cap, fill=(232, 180, 106), font=F(24), anchor='rm')
        imgs.append(c)
    pal = imgs[12].quantize(colors=255, method=Image.Quantize.MAXCOVERAGE)
    q = [i.quantize(palette=pal, dither=Image.Dither.NONE) for i in imgs]
    durs = [500] * 5 + [450] * 3 + [180, 220] + [260] * 3 + [380] * 8 + [900, 1400]
    q[0].save('nuke_strike.gif', save_all=True, append_images=q[1:], duration=durs[:len(q)], loop=0)
    print('gif', len(q))


if __name__ == '__main__':
    sheet(); nuke_sequence(); strike_gif()
