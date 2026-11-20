"""Characters (fine grid). Sprite box 9x15; body anchored at (x+1, y+2). Light from top-left."""
import random
from lib import *

SKIN = [hx('#f0c9a3'), hx('#e0b48c'), hx('#c58e63'), hx('#8d5a3b'), hx('#6b4229')]
HAIR = [hx('#2b211b'), hx('#5a3a22'), hx('#a8763d'), hx('#1c1c22'), hx('#d8cdb8')]
ROLES = ['poor', 'rich', 'chief', 'soldier', 'worker', 'scholar']
ROLE_NAMES = {'poor': 'COMMONER', 'rich': 'WEALTHY', 'chief': 'LEADER', 'soldier': 'SOLDIER', 'worker': 'WORKER/MINER', 'scholar': 'SCHOLAR'}


def T(c1, c2, c3): return [hx(c1), hx(c2), hx(c3)]


K = R['K']
# (top ramp, bottom color/'skin'/'robe', hat, item, cape, extra)
SPEC = [
    {'poor': (T('#6e5034', '#93714b', '#b79262'), 'skin', None, None, None, None),
     'rich': (T('#8a6a45', '#b8946a', '#d9bd8c'), 'skin', None, None, None, 'beads'),
     'chief': (T('#6e5034', '#93714b', '#b79262'), 'skin', 'feathers', 'staff', T('#5a3a22', '#7a5434', '#9c7048'), 'paint'),
     'soldier': (T('#5d4229', '#7d5c3a', '#9e7a50'), 'skin', None, 'spear', None, 'paint'),
     'worker': (T('#6e5034', '#93714b', '#b79262'), 'skin', None, 'stonehammer', None, None),
     'scholar': ([K[1], K[2], K[3]], 'robe', 'bones', 'fstaff', None, 'paint')},
    {'poor': (T('#b9ad95', '#d8ccb2', '#ece3cf'), 'skin', None, None, None, None),
     'rich': (T('#22406e', '#2f5a96', '#4579bb'), 'robe', 'circlet', None, None, 'gold_belt'),
     'chief': ([K[1], K[2], K[3]], 'robe', 'crown', 'staff', T('#a8752a', '#d19a3a', '#ecc25c'), 'gold_belt'),
     'soldier': (T('#8a6a45', '#b8946a', '#d9bd8c'), 'skin', 'bronze', 'spear', None, 'shield_bronze'),
     'worker': (T('#b9ad95', '#d8ccb2', '#ece3cf'), 'skin', None, 'pick', None, None),
     'scholar': (T('#c9c2b0', '#e8e2d0', '#f6f1e2'), 'robe', None, 'scroll', None, None)},
    {'poor': (T('#4f3a28', '#6b4f36', '#8a6a4a'), hx('#4a4038'), 'hood', None, None, 'patch'),
     'rich': (T('#45285e', '#5f3a80', '#7d52a3'), hx('#2b2c30'), 'plume', None, None, 'gold_belt'),
     'chief': ([K[1], K[2], K[3]], hx('#2b2c30'), 'crown', 'sword', [K[0], K[1], K[2]], 'gold_belt'),
     'soldier': (T('#6c747c', '#8b939a', '#b4bac0'), hx('#6c747c'), 'knight', 'sword', None, 'shield_K'),
     'worker': (T('#5a3a22', '#7a5434', '#9c7048'), hx('#3a3530'), None, 'hammer', None, 'apron'),
     'scholar': (T('#4a3628', '#6b4c34', '#8c6844'), 'robe', 'tonsure', 'book', None, None)},
    {'poor': (T('#5a5d63', '#74787f', '#91959b'), hx('#3a3530'), 'flatcap', None, None, 'suspenders'),
     'rich': (T('#1c1c22', '#2b2c34', '#3d3e48'), hx('#1c1c22'), 'tophat', 'cane', None, 'white_shirt'),
     'chief': (T('#1c1c22', '#2b2c34', '#3d3e48'), hx('#1c1c22'), 'tophat', None, None, 'sash'),
     'soldier': ([K[1], K[2], K[3]], hx('#e8e2d0'), 'shako', 'musket', None, 'white_belt'),
     'worker': (T('#2f4766', '#3f5f86', '#5878a0'), hx('#2f4766'), 'lamp', 'pick', None, None),
     'scholar': (T('#5a4630', '#7a6044', '#9a7c5a'), hx('#3a3530'), None, 'book', None, 'glasses')},
    {'poor': (T('#4d5258', '#676d74', '#838a92'), hx('#2f4766'), None, None, None, 'hood_down'),
     'rich': (T('#1e2a44', '#2c3b5e', '#3e5079'), hx('#1e2a44'), None, 'briefcase', None, 'tie'),
     'chief': (T('#1c1c22', '#2b2c34', '#3d3e48'), hx('#1c1c22'), None, None, None, 'tie_K'),
     'soldier': (T('#4a5236', '#5f6a45', '#78845a'), hx('#4a5236'), 'helmet', 'rifle', None, 'camo'),
     'worker': (T('#d9661e', '#f08a2c', '#ffb050'), hx('#2f4766'), 'hardhat', None, None, 'hivis'),
     'scholar': (T('#c9cdd2', '#e6e9ec', '#ffffff'), hx('#2f4766'), None, 'tablet', None, None)},
    {'poor': (T('#b9c0c7', '#d9dee3', '#f2f5f7'), hx('#b9c0c7'), None, None, None, 'cyanline'),
     'rich': (T('#1c1f26', '#2a2f3a', '#3c4352'), hx('#1c1f26'), 'visor', None, None, 'cyanline'),
     'chief': (T('#d9dee3', '#eef1f4', '#ffffff'), 'robe', 'circlet', None, T('#a8752a', '#d19a3a', '#ecc25c'), 'cyanline'),
     'soldier': (T('#262b33', '#343a44', '#474f5b'), hx('#262b33'), 'exo', 'erifle', None, 'cyanline'),
     'worker': (T('#d9661e', '#f08a2c', '#ffb050'), hx('#d9661e'), 'visor', 'drone', None, None),
     'scholar': (T('#c9cdd2', '#e6e9ec', '#ffffff'), 'robe', 'visor', 'holo', None, None)},
]


def person(a, x, y, era, role, pose=0, seed=0, shadow=True):
    """Draw at sprite box top-left (x,y). Box 9x15. Feet at y+14."""
    top, bottom, hat, item, cape, extra = SPEC[era][role]
    r = random.Random(seed * 31 + era * 7 + ROLES.index(role))
    skin, hair = r.choice(SKIN), r.choice(HAIR[:4])
    if role in ('chief', 'scholar') and era >= 2 and r.random() < .5: hair = HAIR[4]
    X, Y = x + 1, y + 2
    if shadow: shadow_ell(a, X + 3.5, Y + 12.2, 3.6, 1.2, .35)
    # cape (behind)
    if cape:
        for yy in range(Y + 4, Y + 11): put(a, X + 1, yy, cape[1]); put(a, X + 5, yy, cape[0])
        hline(a, X + 1, Y + 11, 5, cape[0])
    # head
    hline(a, X + 2, Y, 3, hair); put(a, X + 1, Y + 1, hair); put(a, X + 2, Y + 1, hair)
    put(a, X + 3, Y + 1, skin); put(a, X + 4, Y + 1, skin)
    put(a, X + 1, Y + 2, hair); put(a, X + 2, Y + 2, lit(skin, .08)); put(a, X + 3, Y + 2, skin); put(a, X + 4, Y + 2, hx('#2a1d14'))
    put(a, X + 2, Y + 3, lit(skin, -.12)); put(a, X + 3, Y + 3, skin); put(a, X + 4, Y + 3, lit(skin, -.08))
    # torso
    for yy in range(Y + 4, Y + 8):
        put(a, X + 2, yy, top[2]); put(a, X + 3, yy, top[1]); put(a, X + 4, yy, top[0])
    put(a, X + 2, Y + 4, lit(top[2], .1))
    # arms (swing)
    la, ra = (0, 0) if pose == 0 else (-1, 1)
    for yy in range(Y + 4 + max(la, 0), Y + 7 + la): put(a, X + 1, yy, top[2])
    for yy in range(Y + 4 + max(ra, 0), Y + 7 + ra): put(a, X + 5, yy, top[0])
    put(a, X + 1, Y + 7 + la, skin); put(a, X + 5, Y + 7 + ra, lit(skin, -.1))
    # belt row
    hline(a, X + 2, Y + 8, 3, lit(top[0], -.25))
    # legs / robe
    if bottom == 'robe':
        hline(a, X + 2, Y + 8, 3, top[1])
        for yy in (Y + 9, Y + 10):
            put(a, X + 1, yy, top[2]); put(a, X + 2, yy, top[2]); put(a, X + 3, yy, top[1]); put(a, X + 4, yy, top[0]); put(a, X + 5, yy, top[0])
        hline(a, X + 1, Y + 11, 5, lit(top[0], -.15))
        put(a, X + 2, Y + 12, hx('#26201c')); put(a, X + 4, Y + 12, hx('#26201c'))
    else:
        leg = skin if bottom == 'skin' else bottom
        legd = lit(leg, -.18)
        if bottom == 'skin':
            hline(a, X + 2, Y + 8, 3, top[0])
        if pose == 0:
            put(a, X + 2, Y + 9, leg); put(a, X + 4, Y + 9, legd); put(a, X + 2, Y + 10, leg); put(a, X + 4, Y + 10, legd)
            put(a, X + 2, Y + 11, leg); put(a, X + 4, Y + 11, legd)
            put(a, X + 2, Y + 12, hx('#26201c')); put(a, X + 4, Y + 12, hx('#26201c'))
        else:
            hline(a, X + 2, Y + 9, 3, leg); put(a, X + 1, Y + 10, leg); put(a, X + 5, Y + 10, legd)
            put(a, X + 1, Y + 11, leg); put(a, X + 5, Y + 11, legd)
            put(a, X + 1, Y + 12, hx('#26201c')); put(a, X + 5, Y + 12, hx('#26201c'))
    # extras
    G = C['gold']
    if extra == 'beads': hline(a, X + 2, Y + 4, 3, G); put(a, X + 3, Y + 5, hx('#3fb39a'))
    if extra == 'paint': put(a, X + 2, Y + 2, K[2]); put(a, X + 3, Y + 2, K[3])
    if extra == 'gold_belt': hline(a, X + 2, Y + 8, 3, G)
    if extra == 'patch': put(a, X + 3, Y + 6, hx('#8a6a4a')); put(a, X + 4, Y + 5, hx('#4f3a28'))
    if extra == 'apron': rect(a, X + 2, Y + 6, 3, 4, hx('#3a2a1e')); put(a, X + 2, Y + 6, hx('#5a4430'))
    if extra == 'suspenders': vline(a, X + 2, Y + 4, 4, hx('#3a3530')); vline(a, X + 4, Y + 4, 4, hx('#3a3530'))
    if extra == 'white_shirt': vline(a, X + 3, Y + 4, 3, hx('#ece6da'))
    if extra == 'sash': put(a, X + 2, Y + 4, K[3]); put(a, X + 3, Y + 5, K[2]); put(a, X + 4, Y + 6, K[2]); put(a, X + 4, Y + 7, K[1]); vline(a, X + 3, Y + 4, 1, hx('#ece6da'))
    if extra == 'white_belt': put(a, X + 2, Y + 4, hx('#ece6da')); put(a, X + 3, Y + 5, hx('#ece6da')); put(a, X + 4, Y + 6, hx('#ece6da')); hline(a, X + 2, Y + 8, 3, hx('#ece6da'))
    if extra == 'glasses': put(a, X + 3, Y + 2, hx('#e8eef6')); put(a, X + 4, Y + 2, hx('#2a1d14'))
    if extra == 'hood_down': hline(a, X + 2, Y + 4, 3, lit(top[1], -.2))
    if extra == 'tie': vline(a, X + 3, Y + 4, 3, hx('#ece6da')); put(a, X + 3, Y + 5, K[2]); put(a, X + 3, Y + 6, K[1])
    if extra == 'tie_K': vline(a, X + 3, Y + 4, 4, K[2]); put(a, X + 3, Y + 4, hx('#ece6da')); put(a, X + 2, Y + 5, G)
    if extra == 'camo': put(a, X + 3, Y + 5, hx('#3a3f2a')); put(a, X + 2, Y + 7, hx('#6b5a3a')); put(a, X + 4, Y + 4, hx('#3a3f2a'))
    if extra == 'hivis': hline(a, X + 1, Y + 6, 5, hx('#e8eef6')); hline(a, X + 2, Y + 8, 3, hx('#2f4766'))
    if extra == 'cyanline': vline(a, X + 3, Y + 4, 5, C['cyan']); put(a, X + 3, Y + 4, C['cyan2'])
    if extra == 'shield_bronze':
        dome(a, X + .5, Y + 6.5, 2.2, 2.6, R['gold']); put(a, X + .5, Y + 6, hx('#6b4a12'))
    if extra == 'shield_K':
        rect(a, X - 1, Y + 4, 3, 5, K[2]); vline(a, X - 1, Y + 4, 5, K[3]); put(a, X, Y + 9, K[1]); vline(a, X, Y + 5, 3, hx('#ece6da')); hline(a, X - 1, Y + 6, 3, hx('#ece6da'))
    # hats
    if hat == 'feathers':
        for i, c in enumerate([K[2], G, hx('#ece6da'), K[3], G]):
            put(a, X + 1 + i, Y - 1 - (i % 2), c); put(a, X + 1 + i, Y - (i % 2) * 0, c)
        hline(a, X + 1, Y, 5, K[1])
    if hat == 'bones': put(a, X + 1, Y - 1, hx('#ece6da')); put(a, X + 5, Y - 1, hx('#ece6da')); hline(a, X + 2, Y, 3, hx('#ece6da'))
    if hat == 'circlet': hline(a, X + 1, Y + 1, 4, G); put(a, X + 3, Y + 1, hx('#3fb39a'))
    if hat == 'crown':
        hline(a, X + 1, Y, 5, G); put(a, X + 1, Y - 1, G); put(a, X + 3, Y - 1, G); put(a, X + 5, Y - 1, G); put(a, X + 3, Y, K[2])
    if hat == 'bronze':
        hline(a, X + 1, Y - 1, 4, R['gold'][2]); hline(a, X + 1, Y, 5, R['gold'][1]); put(a, X + 1, Y + 1, R['gold'][1]); put(a, X + 2, Y - 1, R['gold'][4])
        put(a, X + 3, Y - 2, K[2]); put(a, X + 2, Y - 2, K[3])
    if hat == 'hood':
        hline(a, X + 1, Y - 1, 4, top[1]); for_ = [put(a, X + 1, Y + i, top[2]) for i in range(0, 4)]; put(a, X + 2, Y, top[1]); hline(a, X + 2, Y, 3, top[1])
    if hat == 'plume': hline(a, X + 1, Y, 5, hx('#2b2c30')); put(a, X + 1, Y - 1, hx('#2b2c30')); put(a, X + 4, Y - 1, hx('#ece6da')); put(a, X + 5, Y - 2, hx('#ece6da')); put(a, X + 6, Y - 2, K[2])
    if hat == 'knight':
        rect(a, X + 1, Y - 1, 5, 5, R['metal'][3]); vline(a, X + 1, Y - 1, 5, R['metal'][4]); vline(a, X + 5, Y - 1, 5, R['metal'][1])
        hline(a, X + 3, Y + 1, 3, hx('#14110e')); put(a, X + 3, Y - 2, K[2]); put(a, X + 4, Y - 2, K[2])
    if hat == 'tonsure': hline(a, X + 2, Y, 3, lit(skin, .05)); put(a, X + 1, Y + 1, hair)
    if hat == 'flatcap': hline(a, X + 1, Y, 5, hx('#55575e')); put(a, X + 6, Y + 1, hx('#3d3e44')); put(a, X + 2, Y - 1, hx('#6d6f78'))
    if hat == 'tophat':
        rect(a, X + 2, Y - 4, 3, 4, hx('#141418')); hline(a, X + 1, Y, 5, hx('#141418')); hline(a, X + 2, Y - 1, 3, K[2] if role == 'chief' else hx('#55575e')); put(a, X + 2, Y - 4, hx('#3d3e48'))
    if hat == 'shako':
        rect(a, X + 2, Y - 3, 3, 4, hx('#1c1c22')); hline(a, X + 1, Y, 5, hx('#1c1c22')); put(a, X + 3, Y - 2, G); put(a, X + 3, Y - 4, hx('#ece6da'))
    if hat == 'lamp':
        hline(a, X + 1, Y, 5, hx('#2f4766')); hline(a, X + 2, Y - 1, 3, hx('#3f5f86')); put(a, X + 4, Y - 1, C['lit']); put(a, X + 5, Y - 1, hx('#fff2c4'))
    if hat == 'helmet':
        hline(a, X + 1, Y, 5, hx('#4a5236')); hline(a, X + 2, Y - 1, 3, hx('#5f6a45')); put(a, X + 2, Y - 1, hx('#78845a'))
    if hat == 'hardhat':
        hline(a, X + 1, Y, 6, hx('#e8b42c')); hline(a, X + 2, Y - 1, 3, hx('#ffd34a')); put(a, X + 2, Y - 1, hx('#fff0a0'))
    if hat == 'visor':
        hline(a, X + 1, Y, 5, W['dark'][1]); hline(a, X + 2, Y + 2, 3, C['cyan']); put(a, X + 4, Y + 2, C['cyan2'])
    if hat == 'exo':
        rect(a, X + 1, Y - 1, 5, 4, W['dark'][2]); hline(a, X + 2, Y + 1, 4, C['cyan']); put(a, X + 5, Y + 1, C['cyan2']); vline(a, X + 1, Y - 1, 4, W['dark'][1])
        hline(a, X + 1, Y + 4, 5, W['dark'][2])
    # held items (right hand at X+5,Y+7)
    hxp, hyp = X + 6, Y + 7 + ra
    wd = C['wood']
    if item == 'spear':
        vline(a, hxp, Y - 3, 14, wd[2]); put(a, hxp, Y - 4, R['metal'][4]); put(a, hxp, Y - 3, R['metal'][3])
        if era == 1: put(a, hxp, Y - 4, R['gold'][3])
    if item == 'staff':
        vline(a, hxp, Y - 1, 13, wd[1]); dome(a, hxp + .5, Y - 2, 1.4, 1.4, R['gold'] if era else [K[1], K[2], K[3], K[3], K[4]])
    if item == 'fstaff':
        vline(a, hxp, Y - 1, 13, wd[1]); put(a, hxp, Y - 2, hx('#ece6da')); put(a, hxp + 1, Y - 2, K[3]); put(a, hxp - 1, Y - 1, G)
    if item == 'sword': vline(a, hxp, hyp - 5, 5, R['metal'][4]); hline(a, hxp - 1, hyp, 3, G); put(a, hxp, hyp + 1, wd[1])
    if item == 'pick':
        vline(a, hxp, hyp - 4, 6, wd[2]); hline(a, hxp - 1, hyp - 5, 3, R['metal'][3]); put(a, hxp - 2, hyp - 4, R['metal'][2]); put(a, hxp + 2, hyp - 4, R['metal'][2])
    if item == 'hammer': vline(a, hxp, hyp - 3, 4, wd[2]); rect(a, hxp - 1, hyp - 4, 3, 2, R['metal'][2])
    if item == 'stonehammer': vline(a, hxp, hyp - 3, 4, wd[2]); rect(a, hxp - 1, hyp - 4, 2, 2, R['stone'][3])
    if item == 'scroll': rect(a, hxp - 1, hyp - 1, 2, 3, hx('#f3e6c8')); put(a, hxp - 1, hyp - 1, hx('#c9a35a'))
    if item == 'book': rect(a, hxp - 1, hyp - 1, 2, 3, K[1] if era == 2 else hx('#2f5a96')); put(a, hxp - 1, hyp - 1, hx('#ece6da'))
    if item == 'cane': vline(a, hxp, hyp, 5, hx('#141418')); put(a, hxp, hyp - 1, G)
    if item == 'musket':
        for i in range(9): put(a, hxp - 2 + i // 2 * 0 + (i // 3), hyp - 7 + i, hx('#2b2c30') if i < 6 else wd[1])
        put(a, hxp - 2, hyp - 8, R['metal'][4])
    if item == 'rifle':
        for i in range(7): put(a, hxp - 2 + i // 2, hyp - 4 + i, hx('#2b2c30') if i < 5 else hx('#4a5236'))
    if item == 'erifle':
        for i in range(7): put(a, hxp - 2 + i // 2, hyp - 4 + i, W['dark'][0])
        put(a, hxp - 2, hyp - 5, C['cyan'])
    if item == 'briefcase': rect(a, hxp - 1, hyp + 1, 3, 2, hx('#3a2a1e')); put(a, hxp, hyp, hx('#3a2a1e'))
    if item == 'tablet': rect(a, hxp - 1, hyp - 2, 2, 3, hx('#1c1f26')); put(a, hxp - 1, hyp - 2, C['cyan'])
    if item == 'holo': rect(a, hxp, hyp - 4, 3, 2, C['cyan']); put(a, hxp, hyp - 4, C['cyan2'])
    if item == 'drone': drone(a, hxp + 1, Y - 3) if False else (put(a, hxp + 1, Y - 3, hx('#2b2c30')), put(a, hxp, Y - 4, hx('#55575e')), put(a, hxp + 2, Y - 4, hx('#55575e')), put(a, hxp + 1, Y - 4, C['cyan']))


# ---------------- animals ----------------
def sheep(a, x, y, pose=0):
    shadow_ell(a, x + 5, y + 7, 4.4, 1.2, .3)
    dome(a, x + 4.5, y + 3.2, 4.2, 3, ramp('#b8b4a8', '#d4d0c4', '#e8e5da', '#f6f4ee', '#ffffff'))
    rect(a, x + 8, y + 2, 2, 3, hx('#2b2620')); put(a, x + 9, y + 3, hx('#14110e')); put(a, x + 8, y + 1, hx('#3d362e'))
    for lx in ((2, 6) if pose == 0 else (3, 5)): vline(a, x + lx, y + 6, 2, hx('#2b2620'))


def cow(a, x, y, pose=0):
    shadow_ell(a, x + 6, y + 8, 5.5, 1.3, .3)
    rect(a, x + 1, y + 2, 9, 4, hx('#ece6da')); hline(a, x + 1, y + 2, 9, hx('#ffffff'))
    rect(a, x + 3, y + 2, 3, 2, hx('#2b2c30')); rect(a, x + 7, y + 4, 2, 2, hx('#2b2c30')); hline(a, x + 1, y + 5, 9, hx('#c9c2b0'))
    rect(a, x + 10, y + 1, 2, 3, hx('#ece6da')); put(a, x + 11, y + 3, hx('#e8a0a0')); put(a, x + 10, y, hx('#c9c2b0')); put(a, x + 12, y, hx('#c9c2b0'))
    put(a, x, y + 3, hx('#2b2c30'))
    for lx in ((2, 4, 7, 9) if pose == 0 else (1, 5, 6, 10)): vline(a, x + lx, y + 6, 2, hx('#3a3530'))


def horse(a, x, y, pose=0, col=None):
    col = col or ramp('#5a3a22', '#7a5434', '#9c7048')
    shadow_ell(a, x + 6, y + 9, 5.5, 1.3, .3)
    rect(a, x + 2, y + 3, 8, 4, col[1]); hline(a, x + 2, y + 3, 8, col[2]); hline(a, x + 2, y + 6, 8, col[0])
    for i in range(3): rect(a, x + 9 + i // 2, y + 2 - i, 2, 2, col[1])
    rect(a, x + 10, y - 1, 3, 2, col[1]); put(a, x + 12, y, col[0]); put(a, x + 11, y - 2, col[0])
    vline(a, x + 9, y - 1, 4, hx('#1c1612')); put(a, x + 1, y + 3, hx('#1c1612')); put(a, x, y + 4, hx('#1c1612')); put(a, x, y + 5, hx('#1c1612'))
    for lx in ((3, 5, 8, 9) if pose == 0 else (2, 6, 7, 10)): vline(a, x + lx, y + 7, 2, col[0]); put(a, x + lx, y + 9, hx('#1c1612'))


def deer(a, x, y, pose=0):
    col = ramp('#8a5a32', '#ad7442', '#c99460')
    shadow_ell(a, x + 5, y + 9, 4.5, 1.2, .3)
    rect(a, x + 1, y + 4, 7, 3, col[1]); hline(a, x + 1, y + 4, 7, col[2]); put(a, x, y + 4, hx('#ece6da'))
    rect(a, x + 7, y + 2, 2, 3, col[1]); rect(a, x + 8, y + 1, 2, 2, col[1]); put(a, x + 9, y + 2, hx('#14110e'))
    for (dx, dy) in [(7, 0), (8, -1), (9, 0), (10, -1), (6, -1), (8, -2), (10, -2)]: put(a, x + dx, y + dy, hx('#d6c3a0'))
    for lx in ((2, 6) if pose == 0 else (1, 7)): vline(a, x + lx, y + 7, 3, col[0])
    for lx in ((3, 7) if pose == 0 else (3, 5)): vline(a, x + lx, y + 7, 3, col[0])


def wolf(a, x, y, pose=0):
    col = ramp('#55575e', '#73767e', '#9a9da4')
    shadow_ell(a, x + 5, y + 7, 4.8, 1.2, .3)
    rect(a, x + 2, y + 2, 7, 3, col[1]); hline(a, x + 2, y + 2, 7, col[2]); hline(a, x + 3, y + 4, 5, hx('#c9c2b0'))
    rect(a, x + 8, y + 1, 3, 2, col[1]); put(a, x + 11, y + 2, col[0]); put(a, x + 8, y, col[2]); put(a, x + 10, y + 1, hx('#ffd34a'))
    put(a, x + 1, y + 2, col[1]); put(a, x, y + 3, col[2])
    for lx in ((3, 7) if pose == 0 else (2, 8)): vline(a, x + lx, y + 5, 2, col[0])
    for lx in ((4, 8) if pose == 0 else (4, 6)): vline(a, x + lx, y + 5, 2, col[0])


def chicken(a, x, y, pose=0):
    shadow_ell(a, x + 2, y + 4, 2, .8, .25)
    rect(a, x, y + 1, 4, 2, hx('#f2efe6')); put(a, x + 3, y, hx('#f2efe6')); put(a, x + 3, y - 1, hx('#d5452d')); put(a, x + 4, y + 1, hx('#e8a43a'))
    vline(a, x + (1 if pose == 0 else 2), y + 3, 1, hx('#e8a43a'))


def camel(a, x, y, pose=0):
    col = ramp('#a8865c', '#c4a275', '#dcbd92')
    shadow_ell(a, x + 6, y + 10, 5.5, 1.3, .3)
    rect(a, x + 1, y + 4, 9, 3, col[1]); hline(a, x + 1, y + 4, 9, col[2])
    dome(a, x + 4, y + 3.5, 2.2, 2, ramp('#8c6b45', '#a8865c', '#c4a275', '#dcbd92', '#efd9b4'))
    for i in range(4): put(a, x + 10, y + 3 - i, col[1]); put(a, x + 11, y + 3 - i, col[0])
    rect(a, x + 10, y - 2, 3, 2, col[1]); put(a, x + 12, y - 1, col[0])
    for lx in ((2, 4, 7, 9) if pose == 0 else (1, 5, 6, 10)): vline(a, x + lx, y + 7, 3, col[0])


def robodog(a, x, y, pose=0):
    shadow_ell(a, x + 5, y + 7, 4.5, 1.2, .3)
    rect(a, x + 2, y + 2, 7, 3, W['white'][1]); hline(a, x + 2, y + 2, 7, W['white'][2]); hline(a, x + 2, y + 4, 7, W['dark'][1])
    rect(a, x + 8, y, 3, 3, W['white'][2]); put(a, x + 10, y + 1, C['cyan']); put(a, x + 1, y + 2, W['dark'][1])
    for lx in ((3, 7) if pose == 0 else (2, 8)): vline(a, x + lx, y + 5, 2, W['dark'][0])


ANIMALS = [('SHEEP', sheep, 11, 9), ('COW', cow, 13, 9), ('HORSE', horse, 13, 11), ('DEER', deer, 12, 11),
           ('WOLF', wolf, 12, 8), ('CHICKEN', chicken, 6, 6), ('CAMEL', camel, 13, 12), ('ROBO-DOG', robodog, 12, 8)]
