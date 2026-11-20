import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from people import person2

CW, CH, S = 20, 34, 6
CULTS = [('riverland', 'RIVERLAND', hx('#cdb27c')), ('northern', 'NORTHERN', hx('#3f6a3c')), ('highland', 'HIGHLAND', hx('#8a9478'))]
COLS = [('poor', 'adult', 'm', 'POOR'), ('poor', 'adult', 'f', ''), ('middle', 'adult', 'm', 'MIDDLE'), ('middle', 'adult', 'f', ''),
        ('rich', 'adult', 'm', 'RICH'), ('rich', 'adult', 'f', ''), ('ruler', 'adult', 'm', 'RULER'),
        ('middle', 'child', 'm', 'CHILD'), ('poor', 'child', 'f', ''), ('middle', 'elder', 'm', 'ELDER'), ('poor', 'elder', 'f', '')]


def cell(tint, fn, seed):
    a = grass_ground(CW, CH, seed, tint=(tint, .35))
    fn(a)
    return Image.fromarray(a).resize((CW * S, CH * S), Image.NEAREST)


fb = ImageFont.load_default(size=30); fm = ImageFont.load_default(size=22); fs = ImageFont.load_default(size=18)
LW, G, TH = 170, 6, 120
rows_h = CH * S + 16
W_ = LW + len(COLS) * (CW * S + G)
H_ = TH + 3 * rows_h + 60 + rows_h + 76 + rows_h + 20
out = Image.new('RGB', (W_, H_), (18, 22, 28))
d = ImageDraw.Draw(out)
d.text((14, 32), 'PEOPLE AT 2x DETAIL  -  CULTURE x CLASS x AGE x GENDER', fill=(240, 228, 200), font=fb, anchor='lm')
d.text((14, 70), 'same medieval era; each culture dresses, wears its hair and carries things differently. skin & hair vary per person.', fill=(150, 160, 175), font=fs, anchor='lm')
for j, (_, _, _, lab) in enumerate(COLS):
    if lab: d.text((LW + j * (CW * S + G) + 4, TH - 16), lab, fill=(232, 180, 106), font=fs, anchor='lm')
y = TH
for ci, (cult, name, tint) in enumerate(CULTS):
    d.text((14, y + CH * S // 2), name, fill=(232, 180, 106), font=fm, anchor='lm')
    for j, (cls, age, g, _) in enumerate(COLS):
        im = cell(tint, lambda a: person2(a, 2, 4, cult, cls, age, g, 0, seed=ci * 31 + j * 7 + 3), ci * 10 + j)
        out.paste(im, (LW + j * (CW * S + G), y))
    y += rows_h
# walk cycles
y += 20
d.text((14, y + 14), 'WALK CYCLE (4 FRAMES)', fill=(240, 228, 200), font=fm, anchor='lm'); y += 40
walkers = [('riverland', 'poor', 'adult', 'f', hx('#cdb27c')), ('northern', 'rich', 'adult', 'm', hx('#3f6a3c')), ('highland', 'middle', 'adult', 'm', hx('#8a9478'))]
for k, (cult, cls, age, g, tint) in enumerate(walkers):
    for f in range(4):
        im = cell(tint, lambda a: person2(a, 2, 4, cult, cls, age, g, f, seed=k * 5 + 1), k * 4 + f)
        out.paste(im, (LW + (k * 4 + f) * (CW * S + G) - (k * 4 + f >= 11) * 0, y)) if k * 4 + f < 11 else None
y += rows_h
# era outfits
y += 20
d.text((14, y + 14), 'ONE RIVERLAND FAMILY ACROSS THE 6 ERAS', fill=(240, 228, 200), font=fm, anchor='lm'); y += 56
eras = ['STONE', 'ANCIENT', 'MEDIEVAL', 'INDUSTRIAL', 'MODERN', 'FUTURE']
k = 0
for e in range(6):
    for g in ('m', 'f'):
        if k >= 11: break
        im = cell(hx('#cdb27c'), lambda a: person2(a, 2, 4, 'riverland', 'middle', 'adult', g, 0, seed=7 + (g == 'f'), era=e), 40 + k)
        out.paste(im, (LW + k * (CW * S + G), y))
        if g == 'm': d.text((LW + k * (CW * S + G) + 4, y - 12), eras[e], fill=(232, 180, 106), font=fs, anchor='lm')
        k += 1
out.save('people_2x.png'); print(out.size)
