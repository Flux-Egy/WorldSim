import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from chars import person, ROLES, ROLE_NAMES, ANIMALS
from buildings import ERAS

S = 8
CWc, CHc = 22, 19
def main():
    rows = len(ERAS)
    a = np.zeros((rows * CHc + 2 * CHc, len(ROLES) * CWc, 3), np.uint8)
    a[:] = grass_ground(a.shape[1], a.shape[0], 3)
    for e in range(rows):
        for i, role in enumerate(ROLES):
            x0, y0 = i * CWc, e * CHc
            person(a, x0 + 2, y0 + 3, e, role, 0, seed=i)
            person(a, x0 + 11, y0 + 3, e, role, 1, seed=i)
    # animals rows
    y0 = rows * CHc
    for k, (name, fn, w, h) in enumerate(ANIMALS):
        col, row = k % 4, k // 4
        x = col * (len(ROLES) * CWc // 4) + 2
        y = y0 + row * CHc + 5
        fn(a, x, y, 0); fn(a, x + w + 1, y, 1)
    img = Image.fromarray(a).resize((a.shape[1] * S, a.shape[0] * S), Image.NEAREST)
    LW, TH = 170, 70
    out = Image.new('RGB', (img.width + LW + 10, img.height + TH + 10), (18, 22, 28))
    out.paste(img, (LW, TH))
    d = ImageDraw.Draw(out)
    fb = ImageFont.load_default(size=24)
    d.text((LW + img.width - 6, TH // 2), 'PAIRS = 2-FRAME WALK', fill=(138, 148, 163), font=ImageFont.load_default(size=15), anchor='rm'); fl = ImageFont.load_default(size=22); fs = ImageFont.load_default(size=18)
    for i, role in enumerate(ROLES):
        d.text((LW + i * CWc * S + CWc * S // 2, TH // 2), ROLE_NAMES[role], fill=(240, 228, 200), font=fs, anchor='mm')
        d.line([(LW + i * CWc * S, TH), (LW + i * CWc * S, TH + rows * CHc * S)], fill=(18, 22, 28), width=3)
    for e in range(rows + 2):
        y = TH + e * CHc * S
        d.line([(LW, y), (LW + img.width, y)], fill=(18, 22, 28), width=3)
        lab = ERAS[e] if e < rows else ('ANIMALS' if e == rows else 'CREATURES')
        d.text((10, y + CHc * S // 2), lab, fill=(232, 180, 106), font=fl, anchor='lm')
    for k, (name, fn, w, h) in enumerate(ANIMALS):
        col, row = k % 4, k // 4
        x = LW + (col * (len(ROLES) * CWc // 4) + 2) * S + (2 * w + 1) * S // 2
        y = TH + (rows * CHc + row * CHc + CHc - 2) * S
        d.text((x, y), name, fill=(243, 230, 200), font=fs, anchor='mm')
    out.save('characters_catalog.png'); print(out.size)
main()
