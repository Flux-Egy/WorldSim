"""v2 observer UI: WATCH / NATION (AR) / CITY+PERSON / CHRONICLE (AR) / POWERS / TAKE CONTROL."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from lib import *
from ui2kit import *
import ui
from buildings import BUILD
from catalog import fine_fx, measure

PW, PH = 240, 520
for _n in ('top_hud', 'zoom_rail', 'dock'): setattr(ui, _n, lambda *a, **k: None)


def worldmap():
    return ui.far_screen()


def dim(f, k=.55, blur=0):
    im = Image.fromarray(f)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(im).astype(np.float32) * (1 - k) + np.array(BG, np.float32) * k
    return a.astype(np.uint8).copy()


def ar_digits(n):
    return str(n).translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩'))


# ------------------------------------------------------------------ shared chrome
def topbar(f, year, rp=R['K'], lang='EN', mode='WATCHING', show_lang=True):
    plate(f, 0, 0, PW, 24, BG, .95)
    hline(f, 0, 24, PW, GOLD[1]); hline(f, 0, 25, PW, INK)
    picon(f, 3, 6, 'eye') if mode == 'WATCHING' else picon(f, 3, 6, 'crown')
    if lang == 'EN':
        t7(f, 17, 4, 'YEAR ' + str(year), TXT)
        t7(f, 17, 14, mode, GOOD if mode == 'WATCHING' else ACC, sh=False)
    else:
        ar(f, 112, 1, 'سنة ' + ar_digits(year), TXT, 11)
        ar(f, 112, 12, 'وضع المشاهدة' if mode == 'WATCHING' else 'أنت تحكم', GOOD if mode == 'WATCHING' else ACC, 10, sh=False)
    # speed pills
    labs = ['||', '1x', '2x', '5x']
    for i, lab in enumerate(labs):
        bx = 120 + i * 21
        button(f, bx, 5, 19, 14, lab, style='primary' if i == 2 else 'ghost', rp=rp)
    # language toggle
    if not show_lang:
        button(f, 206, 5, 31, 14, '', rp=rp); icon(f, 218, 8, 'gear'); return
    rect(f, 206, 5, 31, 14, INK); rect(f, 207, 6, 14, 12, rp[2] if lang == 'EN' else BG3); t7(f, 209, 9, 'EN', TXT, sh=False)
    rect(f, 222, 6, 14, 12, rp[2] if lang == 'AR' else BG3); ar(f, 233, 4, 'ع', TXT, 10, sh=False)


DOCK = [('eye', 'WATCH', 'مشاهدة'), ('crown', 'NATIONS', 'الدول'), ('book', 'HISTORY', 'السجل'), ('human', 'FOLLOW', 'تتبّع'), ('bolt', 'POWERS', 'القوى')]


def dock(f, active, lang='EN', rp=R['K']):
    y0 = PH - 44
    plate(f, 0, y0, PW, 44, BG, .96)
    hline(f, 0, y0, PW, GOLD[1]); hline(f, 0, y0 + 1, PW, GOLD[3]); hline(f, 0, y0 + 2, PW, INK)
    bw = PW // len(DOCK)
    order = DOCK if lang == 'EN' else DOCK[::-1]
    for i, (ic, en, arl) in enumerate(order):
        bx = i * bw
        act = (DOCK.index((ic, en, arl)) == active)
        if act:
            rect(f, bx + 2, y0 + 5, bw - 4, 37, rp[1]); hline(f, bx + 2, y0 + 5, bw - 4, rp[3]); rect(f, bx + bw // 2 - 6, y0 + 3, 12, 2, GOLD[3])
        if ic == 'bolt' and not act:
            blend_mask(f, ellipse_mask(f.shape[:2], bx + bw // 2, y0 + 16, 11, 9), hx('#9d76c2'), .35)
        picon(f, bx + bw // 2 - 5, y0 + 9, ic)
        if lang == 'EN': t7(f, bx + bw // 2 - t7w(en) // 2, y0 + 26, en if len(en) <= 7 else en[:6] + '.', TXT if act else DIM)
        else: ar(f, bx + bw // 2, y0 + 23, arl, TXT if act else DIM, 10, anchor='c')


# ------------------------------------------------------------------ 1. WATCH
NATS = [('QARNAH', 'K', 'MEDIEVAL', 18420, [5, 6, 6, 7, 9, 10, 12, 13, 15, 18]), ('VELMORA', 'blue', 'INDUSTRIAL', 31200, [8, 9, 11, 14, 17, 20, 22, 26, 28, 31]),
        ('SHAARIN', 'violet', 'ANCIENT', 9100, [6, 7, 7, 8, 8, 9, 9, 9, 9, 9]), ('OKKU', 'gold', 'STONE', 1300, [4, 4, 5, 5, 4, 3, 3, 2, 2, 1])]


def s_watch():
    f = worldmap()
    topbar(f, 1342)
    # nations ranking
    x, y, w, h = 128, 40, 108, 120
    frame(f, x, y, w, h, R['K'], 'NATIONS')
    for i, (n, k, e, p, d) in enumerate(NATS):
        yy = y + 13 + i * 26
        rp = KR[k]
        rect(f, x + 7, yy, 9, 9, rp[1]); rect(f, x + 8, yy + 1, 7, 7, rp[2]); hline(f, x + 8, yy + 1, 7, rp[3]); put(f, x + 11, yy + 4, TXT)
        t7(f, x + 20, yy + 1, n, TXT)
        t7(f, x + 20, yy + 11, e[:5], DIM, sh=False)
        col = GOOD if d[-1] >= d[-3] else BAD
        spark(f, x + 52, yy + 10, 30, 9, d, col)
        t7(f, x + w - 8 - t7w(str(p // 1000) + 'K'), yy + 1, str(p // 1000) + 'K', col)
        t7(f, x + 86, yy + 11, '^' if col == GOOD else 'v', col, sh=False)
    # chronicle toast pointing at Velmora
    tx, ty = 18, 182
    frame(f, tx, ty, 150, 34, KR['blue'])
    picon(f, tx + 8, ty + 11, 'inspire')
    t7(f, tx + 24, ty + 8, 'VELMORA INVENTS', TXT); t7(f, tx + 24, ty + 18, 'THE STEAM ENGINE', ACC)
    for i in range(14): put(f, tx + 150 + i, ty + 20 + i // 2, GOLD[3])
    # follow pin
    rect(f, 6, 30, 92, 15, INK); rect(f, 6, 30, 91, 14, BG2); hline(f, 6, 30, 91, BG3)
    picon(f, 8, 32, 'human'); t7(f, 21, 34, 'AUTO-CAM: ON', GOOD, sh=False)
    # chronicle ticker
    y0 = PH - 44 - 32
    plate(f, 0, y0, PW, 32, INK, .96); hline(f, 0, y0, PW, BG3)
    t7(f, 6, y0 + 5, '1342', ACC); t7(f, 32, y0 + 5, 'OKKU LOSES ITS CHIEF TO WOLVES', TXT)
    t7(f, 6, y0 + 18, '1341', DIM); t7(f, 32, y0 + 18, 'QARNAH OPENS AN IRON MINE', DIM, sh=False)
    dock(f, 0)
    return f


# ------------------------------------------------------------------ 2. NATION (AR)
def s_nation():
    f = dim(worldmap(), .6, 1.2)
    topbar(f, 1342, lang='AR')
    rp = R['K']
    x, y, w, h = 6, 44, 228, 422
    frame(f, x, y, w, h, rp, ar_title='مملكة قرنة', ribbon_w=110)
    # header: portrait right (RTL), name + title
    portrait(f, x + w - 46, y + 18, 'riverland', 'ruler', 'adult', 'm', 7, rp)
    ar(f, x + w - 54, y + 16, 'الملك أوران الثاني', TXT, 12)
    ar(f, x + w - 54, y + 33, 'العمر ' + ar_digits(54) + ' · حكيم · طموح', DIM, 10)
    ar(f, x + w - 54, y + 48, 'ثقافة: أهل النهر', ACC, 10)
    # era progress
    yy = y + 70
    plate(f, x + 8, yy, w - 16, 34, BG2, 1)
    ar(f, x + w - 12, yy + 1, 'العصر الوسيط', TXT, 11)
    ar(f, x + 120, yy + 2, 'التالي: الصناعي', DIM, 10)
    meter(f, x + 14, yy + 20, w - 28, 8, .62, GOLD[2])
    t7(f, x + 16, yy + 6, '62%', ACC)
    # stats 2x2 with sparklines
    stats = [('السكان', '18,420', 'pop', [5, 6, 6, 7, 9, 10, 12, 13, 15, 18], GOOD), ('الثروة', '4,210', 'gold', [3, 4, 4, 5, 5, 6, 7, 7, 8, 9], GOOD),
             ('الجيش', '1,150', 'sword', [6, 6, 7, 7, 8, 8, 7, 6, 6, 5], BAD), ('المعرفة', '880', 'know', [1, 2, 2, 3, 4, 5, 6, 8, 9, 11], GOOD)]
    for i, (lab, val, ic, d, col) in enumerate(stats):
        cx = x + 8 + (1 - i % 2) * 108; cy = yy + 42 + (i // 2) * 46
        plate(f, cx, cy, 104, 42, BG2, 1); hline(f, cx, cy, 104, BG3)
        icon(f, cx + 92, cy + 5, ic)
        ar(f, cx + 88, cy + 1, lab, DIM, 10, sh=False)
        t7(f, cx + 6, cy + 5, val, TXT)
        spark(f, cx + 6, cy + 20, 92, 17, d, col)
    # society
    yy2 = yy + 42 + 92 + 4
    ar(f, x + w - 12, yy2, 'طبقات المجتمع', TXT, 11)
    parts = [(.52, hx('#8a7a5e'), 'فقراء ٥٢٪'), (.36, hx('#3a8a86'), 'متوسطة ٣٦٪'), (.12, GOLD[2], 'أغنياء ١٢٪')]
    bx = x + w - 12; by = yy2 + 18; bw = w - 24
    rect(f, x + 11, by - 1, bw + 2, 10, INK)
    for frac, col, lab in parts:
        ww = int(bw * frac); rect(f, bx - ww, by, ww, 8, col); hline(f, bx - ww, by, ww, lit(col, .3)); bx -= ww
    lx = x + w - 12
    for frac, col, lab in parts:
        rect(f, lx - 6, by + 14, 5, 5, col); x0, ww = ar(f, lx - 9, by + 10, lab, DIM, 10, sh=False); lx = x0 - 8
    # relations
    yy3 = by + 34
    ar(f, x + w - 12, yy3, 'العلاقات', TXT, 11)
    rels = [('VELMORA', 'blue', 'حليف', GOOD, 'peace'), ('OKKU', 'gold', 'حرب', BAD, 'war'), ('SHAARIN', 'violet', 'تجارة', ACC, 'gold')]
    for i, (n, k, lab, col, ic) in enumerate(rels):
        cx = x + w - 12 - (i + 1) * 70 + 4
        plate(f, cx, yy3 + 18, 66, 32, BG2, 1); rect(f, cx, yy3 + 18, 66, 2, col)
        rect(f, cx + 54, yy3 + 24, 8, 8, KR[k][2]); hline(f, cx + 54, yy3 + 24, 8, KR[k][3])
        t7(f, cx + 4, yy3 + 25, n[:7], TXT)
        ar(f, cx + 62, yy3 + 33, lab, col, 10, sh=False)
    # latest
    yl = yy3 + 58
    plate(f, x + 8, yl, w - 16, 40, BG2, 1); rect(f, x + w - 10, yl, 2, 40, BAD)
    ar(f, x + w - 14, yl + 1, 'آخر حدث: إعلان الحرب على أوكّو', TXT, 10)
    ar(f, x + w - 14, yl + 19, 'الجيش يتجه شرقًا · ١٢ يومًا', DIM, 10, sh=False)
    # actions
    by2 = y + h - 52
    hline(f, x + 8, by2 - 6, w - 16, BG3)
    button(f, x + w - 78, by2, 70, 20, ar_label='متابعة', ic='eye', rp=rp)
    button(f, x + w - 152, by2, 70, 20, ar_label='السجل', ic='know', rp=rp)
    button(f, x + 8, by2, 68, 20, ar_label='تولَّ الحكم', style='gold', rp=rp)
    ar(f, x + w // 2, by2 + 24, 'يمكنك الرجوع للمشاهدة في أي وقت', DIM, 10, anchor='c', sh=False)
    dock(f, 1, 'AR')
    return f


# ------------------------------------------------------------------ 3. CITY + PERSON
def city_view():
    import culturecity as cc
    a, occ, fx, lc = cc.city('riverland')
    fv = upscale(a, 2); fine_fx(fv, fx, 2); cc.people(fv, occ, 'riverland', 11)
    return fv


def s_city():
    cv = city_view()
    f = np.zeros((PH, PW, 3), np.uint8); f[:] = BG
    f[26:26 + 300] = np.asarray(Image.fromarray(cv[0:150, 40:160]).resize((240, 300), Image.NEAREST))
    topbar(f, 1342)
    rp = R['K']
    # selected person marker
    px, py = 150, 236
    for t in np.linspace(0, 2 * math.pi, 40):
        put(f, int(px + 9 * math.cos(t)), int(py + 4 * math.sin(t)), GOLD[3])
    for i in range(6): put(f, px - 2 + i % 2, py - 22 - i, GOLD[3])
    rect(f, px - 3, py - 30, 7, 3, GOLD[3])
    # person card (floating)
    x, y, w, h = 8, 34, 150, 102
    frame(f, x, y, w, h, rp)
    portrait(f, x + 10, y + 10, 'riverland', 'middle', 'adult', 'f', 21, rp)
    t7(f, x + 50, y + 10, 'NURA', TXT); t7(f, x + 50 + t7w('NURA') + 5, y + 10, '27', DIM)
    t7(f, x + 50, y + 21, 'WEAVER', ACC); t7(f, x + 50, y + 31, 'MIDDLE CLASS', DIM, sh=False)
    cx_ = x + 50
    for lab, col in (('KIND', GOOD), ('CLEVER', CYAN)):
        cx_ += chip(f, cx_, y + 42, lab, col) + 3
    t7(f, x + 10, y + 58, 'MOTHER OF 2 - WIFE OF HADI', DIM, sh=False)
    t7(f, x + 10, y + 69, 'MOOD', DIM, sh=False); meter(f, x + 36, y + 68, 60, 8, .74, GOOD)
    t7(f, x + 10, y + 82, 'NOW: CARRYING WATER HOME', TXT)
    button(f, x + w - 34, y + 66, 26, 14, '', ic=None, style='ghost', rp=rp); picon(f, x + w - 26, y + 68, 'eye')
    # city sheet
    y0 = 300
    frame(f, 4, y0, 232, 172, rp, 'QARNAH  -  CAPITAL')
    t7(f, 12, y0 + 14, 'POP 6,240', TXT); t7(f, 84, y0 + 14, 'MOOD', DIM, sh=False); meter(f, 110, y0 + 13, 50, 8, .66, GOOD)
    t7(f, 168, y0 + 14, 'FOOD +38', GOOD)
    t7(f, 12, y0 + 30, 'HOUSING', ACC)
    tiers = [('SLUM', 140, hx('#7a6a54')), ('POOR', 610, hx('#a8865a')), ('MIDDLE', 420, hx('#3a8a86')), ('RICH', 96, GOLD[2]), ('PALACE', 1, hx('#e8e2d4'))]
    tot = sum(t[1] for t in tiers); bx = 12
    rect(f, 11, y0 + 41, 218, 10, INK)
    for n, c, col in tiers:
        ww = max(3, int(216 * c / tot)); rect(f, bx, y0 + 42, ww, 8, col); hline(f, bx, y0 + 42, ww, lit(col, .3)); bx += ww
    for i, (n, c, col) in enumerate(tiers):
        lx = 12 + i * 44
        rect(f, lx, y0 + 56, 5, 5, col); t7(f, lx + 8, y0 + 55, n[:4], DIM, sh=False); t7(f, lx + 8, y0 + 64, str(c), TXT)
    t7(f, 12, y0 + 80, 'LEADER', ACC); t7(f, 56, y0 + 80, 'LORD ORAN II', TXT)
    t7(f, 12, y0 + 92, 'BUILDING', ACC); t7(f, 64, y0 + 92, 'GREAT LIBRARY 71%', TXT); meter(f, 12, y0 + 102, 216, 6, .71, GOLD[2])
    button(f, 12, y0 + 118, 66, 20, 'FOLLOW', ic='eye', rp=rp)
    button(f, 84, y0 + 118, 72, 20, 'CHRONICLE', rp=rp)
    button(f, 162, y0 + 118, 66, 20, 'CONTROL', ic='crown', style='gold', rp=rp)
    t7(f, 12, y0 + 146, 'TAP ANYONE TO SEE THEIR LIFE STORY', DIM, sh=False)
    dock(f, 3)
    return f


# ------------------------------------------------------------------ 4. CHRONICLE (AR)
EVENTS = [(1342, 'war', BAD, 'قرنة تعلن الحرب على أوكّو'), (1341, 'inspire', CYAN, 'فيلمورا تخترع المحرّك البخاري'), (1338, 'crown', GOLD[3], 'تتويج الملك أوران الثاني'),
          (1333, 'plague', hx('#8ac04a'), 'وباء في شارين يقتل ألفًا'), (1329, 'tree', GOOD, 'قرية جديدة: تلّ الصفصاف'), (1320, 'quake', hx('#c4a06a'), 'زلزال يهدم سور أوكّو'),
          (1311, 'peace', TXT, 'سلام بين قرنة وفيلمورا'), (1302, 'human', ACC, 'ولادة أوران، ابن الملك')]


def s_chron():
    f = dim(worldmap(), .7, 2)
    topbar(f, 1342, lang='AR')
    rp = R['K']
    x, y, w, h = 6, 44, 228, 422
    frame(f, x, y, w, h, rp, ar_title='سجل العالم', ribbon_w=96, alpha=.97)
    cx = x + w - 10
    for i, lab in enumerate(['الكل', 'حروب', 'اختراعات', 'حكّام']):
        ww = arw(lab, 11) + 10
        rect(f, cx - ww, y + 13, ww, 19, rp[2] if i == 0 else BG2); hline(f, cx - ww, y + 13, ww, rp[3] if i == 0 else BG3)
        ar(f, cx - 5, y + 15, lab, TXT if i == 0 else DIM, 11, sh=False); cx -= ww + 4
    lx = x + w - 30
    vline(f, lx + 5, y + 40, h - 52, GOLD[1])
    for i, (yr, ic, col, txt) in enumerate(EVENTS):
        yy = y + 40 + i * 46
        plate(f, x + 10, yy, lx - x - 14, 40, BG2, 1); rect(f, lx - 6, yy, 2, 40, col)
        rect(f, lx, yy + 12, 12, 12, INK); rect(f, lx + 1, yy + 13, 10, 10, BG3)
        picon(f, lx + 1, yy + 13, ic) if False else None
        rect(f, lx + 3, yy + 15, 6, 6, col); put(f, lx + 4, yy + 16, lit(col, .5))
        ar(f, lx - 10, yy + 1, 'سنة ' + ar_digits(yr), col, 10, sh=False)
        ar(f, lx - 10, yy + 17, txt, TXT, 11)
        picon(f, x + 14, yy + 15, ic)
    dock(f, 2, 'AR')
    return f


# ------------------------------------------------------------------ 5. POWERS
POW = {'NATURE': [('rain', 'RAIN'), ('drought', 'DROUGHT'), ('bolt', 'LIGHTNING'), ('quake', 'QUAKE'), ('meteor', 'METEOR'), ('fire', 'WILDFIRE')],
       'LIFE': [('human', 'HUMANS'), ('sheep', 'ANIMALS'), ('tree', 'FOREST')],
       'FATE': [('bless', 'BLESS'), ('plague', 'PLAGUE'), ('inspire', 'INSPIRE')],
       'NATIONS': [('war', 'WAR'), ('peace', 'PEACE'), ('crown', 'CONTROL')]}


def s_powers():
    f = worldmap()
    topbar(f, 1342)
    # targeting reticle + meteor preview
    tx, ty = 92, 150
    blend_mask(f, ellipse_mask(f.shape[:2], tx, ty, 22, 22), hx('#f49a3c'), .18)
    for t in np.linspace(0, 2 * math.pi, 80):
        if int(t * 8) % 2: put(f, int(tx + 22 * math.cos(t)), int(ty + 22 * math.sin(t)), hx('#ffd34a'))
    for d in (-1, 1):
        hline(f, tx + d * 26 - (6 if d < 0 else 0), ty, 7, hx('#ffd34a')); vline(f, tx, ty + d * 26 - (6 if d < 0 else 0), 7, hx('#ffd34a'))
    for i in range(18): put(f, tx + 30 - i, ty - 46 + i * 2, hx('#ffb84a')); put(f, tx + 31 - i, ty - 46 + i * 2, hx('#fff2b0') if i > 12 else hx('#f49a3c'))
    rp = K2['violet']
    plate(f, tx - 46, ty + 30, 92, 24, INK, .8)
    t7(f, tx - 40, ty + 34, 'TARGET: TALEM', TXT); t7(f, tx - 40, ty + 44, 'EST. -400 POP', BAD, sh=False)
    # drawer
    y0 = 262
    frame(f, 4, y0, 232, PH - 44 - y0 - 4, rp, 'POWERS', alpha=.985)
    tabs = list(POW.keys())
    for i, t in enumerate(tabs):
        bw = 54; bx = 10 + i * (bw + 2)
        rect(f, bx, y0 + 13, bw, 13, rp[2] if i == 0 else BG2); hline(f, bx, y0 + 13, bw, rp[3] if i == 0 else BG3)
        t7(f, bx + (bw - t7w(t)) // 2, y0 + 16, t, TXT if i == 0 else DIM, sh=False)
    items = POW['NATURE']
    for i, (ic, lab) in enumerate(items):
        bx = 12 + (i % 3) * 73; by = y0 + 34 + (i // 3) * 58
        sel = ic == 'meteor'
        rect(f, bx + 1, by + 1, 68, 52, INK)
        rect(f, bx, by, 68, 52, rp[1] if sel else BG2); hline(f, bx, by, 68, rp[3] if sel else BG3)
        if sel:
            for k in range(2): hline(f, bx, by + 51 - k, 68, GOLD[2]); vline(f, bx + k, by, 52, GOLD[2]); vline(f, bx + 67 - k, by, 52, GOLD[2]); hline(f, bx, by + k, 68, GOLD[3])
        picon(f, bx + 23, by + 7, ic, 2)
        t7(f, bx + 34 - t7w(lab) // 2, by + 37, lab, TXT if sel else DIM)
        if ic == 'quake':  # cooldown overlay
            blend_rect(f, bx, by, 68, 52, INK, .55)
            for k in range(26): put(f, bx + 34 + int(14 * math.cos(-math.pi / 2 + k * .17)), by + 26 + int(14 * math.sin(-math.pi / 2 + k * .17)), ACC)
            t7(f, bx + 26, by + 23, '12S', TXT)
    # tooltip
    yy = y0 + 152
    plate(f, 12, yy, 216, 26, BG2, 1); rect(f, 12, yy, 2, 26, hx('#f49a3c'))
    t7(f, 18, yy + 4, 'METEOR - TAP THE MAP TO DROP', TXT); t7(f, 18, yy + 14, 'NATIONS WILL REMEMBER IT', DIM, sh=False)
    dock(f, 4, rp=rp)
    return f


# ------------------------------------------------------------------ 6. TAKE CONTROL
def s_control():
    import scenes
    a, occ, fx = scenes.build_scene(2, 1, seed=3)
    cv = upscale(a, 2); fine_fx(cv, fx, 2); scenes.populate(cv, occ, 2, 1, seed=3)
    f = np.zeros((PH, PW, 3), np.uint8); f[:] = BG
    f[26:26 + 384] = np.asarray(Image.fromarray(cv[0:192, 24:144]).resize((240, 384), Image.NEAREST))
    rp = R['K']
    topbar(f, 1342, rp, mode='YOU RULE')
    # control banner
    plate(f, 0, 26, PW, 22, rp[1], .92); hline(f, 0, 47, PW, GOLD[2])
    picon(f, 4, 31, 'crown'); t7(f, 18, 30, 'YOU RULE QARNAH', TXT); t7(f, 18, 39, 'TIME KEEPS FLOWING', GOLD[3], sh=False)
    button(f, 170, 29, 66, 16, 'RELEASE', ic='eye', style='ghost', rp=rp)
    # ghost placement of a building
    gx, gy = 150, 300
    from buildings import BUILD as B
    tmp = np.zeros((90, 120, 3), np.uint8); tmp[:] = (1, 254, 3)
    B[2]['research'](tmp, 40, 60, 5)
    m = np.any(tmp != (1, 254, 3), axis=2)
    ys, xs = np.nonzero(m)
    for yy, xx in zip(ys, xs):
        Y, X = gy + (yy - 60) * 2, gx + (xx - 40) * 2
        if 0 <= Y < PH - 1 and 0 <= X < PW - 1:
            c = np.array(tmp[yy, xx], float) * .55 + np.array([120, 220, 140]) * .45
            f[Y:Y + 2, X:X + 2] = c.astype(np.uint8)
    rect(f, gx - 52, gy + 4, t7w('OK - PLACE LIBRARY') + 6, 11, INK); t7(f, gx - 49, gy + 6, 'OK - PLACE LIBRARY', GOOD, sh=False)
    # side management rail
    rail = [('hammer', 'BUILD'), ('shield', 'LAWS'), ('flask', 'TECH'), ('sword', 'ARMY'), ('flag', 'TRADE')]
    x0 = 4
    for i, (ic, lab) in enumerate(rail):
        yy = 58 + i * 34
        sel = i == 0
        rect(f, x0 + 1, yy + 1, 30, 30, INK); rect(f, x0, yy, 30, 30, rp[2] if sel else BG2); hline(f, x0, yy, 30, rp[3] if sel else BG3)
        icon(f, x0 + 8, yy + 5, ic, 2)
        t7(f, x0 + 15 - t7w(lab) // 2, yy + 21, lab, TXT if sel else DIM, sh=False)
    # build tray
    y0 = 360
    frame(f, 4, y0, 232, 112, rp, 'BUILD - MEDIEVAL')
    cats = [('poor', 'HOUSE', '20'), ('rich', 'MANOR', '120'), ('commerce', 'MARKET', '60'), ('research', 'LIBRARY', '90')]
    for i, (cat, lab, cost) in enumerate(cats):
        bx = 12 + i * 55; by = y0 + 14
        sel = cat == 'research'
        rect(f, bx + 1, by + 1, 52, 70, INK); rect(f, bx, by, 52, 70, rp[1] if sel else BG2); hline(f, bx, by, 52, rp[3] if sel else BG3)
        tmp = grass_ground(26, 24, i)
        x0_, x1_, y0_, y1_ = measure(BUILD[2][cat])
        sc = max(1, min(int(24 / max(1, x1_ - x0_ + 1)) if x1_ - x0_ + 1 > 24 else 1, 1))
        cw, ch_ = x1_ - x0_ + 1, y1_ - y0_ + 1
        big = np.zeros((max(24, ch_ + 2), max(26, cw + 2), 3), np.uint8); big[:] = grass_ground(big.shape[1], big.shape[0], i)
        BUILD[2][cat](big, (big.shape[1] - cw) // 2 - x0_, big.shape[0] - 1 - y1_, 3)
        thumb = np.asarray(Image.fromarray(big).resize((48, 48 * big.shape[0] // big.shape[1]) if big.shape[1] > big.shape[0] else (48 * big.shape[1] // big.shape[0], 48), Image.NEAREST))
        th, tw_ = thumb.shape[:2]
        f[by + 2 + (48 - th) // 2: by + 2 + (48 - th) // 2 + th, bx + 2 + (48 - tw_) // 2: bx + 2 + (48 - tw_) // 2 + tw_] = thumb
        t7(f, bx + 26 - t7w(lab) // 2, by + 52, lab, TXT if sel else DIM, sh=False)
        icon(f, bx + 8, by + 61, 'gold'); t7(f, bx + 18, by + 61, cost, ACC, sh=False)
    t7(f, 12, y0 + 92, 'TREASURY 4,210', ACC); t7(f, 120, y0 + 92, 'ADVISOR: BUILD A LIBRARY', DIM, sh=False) if False else t7(f, 108, y0 + 92, 'ADVISOR: MORE SCHOLARS', DIM, sh=False)
    dock(f, 1)
    return f


def compose(screens, labels, path, S=3):
    TH = 70; gap = 26
    imgs = [Image.fromarray(s).resize((PW * S, PH * S), Image.NEAREST) for s in screens]
    out = Image.new('RGB', (len(imgs) * (PW * S + gap) + gap, PH * S + TH + gap), (18, 22, 28))
    d = ImageDraw.Draw(out)
    fb = ImageFont.load_default(size=28)
    for i, (im, lab) in enumerate(zip(imgs, labels)):
        x = gap + i * (PW * S + gap)
        d.text((x, TH // 2), lab, fill=(240, 228, 200), font=fb, anchor='lm')
        d.rounded_rectangle([x - 7, TH - 7, x + PW * S + 7, TH + PH * S + 7], 20, outline=(60, 70, 84), width=5)
        out.paste(im, (x, TH))
    out.save(path); print(path, out.size)


if __name__ == '__main__':
    compose([s_watch(), s_nation(), s_city()], ['1. WATCH THE WORLD (EN)', '2. NATION PANEL (AR)', '3. CITY + ANY PERSON'], 'ui_v2_observer_1.png')
    compose([s_chron(), s_powers(), s_control()], ['4. CHRONICLE (AR)', '5. POWERS', '6. OPTIONAL: TAKE CONTROL'], 'ui_v2_observer_2.png')
