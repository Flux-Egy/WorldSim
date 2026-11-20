import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
import culturegen as cg
from people import person2
from catalog import fine_fx

SENT = (1, 254, 3)
F = lambda s: ImageFont.load_default(size=s)
BGC = (24, 29, 37)


def to_img(a, s): return Image.fromarray(a).resize((a.shape[1] * s, a.shape[0] * s), Image.NEAREST)


def houses_strip(g):
    ms = []
    for t in range(5):
        a = np.zeros((90, 130, 3), np.uint8); a[:] = SENT
        cg.gen_house(a, 45, 70, g, t, g['seed'] * 10 + t)
        ys, xs = np.nonzero(np.any(a != SENT, axis=2)); ms.append((xs.min() - 45, xs.max() - 45, ys.min() - 70, ys.max() - 70))
    W_ = sum(m[1] - m[0] + 1 for m in ms) + 6 * 6 + 4
    H_ = max(-m[2] for m in ms) + max(m[3] for m in ms) + 8
    a = grass_ground(W_, H_, g['seed'], tint=(g['tint'], .4))
    x = 5; fx = []
    base = 4 + max(-m[2] for m in ms)
    for t, m in enumerate(ms):
        fx += cg.gen_house(a, x - m[0], base, g, t, g['seed'] * 10 + t) or []
        x += m[1] - m[0] + 1 + 6
    f = upscale(a, 2); fine_fx(f, fx, 2)
    return f


def people_strip(g):
    roles = [('poor', 'adult', 'm'), ('poor', 'adult', 'f'), ('middle', 'adult', 'm'), ('middle', 'adult', 'f'), ('rich', 'adult', 'm'), ('rich', 'adult', 'f'),
             ('ruler', 'adult', 'm'), ('middle', 'child', 'f'), ('poor', 'elder', 'm')]
    a = grass_ground(len(roles) * 17 + 4, 32, g['seed'] + 3, tint=(g['tint'], .4))
    for i, (c, ag, gd) in enumerate(roles):
        person2(a, 2 + i * 17, 2, None, c, ag, gd, 0, seed=g['seed'] + i * 13, og=g)
    return a


def founder_tile(g, i):
    f_ = g['founders'][i]
    a = np.zeros((30, 18, 3), np.uint8)
    for j in range(30): a[j, :] = lit(g['acc'][1], -.55 + j * .01)
    person2(a, 1, 1, None, 'rich' if i else 'ruler', 'adult', f_['gender'], 0, seed=g['seed'] + 99 + i, og=g, shadow=False)
    return a[2:22]


def clan_tile(g, c):
    a = np.zeros((15, 13, 3), np.uint8); a[:] = BGC
    cg.crest(a, 1, 1, g, 1, c['col'], c['symbol'])
    return a


def card(g):
    Wc = 1040
    hs = houses_strip(g); ps = people_strip(g)
    hs_img = to_img(hs, max(1, min(4, (Wc - 40) // hs.shape[1])))
    if hs_img.width > Wc - 40: hs_img = hs_img.resize((Wc - 40, int(hs_img.height * (Wc - 40) / hs_img.width)), Image.NEAREST)
    ps_img = to_img(ps, 6)
    if ps_img.width > Wc - 40: ps_img = to_img(ps, 5)
    H = 150 + 150 + 30 + hs_img.height + 40 + ps_img.height + 30 + 110
    im = Image.new('RGB', (Wc, H), BGC)
    d = ImageDraw.Draw(im)
    col = tuple(g['acc'][3])
    # header
    cr = np.zeros((15, 13, 3), np.uint8); cr[:] = BGC; cg.crest(cr, 1, 1, g, 1)
    im.paste(to_img(cr, 6), (18, 14))
    d.text((112, 30), g['name'], fill=(240, 228, 200), font=F(40), anchor='lm')
    d.text((112, 70), f"THE {g['people']} PEOPLE  -  born in the {g['biome'].lower()}", fill=(150, 160, 175), font=F(20), anchor='lm')
    d.rectangle([112, 88, 112 + 160, 96], fill=tuple(g['acc'][2])); d.rectangle([272, 88, 272 + 80, 96], fill=tuple(g['acc2'][2]))
    # founders
    y = 120
    d.text((18, y), 'FOUNDERS', fill=(232, 180, 106), font=F(22))
    for i, f_ in enumerate(g['founders']):
        x = 18 + i * 200
        t = founder_tile(g, i); im.paste(to_img(t, 4), (x, y + 30))
        d.text((x + 80, y + 40), f_['name'], fill=(240, 228, 200), font=F(19))
        for k, tr in enumerate(f_['traits']):
            c = hx(cg.TRAIT_COL[tr])
            d.rounded_rectangle([x + 80, y + 66 + k * 26, x + 80 + 11 * len(tr) + 12, y + 88 + k * 26], 5, fill=tuple(int(v * .3) for v in c), outline=c)
            d.text((x + 86, y + 77 + k * 26), tr, fill=c, font=F(15), anchor='lm')
        if i == 0: d.text((x + 80, y + 122), 'LEADER (x2 vote)', fill=(138, 148, 163), font=F(14))
    # derived
    dx = 625
    d.text((dx, y), 'SO THE CULTURE BECAME', fill=(232, 180, 106), font=F(22))
    rows = [('VALUES', ' + '.join(g['values'])), ('BELIEF', g['belief']), ('RULE', g['rule']), ('TOWNS', g['layout']),
            ('ROOFS', g['roof'].upper() + ' / ' + g['wall'].upper()), ('DRESS', (g['garment'] + ', ' + (g['head'] or 'bare head')).upper())]
    for k, (a_, b_) in enumerate(rows):
        d.text((dx, y + 36 + k * 22), a_, fill=(138, 148, 163), font=F(16))
        d.text((dx + 80, y + 36 + k * 22), b_, fill=(240, 228, 200), font=F(16))
    # houses
    y = 300
    d.text((18, y), 'HOUSING  (SLUM -> PALACE)  generated from the genome', fill=(232, 180, 106), font=F(20))
    im.paste(hs_img, (20, y + 30))
    y += 30 + hs_img.height + 14
    d.text((18, y), 'PEOPLE  (poor / middle / rich / ruler / child / elder)', fill=(232, 180, 106), font=F(20))
    im.paste(ps_img, (20, y + 28))
    y += 28 + ps_img.height + 16
    d.text((18, y), 'CLANS INSIDE THE KINGDOM', fill=(232, 180, 106), font=F(20))
    for i, c in enumerate(g['clans']):
        x = 18 + i * 340
        im.paste(to_img(clan_tile(g, c), 4), (x, y + 30))
        d.text((x + 62, y + 38), c['name'], fill=(240, 228, 200), font=F(18))
        d.text((x + 62, y + 62), f"from {c['founder']}  -  {c['trait'].lower()}", fill=(150, 160, 175), font=F(15))
    d.rectangle([0, 0, Wc - 1, H - 1], outline=col, width=3)
    return im


if __name__ == '__main__':
    seeds = [3, 37, 105, 88]
    cards = [card(cg.make_culture(s)) for s in seeds]
    G, TH = 20, 110
    Wd = 2 * cards[0].width + 3 * G
    rows = [max(cards[0].height, cards[1].height), max(cards[2].height, cards[3].height)]
    out = Image.new('RGB', (Wd, TH + rows[0] + rows[1] + 3 * G), (14, 17, 22))
    d = ImageDraw.Draw(out)
    d.text((G, 40), 'CULTURES ARE BORN, NOT PICKED  -  4 RANDOM ROLLS', fill=(240, 228, 200), font=F(38), anchor='lm')
    d.text((G, 84), 'founder traits -> values -> belief, rule, town layout, roofs, dress, colours, names, clans.   every new kingdom rolls a new one.',
           fill=(150, 160, 175), font=F(21), anchor='lm')
    for k, c in enumerate(cards):
        out.paste(c, (G + (k % 2) * (c.width + G), TH + (k // 2) * (rows[0] + G)))
    out.save('cultures_generated.png'); print(out.size)
