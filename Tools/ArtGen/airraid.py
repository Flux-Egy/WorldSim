"""Animated air raid over a modern city: bombers + escorts vs interceptors, radar, SAM launches, mid-air intercepts, bombs."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
import air, scenes
from catalog import fine_fx

RED, BLUE = R['K'], K2['blue']
N = 14


def base():
    a, occ, fx = scenes.build_scene(4, 1, seed=3)
    f = upscale(a, 2); fine_fx(f, fx, 2); scenes.populate(f, occ, 4, 1, seed=3)
    return f


def frames():
    B = base()
    H, W = B.shape[:2]
    out = []
    rng = random.Random(4)
    craters = []
    for k in range(N):
        f = B.copy()
        # ground air defence (blue side, bottom right) on a concrete pad
        rect(f, 190, 150, 98, 42, hx('#8a8c86')); hline(f, 190, 150, 98, hx('#a8aaa2'))
        for xx in range(196, 288, 12): vline(f, xx, 152, 38, hx('#7a7c76'))
        air.radar(f, 214, 184, k % 4)
        air.sam(f, 240, 186, 3 if k in (3, 7) else 2)
        air.flak(f, 196, 178, k % 2 if k >= 5 else 0)
        for (cx, cy, kk) in craters:
            if k - kk < 4: air.boom(f, cx, cy, 1.6, k - kk)
            else: blend_mask(f, ellipse_mask(f.shape[:2], cx, cy, 5, 3), hx('#2a2622'), .6); blend_mask(f, ellipse_mask(f.shape[:2], cx + 2, cy - 8 - (k % 3), 3, 3), hx('#5a5650'), .5)
        # attackers (red): 2 bombers + 2 escorts, flying right
        bx = -30 + k * 16
        b1_alive = k < 6
        if b1_alive: air.fly(f, 'bomber', bx, 70, 40, 0, RED, 1.35, True)
        elif k < 10:
            for i in range(4): blend_mask(f, ellipse_mask(f.shape[:2], bx - 30 + i * 4, 30 + (k - 6) * 9 + i, 2 + i * .6, 2 + i * .5), hx('#4a4642'), .6)
            if k < 9: air.boom(f, bx - 22, 30 + (k - 6) * 9, .6, min(3, k - 6))
        air.fly(f, 'bomber', bx - 26, 120, 44, 0, RED, 1.35, True)
        if k in (6, 7): air.flares(f, bx - 40, 76, k - 6)
        e_alive = k < 9
        if e_alive: air.fly(f, 'fighter', bx + 28, 52, 38, 0 if k < 6 else -20, RED, 1.9, True)
        air.fly(f, 'fighter', bx + 20, 140, 40, 0, RED, 1.9, True)
        # defenders (blue) interceptors from right, turning
        dx = W + 30 - k * 20
        ang = 180 if k < 7 else 200
        air.fly(f, 'interceptor', dx, 40, 36, ang, BLUE, 1.8, True)
        air.fly(f, 'stealth', dx + 18, 92, 36, 180, BLUE, 1.9, True)
        # SAM missiles
        if 3 <= k <= 5:
            t = (k - 3) / 2
            mx, my = 246 + (bx + 4 - 246) * t, 168 + (30 - 168) * t
            if k < 5: air.missile(f, mx, my, 135 + 10, trail=6 + k * 2, big=True)
        if k == 5: air.boom(f, bx + 2, 30, 1.8, 1)
        if k == 6: air.boom(f, bx - 14, 30, 1.8, 2)
        # dogfight missile from interceptor to escort
        if 6 <= k <= 8:
            t = (k - 6) / 2
            sx, sy = dx + 10, 4
            ex, ey = bx + 28, 14
            air.missile(f, sx + (ex - sx) * t, sy + (ey - sy) * t + 2, 190, trail=5, big=True)
        if k == 9: air.boom(f, bx + 12, 14, 1.5, 1)
        if k == 10: air.boom(f, bx + 10, 18, 1.5, 2)
        # bombs from bomber 2
        if 7 <= k <= 9:
            for i in range(3): air.bomb(f, bx - 34 + i * 6 - (k - 7) * 4, 82 + (k - 7) * 12 + i * 2, 3 - (k - 7))
        if k == 10:
            for i in range(3): craters.append((bx - 70 + i * 12, 128 + i * 3, k))
        # caption
        cap = ['RADAR CONTACT', 'RADAR CONTACT', 'SAM BATTERY ARMED', 'SAM LAUNCH', 'MISSILE TRACKING', 'BOMBER HIT', 'BOMBER DOWN - FLARES',
               'INTERCEPTORS ENGAGE', 'BOMBS AWAY', 'ESCORT SHOT DOWN', 'IMPACT', 'IMPACT', 'RAID REPELLED', 'RAID REPELLED'][k]
        out.append((f, cap))
    return out


if __name__ == '__main__':
    S = 3
    fr = frames()
    imgs = []
    for f, cap in fr:
        im = Image.fromarray(f).resize((f.shape[1] * S, f.shape[0] * S), Image.NEAREST)
        canvas = Image.new('RGB', (im.width, im.height + 56), (18, 22, 28)); canvas.paste(im, (0, 56))
        d = ImageDraw.Draw(canvas)
        d.text((16, 28), 'AIR RAID ON QARNAH', fill=(240, 228, 200), font=ImageFont.load_default(size=26), anchor='lm')
        d.text((im.width - 16, 28), cap, fill=(232, 180, 106), font=ImageFont.load_default(size=24), anchor='rm')
        imgs.append(canvas)
    pal = imgs[6].quantize(colors=255, method=Image.Quantize.MAXCOVERAGE)
    q = [i.quantize(palette=pal, dither=Image.Dither.NONE) for i in imgs]
    q[0].save('air_raid.gif', save_all=True, append_images=q[1:], duration=[420] * (N - 2) + [900, 900], loop=0)
    # contact sheet of 6 key frames
    keys = [0, 3, 5, 8, 10, 12]
    tw, th = imgs[0].width // 2, imgs[0].height // 2
    sheet = Image.new('RGB', (3 * tw + 4 * 10, 2 * th + 3 * 10), (18, 22, 28))
    for i, k in enumerate(keys):
        sheet.paste(imgs[k].resize((tw, th), Image.NEAREST), (10 + (i % 3) * (tw + 10), 10 + (i // 3) * (th + 10)))
    sheet.save('air_raid_frames.png'); print(sheet.size)
