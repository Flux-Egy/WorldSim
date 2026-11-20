import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
import air

F = lambda s: ImageFont.load_default(size=s)
BG = (18, 22, 28)
NAMES = [('fighter', 'MULTIROLE FIGHTER', 'MODERN', 'OIL+ALUMINIUM'), ('stealth', 'STEALTH FIGHTER', 'MODERN+', 'COMPOSITES'),
         ('interceptor', 'INTERCEPTOR', 'FUTURE', 'FUSION'), ('bomber', 'HEAVY BOMBER', 'MODERN', 'OIL+STEEL'),
         ('wing', 'STEALTH BOMBER', 'MODERN+', 'COMPOSITES'), ('transport', 'TRANSPORT / PARATROOPS', 'MODERN', 'OIL+ALUMINIUM'),
         ('recon', 'RECON DRONE', 'MODERN', 'SILICON'), ('loiter', 'LOITERING DRONE', 'MODERN', 'SILICON+EXPLOSIVE')]


def sky(w, h, seed):
    return grass_ground(w, h, seed, tint=(hx('#7a8a6a'), .3))


def aircraft_sheet():
    S, CW = 3, 46
    LW, TH, G = 250, 100, 6
    rows = len(NAMES) + 1
    W_ = LW + 8 * (CW * S + G) + G
    H_ = TH + rows * (CW * S + G) + 20
    out = Image.new('RGB', (W_, H_), BG); d = ImageDraw.Draw(out)
    d.text((14, 34), 'AIR FORCE ASSETS  -  8 DIRECTIONS EACH (TOP-DOWN, SHADOW = ALTITUDE)', fill=(240, 228, 200), font=F(32), anchor='lm')
    d.text((14, 72), 'flat pixel shading, light from top-left, team colour on wing tips & tail. same style rules as the ground units.', fill=(150, 160, 175), font=F(19), anchor='lm')
    for r, (n, lab, era, req) in enumerate(NAMES):
        y = TH + r * (CW * S + G)
        d.text((14, y + 40), lab, fill=(240, 228, 200), font=F(19))
        d.text((14, y + 66), era, fill=(232, 180, 106), font=F(16))
        d.text((14, y + 88), 'NEEDS ' + req, fill=(150, 160, 175), font=F(14))
        for k in range(8):
            a = sky(CW, CW, r * 8 + k)
            s = air.plane(n, k * 45, scale={'fighter': 1.5, 'stealth': 1.5, 'interceptor': 1.4, 'bomber': 1.05, 'wing': 1.05, 'transport': 1.1, 'recon': 1.5, 'loiter': 1.9}[n])
            h, w = s[1].shape
            air.shadow_of(a, s, (CW - w) // 2 + 5, (CW - h) // 2 + 6, .3)
            air.paste(a, s, (CW - w) // 2, (CW - h) // 2 - 2)
            out.paste(Image.fromarray(a).resize((CW * S, CW * S), Image.NEAREST), (LW + k * (CW * S + G), y))
    y = TH + len(NAMES) * (CW * S + G)
    d.text((14, y + 40), 'ATTACK HELICOPTER', fill=(240, 228, 200), font=F(19)); d.text((14, y + 66), 'MODERN  - 4 rotor frames', fill=(232, 180, 106), font=F(16))
    for k in range(8):
        a = sky(CW, CW, 90 + k)
        air.heli_top(a, CW // 2, CW // 2 + 8, 8, (k // 4) * 180 + 0 if k >= 4 else 0, k % 4)
        if k >= 4:
            a2 = sky(CW, CW, 90 + k); air.heli_top(a2, CW // 2, CW // 2 + 8, 8, [45, 90, 135, 225][k - 4], 0); a = a2
        out.paste(Image.fromarray(a).resize((CW * S, CW * S), Image.NEAREST), (LW + k * (CW * S + G), y))
    out.save('air_assets_aircraft.png'); print('aircraft', out.size)


def defence_sheet():
    S, PW_, PH_ = 4, 60, 42
    LW, TH, G = 270, 100, 8
    rows = [('SAM BATTERY', 'stowed / raising / ready / LAUNCH', lambda f, k: air.sam(f, 6, PH_ - 4, k), 4),
            ('RADAR', 'dish turns, sweep pings', lambda f, k: air.radar(f, 6, PH_ - 4, k), 4),
            ('FLAK GUN', 'idle / firing (airburst puffs)', lambda f, k: air.flak(f, 8, PH_ - 4, k), 2),
            ('CIWS TURRET', 'idle / tracer stream', lambda f, k: air.ciws(f, 8, PH_ - 4, k), 2),
            ('LASER DEFENCE', 'FUTURE - charging / beam', lambda f, k: air.laser_ad(f, 8, PH_ - 4, k), 2)]
    fx = [('MISSILE + SMOKE TRAIL', 4), ('MID-AIR INTERCEPT', 4), ('BOMB DROP + GROUND HIT', 4), ('FLARES', 2)]
    W_ = LW + 4 * (PW_ * S + G) + G
    H_ = TH + (len(rows) + len(fx)) * (PH_ * S + G + 8) + 44 * S + 20
    out = Image.new('RGB', (W_, H_), BG); d = ImageDraw.Draw(out)
    d.text((14, 34), 'AIR DEFENCE, FX & AIRBASE  -  ANIMATION FRAMES', fill=(240, 228, 200), font=F(32), anchor='lm')
    d.text((14, 72), 'ground units in the same 3/4 view as tanks & soldiers. radars spot planes, SAMs launch, interceptions burst mid-air.', fill=(150, 160, 175), font=F(19), anchor='lm')
    y = TH
    for (lab, sub, fn, n) in rows:
        d.text((14, y + 50), lab, fill=(240, 228, 200), font=F(19)); d.text((14, y + 76), sub, fill=(150, 160, 175), font=F(14))
        for k in range(n):
            f = grass_ground(PW_, PH_, k + len(lab), tint=(hx('#8a8a70'), .25)); fn(f, k)
            out.paste(Image.fromarray(f).resize((PW_ * S, PH_ * S), Image.NEAREST), (LW + k * (PW_ * S + G), y))
        y += PH_ * S + G + 8
    for r, (lab, n) in enumerate(fx):
        d.text((14, y + 50), lab, fill=(240, 228, 200), font=F(19))
        for k in range(n):
            f = grass_ground(PW_, PH_, 40 + r * 4 + k, tint=(hx('#8a8a70'), .25))
            if r == 0:
                air.missile(f, 14 + k * 11, 34 - k * 7, 35, trail=2 + k * 2)
            elif r == 1:
                s = air.plane('fighter', 0)
                if k == 0: air.paste(f, s, 40, 10); air.missile(f, 30, 24, 20, 4)
                else: air.boom(f, 48, 16, 1.0, k);
                if k >= 2:
                    for i in range(5): put(f, 38 + i * 3, 20 + i * 4 + k * 2, hx('#3a3e44'))
            elif r == 2:
                if k < 2:
                    for i in range(3): air.bomb(f, 14 + i * 14, 6 + k * 14 + i * 2, 3 - k)
                    for i in range(3): blend_mask(f, ellipse_mask(f.shape[:2], 15 + i * 14, 37, 2 - k * .5 + 1, 1), SHADOW, .35)
                else:
                    for i in range(3): air.boom(f, 15 + i * 14, 34, .9, k - 1 + (i % 2))
            else:
                s = air.plane('bomber', 0, scale=.8); air.paste(f, s, 24, 8); air.flares(f, 24, 18, k)
            out.paste(Image.fromarray(f).resize((PW_ * S, PH_ * S), Image.NEAREST), (LW + k * (PW_ * S + G), y))
        y += PH_ * S + G + 8
    d.text((14, y + 30), 'AIRBASE  (world building)', fill=(240, 228, 200), font=F(19))
    f = grass_ground(140, 44, 5, tint=(hx('#8a8a70'), .25)); air.airbase(f, 8, 12)
    s = air.plane('fighter', 0); air.paste(f, s, 80, 30); s2 = air.plane('fighter', 180); air.paste(f, s2, 100, 28)
    out.paste(Image.fromarray(f).resize((140 * S, 44 * S), Image.NEAREST), (LW, y))
    out.save('air_assets_defence.png'); print('defence', out.size)


if __name__ == '__main__':
    aircraft_sheet(); defence_sheet()
