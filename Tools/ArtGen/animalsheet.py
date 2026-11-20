import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from animals import draw, ALL

SENT = (1, 254, 3)
NAMES = {'sheep': 'SHEEP / LAMB', 'goat': 'GOAT / KID', 'cow': 'COW / CALF', 'pig': 'PIG / PIGLET', 'horse': 'HORSE / FOAL',
         'donkey': 'DONKEY / FOAL', 'camel': 'CAMEL / CALF', 'dog': 'DOG / PUPPY', 'cat': 'CAT / KITTEN', 'deer': 'DEER / FAWN',
         'rabbit': 'RABBIT / KIT', 'wolf': 'WOLF / PUP', 'bear': 'BEAR / CUB', 'boar': 'BOAR / PIGLET', 'fox': 'FOX / KIT',
         'chicken': 'HEN / CHICK', 'duck': 'DUCK / DUCKLING', 'fish': 'FISH / FRY', 'crocodile': 'CROCODILE / HATCHLING'}


def bbox(name, frame, young):
    a = np.zeros((70, 80, 3), np.uint8); a[:] = SENT
    draw(a, 14, 14, name, frame, young, 3)
    ys, xs = np.nonzero(np.any(a != SENT, axis=2))
    return xs.min() - 14, xs.max() - 14, ys.min() - 14, ys.max() - 14


def tile(name, frame, young, w, h, seed):
    if name == 'fish':
        a = np.zeros((h, w, 3), np.uint8); a[:] = C['water'][2]
        for y in range(h):
            for x in range(w):
                if (x * 7 + y * 13) % 29 == 0: a[y, x] = C['water'][3]
    else:
        a = grass_ground(w, h, seed)
    x0, x1, y0, y1 = bbox(name, frame, young)
    # align feet to a common baseline, centre horizontally
    ox = (w - (x1 - x0 + 1)) // 2 - x0
    oy = h - 3 - y1
    draw(a, ox, oy, name, frame, young, 3)
    return a


S1, S2 = 7, 3
CW, CH = 44, 38
COLS = 3


def card(name, i):
    big = tile(name, 0, False, CW, CH, i)
    yg = tile(name, 0, True, 28, CH, i + 50)
    walk = [tile(name, f, False, CW, CH, i + 9) for f in range(4)]
    wy = [tile(name, f, True, 30, CH, i + 19) for f in range(4)]
    w = CW * S1 + 28 * S1 + 10
    hh = 34 + CH * S1 + 12 + ((CW * S1 + 28 * S1 - 2) // 4) * CH // CW + 8
    img = Image.new('RGB', (w, hh), (26, 31, 39))
    d = ImageDraw.Draw(img)
    d.text((6, 17), NAMES[name], fill=(232, 180, 106), font=ImageFont.load_default(size=20), anchor='lm')
    img.paste(Image.fromarray(big).resize((CW * S1, CH * S1), Image.NEAREST), (0, 34))
    img.paste(Image.fromarray(yg).resize((28 * S1, CH * S1), Image.NEAREST), (CW * S1 + 10, 34))
    x = 0
    tw = (w - 12) // 4; th = tw * CH // CW
    for t in walk:
        img.paste(Image.fromarray(t).resize((tw, th), Image.NEAREST), (x, 34 + CH * S1 + 12))
        x += tw + 4
    return img


if __name__ == '__main__':
    cards = [card(n, i) for i, n in enumerate(ALL)]
    cw, chh = cards[0].width, cards[0].height
    G, TH = 16, 96
    rows = (len(cards) + COLS - 1) // COLS
    out = Image.new('RGB', (COLS * cw + (COLS + 1) * G, TH + rows * (chh + G)), (18, 22, 28))
    d = ImageDraw.Draw(out)
    d.text((G, 34), 'CREATURES AT 2x DETAIL  -  19 SPECIES, ADULT + YOUNG, 4-FRAME WALK', fill=(240, 228, 200), font=ImageFont.load_default(size=30), anchor='lm')
    d.text((G, 72), 'big = adult next to its young (same scale)   |   strip = 4-frame walk cycle', fill=(150, 160, 175), font=ImageFont.load_default(size=19), anchor='lm')
    for k, c in enumerate(cards):
        out.paste(c, (G + (k % COLS) * (cw + G), TH + (k // COLS) * (chh + G)))
    out.save('animals_2x.png'); print(out.size)
