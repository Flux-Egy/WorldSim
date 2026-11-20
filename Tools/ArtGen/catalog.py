import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from buildings import BUILD, ERAS, CATS, CAT_NAMES, SUBTITLE

SENT = (1, 254, 3)

def measure(fn):
    a = np.zeros((90, 120, 3), np.uint8); a[:] = SENT
    fn(a, 40, 60, 3)
    ys, xs = np.nonzero(np.any(a != SENT, axis=2))
    return int(xs.min()) - 40, int(xs.max()) - 40, int(ys.min()) - 60, int(ys.max()) - 60

CW = 42
S = 6
def build_catalog():
    cols, rows = len(ERAS), len(CATS)
    ext = {}
    for cat in CATS:
        y0 = min(measure(BUILD[e][cat])[2] for e in range(cols)); y1 = max(measure(BUILD[e][cat])[3] for e in range(cols))
        ext[cat] = (y0, y1)
    heights = [(-ext[c][0]) + ext[c][1] + 1 + 4 + 8 for c in CATS]
    tops = np.cumsum([0] + heights)
    a = np.zeros((int(tops[-1]), cols * CW, 3), np.uint8)
    fx_all = []
    for r, cat in enumerate(CATS):
        for c in range(cols):
            a[tops[r]:tops[r + 1], c * CW:(c + 1) * CW] = grass_ground(CW, heights[r], seed=r * 10 + c)
            fn = BUILD[c][cat]
            x0, x1, y0, y1 = measure(fn)
            ax = int(c * CW + (CW - (x1 - x0 + 1)) // 2 - x0)
            ab = int(tops[r] + 4 - ext[cat][0])
            fx = fn(a, ax, ab, r * 7 + c)
            fx_all += fx or []
    return a, fx_all, heights, tops


def fine_fx(f, fx, k):
    import math, random
    for e in fx:
        kind, x, y = e[0], e[1] * k, e[2] * k
        if kind == 'smoke':
            for t in range(6):
                s = 1.2 + t * .5
                blend_mask(f, ellipse_mask(f.shape[:2], x + t * 1.2 + math.sin(t) * 2, y - t * 4, s + 1, s), (150 + t * 10,) * 3, .55 - t * .07)
        elif kind == 'steam':
            for t in range(6):
                s = 2.5 + t * .8
                blend_mask(f, ellipse_mask(f.shape[:2], x + t, y - t * 4, s + 1, s), (235, 238, 240), .7 - t * .09)
        elif kind == 'fire':
            blend_mask(f, ellipse_mask(f.shape[:2], x + 1, y, 14, 9), hx('#ffb35a'), .18)
            pat = ["..y..", ".yoy.", "yoroy", "orrro", ".rrr."]
            cm = {'y': C['fire'][2], 'o': C['fire'][1], 'r': C['fire'][0]}
            for j, row in enumerate(pat):
                for i, ch in enumerate(row):
                    if ch != '.': put(f, x - 2 + i + 1, y - 6 + j, cm[ch])
        elif kind in ('glow', 'holo'):
            col = e[3]
            blend_mask(f, ellipse_mask(f.shape[:2], x + 1, y + 1, 9, 6), col, .22)

if __name__ == '__main__':
    a, fx, heights, tops = build_catalog()
    f = upscale(a, 2)
    fine_fx(f, fx, 2)
    img = Image.fromarray(f).resize((f.shape[1] * 3, f.shape[0] * 3), Image.NEAREST)  # total x6
    LW, TH = 190, 80
    out = Image.new('RGB', (img.width + LW + 12, img.height + TH + 12), (18, 22, 28))
    out.paste(img, (LW, TH))
    d = ImageDraw.Draw(out)
    fb = ImageFont.load_default(size=30); fs = ImageFont.load_default(size=19); fl = ImageFont.load_default(size=21)
    cw = CW * S
    for c, e in enumerate(ERAS):
        d.text((LW + c * cw + cw // 2, TH // 2), e, fill=(240, 228, 200), font=fb, anchor='mm')
        d.line([(LW + c * cw, TH), (LW + c * cw, TH + img.height)], fill=(18, 22, 28), width=3)
    for r, cat in enumerate(CATS):
        ry, ch = TH + int(tops[r]) * S, heights[r] * S
        d.text((10, ry + ch // 2), CAT_NAMES[cat], fill=(232, 180, 106), font=fl, anchor='lm')
        d.line([(LW, ry), (LW + img.width, ry)], fill=(18, 22, 28), width=4)
        for c in range(len(ERAS)):
            name = SUBTITLE[c][cat]
            x, y = LW + c * cw + cw // 2, ry + ch - 22
            d.rounded_rectangle([x - 8 - len(name) * 5.5, y - 13, x + 8 + len(name) * 5.5, y + 12], 5, fill=(20, 26, 34))
            d.text((x, y), name, fill=(243, 230, 200), font=fs, anchor='mm')
    out.save('buildings_catalog.png')
    print(out.size)
