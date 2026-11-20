"""Terrain: 24 biome ground types with their props, and a 2.5D elevation render (10 levels, cliffs, water depth)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from lib import *
from culturecity import pine

F = lambda s: ImageFont.load_default(size=s)


def ground(w, h, cols, seed, cell=10, speck=None, nspeck=0):
    n = smooth_noise(w, h, cell, seed)
    n2 = smooth_noise(w, h, 4, seed + 3)
    v = n * .7 + n2 * .3
    idx = np.clip((v * len(cols)).astype(int), 0, len(cols) - 1)
    a = np.array([hx(c) for c in cols], np.uint8)[idx]
    r = np.random.default_rng(seed)
    jit = r.integers(-3, 4, (h, w))
    a = np.clip(a.astype(int) + jit[..., None], 0, 255).astype(np.uint8)
    if speck:
        for _ in range(nspeck):
            x, y = r.integers(0, w), r.integers(0, h); a[y, x] = hx(speck[r.integers(0, len(speck))])
    return a


def cactus(a, x, y):
    c = [hx('#2e5a2c'), hx('#3e7a38'), hx('#5a9a48')]
    shadow_ell(a, x + 2, y + 7, 2, 1)
    vline(a, x, y, 7, c[1]); vline(a, x + 1, y, 7, c[0]); put(a, x, y, c[2])
    vline(a, x - 2, y + 2, 2, c[1]); put(a, x - 1, y + 3, c[1]); vline(a, x + 3, y + 1, 3, c[0]); put(a, x + 2, y + 3, c[0])


def deadtree(a, x, y):
    c = hx('#5a4a3a')
    shadow_ell(a, x + 2, y + 8, 2, 1)
    vline(a, x, y + 2, 6, c); put(a, x - 1, y + 2, c); put(a, x - 2, y + 1, c); put(a, x + 1, y + 3, c); put(a, x + 2, y + 2, c); put(a, x + 1, y, c)


def reeds(a, x, y):
    for i in range(4): vline(a, x + i, y + (i % 2), 4 - (i % 2), hx('#7a8a3a') if i % 2 else hx('#9aa84a')); put(a, x + i, y + (i % 2) - 1, hx('#6a4a2a'))


def mushroom(a, x, y, big=False):
    s = 2.6 if big else 1.6
    vline(a, x, y + 1, 3 if big else 2, hx('#e8e0cc'))
    dome(a, x + .5, y, s + 1, s, [hx('#6a2a5a'), hx('#8a3a76'), hx('#a85a94'), hx('#c87ab4'), hx('#e8a8d8')], x)
    put(a, x, y - 1, hx('#ffffff'))


def fern(a, x, y):
    c = [hx('#2e6a2c'), hx('#4a8a3a'), hx('#6aaa4a')]
    for i in range(-3, 4): put(a, x + i, y + abs(i) // 2, c[1 + (i < 0)]); put(a, x + i // 2, y - 2 + abs(i) // 2, c[2])
    vline(a, x, y - 3, 4, c[0])


def crystal(a, x, y, col):
    for i in range(4): vline(a, x + i, y + abs(i - 1), 4 - abs(i - 1), lit(col, .2 if i < 2 else -.2))
    put(a, x + 1, y, hx('#ffffff'))


def coral(a, x, y, col):
    for i in range(3): vline(a, x + i * 2, y + (i % 2), 3, col); put(a, x + i * 2, y - 1 + (i % 2), lit(col, .3))


def iceblock(a, x, y):
    rect(a, x, y, 5, 3, hx('#cfe6f0')); hline(a, x, y, 5, hx('#ffffff')); hline(a, x, y + 2, 5, hx('#9ac0d4'))


def lavapool(a, x, y, rx, ry, seed):
    m = ellipse_mask(a.shape[:2], x, y, rx, ry)
    a[m] = hx('#d5452d')
    m2 = ellipse_mask(a.shape[:2], x - 1, y - .5, rx * .6, ry * .5); a[m2] = hx('#f49a3c')
    m3 = ellipse_mask(a.shape[:2], x - 1, y - 1, rx * .25, ry * .25); a[m3] = hx('#ffe27a')
    e = ellipse_mask(a.shape[:2], x, y, rx + 1, ry + 1) & ~m; a[e] = hx('#2a2420')


def crops(a, x, y, w, h, col):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            a[yy, xx] = hx('#7a5a3a') if yy % 2 else hx(col)


W_, H_ = 60, 40
BIOMES = [
    ('MEADOW', ['#6c9e4c', '#74a753', '#7cb05a'], 'tree:3,bush:6', '#e4d27a,#d98a8a'),
    ('FLOWER FIELD', ['#74a753', '#7cb05a', '#84b860'], 'bush:3', '#e8c84a,#d5452d,#f0efe2,#c45aa8'),
    ('FOREST', ['#4e8a3c', '#56923f', '#5e9a46'], 'tree:14', None),
    ('PINE TAIGA', ['#3f6a3c', '#46723f', '#4e7a46'], 'pine:16', None),
    ('JUNGLE', ['#2f6a34', '#36743a', '#3e7e40'], 'palm:6,tree:8,fern:10', None),
    ('SWAMP', ['#4a5a34', '#52643a', '#5a6c40'], 'water:5,reeds:10,deadtree:3', None),
    ('SAVANNA', ['#b8a860', '#c4b46a', '#ccbc72'], 'tree:2,bush:5', '#a89850'),
    ('DESERT DUNES', ['#d9c08a', '#e2cc96', '#c9ad78'], 'cactus:4,rock:3', '#e8d6a6'),
    ('BADLANDS', ['#b0603a', '#c07040', '#a0502e'], 'rock:6,deadtree:2', '#d8905a'),
    ('STEPPE', ['#a8a868', '#b4b070', '#9c9c60'], 'bush:4,rock:2', '#c8c080'),
    ('TUNDRA', ['#8a9a7a', '#9aa888', '#7a8a6c'], 'rock:5,pine:2', '#d8dde0'),
    ('SNOW', ['#e8eef2', '#dfe8ec', '#f4f8fa'], 'snowpine:6,rock:2', '#c8d4dc'),
    ('GLACIER', ['#b8d8e8', '#cfe6f0', '#a8c8dc'], 'ice:8', '#ffffff'),
    ('BEACH', ['#e2cc96', '#ead6a4', '#d8c08a'], 'palm:3,shell:6', '#f4ecd8'),
    ('ROCKY HIGHLAND', ['#7a8070', '#8a9080', '#6a7062'], 'rock:10,bush:3', '#a8aca0'),
    ('MOUNTAIN', ['#6d6a63', '#87837a', '#5a5852'], 'rock:12', '#bdb8ad'),
    ('VOLCANIC', ['#2a2420', '#3a3430', '#4a4038'], 'lava:3,rock:4', '#d5452d'),
    ('ASH WASTE', ['#5a5650', '#6a6660', '#4a4640'], 'deadtree:5,rock:3', '#8a8680'),
    ('SALT FLATS', ['#e8e4dc', '#f0ece4', '#dcd8d0'], 'crack:14', '#c8c4bc'),
    ('FUNGAL GROVE', ['#4a3a5a', '#54446a', '#3e3050'], 'mushroom:10', '#8a6aa8'),
    ('CORAL SHALLOWS', ['#3a8ab0', '#4b95c2', '#5aa4c8'], 'coral:10', '#8ad0e0'),
    ('FARMLAND', ['#7cb05a', '#74a753', '#6c9e4c'], 'farm:1', None),
    ('CRYSTAL CAVES', ['#3a3a52', '#44445e', '#32324a'], 'crystal:8,rock:4', '#6a6a8a'),
    ('IRRADIATED WASTE', ['#5a6a3a', '#647444', '#4e5e32'], 'deadtree:4,glow:5', '#9ae04a'),
]


def biome(name, cols, props, speck, seed):
    a = ground(W_, H_, cols, seed, speck=speck.split(',') if speck else None, nspeck=60 if speck else 0)
    r = random.Random(seed)
    items = []
    for p in props.split(','):
        k, n = p.split(':')
        for _ in range(int(n)):
            items.append((r.randint(2, H_ - 6), r.randint(3, W_ - 6), k))
    if 'farm' in props:
        for i in range(3): crops(a, 4 + i * 18, 6, 15, 12, ['#c9a94e', '#6ea447', '#d8bb5e'][i])
        for i in range(3): crops(a, 4 + i * 18, 22, 15, 12, ['#8fae68', '#c9a94e', '#5b8f3a'][i])
        for x in range(2, W_ - 2): put(a, x, 20, hx('#9c7f55'))
    items.sort()
    for (y, x, k) in items:
        if k == 'tree': tree(a, x, y - 3, r.choice([3, 4]), x * 7 + y)
        elif k == 'pine': pine(a, x, y - 6, 4, x + y)
        elif k == 'snowpine': pine(a, x, y - 6, 4, x + y, snow=True); put(a, x - 1, y - 3, hx('#ffffff')); put(a, x + 1, y - 2, hx('#ffffff'))
        elif k == 'bush': bush(a, x, y, x)
        elif k == 'palm': palm(a, x, y - 7, x)
        elif k == 'rock': rock(a, x, y, r.choice([1.4, 1.8, 2.4]), x * 3 + y)
        elif k == 'cactus': cactus(a, x, y - 4)
        elif k == 'deadtree': deadtree(a, x, y - 4)
        elif k == 'reeds': reeds(a, x, y)
        elif k == 'fern': fern(a, x, y)
        elif k == 'mushroom': mushroom(a, x, y, r.random() < .3)
        elif k == 'coral': coral(a, x, y, hx(r.choice(['#e87a8a', '#f0a050', '#c45aa8', '#e8e070'])))
        elif k == 'ice': iceblock(a, x, y)
        elif k == 'lava': lavapool(a, x, y, r.uniform(4, 7), r.uniform(2.5, 4), x)
        elif k == 'water':
            m = ellipse_mask(a.shape[:2], x, y, r.uniform(3, 6), r.uniform(2, 3)); a[m] = hx('#3a5a4a'); a[m & (np.random.default_rng(x).random(m.shape) > .85)] = hx('#5a7a5a')
        elif k == 'shell': put(a, x, y, hx('#f4dcc8')); put(a, x + 1, y, hx('#e8b8a0'))
        elif k == 'crack':
            for i in range(5): put(a, x + i, y + (i * 7 % 3) - 1, hx('#b8b4ac'))
        elif k == 'crystal': crystal(a, x, y, hx(r.choice(['#5fe0e8', '#c45aa8', '#8a7ae8'])))
        elif k == 'glow':
            blend_mask(a, ellipse_mask(a.shape[:2], x, y, 4, 3), hx('#9ae04a'), .45); put(a, x, y, hx('#d8ff8a'))
    return a


def biome_sheet():
    S, G, cols = 4, 10, 6
    rows = (len(BIOMES) + cols - 1) // cols
    cw, ch = W_ * S, H_ * S
    out = Image.new('RGB', (cols * (cw + G) + G, 100 + rows * (ch + 40 + G)), (18, 22, 28)); d = ImageDraw.Draw(out)
    d.text((G, 34), 'TERRAIN  -  24 BIOME GROUND TYPES WITH THEIR OWN PLANTS, ROCKS & DETAILS', fill=(240, 228, 200), font=F(30), anchor='lm')
    d.text((G, 70), 'biomes come from height + moisture + temperature. cultures born in each biome build with its materials.', fill=(150, 160, 175), font=F(19), anchor='lm')
    for i, (n, c, p, s) in enumerate(BIOMES):
        x = G + (i % cols) * (cw + G); y = 100 + (i // cols) * (ch + 40 + G)
        d.text((x, y + 16), n, fill=(232, 180, 106), font=F(18), anchor='lm')
        out.paste(Image.fromarray(biome(n, c, p, s, i * 11 + 3)).resize((cw, ch), Image.NEAREST), (x, y + 32))
    out.save('terrain_biomes.png'); print('biomes', out.size)


# ------------------------------------------------------------------ elevation render
LEVELS = [('DEEP OCEAN', '#1d4a82'), ('OCEAN', '#255c98'), ('SHALLOWS', '#3277b0'), ('BEACH', '#dcc896'), ('LOWLAND', '#74a753'),
          ('PLAINS / FOREST', '#5e9a46'), ('HILLS', '#7a9a52'), ('HIGHLAND', '#8a8a6a'), ('MOUNTAIN', '#87837a'), ('PEAK', '#f2f4f6')]


def heightmap(w, h, seed):
    n = smooth_noise(w, h, 60, seed) * .55 + smooth_noise(w, h, 22, seed + 1) * .3 + smooth_noise(w, h, 7, seed + 2) * .15
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot((xx - w * .5) / (w * .5), (yy - h * .55) / (h * .5))
    n = n * 1.25 - d * .45
    n = (n - n.min()) / (n.max() - n.min())
    qs = np.quantile(n, [.10, .22, .34, .39, .56, .71, .82, .91, .97])
    lv = np.searchsorted(qs, n)
    moist = smooth_noise(w, h, 40, seed + 9)
    return lv, moist


def top_color(l, m, x, y, rnd):
    if l <= 2: return hx(LEVELS[l][1])
    if l == 3: return hx('#dcc896') if (x + y) % 7 else hx('#e8d6a6')
    if l in (4, 5):
        if m < .24: return hx(['#c9b07a', '#d2ba84', '#bea06c'][rnd % 3])   # dry steppe-desert
        if m > .7: return hx(['#4a5a34', '#52643a'][rnd % 2])                 # swamp
        return hx(['#6c9e4c', '#74a753', '#7cb05a'][rnd % 3]) if l == 4 else hx(['#56923f', '#5e9a46', '#4e8a3c'][rnd % 3])
    if l == 6: return hx(['#7a9a52', '#84a45a', '#6e8e4a'][rnd % 3])
    if l == 7: return hx(['#8a8a6a', '#9a9a78', '#7a7a5e'][rnd % 3])
    if l == 8: return hx(['#87837a', '#a29d92', '#6d6a63'][rnd % 3])
    return hx(['#f2f4f6', '#e8eef2', '#ffffff'][rnd % 3])


def render_levels(w=170, h=110, seed=8, K=3):
    lv, moist = heightmap(w, h, seed)
    rnd = np.random.default_rng(seed).integers(0, 9, (h, w))
    H = h + 10 * K + 4
    a = np.zeros((H, w, 3), np.uint8); a[:] = hx('#1d4a82')
    wl = 3   # water surface level
    for y in range(h):
        for x in range(w):
            l = lv[y, x]
            el = max(l, wl - 1) if l < wl else l
            sy = y + 10 * K - el * K
            c = top_color(l, moist[y, x], x, y, rnd[y, x])
            # cliff face from top to the ground line of the cell in front
            front = lv[y + 1, x] if y + 1 < h else 0
            fe = max(front, wl - 1) if front < wl else front
            depth = (el - fe) * K
            if depth > 0 and l >= wl:
                for k in range(1, depth + 2):
                    if 0 <= sy + k < H:
                        rk = hx('#6a5a46') if l <= 5 else hx('#5f5b55') if l <= 8 else hx('#c8d0d8')
                        a[sy + k, x] = lit(rk, -.05 * (k % 3) - (.12 if k > K else 0))
            if 0 <= sy < H:
                a[sy, x] = c
                if l < wl:  # water: depth tint + foam near shore
                    a[sy, x] = hx(LEVELS[l][1])
                    if l == 2 and rnd[y, x] > 6: a[sy, x] = hx('#4b95c2')
                if l >= 4 and front < l and depth > 0: a[sy, x] = lit(c, .12)   # rim light on edges
    # props: trees on forest/plains, pines on hills, rocks on mountain
    r = random.Random(seed)
    for _ in range(420):
        x, y = r.randint(2, w - 4), r.randint(2, h - 4)
        l = lv[y, x]; sy = y + 10 * K - l * K
        if l == 5 and .24 < moist[y, x] < .7 and r.random() < .55: tree(a, x, sy - 4, 2, x * 5 + y)
        elif l == 6 and r.random() < .5: pine(a, x, sy - 6, 3, x + y)
        elif l == 8 and r.random() < .3: rock(a, x, sy, 1.2, x)
        elif l == 4 and moist[y, x] < .24 and r.random() < .3: cactus(a, x, sy - 6)
        elif l == 4 and moist[y, x] > .7 and r.random() < .5: reeds(a, x, sy - 3)
    return a, lv


def levels_sheet():
    a, lv = render_levels()
    S = 5
    img = Image.fromarray(a).resize((a.shape[1] * S, a.shape[0] * S), Image.NEAREST)
    LW = 330
    out = Image.new('RGB', (img.width + LW + 30, img.height + 120), (18, 22, 28)); d = ImageDraw.Draw(out)
    d.text((14, 34), 'ELEVATION  -  10 HEIGHT LEVELS WITH CLIFFS, WATER DEPTH & SNOW CAPS', fill=(240, 228, 200), font=F(32), anchor='lm')
    d.text((14, 74), 'each level raises the ground 3 px and draws a cliff face. armies slow uphill, high ground sees further, rivers run downhill.',
           fill=(150, 160, 175), font=F(19), anchor='lm')
    out.paste(img, (LW + 16, 104))
    y = 110
    for i in range(9, -1, -1):
        n, c = LEVELS[i]
        d.rectangle([16, y, 56, y + 34], fill=hx(c), outline=(60, 70, 84))
        d.text((70, y + 17), f'{i}  {n}', fill=(240, 228, 200), font=F(19), anchor='lm')
        cnt = int((lv == i).sum() / lv.size * 100)
        d.text((300, y + 17), f'{cnt}%', fill=(150, 160, 175), font=F(16), anchor='rm')
        y += 46
    # side cross-section
    y += 14
    d.text((16, y), 'CROSS-SECTION', fill=(232, 180, 106), font=F(19)); y += 30
    row = lv[lv.shape[0] // 2]
    for x in range(min(len(row), 150)):
        hh = row[x] * 14 + 8
        c = hx(LEVELS[row[x]][1]) if row[x] > 2 else hx('#3277b0')
        d.rectangle([16 + x * 2, y + 150 - hh, 16 + x * 2 + 1, y + 150], fill=c)
    d.line([16, y + 150 - 3 * 14 - 8, 316, y + 150 - 3 * 14 - 8], fill=(90, 160, 220), width=1)
    out.save('terrain_levels.png'); print('levels', out.size)


if __name__ == '__main__':
    biome_sheet(); levels_sheet()
