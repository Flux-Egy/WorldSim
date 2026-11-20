"""Full army roster: 6 unit types per era (36), each gated by resources. Reuses weapons.py drawing kit."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from weapons import (soldier, helmet, line, catapult, cannon, tank, drone, mech, fx_arrow, fx_smoke, fx_flash, fx_flame, fx_laser,
                     fx_boom, dummy, outfit, PW_, PH_, INKC, STEEL, BRONZE, TEAM, SMOKE)
from people import person2, T
from animals import draw as adraw

B = PH_ - 3


def bg(e, k): return grass_ground(PW_, PH_, e * 13 + k, tint=(hx(['#8a9a5a', '#c8b480', '#74a753', '#8a8a70', '#7a8a6a', '#6a7a7a'][e]), .25))


def rider(f, x, mount, kind, frame=0, helm=None, lance=False, sabre=False, seed=2):
    y = B - 28 if mount == 'horse' else B - 30
    adraw(f, x, y, mount, frame, False, seed)
    ry_ = y - 8 if mount == 'horse' else y - 9
    soldier(f, x + 5, ry_, kind, 0, seed=seed)
    if helm: helmet(f, x + 5, ry_, helm)
    hx_, hy_ = x + 16, ry_ + 19
    if lance: line(f, hx_ - 4, hy_ + 1, hx_ + 18, hy_ - 6, C['wood'][2]); put(f, hx_ + 19, hy_ - 7, STEEL[2]); rect(f, hx_ + 2, hy_ - 2, 3, 2, TEAM[2])
    if sabre:
        for i in range(7): put(f, hx_ + i, hy_ - 4 - i + i * i // 8, STEEL[2])


def ram(f, x):
    shadow_ell(f, x + 11, B + 1, 12, 1.5)
    for wx in (x + 4, x + 18): dome(f, wx, B - 1, 2.2, 2.2, [C['wood'][0]] * 2 + [C['wood'][1]] * 2 + [C['wood'][2]], wx); put(f, wx, B - 1, INKC)
    rect(f, x, B - 9, 22, 6, C['wood'][1]); hline(f, x, B - 9, 22, C['wood'][2])
    for i in range(12): hline(f, x - 1 + i // 2, B - 15 + i // 2, 24 - i, R['hide'][2 + (i % 2)])
    rect(f, x + 20, B - 7, 7, 3, C['wood'][2]); rect(f, x + 26, B - 8, 2, 5, STEEL[1])


def trebuchet(f, x, frame=1):
    shadow_ell(f, x + 10, B + 1, 11, 1.4)
    rect(f, x, B - 2, 22, 2, C['wood'][1])
    line(f, x + 4, B - 2, x + 10, B - 18, C['wood'][1]); line(f, x + 16, B - 2, x + 10, B - 18, C['wood'][1])
    line(f, x + 1, B - 26, x + 22, B - 10, C['wood'][2]); rect(f, x + 19, B - 10, 5, 6, R['stone'][1]); hline(f, x + 19, B - 10, 5, R['stone'][3])
    for i in range(5): put(f, x + 1 - i, B - 26 + i * 2, hx('#c8c2b6'))


def gatling(f, x):
    shadow_ell(f, x + 8, B + 1, 9, 1.4)
    for i in range(3): line(f, x + 3, B - 7 - i, x + 15, B - 8 - i, [INKC, hx('#4a4e56'), hx('#2a2c30')][i])
    rect(f, x + 3, B - 10, 4, 4, hx('#5a4a3a'))
    for wx in (x + 3, x + 11): dome(f, wx, B - 2, 2.4, 2.4, [C['wood'][0]] * 2 + [C['wood'][1]] * 2 + [C['wood'][2]], wx); put(f, wx, B - 2, INKC)


def zeppelin(f, x, y):
    dome(f, x + 18, y + 6, 17, 6, [hx('#8a8478'), hx('#a8a294'), hx('#c8c2b4'), hx('#e2ddd2'), hx('#f4f1ea')], 3)
    for i in range(0, 34, 6): vline(f, x + 2 + i, y + 2, 9, hx('#a8a294'))
    rect(f, x + 2, y + 5, 32, 2, TEAM[2])
    for (dx, dy) in [(-1, 2), (-2, 3), (-1, 9), (-2, 9)]: put(f, x + dx, y + dy + 1, hx('#8a8478'))
    rect(f, x + 13, y + 13, 9, 3, hx('#4a3a2a')); hline(f, x + 13, y + 13, 9, hx('#6a5a44')); put(f, x + 15, y + 14, C['lit']); put(f, x + 18, y + 14, C['lit'])


def heli(f, x, y, frame=0):
    shadow_ell(f, x + 10, B + 1, 8, 1.2, .25)
    dome(f, x + 10, y + 7, 6, 4, [hx('#2e3626'), hx('#3e4832'), hx('#566244'), hx('#6e7c58'), hx('#8a9870')], 2)
    rect(f, x + 13, y + 5, 3, 3, hx('#8ad0e0')); hline(f, x - 4, y + 6, 10, hx('#3e4832')); rect(f, x - 5, y + 3, 2, 4, hx('#3e4832'))
    hline(f, x - 2, y + 1, 26, hx('#c8ced4') if frame % 2 else hx('#6a7488')); vline(f, x + 10, y + 1, 3, INKC)
    hline(f, x + 6, y + 12, 9, INKC); put(f, x + 4, y + 9, TEAM[2]); put(f, x + 5, y + 9, TEAM[3])


def howitzer(f, x):
    shadow_ell(f, x + 12, B + 1, 12, 1.5)
    line(f, x + 6, B - 6, x + 26, B - 16, hx('#3e4832')); line(f, x + 6, B - 5, x + 26, B - 15, hx('#566244')); line(f, x + 6, B - 7, x + 25, B - 17, hx('#6e7c58'))
    rect(f, x + 2, B - 6, 10, 4, hx('#3e4832')); line(f, x + 2, B - 2, x - 3, B, hx('#3e4832'))
    for wx in (x + 6, x + 12): dome(f, wx, B - 1, 2.6, 2.6, [INKC] * 2 + [hx('#3a3a40')] * 2 + [hx('#5a5a60')], wx)


def hovertank(f, x):
    blend_mask(f, ellipse_mask(f.shape[:2], x + 13, B, 13, 2), C['cyan'], .4)
    rect(f, x, B - 9, 26, 6, hx('#d8dee4')); hline(f, x, B - 9, 26, hx('#ffffff')); hline(f, x, B - 4, 26, hx('#9aa4ae'))
    for i in range(0, 26, 4): put(f, x + i + 1, B - 3, C['cyan'])
    rect(f, x + 8, B - 13, 10, 4, hx('#c8ced4')); hline(f, x + 8, B - 13, 10, hx('#ffffff')); hline(f, x + 18, B - 12, 10, hx('#6a7488'))
    put(f, x + 10, B - 12, TEAM[2]); put(f, x + 11, B - 12, TEAM[3])


def hexshield(f, cx, cy):
    for t in np.linspace(-1.2, 1.2, 40):
        put(f, int(cx + 8 * math.cos(t)), int(cy + 11 * math.sin(t)), C['cyan2'])
    blend_mask(f, ellipse_mask(f.shape[:2], cx + 2, cy, 7, 11), C['cyan'], .18)


def grenade_arc(f, x0, y0, x1, y1):
    for i in range(8):
        u = i / 7
        put(f, int(x0 + (x1 - x0) * u), int(y0 + (y1 - y0) * u - 10 * math.sin(u * math.pi)), hx('#3a3a40') if i == 7 else hx('#c8c2b6'))


def dog(f, x, frame=0):
    adraw(f, x, B - 16, 'dog', frame, False, 5)


def unit(e, k):
    f = bg(e, k)
    if e == 0:
        if k == 0: soldier(f, 4, B - 27, 'club', 1); soldier(f, 18, B - 27, 'club', 3, seed=4); dummy(f, 56, B, True)
        elif k == 1:
            soldier(f, 4, B - 27, 'sling', 0); line(f, 22, 12, 44, 16, C['wood'][2]); put(f, 45, 16, R['stone'][3]); dummy(f, 58, B, True)
        elif k == 2: soldier(f, 4, B - 27, 'sling', 0); dummy(f, 58, B, True); [put(f, 24 + i * 6, int(B - 22 - 6 * math.sin(i / 5 * math.pi)), R['stone'][3]) for i in range(6)]
        elif k == 3: dog(f, 24, 1); dog(f, 40, 3); soldier(f, 2, B - 27, 'club', 0, seed=9)
        elif k == 4:
            soldier(f, 4, B - 27, 'club', 0, seed=11); vline(f, 17, B - 18, 7, C['wood'][1]); put(f, 17, B - 19, C['fire'][1]); put(f, 17, B - 20, C['fire'][2])
            for xx in (34, 48):
                for i in range(4): put(f, xx + i, B - 12 - i, R['hide'][2])
            fx_flame(f, 36, B - 8, 14, 2)
        else:
            o = outfit('club'); o['head'] = 'feathers'; o['hcol'] = T('#6e2a22', '#8a3a30', '#a84a3a'); o['cape'] = T('#5a3a22', '#7a5434', '#9c7048')
            person2(f, 10, B - 27, 'highland', 'middle', 'adult', 'm', 0, seed=4, o_over=o)
            line(f, 21, B - 8, 26, B - 22, C['wood'][1]); rect(f, 25, B - 25, 4, 4, R['stone'][2]); put(f, 26, B - 26, R['stone'][3])
    elif e == 1:
        if k == 0:
            for i in range(3): soldier(f, 2 + i * 9, B - 27, 'hoplite', 0, seed=i)
            dummy(f, 58, B)
        elif k == 1: soldier(f, 4, B - 27, 'archer', 0); fx_arrow(f, 30, B - 21); fx_arrow(f, 44, B - 18); dummy(f, 58, B, True)
        elif k == 2:
            person2(f, 4, B - 27, 'riverland', 'middle', 'adult', 'm', 1, seed=7, o_over=outfit('archer')); helmet(f, 4, B - 27, 'bronze')
            line(f, 15, B - 8, 20, B - 22, C['wood'][2]); put(f, 20, B - 23, BRONZE[2])
            line(f, 28, B - 24, 44, B - 22, C['wood'][2]); put(f, 45, B - 22, BRONZE[2]); dummy(f, 58, B, True)
        elif k == 3: rider(f, 6, 'camel', 'archer', 1, 'bronze', lance=True); dummy(f, 60, B, True)
        elif k == 4: ram(f, 8); vline(f, 46, B - 22, 23, R['stone'][1]); rect(f, 46, B - 22, 20, 23, R['stone'][2]); hline(f, 46, B - 22, 20, R['stone'][3]); fx_smoke(f, 40, B - 8, 2)
        else:
            o = outfit('hoplite'); o['cape'] = [TEAM[0], TEAM[1], TEAM[2]]; o['head'] = 'crown_north'
            person2(f, 10, B - 27, 'riverland', 'rich', 'adult', 'm', 0, seed=2, o_over=o); helmet(f, 10, B - 27, 'bronze')
            line(f, 21, B - 8, 21, B - 22, BRONZE[2]); hline(f, 20, B - 8, 3, C['gold'])
    elif e == 2:
        if k == 0:
            for i in range(3):
                soldier(f, 2 + i * 9, B - 27, 'xbow', 0, seed=i + 3); helmet(f, 2 + i * 9, B - 27, 'kettle')
                line(f, 13 + i * 9, B - 6, 26 + i * 9, B - 30, C['wood'][2]); put(f, 26 + i * 9, B - 31, STEEL[2])
        elif k == 1:
            soldier(f, 4, B - 27, 'archer', 0, seed=5)
            for i in range(-9, 10): put(f, 18 + int(3 * math.cos(i / 9 * 1.4)), B - 18 + i, C['wood'][2])
            for j in range(3): [put(f, 26 + j * 10 + i, int(B - 24 - j * 3 + i * .2), C['wood'][2]) for i in range(5)]
            dummy(f, 60, B, True)
        elif k == 2: soldier(f, 4, B - 27, 'xbow', 0); fx_arrow(f, 32, B - 22, True); dummy(f, 58, B, True)
        elif k == 3: rider(f, 4, 'horse', 'knight', 2, 'knight', lance=True)
        elif k == 4: catapult(f, 4, B, 1); [rect(f, 22 + i * 5, int(B - 22 - 10 * math.sin(i / 8 * math.pi)), 2, 1, hx('#e8e4da')) for i in range(9)]; fx_boom(f, 66, B - 3, .6)
        else: trebuchet(f, 6); [rect(f, 30 + i * 5, int(B - 30 + i * 2), 2, 1, hx('#e8e4da')) for i in range(7)]
    elif e == 3:
        if k == 0:
            soldier(f, 4, B - 27, 'musket', 0); soldier(f, 16, B - 27, 'musket', 0, seed=5)
            fx_flash(f, 31, B - 26); fx_smoke(f, 33, B - 27, 3); dummy(f, 60, B, True)
        elif k == 1:
            soldier(f, 4, B - 27, 'musket', 0, seed=8); helmet(f, 4, B - 27, 'shako'); grenade_arc(f, 16, B - 22, 50, B - 6); fx_boom(f, 54, B - 6, .7)
        elif k == 2: cannon(f, 6, B); fx_flash(f, 23, B - 9); fx_smoke(f, 24, B - 11, 4, 1.3); dome(f, 46, B - 16, 1.6, 1.6, [INKC, INKC, hx('#2a2c30'), hx('#4a4e56'), hx('#6a6e76')], 1)
        elif k == 3: rider(f, 4, 'horse', 'gunner', 1, 'shako', sabre=True)
        elif k == 4:
            gatling(f, 8); soldier(f, -2, B - 27, 'gunner', 0, seed=3); helmet(f, -2, B - 27, 'shako')
            for i in range(4): fx_flash(f, 26 + i * 9, B - 11 - i % 2)
        else: zeppelin(f, 14, 3); [put(f, 30, 20 + i * 3, INKC) for i in range(3)]; fx_boom(f, 30, B - 4, .7)
    elif e == 4:
        if k == 0:
            soldier(f, 4, B - 27, 'rifle', 0); fx_flash(f, 20, B - 23)
            for i in range(3): hline(f, 26 + i * 12, B - 23 - i // 2, 4, hx('#ffe27a'))
            dummy(f, 60, B, True)
        elif k == 1:
            soldier(f, 4, B - 27, 'rifle', 0, seed=6); line(f, 15, B - 22, 26, B - 25, INKC); rect(f, 18, B - 25, 3, 1, hx('#8ad0e0'))
            hline(f, 28, B - 25, 34, hx('#fff2b0')); dummy(f, 62, B, True)
        elif k == 2: soldier(f, 2, B - 27, 'flame', 0); fx_flame(f, 20, B - 22, 40, 3)
        elif k == 3: tank(f, 2, B); fx_flash(f, 40, B - 12); fx_smoke(f, 41, B - 13, 3); fx_boom(f, 62, B - 6, .9)
        elif k == 4: heli(f, 18, 4, 1); [hline(f, 34 + i * 6, 14 + i * 4, 3, hx('#ffe27a')) for i in range(4)]; fx_boom(f, 60, B - 4, .7)
        else:
            o = outfit('rifle'); o['top'] = T('#c9cdd2', '#e6e9ec', '#ffffff')
            person2(f, 6, B - 27, 'highland', 'middle', 'adult', 'f', 0, seed=4, o_over=o); helmet(f, 6, B - 27, 'modern')
            rect(f, 9, B - 15, 6, 5, hx('#ffffff')); [put(f, 10 + i, B - 14 + j, hx('#3e9a4e')) for (i, j) in [(0, 0), (1, 0), (3, 0), (4, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2), (2, 3)]]
            p = np.zeros((1,)); person2(f, 30, B - 27, 'riverland', 'middle', 'adult', 'm', 0, seed=9, o_over=outfit('rifle'))
            for (dx, dy) in [(0, -6), (3, -9), (-2, -10)]: put(f, 36 + dx, B - 20 + dy, hx('#7cc46a'))
    else:
        if k == 0: soldier(f, 4, B - 27, 'laser', 0); fx_laser(f, 20, B - 23, 60); dummy(f, 60, B, True)
        elif k == 1: soldier(f, 4, B - 27, 'laser', 0, seed=3); hexshield(f, 20, B - 15)
        elif k == 2: drone(f, 10, 4, 1); drone(f, 30, 9, 0); [put(f, 18 + i * 3, 12 + i * 2, hx('#c8ced4') if i % 2 else SMOKE) for i in range(10)]; fx_boom(f, 54, B - 5, .8)
        elif k == 3: hovertank(f, 4); fx_laser(f, 30, B - 12, 66)
        elif k == 4:
            for i in range(9): drone(f, 4 + (i % 3) * 16, 2 + (i // 3) * 8, i)
            for t in np.linspace(0, 2 * math.pi, 60): put(f, int(54 + 9 * math.cos(t)), int(B - 8 + 5 * math.sin(t)), C['cyan2'])
        else: soldier(f, 2, B - 27, 'pilot', 0); mech(f, 18, B); fx_laser(f, 40, B - 13, 64); dummy(f, 64, B, True)
    return f


ERAS_ = ['STONE', 'ANCIENT', 'MEDIEVAL', 'INDUSTRIAL', 'MODERN', 'FUTURE']
ROLES = ['INFANTRY', 'RANGED', 'RANGED 2', 'MOUNTED / BEAST', 'SIEGE / FIRE', 'ELITE / SPECIAL']
U = [[('CLUB WARBAND', 'WOOD'), ('SPEAR THROWER', 'WOOD'), ('SLINGER', 'STONE'), ('WAR DOGS', 'TAMED DOGS'), ('TORCH RAIDERS', 'FIRE'), ('CHIEFTAIN', 'TRIBE 50+')],
     [('BRONZE PHALANX', 'COPPER+TIN'), ('ARCHER', 'WOOD'), ('JAVELINEER', 'COPPER'), ('CAMEL LANCER', 'CAMELS'), ('BATTERING RAM', 'WOOD+HIDE'), ('WAR KING', 'GOLD')],
     [('PIKEMEN', 'IRON'), ('LONGBOWMAN', 'YEW WOOD'), ('CROSSBOWMAN', 'IRON'), ('KNIGHT LANCER', 'IRON+HORSES'), ('CATAPULT', 'WOOD+STONE'), ('TREBUCHET', 'WOOD+ENGINEERS')],
     [('MUSKET LINE', 'IRON+SALTPETER'), ('GRENADIER', 'GUNPOWDER'), ('FIELD CANNON', 'IRON+COAL'), ('HUSSARS', 'HORSES+IRON'), ('GATLING GUN', 'STEEL'), ('ZEPPELIN', 'HYDROGEN+STEEL')],
     [('RIFLEMAN', 'STEEL'), ('SNIPER', 'STEEL+OPTICS'), ('FLAMETHROWER', 'OIL'), ('TANK', 'STEEL+OIL'), ('GUNSHIP', 'OIL+ALUMINIUM'), ('FIELD MEDIC', 'MEDICINE')],
     [('LASER TROOPER', 'ENERGY CELLS'), ('SHIELD BEARER', 'ENERGY CELLS'), ('STRIKE DRONES', 'SILICON'), ('HOVER TANK', 'FUSION'), ('DRONE SWARM + EMP', 'SILICON+AI'), ('EXO-MECH', 'FUSION+ALLOYS')]]

if __name__ == '__main__':
    S = 3; G = 10; TH = 96; LW = 150
    pw, ph = PW_ * S, PH_ * S
    W_ = LW + 6 * (pw + G) + G
    H_ = TH + 6 * (ph + 62 + G)
    out = Image.new('RGB', (W_, H_), (18, 22, 28)); d = ImageDraw.Draw(out)
    d.text((G, 32), 'ARMY ROSTER  -  6 UNIT TYPES PER ERA (36)', fill=(240, 228, 200), font=ImageFont.load_default(size=34), anchor='lm')
    d.text((G, 70), 'a nation only fields what it can supply: no iron = no knights, no oil = no tanks. mixes of eras happen when a rich and a poor nation fight.',
           fill=(150, 160, 175), font=ImageFont.load_default(size=19), anchor='lm')
    for e in range(6):
        y = TH + e * (ph + 62 + G)
        d.text((G, y + 34 + ph // 2), ERAS_[e], fill=(232, 180, 106), font=ImageFont.load_default(size=24), anchor='lm')
        for k in range(6):
            x = LW + k * (pw + G)
            n, req = U[e][k]
            d.text((x, y + 14), n, fill=(240, 228, 200), font=ImageFont.load_default(size=17), anchor='lm')
            out.paste(Image.fromarray(unit(e, k)).resize((pw, ph), Image.NEAREST), (x, y + 28))
            d.text((x, y + 28 + ph + 14), 'NEEDS ' + req, fill=(124, 196, 106) if e < 2 else (200, 180, 120), font=ImageFont.load_default(size=14), anchor='lm')
    out.save('army_roster.png'); print(out.size)
