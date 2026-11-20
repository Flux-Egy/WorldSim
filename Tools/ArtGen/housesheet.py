import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from houses import house, CULTURES, CULT_NAMES, TIERS
from catalog import fine_fx

SENT = (1, 254, 3)
def meas(c, t, s, ar):
    a = np.zeros((100, 120, 3), np.uint8); a[:] = SENT
    house(a, 40, 70, c, t, s, ar)
    ys, xs = np.nonzero(np.any(a != SENT, axis=2))
    return int(xs.min()) - 40, int(xs.max()) - 40, int(ys.min()) - 70, int(ys.max()) - 70

NV = 6
def sheet(cult, S=6):
    seeds = [[1000 * t + 37 * v + 11 for v in range(NV)] for t in range(5)]
    ms = [[meas(cult, t, seeds[t][v], v % 3) for v in range(NV)] for t in range(5)]
    CWd = max(m[1] - m[0] + 1 for row in ms for m in row) + 6
    hs = [max(-m[2] for m in row) + max(m[3] for m in row) + 1 + 12 for row in ms]
    tops = np.cumsum([0] + hs)
    a = np.zeros((int(tops[-1]), NV * CWd, 3), np.uint8)
    fx = []
    for t in range(5):
        top = -max(-m[2] for m in ms[t]) if False else min(m[2] for m in ms[t])
        for v in range(NV):
            x0, x1, y0, y1 = ms[t][v]
            a[tops[t]:tops[t + 1], v * CWd:(v + 1) * CWd] = grass_ground(CWd, hs[t], seed=t * 9 + v)
            ax = v * CWd + (CWd - (x1 - x0 + 1)) // 2 - x0
            ab = int(tops[t]) + 4 - top
            fx += house(a, ax, ab, cult, t, seeds[t][v], v % 3)
    f = upscale(a, 2); fine_fx(f, fx, 2)
    img = Image.fromarray(f).resize((f.shape[1] * S // 2, f.shape[0] * S // 2), Image.NEAREST)
    LW, TH = 150, 70
    out = Image.new('RGB', (img.width + LW + 10, img.height + TH + 10), (18, 22, 28))
    out.paste(img, (LW, TH))
    d = ImageDraw.Draw(out)
    fb = ImageFont.load_default(size=30); fl = ImageFont.load_default(size=22); fs = ImageFont.load_default(size=16)
    d.text((10, TH // 2), CULT_NAMES[cult] + '  -  HOUSING: 5 TIERS x 6 VARIANTS', fill=(240, 228, 200), font=fb, anchor='lm')
    for t in range(5):
        y = TH + int(tops[t]) * S
        d.line([(LW, y), (LW + img.width, y)], fill=(18, 22, 28), width=4)
        d.text((12, y + hs[t] * S // 2), TIERS[t], fill=(232, 180, 106), font=fl, anchor='lm')
    for v in range(1, NV):
        x = LW + v * CWd * S
        d.line([(x, TH), (x, TH + img.height)], fill=(18, 22, 28), width=3)
    out.save(f'houses_{cult}.png'); print(cult, out.size)

for c in CULTURES: sheet(c)
