"""Action rig for people and soldiers (Phase 2).  Same pixel scale as people.person2 (adult ~27 px tall), facing right.
human(a, x, y, look, action, frame, ctx)  -> draws one frame.   look = species / gender / outfit / item / helmet ...
Colours that the runtime recolours come from ctx: ACC (clothes = culture/kingdom), ACC2 (accent), SKIN, HAIR, TEAM (soldier uniform).
Death frames are drawn here too (12 death types), so every way a human can die has its own sprites."""
import math, random
import numpy as np
from lib import *
from animals import R5, DARK

SPECIES = {
    #          skin default       leg  torso w  head  extra
    'human': dict(skin='#c89a74', lh=7, tw=8, th=7, hw=6, hh=6),
    'elf': dict(skin='#e8c8a8', lh=8, tw=7, th=7, hw=6, hh=6, ears=True),
    'orc': dict(skin='#7a9a52', lh=7, tw=10, th=8, hw=7, hh=6, tusks=True, brow=True),
    'dwarf': dict(skin='#d4a07c', lh=4, tw=10, th=7, hw=7, hh=6, beard=True),
}
OUTFITS = ['tribal', 'medieval', 'modern']

ITEMS = {   # name: (length px, colour shaft, colour head, kind)
    'axe': (8, '#8c6844', '#b4bcc4', 'axe'), 'pickaxe': (8, '#8c6844', '#9aa4ae', 'pick'), 'hoe': (9, '#8c6844', '#8a8a90', 'hoe'),
    'hammer': (6, '#8c6844', '#6a6a72', 'hammer'), 'rod': (12, '#a88a5a', '#e8e8e8', 'rod'), 'sword': (8, '#6b4c34', '#dfe4ea', 'blade'),
    'club': (7, '#6b4c34', '#4a3424', 'club'), 'spear': (13, '#8c6844', '#cfd4da', 'spear'), 'bow': (10, '#7a5430', '#e8e0c8', 'bow'),
    'xbow': (7, '#5a4430', '#9aa4ae', 'xbow'), 'musket': (11, '#5a3a22', '#4a4a50', 'gun'), 'rifle': (10, '#2a2a2e', '#3a3e44', 'gun'),
    'flamer': (9, '#4a4e44', '#c84a2a', 'gun'), 'laser': (9, '#cfd4da', '#5fe0e8', 'gun'), 'staff': (14, '#5a4430', '#9a6ae8', 'staff'),
    'torch': (6, '#6b4c34', '#ffb84a', 'torch'), 'sling': (5, '#a88a5a', '#7a7a7a', 'sling'), 'shield': (0, '#6b4c34', '#9aa4ae', 'shield'),
    'bucket': (0, '#8c6844', '#6a8ab4', 'bucket'), 'basket': (0, '#b49a5a', '#8ab45a', 'basket'), 'crate': (0, '#a8844a', '#7a5a30', 'crate'),
}


def seg(a, x0, y0, x1, y1, w, col, col2=None):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n):
        t = i / max(n - 1, 1)
        x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
        rect(a, x, y, w, 1, col)
        if col2 is not None: put(a, x + w - 1, y, col2)


# ------------------------------------------------------------------ poses
def P(**k):
    d = dict(by=0, lean=0, lf=(0, 0), rf=(0, 0), knee=0, fh=(3, 7), bh=(-2, 7), item=None, ang=0.0, head=0, sit=False, mouth=0, eyes='open', fx=None)
    d.update(k)
    return d


def pose(action, f):
    walk = [(-2, 2), (0, 0), (2, -2), (0, 0)]
    if action == 'idle': return P(by=[0, 0][f], head=[0, 1][f] * 0, fh=(3, 7), bh=(-2, 7 - f % 2 * 0))
    if action == 'walk':
        b, fr = walk[f]; return P(by=f % 2 * -1, lf=(b, 0), rf=(fr, 0), fh=(1 - b, 7), bh=(-1 + b, 7))
    if action == 'run':
        s = [(-4, 4), (-1, 1), (4, -4), (1, -1)][f]
        return P(by=-1 if f % 2 else 0, lean=2, lf=(s[0], 1 if f == 2 else 0), rf=(s[1], 1 if f == 0 else 0), fh=(4 - s[0] // 2, 4), bh=(-3 - s[1] // 2, 5))
    if action == 'flee':
        s = [(-4, 4), (-1, 1), (4, -4), (1, -1)][f]
        return P(by=-1 if f % 2 else 0, lean=2, lf=(s[0], 0), rf=(s[1], 0), fh=(2, -4 - f % 2), bh=(-1, -4 + f % 2), mouth=2, fx='sweat')
    if action == 'limp': return P(lean=-1, fh=(0, 3), bh=(-3, 4), eyes='shut')
    if action == 'hurt': return P(lean=-2, by=0, fh=(0, 2), bh=(-4, 3), head=1, mouth=1, eyes='shut', fx='blood')
    if action == 'cheer': return P(by=[-2, 0][f], fh=(3, [-6, -4][f]), bh=(-3, [-6, -4][f]), mouth=2)
    if action == 'talk': return P(fh=(4, [4, 3][f]), bh=(-2, 7), mouth=[1, 0][f])
    if action == 'eat': return P(fh=([2, 1][f], [5, 1][f]), bh=(-2, 7), mouth=[0, 1][f], item='food')
    if action == 'cower': return P(by=5, knee=4, fh=(1, -2), bh=(-1, -2), head=3, eyes='shut', fx='shake' if f else None)
    if action == 'sick': return P(by=2, knee=1, lean=1, fh=(2, 3), bh=(-1, 4), head=2, mouth=[0, 1][f], eyes='shut', fx='sick')
    if action == 'possessed': return P(by=[-1, -2][f], fh=(6, 1), bh=(-5, 1), eyes='glow', head=-1)
    if action == 'grabbed': return P(by=0, lf=([-2, 2][f], -2), rf=([2, -2][f], -1), fh=(3, -5), bh=(-3, -5 + f), mouth=2, fx='sweat')
    if action == 'ride': return P(by=4, sit=True, fh=(4, 4), bh=(-1, 6))
    if action == 'sleep': return P(eyes='shut', fh=(2, 7), bh=(-2, 7), fx='zz' if f else None)
    if action == 'swim':
        return P(by=8, lean=3, fh=([6, 2, -2, 2][f], [1, -1, 1, 3][f]), bh=([-4, -1, 3, -1][f], [2, 0, 2, 3][f]), fx='water')
    if action == 'drown': return P(by=[10, 12, 14, 18][f], fh=(2, [-6, -8, -6, -10][f]), bh=(-2, [-7, -5, -8, -9][f]), mouth=2, fx='water_bubbles')
    if action == 'burning':
        s = [(-4, 4), (-1, 1), (4, -4), (1, -1)][f]
        return P(by=-1 if f % 2 else 0, lean=2, lf=(s[0], 0), rf=(s[1], 0), fh=(2, -3 - f % 2), bh=(-2, -4 + f % 2), mouth=2, fx='fire')
    if action == 'carry': b, fr = walk[f]; return P(by=f % 2 * -1, lf=(b, 0), rf=(fr, 0), fh=(1, -8), bh=(-2, -8), item='crate')
    if action == 'chop': return P(fh=[(0, -6), (3, -3), (7, 4), (6, 5)][f], bh=[(-1, -5), (1, -2), (4, 4), (4, 5)][f], item='axe', ang=[-2.3, -1.5, .2, .5][f], lean=[-1, 0, 2, 2][f], fx='chips' if f == 3 else None)
    if action == 'mine': return P(fh=[(0, -6), (3, -3), (6, 4), (6, 5)][f], bh=[(-1, -5), (1, -2), (4, 4), (4, 5)][f], item='pickaxe', ang=[-2.3, -1.5, .4, .7][f], lean=[-1, 0, 2, 2][f], fx='sparks' if f == 3 else None)
    if action == 'farm': return P(fh=[(3, 0), (5, 3), (6, 6), (4, 3)][f], bh=[(1, 1), (2, 4), (3, 6), (2, 4)][f], item='hoe', ang=[-1.2, -.3, .9, .3][f], lean=[0, 1, 2, 1][f], by=[0, 1, 2, 1][f], fx='dirt' if f == 2 else None)
    if action == 'build': return P(by=3, knee=2, fh=[(4, -2), (5, 1), (6, 4), (5, 1)][f], bh=(3, 5), item='hammer', ang=[-2.0, -1.0, .2, -1.0][f], fx='sparks' if f == 2 else None)
    if action == 'fish': return P(fh=(4, 3), bh=(2, 4), item='rod', ang=[-.9, -.8][f], fx='line')
    if action == 'gather': return P(by=[2, 4][f], knee=[1, 3][f], fh=(4, [6, 8][f]), bh=(-1, 7), item='basket')
    if action == 'water': return P(fh=(5, 4), bh=(2, 5), item='bucket', lean=1, fx='pour' if f else None)
    if action == 'herd': return P(fh=(4, [-2, 1][f]), bh=(-2, 7), item='staff', ang=[-1.4, -1.1][f], mouth=1)
    if action == 'milk': return P(by=5, knee=4, fh=(5, [5, 6][f]), bh=(4, [6, 5][f]), item='bucket')
    if action == 'tame': return P(fh=(6, 2), bh=(-2, 7), item='food', lean=1)
    if action == 'torch': b, fr = walk[f]; return P(by=f % 2 * -1, lf=(b, 0), rf=(fr, 0), fh=(4, 1), bh=(-1 + b, 7), item='torch', ang=-1.4)
    # ---- combat
    if action == 'melee': return P(fh=[(-1, -5), (3, -4), (7, 3)][f], bh=[(-3, 3), (-3, 4), (-2, 5)][f], item='sword', ang=[-2.4, -1.4, .3][f], lean=[-1, 0, 2][f], lf=(-2, 0), rf=(2, 0))
    if action == 'stab': return P(fh=[(1, 3), (4, 3), (9, 3)][f], bh=[(-1, 3), (1, 3), (4, 3)][f], item='spear', ang=0.0, lean=[-1, 0, 2][f], lf=(-2, 0), rf=(2, 0))
    if action == 'throw': return P(fh=[(-4, -4), (0, -6), (7, -1)][f], bh=(3, 2), item='spear' if f < 2 else None, ang=[-.2, -.4, 0][f], lean=[-2, 0, 2][f], lf=(-2, 0), rf=(2, 0))
    if action == 'shoot_bow': return P(fh=(7, 2), bh=[(2, 2), (0, 2), (3, 2)][f], item='bow', ang=0.0, fx=['draw0', 'draw1', 'loose'][f], lf=(-2, 0), rf=(2, 0))
    if action == 'shoot_gun': return P(fh=(6, 3), bh=(3, 4), item='rifle', ang=0.0, lean=[0, -1, 0][f], fx=['', 'flash', 'smoke'][f], lf=(-2, 0), rf=(2, 0))
    if action == 'cast': return P(fh=[(3, 0), (4, -4), (7, -2)][f], bh=[(-2, 2), (-3, -3), (-2, 1)][f], item='staff', ang=-1.5, fx=['orb0', 'orb1', 'orb2'][f])
    if action == 'blinded': return P(fh=(2, -5), bh=(0, -5), eyes='shut', mouth=2, head=1, lean=-1, fx='shake' if f else None)
    if action == 'block': return P(fh=(5, 2), bh=(3, 3), item='shield', lean=-1, lf=(-2, 0), rf=(2, 0))
    return P()


# ------------------------------------------------------------------ drawing
def human(a, x, y, look, action='idle', frame=0, ctx=None):
    sp = SPECIES[look.get('species', 'human')]
    v = ctx.v if ctx is not None else {}
    acc = v.get('ACC') or R5('#2a4a6a', '#3a6086', '#5a7ea0', '#7a9cbc', '#a0bcd6')
    acc2 = v.get('ACC2') or R5('#6a2a5a', '#8a3a76', '#a85a94', '#c87ab4', '#e8a8d8')
    team = v.get('TEAM') if look.get('soldier') else None
    skin = v.get('SKIN') if v.get('SKIN') is not None and look.get('species', 'human') == 'human' else hx(sp['skin'])
    if look.get('species', 'human') != 'human' and v.get('SKIN') is not None and v['SKIN'] != hx('#c89a74'): skin = v['SKIN']
    hair = v.get('HAIR') or hx('#3a2618')
    if look.get('species') == 'elf' and v.get('HAIR') == hx('#3a2618'): hair = hx('#d8c890')
    if look.get('elder'): hair = hx('#b8b4ac')
    sk = [lit(skin, -.2), skin, lit(skin, .1)]
    cloth = team if team is not None else acc
    p = pose(action, frame)
    m = look.get('gender', 'm') == 'm'
    lh, tw, th, hw, hh = sp['lh'], sp['tw'], sp['th'], sp['hw'], sp['hh']
    child = look.get('child')
    if child: lh, th, tw = max(3, lh - 3), th - 2, tw - 2
    feet = y + 31
    cx = x + 13
    by = p['by']
    hip = feet - lh + by + p['knee'] // 2
    ttop = hip - th
    lean = p['lean']
    htop = ttop - hh - 1 + p['head']
    tx = cx - tw // 2
    shade = look.get('outfit', 'medieval')
    # shadow
    if action not in ('swim', 'drown', 'grabbed') and not look.get('noshadow'): shadow_ell(a, cx + 1, feet + 1, 4.5, 1.3, .3)
    # ---- legs
    pants = lit(cloth[1], -.25) if shade == 'modern' else (sk if shade == 'tribal' else lit(acc2[1], -.1) if not m else [lit(c, -.3) for c in cloth][1:4])
    if isinstance(pants, tuple): pants = [lit(pants, -.1), pants, lit(pants, .1)]
    shoes = hx('#3a2a20') if shade != 'tribal' else lit(skin, -.25)
    if action not in ('swim', 'drown'):
        for (side, fo, col) in ((-1, p['lf'], pants[0]), (1, p['rf'], pants[1])):
            lx = cx - 3 if side < 0 else cx + 1
            if p['sit']:
                seg(a, lx, hip, lx + 4, hip + 1, 2, col); seg(a, lx + 4, hip + 1, lx + 3, hip + 5, 2, col)
                rect(a, lx + 3, hip + 5, 3, 1, shoes); continue
            fx_, fy_ = lx + fo[0], feet - fo[1]
            if p['knee']:
                kx, ky = lx + 3, hip + (feet - hip) // 2
                seg(a, lx, hip, kx, ky, 2, col); seg(a, kx, ky, fx_, fy_, 2, col)
            else:
                seg(a, lx, hip, fx_, fy_, 2, col)
            rect(a, fx_, fy_, 3, 1, shoes)
    # skirt / kilt / loincloth over the hips
    if shade == 'tribal':
        for yy in range(hip - 1, hip + 3): hline(a, tx, yy, tw, hx('#8a6a44') if yy % 2 else hx('#a8844e'))
    elif not m:
        for yy in range(hip - 1, hip + 4 + (lh > 5)):
            sp_ = (yy - hip) // 2 + 1
            hline(a, tx - sp_ + 1 + lean // 2, yy, tw + 2 * sp_ - 2, cloth[1] if yy % 4 else cloth[0])
    # ---- back arm
    shy = ttop + 1
    bsx, fsx = tx + lean, tx + tw - 2 + lean
    def arm(sx, h, col, hand_col):
        hxp, hyp = sx + h[0], shy + h[1]
        ex_, ey_ = (sx + hxp) / 2 - (1 if h[1] < 3 else 0), (shy + hyp) / 2 + (1 if h[1] < 3 else 0)
        seg(a, sx, shy, ex_, ey_, 2, col); seg(a, ex_, ey_, hxp, hyp, 2, col)
        rect(a, hxp, hyp, 2, 2, hand_col)
        return hxp, hyp
    sleeve = cloth if shade != 'tribal' else sk
    bhand = arm(bsx, p['bh'], lit(sleeve[0], -.05), sk[0])
    # ---- torso
    for yy in range(ttop, hip):
        sh_ = lean * (hip - yy) // max(th, 1)
        for xx in range(tx + sh_, tx + tw + sh_):
            c = sleeve[2] if xx < tx + sh_ + 2 else sleeve[0] if xx > tx + sh_ + tw - 3 else sleeve[1]
            put(a, xx, yy, c)
    if shade == 'tribal':
        hline(a, tx + lean, ttop, tw, hx('#a8844e')); put(a, tx + lean + 2, ttop + 1, hx('#e8e0c8'))
        if not m: hline(a, tx + lean, ttop + 2, tw, hx('#8a6a44')); hline(a, tx + lean, ttop + 3, tw, hx('#a8844e'))
    else:
        hline(a, tx + lean, hip - 1, tw, lit(cloth[0], -.3))              # belt
        put(a, tx + lean + tw // 2, ttop, sk[1])                               # neckline
        if shade == 'modern': vline(a, tx + lean + tw // 2, ttop + 1, th - 2, acc2[3])
        else: put(a, tx + lean + tw // 2, hip - 1, acc2[3])
    if look.get('armor'):
        ar = R5('#4a4e56', '#6a707a', '#8a919a', '#aab0b8', '#cfd4da')
        for yy in range(ttop, ttop + th - 2): hline(a, tx + lean + 1, yy, tw - 2, ar[2] if yy % 3 else ar[3])
    if look.get('vest'):   # modern soldier webbing
        vline(a, tx + lean + 2, ttop, th, hx('#3a3a2e')); vline(a, tx + lean + tw - 3, ttop, th, hx('#3a3a2e')); hline(a, tx + lean + 1, ttop + 3, tw - 2, hx('#4a4a3a'))
    # ---- head
    hx0 = cx - hw // 2 + lean
    for yy in range(htop, htop + hh):
        for xx in range(hx0, hx0 + hw):
            c = sk[2] if xx < hx0 + 2 and yy < htop + hh - 2 else sk[0] if xx == hx0 + hw - 1 or yy == htop + hh - 1 else sk[1]
            put(a, xx, yy, c)
    # hair
    if not look.get('bald'):
        hline(a, hx0, htop - 1, hw, hair); hline(a, hx0 - 1, htop, hw + 1, lit(hair, .12)); put(a, hx0 - 1, htop + 1, hair); put(a, hx0, htop + 1, hair)
        if not m: vline(a, hx0 - 1, htop + 1, hh + 2, hair); vline(a, hx0, htop + 2, hh, lit(hair, -.1))
    ey = htop + 3
    if p['eyes'] == 'open':
        put(a, hx0 + 3, ey, DARK); put(a, hx0 + 5, ey, DARK)
    elif p['eyes'] == 'glow':
        put(a, hx0 + 3, ey, hx('#5fe0e8')); put(a, hx0 + 5, ey, hx('#5fe0e8'))
    else:
        put(a, hx0 + 3, ey, lit(skin, -.35)); put(a, hx0 + 5, ey, lit(skin, -.35))
    if p['mouth'] == 2: rect(a, hx0 + 4, ey + 2, 2, 1, hx('#3a1a1a'))
    elif p['mouth'] == 1: put(a, hx0 + 4, ey + 2, hx('#3a1a1a'))
    else: put(a, hx0 + 4, ey + 2, lit(skin, -.28))
    if sp.get('ears'): put(a, hx0, ey - 1, sk[1]); put(a, hx0 - 1, ey - 2, sk[2])
    else: put(a, hx0 + 1, ey, sk[0])
    if sp.get('tusks'): put(a, hx0 + 5, ey + 2, hx('#f2ece0')); put(a, hx0 + 3, ey + 2, hx('#f2ece0'))
    if sp.get('brow'): hline(a, hx0 + 2, ey - 1, 4, lit(skin, -.3))
    if (sp.get('beard') and m) or look.get('beard'):
        for xx in range(hx0 + 2, hx0 + hw + 1): vline(a, xx, htop + hh - 2, 3 if sp.get('beard') else 1, hair)
    # headgear
    hg = look.get('helmet')
    if hg == 'leather': hline(a, hx0 - 1, htop - 1, hw + 2, hx('#6b4c34')); hline(a, hx0, htop - 2, hw, hx('#8c6844'))
    elif hg == 'iron':
        hline(a, hx0 - 1, htop - 1, hw + 2, hx('#8a919a')); hline(a, hx0, htop - 2, hw, hx('#aab0b8')); vline(a, hx0 + hw - 2, htop, 3, hx('#6a707a'))
    elif hg == 'tricorn': hline(a, hx0 - 2, htop - 1, hw + 4, hx('#1e1e24')); hline(a, hx0, htop - 2, hw, hx('#2a2a32'))
    elif hg == 'steel': hline(a, hx0 - 1, htop - 1, hw + 2, hx('#4a5a3a')); hline(a, hx0, htop - 2, hw, hx('#5a6a44')); hline(a, hx0 - 1, htop, 2, hx('#4a5a3a'))
    elif hg == 'visor':
        hline(a, hx0 - 1, htop - 1, hw + 2, hx('#cfd4da')); hline(a, hx0, htop - 2, hw, hx('#eef2f6')); hline(a, hx0 + 2, ey, hw - 1, hx('#5fe0e8'))
    elif hg == 'band': hline(a, hx0 - 1, htop, hw + 1, acc2[3])
    elif hg == 'feather': hline(a, hx0 - 1, htop, hw + 1, hx('#a8844e')); vline(a, hx0 - 1, htop - 4, 4, hx('#e8e0c8')); put(a, hx0 - 1, htop - 4, hx('#c83a3a'))
    # ---- front arm + item
    fhand = arm(fsx, p['fh'], sleeve[1], sk[1])
    it = p['item'] or (look.get('weapon') if action in ('idle', 'walk', 'run', 'hurt') and look.get('soldier') else None)
    if action in ('shoot_gun',) and look.get('weapon'): it = look['weapon']
    if action in ('melee',) and look.get('weapon') in ('club', 'axe', 'sword'): it = look['weapon']
    if action in ('stab', 'throw') and look.get('weapon') in ('spear',) and p['item']: it = 'spear'
    if action == 'shoot_bow' and look.get('weapon') == 'xbow': it = 'xbow'
    if action == 'throw' and look.get('weapon') == 'sling': it = 'sling' if frame < 2 else None
    if it: draw_item(a, it, fhand[0], fhand[1], p['ang'] if p['item'] or action in ('melee', 'shoot_gun', 'shoot_bow', 'stab') else (-1.2 if ITEMS.get(it, (0,))[0] > 9 else -.6), frame, action)
    if look.get('shield') and action not in ('chop', 'mine', 'farm', 'build', 'carry', 'shoot_gun', 'shoot_bow'):
        sx_, sy_ = (fhand if action == 'block' else bhand)
        dome(a, sx_ + 1, sy_, 3, 4, R5('#4a3424', '#6b4c34', '#8c6844', '#a8844e', '#c8a46a') if look['shield'] == 'wood' else R5('#4a4e56', '#6a707a', '#8a919a', '#aab0b8', '#cfd4da'), 3)
        put(a, sx_ + 1, sy_, cloth[3])
    # ---- fx
    fx = p['fx']
    if fx == 'sweat': put(a, hx0 - 1, htop + 1, hx('#9ad0f0')); put(a, hx0 - 1, htop + 2, hx('#9ad0f0'))
    elif fx == 'blood':   # cartoon impact stars (no gore - STYLE_GUIDE)
        for (sx, sy) in ((hx0 + hw + 1, htop + 2), (tx + tw + 2, ttop + 3)):
            put(a, sx, sy, hx('#fff6c0')); put(a, sx - 1, sy, hx('#ffd34a')); put(a, sx + 1, sy, hx('#ffd34a')); put(a, sx, sy - 1, hx('#ffd34a')); put(a, sx, sy + 1, hx('#ffd34a'))
    elif fx == 'zz': put(a, hx0 + hw + 1, htop - 2, hx('#f6f2ea')); hline(a, hx0 + hw + 2, htop - 4, 2, hx('#f6f2ea'))
    elif fx == 'sick':
        for i in range(3): put(a, hx0 + hw + 1 + i, htop + 2 - i, hx('#9ab07a'))
    elif fx == 'shake': put(a, hx0 - 2, htop + 2, hx('#f6f2ea')); put(a, hx0 + hw + 1, htop + 2, hx('#f6f2ea'))
    elif fx == 'fire':
        rr = random.Random(frame)
        for i in range(10):
            fx_, fy_ = rr.randint(tx - 1, tx + tw + 1), rr.randint(htop - 3, feet - 4)
            put(a, fx_, fy_, hx('#ffd34a')); put(a, fx_, fy_ + 1, hx('#f49a3c')); put(a, fx_ + 1, fy_ + 1, hx('#d5452d'))
    elif fx in ('water', 'water_bubbles'):
        wl = y + 26
        for xx in range(x + 2, x + 26): put(a, xx, wl, hx('#bfe6f8') if (xx + frame) % 3 else hx('#ffffff'))
        a[wl + 1:y + 40, x:x + 28] = (a[wl + 1:y + 40, x:x + 28] * .45 + np.array(hx('#2a6aa8')) * .55).astype(np.uint8) if False else a[wl + 1:y + 40, x:x + 28]
        if fx == 'water_bubbles':
            for i in range(3): put(a, cx - 2 + i * 2, wl - 2 - (frame + i) % 3, hx('#e8f6ff'))
    elif fx == 'chips':
        for i in range(3): put(a, fhand[0] + 4 + i, fhand[1] - 2 - i, hx('#c8a46a'))
    elif fx == 'sparks':
        for i in range(3): put(a, fhand[0] + 5 + i, fhand[1] - 1 - (i % 2) * 2, hx('#ffe27a'))
    elif fx == 'dirt':
        for i in range(4): put(a, fhand[0] + 6 + i, feet - 1 - (i % 2), hx('#7a5a3a'))
    elif fx == 'pour':
        for i in range(5): put(a, fhand[0] + 4, fhand[1] + 2 + i, hx('#8ac8f0'))
    elif fx == 'flash':
        L = ITEMS.get(it or 'rifle', (10,))[0]
        put(a, fhand[0] + L + 1, fhand[1], hx('#fff6c0')); put(a, fhand[0] + L + 2, fhand[1], hx('#ffd34a')); put(a, fhand[0] + L + 2, fhand[1] - 1, hx('#ffb84a')); put(a, fhand[0] + L + 2, fhand[1] + 1, hx('#ffb84a'))
        if it == 'flamer':
            for i in range(10): put(a, fhand[0] + L + 2 + i, fhand[1] + (i % 3) - 1, [hx('#ffe27a'), hx('#f49a3c'), hx('#d5452d')][i % 3])
        if it == 'laser':
            for i in range(10): put(a, fhand[0] + L + 2 + i, fhand[1], hx('#bff6fa'))
    elif fx == 'smoke':
        L = ITEMS.get(it or 'rifle', (10,))[0]
        blend_mask(a, ellipse_mask(a.shape[:2], fhand[0] + L + 3, fhand[1] - 1, 2, 1.5), hx('#c8c8cc'), .6)
    elif fx and fx.startswith('orb'):
        r_ = int(fx[-1]) + 1
        blend_mask(a, ellipse_mask(a.shape[:2], fhand[0] + 1, fhand[1] - 8, r_ + 1.5, r_ + 1.5), hx('#c87ae8'), .4)
        put(a, fhand[0] + 1, fhand[1] - 8, hx('#ffffff'))
    elif fx == 'loose':
        for i in range(6): put(a, fhand[0] + 3 + i, fhand[1], hx('#cfd4da'))
    return dict(head=(hx0 + hw // 2, htop), hand=fhand, feet=(cx, feet), hip=(cx, hip))


def draw_item(a, it, hx_, hy_, ang, frame, action):
    L, c1, c2, kind = ITEMS[it]
    c1, c2 = hx(c1), hx(c2)
    dx, dy = math.cos(ang), math.sin(ang)
    if kind in ('axe', 'pick', 'hoe', 'hammer', 'blade', 'club', 'spear', 'staff', 'torch', 'rod'):
        back = 2 if kind in ('spear', 'staff', 'hoe', 'rod') else 0
        for i in range(-back, L):
            put(a, int(hx_ + 1 + dx * i), int(hy_ + dy * i), c1 if kind != 'blade' or i < 2 else c2)
        ex, ey = hx_ + 1 + dx * L, hy_ + dy * L
        if kind == 'axe':
            for j in range(-1, 3): put(a, int(ex - dy * j), int(ey + dx * j), c2); put(a, int(ex - dy * j - dx), int(ey + dx * j - dy), c2)
        elif kind == 'pick':
            for j in range(-3, 4): put(a, int(ex - dy * j + (abs(j) * dx * -.3)), int(ey + dx * j + abs(j) * dy * -.3), c2)
        elif kind == 'hoe':
            for j in range(3): put(a, int(ex + dy * j * -1 * -1), int(ey + j), c2)
        elif kind == 'hammer':
            for j in range(-2, 3): put(a, int(ex - dy * j), int(ey + dx * j), c2); put(a, int(ex - dy * j + dx), int(ey + dx * j + dy), c2)
        elif kind == 'blade':
            put(a, int(hx_ + 1 - dy), int(hy_ + dx), hx('#c8a040')); put(a, int(hx_ + 1 + dy), int(hy_ - dx), hx('#c8a040'))
        elif kind == 'club':
            dome(a, ex, ey, 1.8, 1.8, R5('#3a2618', '#4a3424', '#6b4c34', '#8c6844', '#a8844e'), 1)
        elif kind == 'spear':
            put(a, int(ex), int(ey), c2); put(a, int(ex + dx), int(ey + dy), c2); put(a, int(ex + 2 * dx), int(ey + 2 * dy), lit(c2, .2))
        elif kind == 'staff':
            dome(a, ex, ey, 1.5, 1.5, R5('#3a1a6a', '#5a2a9a', '#9a6ae8', '#c8a8ff', '#ffffff'), 1)
        elif kind == 'torch':
            fl = frame % 2
            put(a, int(ex), int(ey), hx('#d5452d')); put(a, int(ex), int(ey) - 1, hx('#f49a3c')); put(a, int(ex) + fl, int(ey) - 2, hx('#ffe27a'))
            blend_mask(a, ellipse_mask(a.shape[:2], ex, ey - 1, 4, 4), hx('#ffb84a'), .25)
        elif kind == 'rod':
            for i in range(8): put(a, int(ex + i * .5), int(ey + i), hx('#e8e8e8'))
    elif kind == 'bow':
        draw = {'draw0': 1, 'draw1': 3, 'loose': 0}.get(None, 0)
        for j in range(-5, 6): put(a, int(hx_ + 2 + (25 - j * j) / 10), int(hy_ + j), c1)
        pull = 3 if action == 'shoot_bow' and frame == 1 else 1 if action == 'shoot_bow' and frame == 0 else 0
        for j in (-5, 5): seg(a, hx_ + 2, hy_ + j, hx_ + 2 - pull, hy_, 1, c2)
        if action == 'shoot_bow' and frame < 2:
            for i in range(7): put(a, hx_ + 2 - pull + i, hy_, hx('#cfd4da') if i > 4 else hx('#8c6844'))
    elif kind == 'xbow':
        hline(a, hx_ - 2, hy_, L, c1); vline(a, hx_ + L - 3, hy_ - 3, 7, c2)
    elif kind == 'gun':
        hline(a, hx_ - 3, hy_, L, c1); hline(a, hx_ - 3, hy_ + 1, 3, c1); hline(a, hx_ + 1, hy_ - 1, L - 4, c2)
        if it == 'flamer': rect(a, hx_ - 6, hy_ - 3, 2, 5, hx('#c84a2a'))
    elif kind == 'sling':
        seg(a, hx_ + 1, hy_, hx_ + 1 + int(dx * 5), hy_ + int(dy * 5), 1, c1); put(a, hx_ + 1 + int(dx * 5), hy_ + int(dy * 5), c2)
    elif kind == 'bucket':
        rect(a, hx_, hy_ + 1, 3, 3, c1); hline(a, hx_, hy_ + 1, 3, c2)
    elif kind == 'basket':
        rect(a, hx_ - 1, hy_ + 1, 4, 3, c1); hline(a, hx_ - 1, hy_ + 1, 4, c2)
    elif kind == 'crate':
        rect(a, hx_ - 4, hy_ - 5, 8, 5, c1); hline(a, hx_ - 4, hy_ - 5, 8, lit(c1, .2)); vline(a, hx_, hy_ - 5, 5, c2)
    if kind == 'food': draw_food(a, hx_ + 2, hy_)


def draw_food(a, x, y):
    put(a, x, y, hx('#c83a3a')); put(a, x + 1, y, hx('#e85a4a')); put(a, x, y - 1, hx('#4a8a3a'))


ITEMS['food'] = (0, '#c83a3a', '#e85a4a', 'food')


# ------------------------------------------------------------------ deaths (12 types, 4-6 frames each)
DEATHS = {
    'weapon': 5, 'arrow': 5, 'explosion': 6, 'burn': 6, 'freeze': 5, 'electric': 5, 'poison': 6, 'drown': 5, 'crushed': 4, 'eaten': 4, 'dissolve': 5, 'irradiated': 6, 'vaporized': 4,
}


def _lying(a, x, y, look, ctx, cx_shift=0, flip=False, action='limp'):
    """draw the standing person on a temp canvas and rotate it 90 deg to lie on the ground."""
    t = np.zeros((40, 28, 3), np.uint8); t[:] = (255, 0, 255)
    human(t, 0, 0, dict(look, noshadow=True), action, 0, ctx)
    rot = np.rot90(t, 1 if not flip else -1)            # lie on the back
    h, w = rot.shape[:2]
    gy = y + 32
    ys, xs = np.nonzero(~np.all(rot == (255, 0, 255), axis=2))
    rot = rot[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = rot.shape[:2]
    ox, oy = x + 13 - w // 2 + cx_shift, gy - h + 1
    m = ~np.all(rot == (255, 0, 255), axis=2) & ~((rot[..., 0] < 8) & (rot[..., 1] < 8) & (rot[..., 2] < 8) & False)
    H, W = a.shape[:2]
    for yy in range(h):
        for xx in range(w):
            if m[yy, xx] and 0 <= oy + yy < H and 0 <= ox + xx < W: a[oy + yy, ox + xx] = rot[yy, xx]
    return (ox, oy, w, h), m


def _tilt(a, x, y, look, ctx, deg, action='hurt', frame=0):
    """person rotated around the feet (falling backwards)."""
    from PIL import Image
    t = np.zeros((40, 28, 3), np.uint8); t[:] = (255, 0, 255)
    human(t, 0, 0, dict(look, noshadow=True), action, frame, ctx)
    big = np.zeros((80, 80, 3), np.uint8); big[:] = (255, 0, 255); big[20:60, 26:54] = t
    im = Image.fromarray(big).rotate(deg, resample=Image.NEAREST, center=(39, 51), fillcolor=(255, 0, 255))
    r = np.array(im)
    ys, xs = np.nonzero(~np.all(r == (255, 0, 255), axis=2))
    shadow_ell(a, x + 13 - min(deg, 90) / 12, y + 33, 5 + min(deg, 90) / 18, 1.3, .3) if deg <= 100 else None
    H, W = a.shape[:2]
    for yy, xx in zip(ys, xs):
        X, Y = x + xx - 26, y + yy - 20
        if 0 <= Y < H and 0 <= X < W: a[Y, X] = r[yy, xx]


def blood_pool(a, cx, cy, r, al=.85):
    """kept name for call sites; draws a light dust puff on the ground (no blood - STYLE_GUIDE 'no gore')."""
    blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, r * .8, max(1, r * .3)), hx('#c8b48e'), al * .45)
    put(a, int(cx - r * .4), int(cy - 1), hx('#d8c8a6')); put(a, int(cx + r * .3), int(cy - 2), hx('#d8c8a6'))


def death(a, x, y, look, kind, f, ctx=None):
    gy = y + 32
    cx = x + 13
    if kind in ('weapon', 'arrow', 'poison', 'irradiated') and f < 3:
        ang = [15, 45, 75][f] if kind != 'poison' else [0, 20, 60][f]
        if kind == 'poison' and f == 0:
            human(a, x, y, look, 'sick', 1, ctx); blend_mask(a, ellipse_mask(a.shape[:2], cx, y + 14, 7, 12), hx('#7ac04a'), .25); return
        _tilt(a, x, y, look, ctx, ang)
        if kind == 'arrow':
            for i in range(2): seg(a, cx + 2 + i * 2, y + 14 + i * 3 + f * 2, cx + 6 + i * 2, y + 11 + i * 3 + f * 2, 1, hx('#8c6844'))
        if kind == 'irradiated':
            for i in range(5): put(a, cx - 4 + i * 2, y + 8 + (i * 7 + f * 3) % 20, hx('#c8ff7a'))
        return
    if kind in ('weapon', 'arrow', 'poison', 'irradiated'):
        if kind == 'irradiated' and f >= 4:
            skeleton_lying(a, x, y, glow=f == 4); blend_mask(a, ellipse_mask(a.shape[:2], cx, gy - 2, 12, 3), hx('#9ae04a'), .3); return
        box, m = _lying(a, x, y, look, ctx)
        if kind == 'weapon': blood_pool(a, cx - 4, gy, 3 + f * 1.5)
        if kind == 'arrow':
            for i in range(2): seg(a, box[0] + 6 + i * 5, box[1] - 1, box[0] + 8 + i * 5, box[1] - 5, 1, hx('#8c6844')); put(a, box[0] + 8 + i * 5, box[1] - 6, hx('#f6f2ea'))
            blood_pool(a, cx, gy, 2 + f)
        if kind == 'poison':
            blend_mask(a, ellipse_mask(a.shape[:2], cx, gy - 2, 12, 3), hx('#7ac04a'), .45)
            for i in range(3): put(a, cx - 6 + i * 6, gy - 5 - (f + i) % 3, hx('#9ae04a'))
        if kind == 'irradiated': blend_mask(a, ellipse_mask(a.shape[:2], cx, gy - 2, 12, 3), hx('#9ae04a'), .5)
        return
    if kind == 'explosion':
        if f < 4:
            ang = [40, 100, 170, 250][f]
            yy = y - [4, 10, 8, 2][f]
            _tilt(a, x + f * 3, yy, look, ctx, ang, 'hurt')
            if f < 2: blend_mask(a, ellipse_mask(a.shape[:2], cx - 6, gy - 6, 9 - f * 3, 7 - f * 2), hx('#ffb84a'), .6)
            return
        box, m = _lying(a, x + 6, y, look, ctx, flip=True)
        _char(a, box, m, .55)
        blend_mask(a, ellipse_mask(a.shape[:2], cx, gy, 10, 3), hx('#1e1a16'), .5 if f == 4 else .65)
        return
    if kind == 'burn':
        if f < 3:
            if f == 2:
                t = np.zeros((40, 28, 3), np.uint8); t[:] = (255, 0, 255)
                human(t, 0, 0, dict(look, noshadow=True), 'burning', f, ctx)
                mm = ~np.all(t == (255, 0, 255), axis=2)
                t[mm] = (t[mm] * .55 + 12).astype(np.uint8)
                shadow_ell(a, x + 14, y + 33, 4.5, 1.3, .3)
                ys, xs = np.nonzero(mm)
                for yy, xx in zip(ys, xs): put(a, x + xx, y + yy, tuple(int(c) for c in t[yy, xx]))
            else: human(a, x, y, look, 'burning', f, ctx)
            return
        if f < 5:
            box, m = _lying(a, x, y, look, ctx); _char(a, box, m, .8)
            for i in range(4): put(a, box[0] + 3 + i * 5, box[1] - 1 - (i + f) % 2, hx('#ffb84a')); put(a, box[0] + 3 + i * 5, box[1] - 2 - (i + f) % 3, hx('#ffe27a'))
            return
        ash_pile(a, cx, gy); return
    if kind == 'freeze':
        if f < 2:
            human(a, x, y, look, 'hurt', 0, ctx); blend_mask(a, ellipse_mask(a.shape[:2], cx, y + 18, 8, 14), hx('#bfe6f8'), .35 + .25 * f); return
        human(a, x, y, look, 'hurt', 0, ctx)
        a2 = a  # ice block
        blend_rect(a2, cx - 8, y + 2, 17, 31, hx('#9ad0f0'), .55)
        hline(a2, cx - 8, y + 2, 17, hx('#e8f6ff')); vline(a2, cx - 8, y + 2, 31, hx('#e8f6ff')); vline(a2, cx + 8, y + 2, 31, hx('#5a9ac4'))
        if f == 4:   # shattered
            a[y:gy + 2, x:x + 28] = a[y:gy + 2, x:x + 28]
            for i in range(14):
                rr = random.Random(i)
                rect(a, cx - 10 + rr.randint(0, 20), gy - rr.randint(0, 4), 2, 1, hx('#cfefff') if i % 2 else hx('#9ad0f0'))
        return
    if kind == 'electric':
        if f < 3:
            if f == 1: skeleton_standing(a, x, y)
            else: human(a, x, y, look, 'possessed', 0, ctx)
            for i in range(3):
                xx = cx - 6 + i * 6; yy = y + 4
                for k in range(8): put(a, xx + random.Random(i * 9 + k + f).choice((-1, 0, 1)), yy + k * 3, hx('#d8e4ff'))
            return
        box, m = _lying(a, x, y, look, ctx); _char(a, box, m, .5 if f == 3 else .6)
        put(a, box[0] + 4, box[1] - 2, hx('#c8c8cc')); put(a, box[0] + 10, box[1] - 3, hx('#a8a8b0'))
        return
    if kind == 'drown':
        human(a, x, y, look, 'drown', min(f, 3), ctx)
        if f == 4:
            a[:, :] = a
            for i in range(4): put(a, cx - 3 + i * 2, y + 24 - i, hx('#e8f6ff'))
        return
    if kind == 'crushed':
        if f == 0: human(a, x, y, look, 'cower', 1, ctx); return
        t = np.zeros((40, 28, 3), np.uint8); t[:] = (255, 0, 255)
        human(t, 0, 0, dict(look, noshadow=True), 'idle', 0, ctx)
        sq = [None, 10, 5, 4][f]
        ys, xs = np.nonzero(~np.all(t == (255, 0, 255), axis=2))
        part = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        from PIL import Image
        im = np.array(Image.fromarray(part).resize((part.shape[1] + 6, sq), Image.NEAREST))
        mm = ~np.all(np.abs(im.astype(int) - (255, 0, 255)) < 40, axis=2)
        ox, oy = cx - im.shape[1] // 2, gy - sq + 1
        blood_pool(a, cx, gy, 5 + f * 2, .9)
        for yy in range(im.shape[0]):
            for xx in range(im.shape[1]):
                if mm[yy, xx]: put(a, ox + xx, oy + yy, tuple(int(c) for c in im[yy, xx]))
        return
    if kind == 'eaten':     # cartoon-clean: knocked over, poof of dust, a plain grave stone
        if f == 0: _lying(a, x, y, look, ctx); return
        if f == 1: _fade_lying(a, x, y, look, ctx, .5); blood_pool(a, cx, gy, 8); return
        if f == 2: blood_pool(a, cx, gy, 10, 1.0); _poof(a, cx, gy - 4); return
        grave_stone(a, cx, gy); return
    if kind == 'fade':
        if f == 0: _lying(a, x, y, look, ctx); return
        if f < 3: _fade_lying(a, x, y, look, ctx, [0, .45, .8][f], f); _poof(a, cx, gy - 3) if f == 2 else None; return
        grave_stone(a, cx, gy); return
    if kind == 'vaporized':     # inside the fireball: white flash -> charred figure -> crumbling ash -> ash shadow
        t = np.zeros((40, 28, 3), np.uint8); t[:] = (255, 0, 255)
        human(t, 0, 0, dict(look, noshadow=True), 'blinded', 0, ctx)
        mm = ~np.all(t == (255, 0, 255), axis=2)
        rr = np.random.default_rng(f)
        if f == 3:
            blend_mask(a, ellipse_mask(a.shape[:2], cx, gy - 1, 6, 1.6), hx('#141210'), .8)
            for i in range(4): put(a, cx - 4 + i * 3, gy - 2 + (i % 2), hx('#5a5650'))
            return
        col = [hx('#fffbe8'), hx('#2a1e16'), hx('#6a655c')][f]
        for yy, xx in zip(*np.nonzero(mm)):
            if f == 2 and rr.random() < .45: continue
            c = col if f != 1 or rr.random() > .08 else hx('#f49a3c')
            put(a, x + xx, y + yy + (rr.integers(0, 3) if f == 2 else 0), c)
        if f == 0: blend_mask(a, ellipse_mask(a.shape[:2], cx, y + 18, 10, 16), hx('#fff6c0'), .5)
        return
    if kind == 'dissolve':
        t = np.zeros((40, 28, 3), np.uint8); t[:] = (255, 0, 255)
        human(t, 0, 0, dict(look, noshadow=True), 'possessed', 0, ctx)
        rr = np.random.default_rng(f)
        tt = [.0, .25, .5, .75, .95][f]
        H, W = a.shape[:2]
        for yy in range(40):
            for xx in range(28):
                c = t[yy, xx]
                if np.all(c == (255, 0, 255)) or rr.random() < tt: continue
                if rr.random() < tt * .7: c = hx('#c87ae8')
                if 0 <= y + yy < H and 0 <= x + xx < W: a[y + yy, x + xx] = c
        for i in range(int(6 * tt) + 1): put(a, cx - 6 + i * 2, y + 4 + (f * 3 + i * 5) % 26, hx('#e8c8ff'))


def _char(a, box, m, k):
    ox, oy, w, h = box
    H, W = a.shape[:2]
    for yy in range(h):
        for xx in range(w):
            if m[yy, xx] and 0 <= oy + yy < H and 0 <= ox + xx < W:
                c = a[oy + yy, ox + xx].astype(int)
                l = c.mean()
                a[oy + yy, ox + xx] = np.clip(c * (1 - k) + (l * .3 + 14) * k, 0, 255).astype(np.uint8)


def _char_rect(a, x, y, k):
    blk = a[y:y + 34, x:x + 28].astype(int)
    mask = ~np.all(blk == blk[0, 0], axis=2)
    blk[mask] = (blk[mask] * (1 - k) + 20 * k).astype(int)
    a[y:y + 34, x:x + 28] = blk.astype(np.uint8)


def _bite(a, box, m):
    ox, oy, w, h = box
    for i in range(3): put(a, ox + w // 2 - 2 + i * 2, oy - 2 - (i % 2), hx('#fff6c0'))   # cartoon "poof" marks


def _fade_lying(a, x, y, look, ctx, t, seed=0):
    tmp = np.zeros_like(a); tmp[:] = (255, 0, 255)
    _lying(tmp, x, y, look, ctx)
    mm = ~np.all(tmp == (255, 0, 255), axis=2)
    rr = np.random.default_rng(seed)
    keep = mm & (rr.random(mm.shape) >= t)
    a[keep] = tmp[keep]


def _poof(a, cx, cy):
    for (dx, dy, r) in ((-3, 0, 2.5), (2, -1, 3), (0, -3, 2.2)):
        blend_mask(a, ellipse_mask(a.shape[:2], cx + dx, cy + dy, r, r), hx('#ece4d2'), .8)


def grave_stone(a, cx, gy):
    """plain rounded stone (STYLE_GUIDE: graves are plain rounded stones)."""
    blend_mask(a, ellipse_mask(a.shape[:2], cx, gy, 6, 1.6), hx('#5a4a36'), .55)
    dome(a, cx, gy - 5, 3.2, 3.6, R5('#5a5852', '#77746c', '#96928a', '#b4b0a6', '#cfcbc2'), 2, top=None)
    rect(a, cx - 3, gy - 5, 7, 4, hx('#96928a')); vline(a, cx - 3, gy - 5, 4, hx('#b4b0a6')); vline(a, cx + 3, gy - 5, 4, hx('#77746c'))
    hline(a, cx - 3, gy - 1, 7, hx('#5a5852'))


def ash_pile(a, cx, gy):
    dome(a, cx, gy - 1, 7, 2.5, R5('#1e1c1a', '#2e2a26', '#4a4640', '#6a655c', '#8a847a'), 3)
    for i in range(5): put(a, cx - 5 + i * 2 + (i % 2), gy - 3 - (i % 2), hx('#f49a3c') if i % 2 else hx('#5a5650'))


def bones_pile(a, cx, gy, f):
    bone = hx('#e2d8c2'); bd = hx('#b4aa94')
    dome(a, cx + 4, gy - 2, 2.2, 2, R5('#8a8474', '#a8a290', '#c4beac', '#e2d8c2', '#f2ecdc'), 1)   # skull
    put(a, cx + 4, gy - 2, DARK); put(a, cx + 5, gy - 2, DARK)
    for i in range(4): hline(a, cx - 6 + i * 2, gy - 1 - (i % 2), 3, bone if i % 2 else bd)
    seg(a, cx - 7, gy, cx - 2, gy - 1, 1, bone); seg(a, cx + 7, gy, cx + 10, gy - 2, 1, bd)


def skeleton_standing(a, x, y):
    cx = x + 13; bone = hx('#f2ecdc'); bd = hx('#b4aa94')
    dome(a, cx, y + 7, 3, 3, R5('#8a8474', '#a8a290', '#c4beac', '#e2d8c2', '#ffffff'), 1)
    put(a, cx + 1, y + 7, DARK); put(a, cx - 1, y + 7, DARK)
    vline(a, cx, y + 10, 10, bone)
    for i in range(3): hline(a, cx - 3, y + 12 + i * 2, 7, bd if i % 2 else bone)
    seg(a, cx - 4, y + 11, cx - 7, y + 4, 1, bone); seg(a, cx + 4, y + 11, cx + 7, y + 4, 1, bone)
    seg(a, cx - 1, y + 20, cx - 3, y + 31, 1, bone); seg(a, cx + 1, y + 20, cx + 3, y + 31, 1, bone)
    blend_mask(a, ellipse_mask(a.shape[:2], cx, y + 17, 9, 15), hx('#b4c8ff'), .25)


def skeleton_lying(a, x, y, glow=False):
    cx, gy = x + 13, y + 32
    bone = hx('#e2d8c2')
    dome(a, cx + 8, gy - 2, 2.4, 2.2, R5('#8a8474', '#a8a290', '#c4beac', '#e2d8c2', '#f2ecdc'), 1)
    put(a, cx + 8, gy - 3, DARK)
    hline(a, cx - 6, gy - 2, 13, bone)
    for i in range(4): vline(a, cx - 1 + i * 2, gy - 4, 4, bone)
    seg(a, cx - 6, gy - 2, cx - 11, gy - 1, 1, bone); seg(a, cx - 6, gy - 2, cx - 11, gy - 3, 1, bone)
    if glow: blend_mask(a, ellipse_mask(a.shape[:2], cx, gy - 2, 12, 4), hx('#9ae04a'), .4)


ACTIONS = {'idle': 2, 'walk': 4, 'run': 4, 'hurt': 1, 'cheer': 2, 'talk': 2, 'eat': 2, 'sleep': 2, 'flee': 4, 'cower': 2, 'sick': 2, 'possessed': 2, 'grabbed': 2,
           'ride': 1, 'swim': 4, 'burning': 4, 'carry': 4, 'torch': 4, 'chop': 4, 'mine': 4, 'farm': 4, 'build': 4, 'fish': 2, 'gather': 2, 'water': 2, 'herd': 2,
           'milk': 2, 'tame': 1, 'knocked': 4, 'blinded': 2, 'melee': 3, 'stab': 3, 'throw': 3, 'shoot_bow': 3, 'shoot_gun': 3, 'cast': 3, 'block': 1}
LYING = {'sleep'}
CHILD_DEATHS = {'fade': 4}     # owner decision: children never show a violent death - they fade and leave a grave stone


def act(a, x, y, look, action, frame, ctx=None):
    """entry point used by the exporter: handles lying actions."""
    if action == 'sleep':
        box, m = _lying(a, x, y, look, ctx, action='sleep')
        shadow_ell(a, x + 13, y + 33, 9, 1.3, .25)
        if frame: put(a, box[0] + box[2], box[1] - 3, hx('#f6f2ea')); hline(a, box[0] + box[2] + 1, box[1] - 5, 2, hx('#f6f2ea'))
        return
    if action == 'knocked':     # blast wave: flung back -> on the ground -> sitting -> getting up
        if frame == 0: _tilt(a, x - 3, y - 4, look, ctx, 55, 'hurt'); return
        if frame == 1: _lying(a, x - 2, y, look, ctx); return
        if frame == 2: return human(a, x, y, look, 'cower', 0, ctx)
        return human(a, x, y, look, 'hurt', 0, ctx)
    return human(a, x, y, look, action, frame, ctx)
