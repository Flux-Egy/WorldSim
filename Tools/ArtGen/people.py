"""2x-detail paper-doll people: culture x class x age x gender (+ era outfits), 4-frame walk.
Sprite box 16 x 28 fine px, feet on the bottom row. 3/4 view facing right, light from top-left."""
import random
import numpy as np
from lib import *

DARK = hx('#1a1410')
SKINS = {'riverland': ['#8a5a3a', '#9e6a44', '#b07a50', '#7a4e32'], 'northern': ['#e8c4a4', '#f0d0b4', '#dcb090', '#e4bc9c'],
         'highland': ['#c89a74', '#d4a882', '#b88a66', '#dcb48e']}
HAIRS = {'riverland': ['#1a1410', '#2a1e16', '#1e1812'], 'northern': ['#d8b46a', '#c8743a', '#e6cc8a', '#a8642e'],
         'highland': ['#3a2618', '#5a3a22', '#2a1e16', '#7a4a26']}
GREY = hx('#c8c4bc')
OVERRIDE = {'skin': None, 'hair': None}   # used by the asset exporter for recolour masks


def T(a, b, c): return [hx(a), hx(b), hx(c)]


# outfit: top ramp, bottom ('pants'/'robe'/'dress'/'kilt'/'wrap'), bottom ramp, shoes, head, item, extras
def outfit(culture, cls, gender, age, era=2):
    m = gender == 'm'
    if era != 2: return ERA_OUTFIT[era](culture, cls, gender)
    if culture == 'riverland':
        if cls == 'poor':
            return dict(top=T('#9a8a6c', '#b8a886', '#d2c4a2'), bot='robe' if m else 'dress', brp=None, shoes=None,
                        head='skullcap' if m else 'scarf', hcol=T('#6a5a44', '#8a7a5e', '#a89878'), item=('basket' if m else 'jug'), ex=['patch'])
        if cls == 'middle':
            return dict(top=T('#c8c2b4', '#e2ddd2', '#f4f1ea'), bot='robe' if m else 'dress', brp=None, shoes=hx('#7a5434'),
                        head='turban' if m else 'scarf', hcol=T('#1f4d4f', '#2b6a6a', '#3a8a86') if m else T('#2b4a7a', '#3a62a0', '#5a82c0'),
                        item='staff' if m else None, ex=['trim_teal'])
        if cls == 'rich':
            return dict(top=T('#1f4d4f', '#2b6a6a', '#3a8a86') if m else T('#6a2a5a', '#8a3a76', '#a85a94'), bot='robe' if m else 'dress', brp=None,
                        shoes=hx('#c8a050'), head='turban' if m else 'veil', hcol=T('#c9c2b4', '#e8e4da', '#ffffff') if m else T('#c8a050', '#e0bc6a', '#f0d48a'),
                        item=None, ex=['trim_gold', 'necklace'])
        return dict(top=T('#e2ddd2', '#f4f1ea', '#ffffff'), bot='robe', brp=None, shoes=hx('#c8a050'), head='crown_river',
                    hcol=T('#1f4d4f', '#2b6a6a', '#3a8a86'), item='crook', ex=['collar_gold', 'trim_gold'], cape=T('#1f4d4f', '#2b6a6a', '#3a8a86'))
    if culture == 'northern':
        if cls == 'poor':
            return dict(top=T('#5a4a3a', '#73604c', '#8c7860'), bot='pants' if m else 'dress', brp=T('#4a3e32', '#5e5040', '#73644f'), shoes=hx('#3a2a1e'),
                        head=None if m else 'kerchief', hcol=T('#6a5a44', '#8a7a5e', '#a89878'), item='axe' if m else 'bucket', ex=['patch', 'legwrap'])
        if cls == 'middle':
            return dict(top=T('#2b4a7a', '#3a62a0', '#5a82c0') if m else T('#7a2a24', '#9a3a30', '#b85444'), bot='pants' if m else 'dress',
                        brp=T('#4a3e32', '#5e5040', '#73644f') if m else T('#5a4a3a', '#73604c', '#8c7860'), shoes=hx('#4a3020'),
                        head=None, hcol=None, item=None, ex=['legwrap', 'belt_brass', 'braids' if not m else 'beard'])
        if cls == 'rich':
            return dict(top=T('#7a2a24', '#9a3a30', '#b85444') if m else T('#2b5a3a', '#3a7a4e', '#5a9a68'), bot='pants' if m else 'dress',
                        brp=T('#3a3a40', '#4e4e56', '#64646c') if m else T('#2b5a3a', '#3a7a4e', '#5a9a68'), shoes=hx('#2a1e16'),
                        head=None, hcol=None, item=None, ex=['furcollar', 'brooch', 'braids' if not m else 'beard'], cape=T('#5a4632', '#7a6044', '#9a7c5a'))
        return dict(top=T('#2b4a7a', '#3a62a0', '#5a82c0'), bot='pants', brp=T('#3a3a40', '#4e4e56', '#64646c'), shoes=hx('#2a1e16'),
                    head='crown_north', hcol=None, item='axe_royal', ex=['furcollar', 'beard', 'belt_brass'], cape=T('#d8d2c4', '#ece8de', '#ffffff'))
    # highland
    plaid = {'poor': T('#4a5a3a', '#5e7048', '#76885c'), 'middle': T('#2a4a6a', '#3a6086', '#5a7ea0'), 'rich': T('#6a2020', '#8a2a2a', '#a84040'),
             'ruler': T('#4a2a5e', '#5f3a80', '#7d52a3')}[cls]
    if cls == 'poor':
        return dict(top=T('#6a5a48', '#84725c', '#9e8a72'), bot='kilt' if m else 'dress', brp=plaid, shoes=None,
                    head='bonnet' if m else 'shawl', hcol=plaid if not m else T('#3a3a40', '#4e4e56', '#64646c'), item='crook' if m else 'basket', ex=['patch', 'plaid'])
    if cls == 'middle':
        return dict(top=T('#c8c2b4', '#e2ddd2', '#f4f1ea'), bot='kilt' if m else 'dress', brp=plaid, shoes=hx('#3a2a1e'),
                    head='bonnet' if m else None, hcol=T('#2a3a5a', '#3a4e74', '#52688e'), item=None, ex=['plaid', 'sash_plaid', 'socks'])
    if cls == 'rich':
        return dict(top=T('#1e2430', '#2a3240', '#3c4656'), bot='kilt' if m else 'dress', brp=plaid, shoes=hx('#1e1812'),
                    head='bonnet' if m else 'cap_lace', hcol=T('#1e2430', '#2a3240', '#3c4656'), item='sword' if m else None, ex=['plaid', 'sash_plaid', 'brooch', 'socks', 'trim_silver'])
    return dict(top=T('#1e2430', '#2a3240', '#3c4656'), bot='kilt', brp=plaid, shoes=hx('#1e1812'), head='circlet', hcol=None, item='sword',
                ex=['plaid', 'sash_plaid', 'brooch', 'socks', 'trim_gold'], cape=plaid)


def _era(top, bot, brp, shoes, head, hcol, item, ex, cape=None):
    return dict(top=top, bot=bot, brp=brp, shoes=shoes, head=head, hcol=hcol, item=item, ex=ex, cape=cape)


ERA_OUTFIT = {
    0: lambda c, k, g: _era(T('#6e5034', '#93714b', '#b79262'), 'wrap', T('#6e5034', '#93714b', '#b79262'), None, None, None, 'spear', ['bone']),
    1: lambda c, k, g: _era(T('#c9c2b0', '#e8e2d0', '#f6f1e2'), 'robe' if g == 'm' else 'dress', None, hx('#a87a44'), 'band', T('#1f4d4f', '#2b6a6a', '#3a8a86'), None, ['collar_gold']),
    3: lambda c, k, g: _era(T('#4a4e56', '#5e646e', '#787e88'), 'pants' if g == 'm' else 'dress', T('#2e3036', '#3c3f46', '#4c5058'), hx('#1e1812'),
                            'flatcap' if g == 'm' else 'bonnet_v', T('#3a3a40', '#4e4e56', '#64646c') if g == 'm' else T('#6a2a5a', '#8a3a76', '#a85a94'), None, ['vest', 'white_shirt']),
    4: lambda c, k, g: _era(T('#2a6a8a', '#3a86a8', '#5aa4c4') if g == 'm' else T('#a83a4a', '#c8505e', '#e0707a'), 'pants', T('#22344e', '#2e4666', '#40587e'),
                            hx('#e8e4dc'), None, None, 'phone', []),
    5: lambda c, k, g: _era(T('#c9cdd2', '#e6e9ec', '#ffffff'), 'pants', T('#b0b6bc', '#ccd2d8', '#e4e8ec'), hx('#5a6068'), None, None, None, ['cyanline']),
}


def person2(a, x, y, culture, cls, age, gender, frame=0, seed=0, era=2, shadow=True, og=None, state=None, o_over=None):
    r = random.Random(seed)
    if o_over is not None:
        o = o_over; skin = hx(r.choice(SKINS[culture])); hair = hx(r.choice(HAIRS[culture]))
    elif og is not None:
        from culturegen import outfit_from
        o = outfit_from(og, cls, gender); skin = hx(r.choice(og['skins'])); hair = hx(r.choice(og['hairs']))
        if og.get('paint'): o['ex'] = o['ex'] + ['facepaint']
    else:
        o = outfit(culture, cls if cls != 'ruler' else 'ruler', gender, age, era)
        skin = hx(r.choice(SKINS[culture])); hair = hx(r.choice(HAIRS[culture]))
    if OVERRIDE.get('skin') is not None: skin = OVERRIDE['skin']
    if OVERRIDE.get('hair') is not None: hair = OVERRIDE['hair']
    if state == 'sick': skin = tuple(int(v) for v in (np.array(skin) * .62 + np.array(hx('#9ab07a')) * .38))
    if age == 'elder': hair = GREY
    sk = [lit(skin, -.2), skin, lit(skin, .1)]
    m = gender == 'm'
    child, elder = age == 'child', age == 'elder'
    # proportions
    if child: hw, hh, tw, th, lh = 6, 5, 6, 4, 4
    else: hw, hh, tw, th, lh = 6, 6, 8, 7, 7
    H = 28
    feet = y + H - 2
    legtop = feet - lh
    ttop = legtop - th - 1
    htop = ttop - hh - 1 + (1 if elder else 0)
    cx = x + 7
    tx = cx - tw // 2
    hx0 = cx - hw // 2 + (1 if elder else 0)
    sw = [1, 0, -1, 0][frame]
    bob = 1 if frame in (1, 3) else 0
    feet_y = feet
    if bob: htop -= 1; ttop -= 1; legtop -= 1
    if shadow: shadow_ell(a, cx + 1, feet + 1, 4.5 if not child else 3.4, 1.3, .32)
    top, brp = o['top'], o['brp'] or o['top']
    # cape behind
    if o.get('cape'):
        cp = o['cape']
        for yy in range(ttop, feet - 1):
            hline(a, tx - 1, yy, tw + 2, cp[0] if yy > ttop + 2 else cp[1])
        hline(a, tx - 1, ttop, tw + 2, cp[2])
    # long hair behind shoulders
    if not m and o['head'] not in ('scarf', 'veil', 'shawl', 'kerchief') and not elder:
        rect(a, hx0 - 1, htop + 1, hw, hh - 2, lit(hair, -.12)); rect(a, hx0 - 1, htop + hh - 1, 3, (4 if not child else 2), lit(hair, -.12))
    # ---- legs / lower garment
    bot = o['bot']
    shoes = o['shoes'] or lit(skin, -.25)
    lx1, lx2 = tx + 1, tx + tw - 3
    if bot in ('pants', 'wrap', 'kilt'):
        for (lx, s_, dark) in ((lx1, -sw, False), (lx2, sw, True)):
            col = brp if bot == 'pants' else sk
            for yy in range(legtop, feet_y):
                u = (yy - legtop) / max(1, lh)
                xx = int(round(lx + s_ * u * 1.5))
                rect(a, xx, yy, 2, 1, col[0] if dark else col[1]); put(a, xx, yy, col[1] if dark else col[2])
                if 'socks' in o['ex'] and yy >= legtop + lh // 2 - 1 and yy < feet_y: rect(a, xx, yy, 2, 1, hx('#e8e2d4') if not dark else hx('#c8c2b4'))
                if 'legwrap' in o['ex'] and yy > legtop + 1 and (yy - legtop) % 2: rect(a, xx, yy, 2, 1, hx('#a89878') if not dark else hx('#8a7a5e'))
            xx = int(round(lx + s_ * 1.5))
            rect(a, xx, feet_y, 3 if not child else 2, 1, shoes if not dark else lit(shoes, -.2))
        if bot == 'pants':
            hline(a, tx + 1, legtop, tw - 2, brp[1])
        if bot == 'kilt':
            kl = (lh + 1) // 2 + 1
            for yy in range(legtop - 1, legtop + kl):
                ww = tw + (1 if yy > legtop else 0)
                for xx in range(tx - (yy > legtop) // 1 * 0, tx + ww):
                    c = brp[2] if xx < tx + 2 else brp[0] if xx > tx + tw - 3 else brp[1]
                    if 'plaid' in o['ex'] and ((xx - tx) % 3 == 0 or (yy - legtop) % 3 == 0): c = lit(c, -.25) if (xx + yy) % 2 else lit(c, .2)
                    put(a, xx, yy, c)
        if bot == 'wrap':
            rect(a, tx, legtop - 1, tw, 3, brp[1]); hline(a, tx, legtop - 1, tw, brp[2])
            for xx in range(tx, tx + tw, 2): put(a, xx, legtop + 2, brp[0])
    else:  # robe / dress: trapezoid to the ankles
        for yy in range(legtop - 1, feet_y):
            sp = (yy - legtop) // 3 + 1
            x0, x1 = tx - sp + 1 + (1 if bot == 'robe' else 0), tx + tw + sp - 1 - (1 if bot == 'robe' else 0)
            for xx in range(x0, x1):
                c = brp[2] if xx < x0 + 2 else brp[0] if xx > x1 - 3 else brp[1]
                if (xx - x0 + yy) % 7 == 0 and yy > legtop + 1: c = lit(c, -.12)  # folds
                put(a, xx, yy, c)
        for (lx, s_) in ((lx1, -sw), (lx2, sw)):
            if s_ != 0 or frame in (0, 2): rect(a, lx + s_ + (1 if s_ > 0 else 0), feet_y, 2, 1, shoes)
        rect(a, lx1, feet_y, 2, 1, shoes) if sw == 0 else None
        hem = feet_y - 1
        if 'trim_gold' in o['ex'] or 'trim_teal' in o['ex']:
            tc = C['gold'] if 'trim_gold' in o['ex'] else hx('#3a8a86')
            sp = (hem - legtop) // 3 + 1
            for xx in range(tx - sp + 2, tx + tw + sp - 2): put(a, xx, hem, tc)
    # ---- torso
    for yy in range(ttop, ttop + th + 1):
        for xx in range(tx, tx + tw):
            c = top[2] if xx < tx + 2 else top[0] if xx > tx + tw - 3 else top[1]
            put(a, xx, yy, c)
    hline(a, tx + 1, ttop, tw - 2, lit(top[2], .08))
    put(a, tx + tw // 2, ttop, sk[1]); put(a, tx + tw // 2 + 1, ttop, sk[0])  # neckline
    belt_y = ttop + th
    if bot in ('pants', 'kilt', 'wrap') or 'belt_brass' in o['ex']:
        hline(a, tx, belt_y, tw, lit(top[0], -.35))
        if 'belt_brass' in o['ex']: put(a, tx + tw // 2, belt_y, C['gold'])
    # ---- arms (swing opposite to legs)
    for (ax_, s_, col) in ((tx - 2, sw, top[2]), (tx + tw, -sw, top[0])):
        for i in range(th - (0 if not child else 1)):
            xx = ax_ + (s_ if i > th // 2 else 0)
            rect(a, xx, ttop + 1 + i, 2, 1, col)
        hand_x = ax_ + s_; hand_y = ttop + th - (0 if not child else 1) + 1
        rect(a, hand_x, hand_y, 2, 1, sk[1] if ax_ < tx else sk[0])
    rhx, rhy = tx + tw - sw, ttop + th + 1
    # ---- extras on torso
    ex = o['ex']
    if 'patch' in ex: rect(a, tx + 2, ttop + 3, 2, 2, lit(top[1], -.22)); put(a, tx + tw - 2, ttop + 5, lit(top[1], .2))
    if 'necklace' in ex: hline(a, tx + 2, ttop + 1, tw - 4, C['gold']); put(a, tx + tw // 2, ttop + 2, hx('#3fb39a'))
    if 'collar_gold' in ex:
        hline(a, tx, ttop + 1, tw, C['gold']); hline(a, tx + 1, ttop + 2, tw - 2, hx('#3a8a86')); hline(a, tx + 2, ttop + 3, tw - 4, C['gold'])
    if 'trim_gold' in ex and bot in ('pants', 'kilt'): hline(a, tx, ttop + th - 1, tw, C['gold'])
    if 'trim_silver' in ex: hline(a, tx, ttop + th - 1, tw, hx('#c8ccd2'))
    if 'furcollar' in ex:
        for xx in range(tx - 1, tx + tw + 1): put(a, xx, ttop, hx('#d8ccb4') if xx % 2 else hx('#b8a88c')); put(a, xx, ttop + 1, hx('#a89878') if xx % 2 else hx('#d8ccb4'))
    if 'brooch' in ex: put(a, tx + 1, ttop + 2, C['gold']); put(a, tx + 2, ttop + 2, hx('#c83a3a'))
    if 'sash_plaid' in ex:
        for i in range(th): put(a, tx + 1 + i * (tw - 2) // th, ttop + i, brp[1]); put(a, tx + 2 + i * (tw - 2) // th, ttop + i, brp[2])
    if 'vest' in ex:
        rect(a, tx, ttop + 1, 2, th - 1, hx('#2a2c32')); rect(a, tx + tw - 2, ttop + 1, 2, th - 1, hx('#1e2024'))
    if 'white_shirt' in ex: vline(a, tx + tw // 2, ttop + 1, th - 2, hx('#ece6da'))
    if 'cyanline' in ex: vline(a, tx + tw // 2, ttop, th + 1, C['cyan']); hline(a, tx, belt_y, tw, C['cyan'])
    if 'bone' in ex: put(a, tx + 2, ttop + 1, hx('#ece4d2')); put(a, tx + 4, ttop + 1, hx('#ece4d2')); put(a, tx + 3, ttop + 2, hx('#c83a3a'))
    # ---- head
    for yy in range(htop, htop + hh):
        for xx in range(hx0, hx0 + hw):
            c = sk[2] if xx < hx0 + 2 and yy < htop + hh - 2 else sk[0] if xx == hx0 + hw - 1 or yy == htop + hh - 1 else sk[1]
            put(a, xx, yy, c)
    # hair cap
    hline(a, hx0, htop - 1, hw, hair); hline(a, hx0 - 1, htop, hw + 1, lit(hair, .12)); put(a, hx0 - 1, htop + 1, hair); put(a, hx0, htop + 1, hair)
    if not m or child: put(a, hx0 - 1, htop + 2, hair)
    if elder: put(a, hx0 - 1, htop + 2, hair); hline(a, hx0 + 1, htop - 1, 2, sk[1])  # thinning
    ey = htop + (2 if child else 3)
    put(a, hx0 + 3, ey, DARK); put(a, hx0 + 5, ey, DARK)
    if child: put(a, hx0 + 3, ey + 1, DARK); put(a, hx0 + 5, ey + 1, DARK)
    put(a, hx0 + 4, ey + 2 - child, lit(skin, -.28))  # nose shadow/mouth
    put(a, hx0 + 1, ey, sk[0])  # ear
    if elder: put(a, hx0 + 2, ey - 1, lit(skin, -.15)); put(a, hx0 + 5, ey + 2, lit(skin, -.15))
    if m and not child and ('beard' in ex or elder or (culture == 'riverland' and cls != 'poor')):
        for xx in range(hx0 + 2, hx0 + hw): put(a, xx, htop + hh - 1, hair if not elder else GREY)
        put(a, hx0 + 3, htop + hh, hair if not elder else GREY); put(a, hx0 + 4, htop + hh, lit(hair, -.1) if not elder else lit(GREY, -.1))
    if 'facepaint' in ex:
        put(a, hx0 + 2, ey + 1, hx('#c83a3a')); put(a, hx0 + 5, ey + 1, hx('#c83a3a'))
    if 'braids' in ex:
        vline(a, hx0 - 1, htop + 2, hh + 3, hair); vline(a, hx0 + hw, htop + 2, hh + 2, lit(hair, -.15))
        put(a, hx0 - 1, htop + hh + 4, hx('#c83a3a'))
    # ---- headwear
    hd, hc = o['head'], o['hcol']
    if hd == 'turban':
        for i in range(3):
            hline(a, hx0 - 1, htop - 2 + i, hw + 1, hc[2 - (i % 2)]); put(a, hx0 + i * 2, htop - 2 + i, hc[0])
        hline(a, hx0, htop - 3, hw - 1, hc[2])
    elif hd == 'skullcap':
        hline(a, hx0, htop - 1, hw, hc[1]); hline(a, hx0 - 1, htop, hw + 1, hc[2])
    elif hd in ('scarf', 'veil', 'shawl', 'kerchief'):
        drop = {'scarf': hh + 2, 'veil': hh + 5, 'shawl': hh + 3, 'kerchief': 2}[hd]
        hline(a, hx0, htop - 2, hw, hc[2]); hline(a, hx0 - 1, htop - 1, hw + 2, hc[2]); hline(a, hx0 - 1, htop, hw + 2, hc[1])
        vline(a, hx0 - 1, htop + 1, drop, hc[1]); vline(a, hx0 - 2, htop + 2, drop - 1, hc[0])
        if hd != 'kerchief': vline(a, hx0 + hw, htop + 1, min(2, drop), hc[0])
        if hd == 'veil': put(a, hx0 + 1, htop - 1, C['gold']); put(a, hx0 + 3, htop - 1, C['gold'])
        if hd == 'shawl' and 'plaid' in ex:
            for yy in range(htop - 1, htop + drop): put(a, hx0 - 1, yy, lit(hc[1], -.25) if yy % 3 == 0 else hc[1])
    elif hd == 'bonnet':
        hline(a, hx0 - 1, htop - 1, hw + 2, hc[1]); hline(a, hx0, htop - 2, hw, hc[2]); hline(a, hx0 + 1, htop - 3, hw - 2, hc[1])
        put(a, hx0 + hw - 1, htop - 3, hx('#c83a3a'))  # pompom
    elif hd == 'cap_lace':
        hline(a, hx0, htop - 2, hw, hx('#f4f0e8')); hline(a, hx0 - 1, htop - 1, hw + 2, hx('#e2ddd2'))
    elif hd == 'crown_river':
        for xx in range(hx0 - 1, hx0 + hw + 1): vline(a, xx, htop - 4, 4, hc[1] if xx > hx0 + 2 else hc[2])
        for xx in range(hx0 - 1, hx0 + hw + 1, 2): put(a, xx, htop - 4, C['gold'])
        hline(a, hx0 - 1, htop - 1, hw + 2, C['gold']); put(a, hx0 + hw, htop - 3, C['gold'])
        vline(a, hx0 - 2, htop, hh + 2, hc[1])
    elif hd == 'crown_north':
        hline(a, hx0 - 1, htop - 1, hw + 2, C['gold'])
        for xx in (hx0 - 1, hx0 + 2, hx0 + hw): put(a, xx, htop - 2, C['gold']); put(a, xx, htop - 3, lit(C['gold'], .2))
        put(a, hx0 + 2, htop - 1, hx('#3a62a0'))
    elif hd == 'circlet':
        hline(a, hx0 - 1, htop, hw + 2, C['gold']); put(a, hx0 + 3, htop, hx('#7d52a3'))
    elif hd == 'band':
        hline(a, hx0 - 1, htop, hw + 2, hc[1]); put(a, hx0 + 2, htop, C['gold'])
    elif hd == 'feathers':
        hline(a, hx0 - 1, htop, hw + 2, hc[1] if hc else hx('#8a3a30'))
        for i, c in enumerate((hx('#e8c84a'), hx('#c83a3a'), hx('#f0ece0'))): vline(a, hx0 + i * 2, htop - 4 + i % 2, 4 - i % 2, c)
    elif hd == 'furhat':
        for yy in range(htop - 3, htop + 1):
            for xx in range(hx0 - 1, hx0 + hw + 1): put(a, xx, yy, hx('#b8a07a') if (xx + yy) % 2 else hx('#8a7454'))
        hline(a, hx0, htop - 4, hw - 1, hx('#a08860')); put(a, hx0 + hw - 2, htop - 4, hc[1] if hc else hx('#c83a3a'))
    elif hd == 'hood':
        hline(a, hx0, htop - 2, hw, hc[2]); hline(a, hx0 - 1, htop - 1, hw + 2, hc[1]); vline(a, hx0 - 1, htop, hh, hc[1]); vline(a, hx0 - 2, htop + 1, hh, hc[0])
    elif hd == 'flatcap':
        hline(a, hx0 - 1, htop - 1, hw + 2, hc[1]); hline(a, hx0, htop - 2, hw - 1, hc[2]); hline(a, hx0 + hw - 1, htop, 2, hc[0])
    elif hd == 'bonnet_v':
        hline(a, hx0 - 1, htop - 2, hw + 2, hc[2]); hline(a, hx0 - 2, htop - 1, hw + 3, hc[1]); put(a, hx0 + 1, htop - 3, hx('#e8e2d4'))
    # ---- held item (right hand)
    it = o['item']
    if child or elder: it = 'cane' if elder else None
    if it == 'staff' or it == 'crook' or it == 'cane':
        h = 16 if it != 'cane' else 9
        vline(a, rhx + 2, rhy - h + 3, h, C['wood'][2] if it != 'cane' else hx('#8a6a44'))
        if it == 'crook': put(a, rhx + 3, rhy - h + 2, C['wood'][2]); put(a, rhx + 3, rhy - h + 3, C['wood'][1])
        if it == 'cane': hline(a, rhx + 1, rhy - 6, 2, hx('#8a6a44'))
    elif it == 'basket':
        rect(a, rhx + 1, rhy, 4, 3, hx('#b8944e')); hline(a, rhx + 1, rhy, 4, hx('#d2ae66')); put(a, rhx + 2, rhy - 1, hx('#8a6a3a'))
        put(a, rhx + 2, rhy, hx('#c83a3a')); put(a, rhx + 3, rhy, hx('#e8c84a'))
    elif it == 'jug':  # carried on the head
        rect(a, hx0 + 1, htop - 6, 4, 4, hx('#a8603a')); hline(a, hx0 + 1, htop - 6, 4, hx('#c87a4a')); put(a, hx0 + 2, htop - 7, hx('#8a4a2a'))
        vline(a, tx - 2 + sw, htop - 2, ttop - htop + 2, top[2])
    elif it == 'bucket':
        rect(a, rhx + 1, rhy, 3, 3, hx('#7a6a54')); hline(a, rhx + 1, rhy + 1, 3, hx('#4e4e56')); put(a, rhx + 2, rhy - 1, hx('#4e4e56'))
    elif it in ('axe', 'axe_royal'):
        vline(a, rhx + 2, rhy - 9, 11, C['wood'][2])
        rect(a, rhx + 3, rhy - 9, 2, 3, hx('#b4bac0')); put(a, rhx + 4, rhy - 10, hx('#d8dde2'))
        if it == 'axe_royal': put(a, rhx + 2, rhy - 10, C['gold']); rect(a, rhx + 3, rhy - 9, 3, 4, hx('#d8dde2'))
    elif it == 'sword':
        vline(a, rhx + 2, rhy - 7, 8, hx('#c8ccd2')); hline(a, rhx + 1, rhy + 1, 3, C['gold']); put(a, rhx + 2, rhy + 2, hx('#5a3a22'))
    elif it == 'spear':
        vline(a, rhx + 2, rhy - 16, 18, C['wood'][2]); put(a, rhx + 2, rhy - 17, hx('#9a948a')); put(a, rhx + 2, rhy - 18, hx('#c8c2b6'))
    elif it == 'phone':
        rect(a, rhx + 1, rhy - 1, 2, 3, hx('#1e2024')); put(a, rhx + 1, rhy - 1, hx('#6ac0e8'))
    return feet


CLASSES = ['poor', 'middle', 'rich', 'ruler']
