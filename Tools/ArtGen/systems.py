"""Remaining systems as observer screens (English): culture tree, royal clans, generated plague, war fronts, legends, WHY-chain."""
import copy, math, random
import numpy as np
from PIL import Image
from lib import *
from ui2kit import *
import ui2
from ui2 import topbar, dock, worldmap, dim, city_view, compose, PW, PH
import culturegen as cg
from people import person2

KQ, KV = R['K'], K2['blue']


def portrait_og(f, x, y, g, cls, age, gender, seed, sc=1, ring=GOLD[2], state=None):
    c = np.zeros((28, 16, 3), np.uint8)
    for j in range(28): c[j, :] = lit(g['acc'][1], -.55 + j * .012)
    person2(c, 0, 4, None, cls, age, gender, 0, seed=seed, shadow=False, og=g, state=state)
    crop = c[2:20]
    img = np.asarray(Image.fromarray(crop).resize((16 * sc, 18 * sc), Image.NEAREST))
    rect(f, x - 2, y - 2, 16 * sc + 4, 18 * sc + 4, INK); rect(f, x - 1, y - 1, 16 * sc + 2, 18 * sc + 2, ring)
    f[y:y + 18 * sc, x:x + 16 * sc] = img


def mutate(g, seed, why):
    r = random.Random(seed)
    h = copy.copy(g)
    h['seed'] = seed
    h['name'] = g['namer'].place()
    h['acc'] = cg.hramp((r.uniform(-40, 40) + 360 + np.degrees(0)) % 360 + 0, .55, .62) if False else [lit(c, r.uniform(-.15, .15)) for c in g['acc']]
    shift = r.choice([('+DOMES', 'roof', 'dome'), ('+TIERED ROOFS', 'roof', 'tiered'), ('+FLAT ROOFS', 'roof', 'flat'), ('+GABLES', 'roof', 'gable')])
    h['roof'] = shift[2]
    h['symbol'] = r.choice(list(cg.SYMBOLS))
    h['why'] = why; h['mut'] = shift[0]
    return h


def node(f, x, y, g, alive=True, sel=False):
    w = max(46, t7w(g['name'][:8]) + 20)
    x0 = x - w // 2
    rect(f, x0 + 1, y + 1, w, 19, INK)
    rect(f, x0, y, w, 19, BG3 if alive else BG2); hline(f, x0, y, w, g['acc'][3] if alive else BG3)
    if sel:
        for k in range(1): rect(f, x0 - 1, y - 1, w + 2, 1, GOLD[3]); rect(f, x0 - 1, y + 19, w + 2, 1, GOLD[3]); vline(f, x0 - 1, y, 19, GOLD[3]); vline(f, x0 + w, y, 19, GOLD[3])
    c = np.zeros((15, 13, 3), np.uint8); c[:] = BG3; cg.crest(c, 1, 1, g, 1)
    if not alive: c = (c * .45).astype(np.uint8)
    f[y + 2:y + 17, x0 + 2:x0 + 15] = c[0:15, 0:13]
    t7(f, x0 + 17, y + 3, g['name'][:8], TXT if alive else DIM, sh=False)
    if alive: meter(f, x0 + 17, y + 12, w - 20, 4, .3 + (g['seed'] % 7) / 10, g['acc'][3])
    else: t7(f, x0 + 17, y + 11, 'GONE', BAD, sh=False)
    return x0, w


def link(f, x0, y0, x1, y1, col=GOLD[1]):
    ym = (y0 + y1) // 2
    vline(f, x0, y0, ym - y0, col); hline(f, min(x0, x1), ym, abs(x1 - x0) + 1, col); vline(f, x1, ym, y1 - ym, col)


def why(f, x, y, s, col):
    w = t7w(s) + 6
    rect(f, x - w // 2, y, w, 10, INK); rect(f, x - w // 2 + 1, y + 1, w - 2, 8, lit(col, -.6)); t7(f, x - w // 2 + 3, y + 2, s, col, sh=False)


# ------------------------------------------------------------------ A. culture tree
def s_tree():
    f = dim(worldmap(), .72, 2)
    topbar(f, 1342, show_lang=False)
    root = cg.make_culture(3)
    A = mutate(root, 11, 'SEA SPLIT'); Bc = mutate(root, 12, 'SEER')
    A1 = mutate(A, 21, ''); A2 = mutate(A, 22, 'CONQUEST'); B1 = mutate(Bc, 23, 'PLAGUE')
    A2a = mutate(A2, 31, ''); A2b = mutate(A2, 32, 'CIVIL WAR')
    if A2b['roof'] == A2['roof']:
        alt = [r for r in ('tiered', 'gable', 'flat', 'dome') if r != A2['roof']][0]
        A2b['roof'] = alt; A2b['mut'] = '+' + {'tiered': 'TIERED ROOFS', 'gable': 'GABLES', 'flat': 'FLAT ROOFS', 'dome': 'DOMES'}[alt]
    A2b['rroof'] = A2b['acc']
    x, y, w, h = 6, 44, 228, 422
    frame(f, x, y, w, h, KQ, 'CULTURE TREE')
    t7(f, 14, 58, 'Y0', DIM, sh=False); node(f, 120, 58, root)
    link(f, 120, 77, 62, 110); link(f, 120, 77, 180, 110)
    why(f, 62, 92, 'Y210 SEA SPLIT', CYAN); why(f, 180, 92, 'Y260 SEER', ACC)
    node(f, 62, 110, A); node(f, 180, 110, Bc)
    link(f, 62, 129, 36, 240); link(f, 62, 129, 104, 170); link(f, 180, 129, 180, 170)
    why(f, 104, 150, 'Y540 CONQUEST', BAD); why(f, 186, 150, 'Y610 PLAGUE', GOOD)
    node(f, 104, 170, A2); node(f, 180, 170, B1, alive=False)
    link(f, 104, 189, 96, 240); link(f, 104, 189, 166, 240)
    why(f, 160, 214, 'Y1290 CIVIL WAR', BAD)
    node(f, 36, 240, A1); node(f, 96, 240, A2a); node(f, 172, 240, A2b, sel=True)
    t7(f, 14, 266, 'Y1342  -  4 LIVING CULTURES', DIM, sh=False)
    # selected detail
    yy = 282
    plate(f, 14, yy, 212, 172, BG2, 1); hline(f, 14, yy, 212, A2b['acc'][3])
    c = np.zeros((15, 13, 3), np.uint8); c[:] = BG2; cg.crest(c, 1, 1, A2b, 1)
    f[yy + 6:yy + 36, 20:46] = np.asarray(Image.fromarray(c).resize((26, 30), Image.NEAREST))
    t7(f, 52, yy + 8, A2b['name'], TXT); t7(f, 52, yy + 19, 'BORN Y1290 FROM ' + A2['name'][:7], DIM, sh=False)
    t7(f, 52, yy + 29, 'GENES KEPT 78%', GOOD, sh=False)
    rows = [('LANGUAGE', 'SAME ROOTS (' + root['namer'].word(2) + ')'), ('MUTATED', A2b['mut']), ('VALUES', ' + '.join(A2b['values'])[:22]),
            ('BELIEF', A2b['belief'][:22]), ('RULE', A2b['rule'][:22])]
    for i, (a_, b_) in enumerate(rows):
        t7(f, 20, yy + 44 + i * 12, a_, DIM, sh=False); t7(f, 78, yy + 44 + i * 12, b_, TXT if i != 1 else ACC, sh=False)
    # houses: parent vs child (shows visual drift)
    hv = grass_ground(104, 30, 5, tint=(A2b['tint'], .4))
    cg.gen_house(hv, 6, 26, A2, 2, 5); cg.gen_house(hv, 56, 26, A2b, 2, 5)
    f[yy + 106:yy + 136, 20:124] = hv
    t7(f, 20, yy + 140, 'PARENT', DIM, sh=False); t7(f, 74, yy + 140, 'CHILD', ACC, sh=False)
    button(f, 132, yy + 110, 88, 18, 'COMPARE', rp=KQ); button(f, 132, yy + 134, 88, 18, 'FOLLOW', ic='eye', rp=KQ)
    dock(f, 1)
    return f


# ------------------------------------------------------------------ B. royal clan
def s_clan():
    f = dim(worldmap(), .72, 2)
    topbar(f, 1342, show_lang=False)
    g = cg.make_culture(3)
    clan = g['clans'][0]
    x, y, w, h = 6, 44, 228, 422
    frame(f, x, y, w, h, clan['col'], clan['name'])
    c = np.zeros((15, 13, 3), np.uint8); c[:] = BG; cg.crest(c, 1, 1, g, 1, clan['col'], clan['symbol'])
    f[58:73, 14:27] = c
    t7(f, 32, 58, 'ROYAL CLAN OF ' + g['name'], TXT); t7(f, 32, 68, '48 ALIVE - 211 IN HISTORY', DIM, sh=False)
    meter(f, 160, 68, 60, 5, .82, GOLD[2]); t7(f, 160, 58, 'PRESTIGE', ACC, sh=False)
    # tree
    P = [(120, 86, 'ruler', 'adult', 'm', 'RAERWAE', 'FOUNDER'), (64, 140, 'rich', 'adult', 'f', 'NIRA', ''), (120, 140, 'ruler', 'adult', 'm', 'OSKAR', 'KING II'),
         (176, 140, 'rich', 'adult', 'm', 'TEVO', 'EXILED'), (40, 196, 'rich', 'adult', 'm', 'KAEL', 'KILLED'), (96, 196, 'ruler', 'adult', 'm', 'ORAN', 'KING NOW'),
         (152, 196, 'rich', 'adult', 'f', 'SELA', 'MARRIED'), (200, 196, 'rich', 'adult', 'm', 'VORN', 'NEW KING')]
    for (a_, b_) in [(0, 1), (0, 2), (0, 3), (1, 4), (2, 5), (2, 6), (3, 7)]:
        link(f, P[a_][0], P[a_][1] + 30, P[b_][0], P[b_][1] - 2)
    for i, (px, py, cls, ag, gd, nm, tag) in enumerate(P):
        ring = GOLD[3] if tag.startswith('KING') or tag == 'FOUNDER' or tag == 'NEW KING' else BAD if tag == 'KILLED' else GOLD[1]
        portrait_og(f, px - 8, py, g, cls, ag, gd, 40 + i, 1, ring)
        t7(f, px - t7w(nm) // 2, py + 21, nm, TXT if tag != 'KILLED' else DIM, sh=False)
        if tag: t7(f, px - t7w(tag) // 2, py + 30, tag, {'KILLED': BAD, 'EXILED': ACC, 'NEW KING': CYAN, 'MARRIED': GOOD}.get(tag, GOLD[3]), sh=False)
    # ring between Oran's sister and another clan
    other = g['clans'][1]
    c2 = np.zeros((15, 13, 3), np.uint8); c2[:] = BG; cg.crest(c2, 1, 1, g, 1, other['col'], other['symbol'])
    t7(f, 166, 238, '+', GOOD); f[236:251, 174:187] = c2
    # exiled branch founded a kingdom
    why(f, 186, 182, 'FOUNDS VORNIA', CYAN)
    # events
    yy = 262
    t7(f, 14, yy, 'CLAN STORY', ACC)
    ev = [('Y1301', 'MARRIAGE ALLIANCE WITH ' + other['name'][6:], GOOD), ('Y1318', 'SUCCESSION WAR: OSKAR VS TEVO', BAD), ('Y1319', 'TEVO EXILED, 40 FOLLOW HIM', ACC),
          ('Y1327', 'BLOOD FEUD WITH ' + g['clans'][2]['name'][6:], BAD), ('Y1333', 'KAEL KILLED IN THE FEUD', BAD), ('Y1340', 'VORN CROWNED IN VORNIA', CYAN)]
    for i, (yr, s, col) in enumerate(ev):
        ry = yy + 12 + i * 22
        plate(f, 14, ry, 212, 19, BG2, 1); rect(f, 14, ry, 2, 19, col)
        t7(f, 20, ry + 6, yr, col, sh=False); t7(f, 54, ry + 6, s[:29], TXT, sh=False)
    t7(f, 14, yy + 150, 'TRAITS RUN IN THE BLOOD:', DIM, sh=False)
    cx = 14
    for lab, col in (('STOIC', hx(cg.TRAIT_COL['STOIC'])), ('BRAVE', hx(cg.TRAIT_COL['BRAVE'])), ('PROUD', hx(cg.TRAIT_COL['PROUD']))):
        cx += chip(f, cx, yy + 162, lab, col) + 3
    button(f, 150, yy + 160, 76, 16, 'FOLLOW', ic='eye', rp=clan['col'])
    dock(f, 1)
    return f


# ------------------------------------------------------------------ C. generated plague
def s_plague():
    f = worldmap()
    topbar(f, 1342, show_lang=False)
    # heat overlay
    rr = random.Random(3)
    for (cx, cy, r) in [(80, 340, 34), (110, 310, 22), (60, 380, 18), (140, 260, 12)]:
        m = ellipse_mask(f.shape[:2], cx, cy, r, r * .8)
        yy, xx = np.nonzero(m)
        for (j, i) in zip(yy, xx):
            if (i + j) % 2 == 0 or math.hypot(i - cx, j - cy) < r * .5: f[j, i] = (np.array(f[j, i]) * .45 + np.array(GOOD if math.hypot(i - cx, j - cy) > r * .5 else hx('#d8e04a')) * .55).astype(np.uint8)
    for (x0, y0, x1, y1) in [(96, 316, 136, 266), (70, 360, 52, 400)]:
        for t in range(0, 20, 3):
            put(f, int(x0 + (x1 - x0) * t / 20), int(y0 + (y1 - y0) * t / 20), INK); put(f, int(x0 + (x1 - x0) * t / 20) + 1, int(y0 + (y1 - y0) * t / 20), GOOD)
        rect(f, x1 - 1, y1 - 1, 3, 3, GOOD)
    rect(f, 120, 288, 5, 3, hx('#5a5048')); put(f, 125, 289, hx('#3a3430')); put(f, 119, 287, INK)   # rat on route
    y0 = 56
    rp = [hx('#2a4a1e'), hx('#3e6a2a'), hx('#5e8a2e'), hx('#8ac04a'), hx('#b8e06a')]
    frame(f, 4, y0, 232, 196, rp, 'GREY COUGH')
    t7(f, 12, y0 + 14, 'BORN Y1339 IN SHAARIN SWAMPS', DIM, sh=False)
    t7(f, 12, y0 + 26, 'SPREADS BY', ACC, sh=False)
    cx = 74
    for lab, col, on in (('AIR', CYAN, True), ('RATS', ACC, True), ('WATER', DIM, False), ('ANIMALS', DIM, False)):
        cx += chip(f, cx, y0 + 24, lab, col if on else hx('#5a6270'), fill=None if on else BG2) + 3
    # symptoms: healthy vs sick portraits
    g = cg.make_culture(37)
    portrait_og(f, 14, y0 + 44, g, 'middle', 'adult', 'm', 5, 1, GOOD)
    portrait_og(f, 42, y0 + 44, g, 'middle', 'adult', 'm', 5, 1, BAD, state='sick')
    t7(f, 14, y0 + 66, 'WELL', GOOD, sh=False); t7(f, 42, y0 + 66, 'SICK', BAD, sh=False)
    t7(f, 70, y0 + 46, 'GREY SKIN, COUGH, FEVER', TXT, sh=False)
    t7(f, 70, y0 + 56, 'KILLS 15%, MOSTLY OLD+POOR', DIM, sh=False)
    t7(f, 70, y0 + 66, 'SURVIVORS: IMMUNE', GOOD, sh=False)
    stats = [('INFECTED', '4,120', [1, 2, 4, 7, 12, 20, 29, 35, 40, 41], GOOD), ('DEAD', '610', [0, 0, 1, 1, 2, 3, 4, 5, 6, 6], BAD), ('IMMUNE', '980', [0, 0, 0, 1, 1, 2, 4, 6, 8, 10], CYAN)]
    for i, (lab, v, d, col) in enumerate(stats):
        bx = 12 + i * 74
        plate(f, bx, y0 + 80, 70, 40, BG2, 1); t7(f, bx + 4, y0 + 84, lab, DIM, sh=False); t7(f, bx + 4, y0 + 94, v, col); spark(f, bx + 40, y0 + 92, 26, 10, d, col)
    t7(f, 12, y0 + 128, 'CURES THE WORLD KNOWS', ACC, sh=False)
    cures = [('HERBS', 'ANCIENT', True, .4), ('QUARANTINE', 'MEDIEVAL', True, .7), ('VACCINE', 'MODERN', False, 0)]
    for i, (n, e, ok, p) in enumerate(cures):
        bx = 12 + i * 74
        plate(f, bx, y0 + 138, 70, 34, BG3 if ok else BG2, 1)
        t7(f, bx + 4, y0 + 142, n[:10], TXT if ok else DIM, sh=False)
        if ok: meter(f, bx + 4, y0 + 154, 62, 6, p, GOOD); t7(f, bx + 4, y0 + 163, 'IN USE', GOOD, sh=False)
        else: icon(f, bx + 4, y0 + 153, 'lock'); t7(f, bx + 14, y0 + 155, e, DIM, sh=False)
    button(f, 12, y0 + 178 - 2, 104, 14, 'CURE IT (BLESS)', rp=rp, style='on'); button(f, 122, y0 + 178 - 2, 104, 14, 'LET IT RUN', rp=rp)
    dock(f, 0)
    return f


# ------------------------------------------------------------------ D. war fronts
def s_war():
    f = worldmap()
    topbar(f, 1342, show_lang=False)
    # front line (jagged) between qarnah (left) and velmora (right)
    pts = [(108, 150), (112, 172), (104, 196), (116, 218), (110, 240), (122, 262), (116, 286)]
    for (a_, b_) in zip(pts, pts[1:]):
        n = 20
        for t in range(n + 1):
            xx = int(a_[0] + (b_[0] - a_[0]) * t / n); yy = int(a_[1] + (b_[1] - a_[1]) * t / n)
            rect(f, xx - 2, yy, 2, 1, KQ[2]); rect(f, xx, yy, 2, 1, KV[2]); put(f, xx - 3, yy, INK); put(f, xx + 2, yy, INK)
    # push arrows (qarnah advancing in middle)
    def chev(cx, cy, col, d=1):
        for i in range(5): hline(f, cx + d * i - (4 if d < 0 else 0), cy - 4 + i, 4, col); hline(f, cx + d * i - (4 if d < 0 else 0), cy + 4 - i, 4, col)
    chev(116, 206, KQ[3]); chev(126, 206, KQ[2]); chev(98, 262, KV[3], -1)
    # army counters
    def counter(x, y, rp, ic, n):
        rect(f, x + 1, y + 1, 26, 12, INK); rect(f, x, y, 26, 12, rp[1]); hline(f, x, y, 26, rp[3]); icon(f, x + 2, y + 2, ic); t7(f, x + 11, y + 3, n, TXT, sh=False)
    counter(76, 180, KQ, 'sword', '900'); counter(70, 222, KQ, 'shield', '400'); counter(132, 166, KV, 'sword', '1.2K'); counter(140, 236, KV, 'gear', '6')
    # siege
    sx, sy = 150, 206
    rect(f, sx - 3, sy - 3, 7, 7, KV[0]); rect(f, sx - 2, sy - 2, 5, 5, KV[3])
    for t in np.linspace(0, 2 * math.pi, 9)[:-1]:
        tx, ty = int(sx + 11 * math.cos(t)), int(sy + 8 * math.sin(t))
        put(f, tx, ty, KQ[3]); put(f, tx - 1, ty + 1, KQ[2]); put(f, tx + 1, ty + 1, KQ[2])
    why(f, sx, sy + 12, 'SIEGE 14 DAYS', BAD)
    # supply lines
    for (x0, y0, x1, y1, cut) in [(60, 150, 104, 196, False), (60, 150, 100, 250, True)]:
        for t in range(0, 30, 2):
            put(f, int(x0 + (x1 - x0) * t / 30), int(y0 + (y1 - y0) * t / 30), GOLD[3])
        if cut:
            mx, my = (x0 + x1) // 2, (y0 + y1) // 2
            for i in range(-3, 4): put(f, mx + i, my + i, BAD); put(f, mx + i, my - i, BAD)
    y0 = 300
    frame(f, 4, y0, 232, 172, KQ, 'WAR OF THE IRON HILLS', alpha=.985)
    t7(f, 12, y0 + 14, 'QARNAH', KQ[3]); t7(f, 228 - t7w('VELMORA'), y0 + 14, 'VELMORA', KV[3])
    rect(f, 12, y0 + 25, 216, 8, INK); rect(f, 13, y0 + 26, 124, 6, KQ[2]); rect(f, 137, y0 + 26, 90, 6, KV[2]); rect(f, 136, y0 + 24, 2, 10, TXT)
    t7(f, 12, y0 + 38, 'CAUSE: THE IRON MINES', ACC, sh=False); t7(f, 140, y0 + 38, 'DAY 212', DIM, sh=False)
    rows = [('KNIGHTS+PIKES', 'MUSKETS+CANNON'), ('LOST 2,140', 'LOST 3,010'), ('SUPPLY 64%', 'SUPPLY 41%')]
    for i, (a_, b_) in enumerate(rows):
        t7(f, 12, y0 + 52 + i * 11, a_[:15], TXT if i else DIM, sh=False); t7(f, 124, y0 + 52 + i * 11, b_[:17], TXT if i else DIM, sh=False)
    plate(f, 12, y0 + 88, 216, 34, BG2, 1); rect(f, 12, y0 + 88, 2, 34, ACC)
    t7(f, 18, y0 + 92, 'QARNAH HAS NO COAL', ACC, sh=False); t7(f, 18, y0 + 102, '-> CANNOT BUILD CANNONS', TXT, sh=False)
    t7(f, 18, y0 + 112, 'VELMORA SUPPLY LINE CUT AT RUSA', BAD, sh=False)
    button(f, 12, y0 + 130, 70, 18, 'BATTLE CAM', ic='eye', rp=KQ); button(f, 86, y0 + 130, 66, 18, 'HISTORY', rp=KQ)
    button(f, 156, y0 + 130, 72, 18, 'FORCE PEACE', style='gold', rp=KQ)
    dock(f, 0)
    return f


# ------------------------------------------------------------------ E. legends
def s_hero():
    cv = city_view()
    f = np.zeros((PH, PW, 3), np.uint8); f[:] = BG
    f[26:26 + 300] = dim(np.asarray(Image.fromarray(cv[0:150, 60:180]).resize((240, 300), Image.NEAREST)), .55)
    topbar(f, 1342, show_lang=False)
    g = cg.make_culture(37)
    x, y, w, h = 6, 44, 228, 422
    frame(f, x, y, w, h, GOLD, 'A LEGEND IS BORN')
    portrait_og(f, 16, 58, g, 'middle', 'adult', 'f', 77, 3, GOLD[3])
    t7(f, 74, 60, 'ORMA', TXT, scale=2); t7(f, 74, 78, 'THE BEAR-SLAYER', ACC)
    t7(f, 74, 90, 'HUNTER - AGE 31', DIM, sh=False)
    cx = 74
    for lab, col in (('BRAVE', hx(cg.TRAIT_COL['BRAVE'])), ('KIND', hx(cg.TRAIT_COL['KIND']))): cx += chip(f, cx, 100, lab, col) + 3
    for i, (lab, v) in enumerate((('FAME', .92), ('STRENGTH', .78), ('WISDOM', .41))):
        t7(f, 74, 116 + i * 10, lab, DIM, sh=False); meter(f, 130, 115 + i * 10, 90, 6, v, [GOLD[2], BAD, CYAN][i])
    t7(f, 14, 150, 'DEEDS', ACC)
    deeds = [('Y1331', 'KILLED THE GREAT BEAR OF TALEM', 'sword'), ('Y1334', 'SAVED 12 CHILDREN FROM WOLVES', 'shield'), ('Y1338', 'LED THE DEFENCE OF RUSA', 'flag'),
             ('Y1340', 'REFUSED THE CROWN', 'crown')]
    for i, (yr, s, ic) in enumerate(deeds):
        ry = 162 + i * 24
        plate(f, 14, ry, 212, 21, BG2, 1); rect(f, 14, ry, 2, 21, GOLD[2])
        icon(f, 20, ry + 7, ic); t7(f, 32, ry + 3, yr, GOLD[3], sh=False); t7(f, 32, ry + 12, s[:31], TXT, sh=False)
    # legendary item + statue
    yy = 262
    plate(f, 14, yy, 102, 74, BG2, 1); t7(f, 18, yy + 4, 'RELIC', ACC, sh=False)
    sp = np.zeros((14, 30, 3), np.uint8); sp[:] = BG2
    for i in range(26): put(sp, 2 + i, 9 - i // 4, C['wood'][2])
    rect(sp, 24, 1, 4, 3, hx('#ece4d2')); put(sp, 27, 1, hx('#ffffff')); put(sp, 6, 8, hx('#c83a3a')); put(sp, 7, 7, hx('#c83a3a'))
    f[yy + 16:yy + 44, 18:78] = np.asarray(Image.fromarray(sp).resize((60, 28), Image.NEAREST))
    t7(f, 18, yy + 50, 'BONE SPEAR', TXT, sh=False); t7(f, 18, yy + 60, '+20 VS BEASTS', GOOD, sh=False)
    plate(f, 122, yy, 104, 74, BG2, 1); t7(f, 126, yy + 4, 'MONUMENT', ACC, sh=False)
    st = grass_ground(30, 30, 3)
    rect(st, 8, 22, 14, 6, R['stone'][1]); hline(st, 8, 22, 14, R['stone'][3])
    person2(st, 7, -4, None, 'middle', 'adult', 'f', 0, seed=77, og=g, shadow=False)
    m = np.any(st[0:22] != grass_ground(30, 30, 3)[0:22], axis=2)
    gm = (np.asarray(st[0:22]).mean(axis=2, keepdims=True) * .7 + 70).clip(0, 255).astype(np.uint8)
    st[0:22][m] = np.repeat(gm, 3, axis=2)[m]
    f[yy + 14:yy + 44, 136:196] = np.asarray(Image.fromarray(st).resize((60, 30), Image.NEAREST))[:, :60] if False else np.asarray(Image.fromarray(st[:, 0:30]).resize((60, 30), Image.NEAREST))
    t7(f, 126, yy + 50, 'STATUE IN QARNAH', TXT, sh=False); t7(f, 126, yy + 60, 'PILGRIMS +5% JOY', GOOD, sh=False)
    t7(f, 14, yy + 84, 'HER CHILDREN INHERIT', DIM, sh=False); chip(f, 136, yy + 82, 'BRAVE', hx(cg.TRAIT_COL['BRAVE']))
    t7(f, 14, yy + 98, 'SONGS ABOUT HER: 3 CULTURES', DIM, sh=False)
    button(f, 14, yy + 116, 102, 20, 'FOLLOW ORMA', ic='eye', rp=GOLD); button(f, 122, yy + 116, 104, 20, 'LIFE STORY', rp=GOLD)
    dock(f, 3)
    return f


# ------------------------------------------------------------------ F. WHY chain
def s_why():
    cv = city_view()
    f = np.zeros((PH, PW, 3), np.uint8); f[:] = BG
    f[26:26 + 300] = np.asarray(Image.fromarray(cv[40:190, 150:270]).resize((240, 300), Image.NEAREST))
    blend_rect(f, 0, 26, PW, 300, hx('#c8a050'), .12)
    topbar(f, 1342, show_lang=False)
    # tapped marker
    rect(f, 110, 60, 15, 15, INK); rect(f, 111, 61, 13, 13, ACC); t7(f, 115, 64, '?', INK, sh=False)
    for i in range(6): put(f, 117, 76 + i, ACC)
    x, y, w, h = 6, 108, 228, 364
    frame(f, x, y, w, h, KQ, 'WHY IS TALEM STARVING?')
    chain = [('FAMINE', 'FOOD -40/DAY, 112 DEAD', 'food', BAD), ('DROUGHT', 'Y1338 - NO RAIN 2 YEARS', 'energy', ACC),
             ('FORESTS CUT', 'Y1330 - SOIL DRIED OUT', 'tree', ACC), ('POPULATION BOOM', 'Y1325 - 3X PEOPLE', 'pop', CYAN),
             ('NEW IRON MINE', 'Y1320 - WORKERS ARRIVED', 'iron', GOOD)]
    for i, (n, s, ic, col) in enumerate(chain):
        ry = y + 16 + i * 46
        plate(f, 14, ry, 212, 34, BG2, 1); rect(f, 14, ry, 2, 34, col)
        rect(f, 20, ry + 7, 20, 20, INK); rect(f, 21, ry + 8, 18, 18, BG3); icon(f, 23, ry + 10, ic, 2)
        t7(f, 46, ry + 7, n, col); t7(f, 46, ry + 19, s, TXT, sh=False)
        if i < len(chain) - 1:
            for k in range(8): put(f, 120, ry + 35 + k, DIM)
            t7(f, 124, ry + 37, 'BECAUSE', DIM, sh=False)
    yy = y + 16 + 5 * 46
    t7(f, 14, yy, 'MOST LIKELY NEXT', ACC)
    for i, (s, p, col) in enumerate((('PEOPLE MIGRATE TO QARNAH', .62, GOOD), ('BREAD RIOTS', .3, BAD))):
        t7(f, 14, yy + 12 + i * 12, s, TXT, sh=False); meter(f, 170, yy + 11 + i * 12, 40, 6, p, col); t7(f, 214, yy + 12 + i * 12, str(int(p * 100)), col, sh=False)
    button(f, 14, yy + 40, 104, 18, 'SEND RAIN', style='on', rp=KQ); button(f, 122, yy + 40, 104, 18, 'JUST WATCH', ic='eye', rp=KQ)
    dock(f, 0)
    return f


if __name__ == '__main__':
    compose([s_tree(), s_clan(), s_plague()], ['A. CULTURES SPLIT & EVOLVE', 'B. ROYAL CLANS & FEUDS', 'C. PLAGUES ARE GENERATED'], 'systems_1.png')
    compose([s_war(), s_hero(), s_why()], ['D. WAR FRONTS & SUPPLY', 'E. HEROES BECOME LEGENDS', 'F. TAP ANYTHING: WHY?'], 'systems_2.png')
