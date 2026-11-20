"""Procedural cultures born from their founders.
founders (traits) + birthplace biome  ->  values -> belief & rule -> architecture, dress, palette, names, clans.
Nothing is fixed: every new kingdom rolls a new genome."""
import colorsys, math, random
import numpy as np
from lib import *
from houses import W, R, block, garden, patch_roof, laundry, woodpile, pergola, tower
from buildings import roof_gable, roof_cone, roof_flat, roof_thatch, roof_crenel, banner, flag, chimney, wall, windows, door

TRAITS = ['BRAVE', 'CRUEL', 'CUNNING', 'GREEDY', 'PIOUS', 'KIND', 'CURIOUS', 'PATIENT', 'PROUD', 'STOIC', 'WANDERER', 'ARTISTIC']
TRAIT_COL = {'BRAVE': '#e06a55', 'CRUEL': '#b03a3a', 'CUNNING': '#9d76c2', 'GREEDY': '#ecc25c', 'PIOUS': '#f0e6c8', 'KIND': '#7cc46a',
             'CURIOUS': '#5fe0e8', 'PATIENT': '#8fb4d8', 'PROUD': '#e8a04a', 'STOIC': '#a0a8b0', 'WANDERER': '#c8a070', 'ARTISTIC': '#e87ab8'}
VALUE_OF = {'BRAVE': 'MARTIAL', 'CRUEL': 'MARTIAL', 'CUNNING': 'MERCANTILE', 'GREEDY': 'MERCANTILE', 'PIOUS': 'DEVOUT', 'KIND': 'COMMUNAL',
            'CURIOUS': 'SCHOLARLY', 'PATIENT': 'SCHOLARLY', 'PROUD': 'GRANDEUR', 'STOIC': 'TRADITION', 'WANDERER': 'NOMADIC', 'ARTISTIC': 'ARTISAN'}
RULE = {'MARTIAL': 'WARLORD CHIEFDOM', 'MERCANTILE': 'MERCHANT COUNCIL', 'DEVOUT': 'THEOCRACY', 'COMMUNAL': 'ELDER COUNCIL', 'SCHOLARLY': 'SAGE KINGS',
        'GRANDEUR': 'SUN MONARCHY', 'TRADITION': 'ANCESTRAL LAW', 'NOMADIC': 'KHANATE', 'ARTISAN': 'GUILD REPUBLIC'}
# Creeds are fully fictional and revere only things of this world (a peak, a tree, a river, founders, a famous event).
BELIEF = {'MARTIAL': ('CREED OF THE IRON PEAK', 210), 'MERCANTILE': ('CREED OF THE GOLDEN SCALE', 45), 'DEVOUT': ('CREED OF THE ELDER TREE', 20), 'COMMUNAL': ('CREED OF THE FIRST HEARTH', 100),
          'SCHOLARLY': ('CREED OF THE OPEN EYE', 185), 'GRANDEUR': ('CREED OF THE SUN CRATER', 35), 'TRADITION': ('CREED OF THE FOUNDERS', 28), 'NOMADIC': ('CREED OF THE GREAT RIVER', 195),
          'ARTISAN': ('CREED OF THE GREAT WORKS', 320)}
BIOMES = {'RIVER': ('mudw', 'adobe', 'whitew'), 'FOREST': ('planks', 'logs'), 'MOUNTAIN': ('stone',), 'COAST': ('whitew', 'plaster'), 'STEPPE': ('hide',),
          'SNOW': ('logs',), 'JUNGLE': ('reedw', 'planks')}
BIOME_TINT = {'RIVER': '#cdb27c', 'FOREST': '#3f6a3c', 'MOUNTAIN': '#8a9478', 'COAST': '#b8c890', 'STEPPE': '#b8b070', 'SNOW': '#dfe8ec', 'JUNGLE': '#2f6a34'}
SKIN_BY = {'RIVER': ['#8a5a3a', '#9e6a44', '#b07a50'], 'FOREST': ['#e8c4a4', '#dcb090', '#c89a74'], 'MOUNTAIN': ['#c89a74', '#d4a882', '#b88a66'],
           'COAST': ['#b07a50', '#c89a74', '#d4a882'], 'STEPPE': ['#c8946a', '#d4a47a', '#b88458'], 'SNOW': ['#f0d0b4', '#e8c4a4', '#f4dcc4'],
           'JUNGLE': ['#6e4428', '#7a4e32', '#8a5a3a']}
HAIR_BY = {'RIVER': ['#1a1410', '#2a1e16'], 'FOREST': ['#5a3a22', '#a8642e', '#3a2618'], 'MOUNTAIN': ['#3a2618', '#2a1e16', '#7a4a26'],
           'COAST': ['#2a1e16', '#5a3a22'], 'STEPPE': ['#1a1410', '#2a1e16'], 'SNOW': ['#d8b46a', '#e6cc8a', '#c8743a'], 'JUNGLE': ['#1a1410', '#120e0a']}
SYMBOLS = {
    'sun': ["..#..", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "..#.."], 'leaf': ["..##.", ".###.", "####.", "###..", "##.#.", "#...#", "....."],
    'tree': [".###.", "#####", "#####", ".###.", "..#..", "..#..", ".###."], 'wave': [".....", ".#...", "#.#.#", "...#.", ".#...", "#.#.#", "...#."],
    'peak': [".....", "..#..", ".###.", ".###.", "#####", "#####", "....."], 'eye': [".....", ".###.", "#...#", "#.#.#", "#...#", ".###.", "....."],
    'axe': [".##..", "###.#", ".####", "...#.", "..#..", ".#...", "#...."], 'gear': [".#.#.", "#####", "##.##", "#...#", "##.##", "#####", ".#.#."], 'hearth': ["..#..", ".###.", "#####", ".#.#.", ".#.#.", ".###.", "....."],
    'horn': ["#....", "##...", ".##..", "..###", "...##", "....#", "....."], 'scale': ["#####", "#...#", "#...#", "##.##", ".....", ".###.", "#####"],
}
SYM_BY_VALUE = {'MARTIAL': 'axe', 'MERCANTILE': 'scale', 'DEVOUT': 'tree', 'COMMUNAL': 'hearth', 'SCHOLARLY': 'eye', 'GRANDEUR': 'sun',
                'TRADITION': 'leaf', 'NOMADIC': 'horn', 'ARTISAN': 'gear'}


def hramp(h, s=.55, v=.62):
    out = []
    for k, (ds, dv) in enumerate([(.15, -.32), (.08, -.17), (0, 0), (-.1, .14), (-.25, .28)]):
        r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, max(0, min(1, s + ds)), max(0, min(1, v + dv)))
        out.append((int(r * 255), int(g * 255), int(b * 255)))
    return out


# ---------------------------------------------------------------- names
CONS = [list('bdgklmnrstvz'), list('hkmnrstwy'), list('fglmnrsvz') + ['th'], list('bdgkpqrtz') + ['kh', 'sh'], list('lmnrsvy') + ['ph'],
        list('dgjkmnrstz') + ['zh', 'ch']]
VOWS = [list('aeiou'), list('aaiou'), list('eeiao'), list('aaoou'), ['a', 'e', 'i', 'ia', 'ae'], ['a', 'o', 'u', 'ai', 'ei']]
ENDS = ['ia', 'an', 'ar', 'eth', 'or', 'um', 'ani', 'esh', 'ova', 'ir', 'ka', 'oth']


class Namer:
    def __init__(self, rng):
        k = rng.randrange(len(CONS))
        self.c, self.v = CONS[k], VOWS[rng.randrange(len(VOWS))]
        self.end = rng.sample(ENDS, 3); self.rng = rng
        self.pat = rng.choice([['CV', 'CVC'], ['CV', 'CV', 'CVC'], ['CVC', 'CV'], ['CV', 'CVN']])
        self.lead = rng.random() < .3

    def syl(self, p):
        r = self.rng
        return ''.join(r.choice(self.c) if ch == 'C' else r.choice('nrls') if ch == 'N' else r.choice(self.v) for ch in p)

    def word(self, n=None):
        r = self.rng
        n = n or r.choice([2, 2, 3])
        w = (r.choice(self.v) if self.lead and r.random() < .5 else '') + ''.join(self.syl(r.choice(self.pat)) for _ in range(n))
        import re
        w = re.sub(r'([aeiouy])[aeiouy]+', lambda m: m.group(0)[:2] if len(set(m.group(0))) > 1 else m.group(1), w)
        w = re.sub(r'(.)\1\1', r'\1\1', w)
        if len(w) < 4: w += self.syl('CV')
        return w[:8].upper()

    def place(self): return (self.word(2) + self.rng.choice(self.end)).upper()[:10]


# ---------------------------------------------------------------- genome
def make_culture(seed):
    rng = random.Random(seed)
    nm = Namer(rng)
    biome = rng.choice(list(BIOMES.keys()))
    founders = []
    for i in range(3):
        tr = rng.sample(TRAITS, 2)
        founders.append(dict(name=nm.word(2), traits=tr, gender=rng.choice('mf')))
    # values: weighted vote of founder traits (the first founder = leader, counts double)
    votes = {}
    for i, f_ in enumerate(founders):
        for t in f_['traits']:
            votes[VALUE_OF[t]] = votes.get(VALUE_OF[t], 0) + (2 if i == 0 else 1)
    values = sorted(votes, key=lambda k: (-votes[k], rng.random()))[:2]
    v0 = values[0]
    alltr = [t for f_ in founders for t in f_['traits']]
    belief, hue = BELIEF[v0]
    hue = (hue + rng.uniform(-18, 18)) % 360
    acc = hramp(hue, .55 + rng.uniform(-.1, .1), .62)
    acc2 = hramp((hue + rng.choice([150, 180, 200])) % 360, .45, .58)
    nomad = 'NOMADIC' in values or biome == 'STEPPE'
    wallm = rng.choice(BIOMES[biome]) if not nomad else 'hide'
    if nomad: roof = 'yurt'
    elif 'GRANDEUR' in values or 'DEVOUT' in values: roof = rng.choice(['dome', 'cone', 'dome'])
    elif 'TRADITION' in values or 'SCHOLARLY' in values: roof = rng.choice(['tiered', 'hip', 'tiered'])
    elif nomad: roof = 'yurt'
    elif 'COMMUNAL' in values: roof = rng.choice(['gable', 'thatch'])
    elif 'MERCANTILE' in values: roof = rng.choice(['flat', 'hip'])
    else: roof = rng.choice(['gable', 'cone', 'flat', 'thatch'])
    if biome in ('RIVER', 'STEPPE') and roof in ('gable', 'tiered') and rng.random() < .5: roof = 'flat'
    if biome in ('SNOW', 'FOREST') and roof == 'flat': roof = 'gable'
    rroof = {'dome': acc, 'cone': acc, 'tiered': acc2 if rng.random() < .5 else acc, 'hip': R['slate'] if biome == 'MOUNTAIN' else acc,
             'gable': rng.choice([R['K'], R['shingle'], R['turf'], acc]), 'flat': R['mud'], 'thatch': R['straw'], 'yurt': hramp(hue, .22, .74)}[roof]
    orn = []
    if 'MARTIAL' in values: orn += ['banner', 'spikes']
    if 'DEVOUT' in values or 'GRANDEUR' in values: orn += ['spire']
    if 'MERCANTILE' in values: orn += ['awning']
    if 'ARTISAN' in values: orn += ['tiles']
    if 'COMMUNAL' in values or 'KIND' in alltr: orn += ['garden']
    if 'TRADITION' in values: orn += ['totem']
    tall = 'PROUD' in alltr or 'GRANDEUR' in values
    # dress
    garment = rng.choice(['robe', 'robe', 'pants']) if biome in ('RIVER', 'COAST', 'JUNGLE') else rng.choice(['pants', 'kilt', 'pants'])
    if nomad: garment = 'pants'
    head = {'MARTIAL': rng.choice(['band', 'feathers']), 'DEVOUT': 'turban' if biome in ('RIVER', 'COAST') else 'hood', 'MERCANTILE': rng.choice(['turban', 'skullcap', 'flatcap']),
            'SCHOLARLY': rng.choice(['skullcap', 'band']), 'GRANDEUR': 'turban', 'TRADITION': rng.choice(['bonnet', 'band']), 'NOMADIC': 'furhat',
            'COMMUNAL': rng.choice([None, 'band']), 'ARTISAN': rng.choice(['feathers', 'bonnet'])}[v0]
    if biome == 'SNOW': head = 'furhat'
    fhead = rng.choice(['scarf', 'veil', None, 'kerchief']) if v0 in ('DEVOUT', 'GRANDEUR', 'TRADITION') else rng.choice([None, None, 'kerchief', 'band'])
    crown = {'MARTIAL': 'crown_north', 'GRANDEUR': 'crown_river', 'DEVOUT': 'crown_river', 'NOMADIC': 'furhat'}.get(v0, 'circlet')
    g = dict(seed=seed, namer=nm, name=nm.place(), people=None, biome=biome, founders=founders, values=values, belief=belief, rule=RULE[v0],
             acc=acc, acc2=acc2, wall=wallm, roof=roof, rroof=rroof, orn=orn, tall=tall, nomad=nomad, garment=garment, head=head, fhead=fhead,
             crown=crown, paint='MARTIAL' in values, gold='GREEDY' in alltr or 'GRANDEUR' in values,
             skins=SKIN_BY[biome], hairs=HAIR_BY[biome], symbol=SYM_BY_VALUE[v0], tint=hx(BIOME_TINT[biome]),
             layout={'MARTIAL': 'RING + WALLS', 'MERCANTILE': 'ALONG ROADS', 'DEVOUT': 'AROUND SANCTUM', 'COMMUNAL': 'CLUSTERS', 'SCHOLARLY': 'GRID',
                     'GRANDEUR': 'AXIAL AVENUE', 'TRADITION': 'TERRACES', 'NOMADIC': 'CAMP CIRCLES', 'ARTISAN': 'WINDING QUARTERS'}[v0])
    g['people'] = g['name'] + 'N' if g['name'][-1] == 'A' else g['name'][:-1] + 'I' if g['name'][-1] in 'EIOU' else g['name'] + 'I'
    g['clans'] = []
    for i, f_ in enumerate(founders):
        g['clans'].append(dict(name='HOUSE ' + nm.word(2), founder=f_['name'], trait=f_['traits'][0],
                               col=hramp((hue + i * 47 + rng.uniform(-10, 10)) % 360, .5, .6), symbol=rng.choice(list(SYMBOLS))))
    return g


# ---------------------------------------------------------------- crest
def crest(f, x, y, g, big=1, col=None, symbol=None):
    col = col or g['acc']; symbol = symbol or g['symbol']
    shape = ["###########", "###########", "###########", "###########", "###########", "###########", "###########", "###########",
             ".#########.", ".#########.", "..#######..", "...#####...", "....###...."]
    split = random.Random(g['seed'] + (hash(symbol) % 7)).choice(['plain', 'pale', 'fess', 'chevron'])
    for j, row in enumerate(shape):
        for i, c in enumerate(row):
            if c != '#': continue
            cc = col[2]
            if split == 'pale' and i >= 6: cc = col[1]
            if split == 'fess' and j >= 6: cc = col[1]
            if split == 'chevron' and j >= 4 + abs(i - 5) // 1 and j < 7 + abs(i - 5): cc = g['acc2'][2]
            if j == 0 or i == 0: cc = lit(cc, .2)
            rect(f, x + i * big, y + j * big, big, big, cc)
    sym = SYMBOLS[symbol]
    for j, row in enumerate(sym):
        for i, c in enumerate(row):
            if c == '#': rect(f, x + (3 + i) * big, y + (2 + j) * big, big, big, hx('#f3e6c8') if not g['gold'] else C['gold'])


# ---------------------------------------------------------------- houses from genome
def yurt(a, x, b, w, g, seed, band=True):
    h = max(3, w // 3)
    shadow_ell(a, x + w / 2 + 2, b + 1, w / 2 + 1, 2)
    wall(a, x, b - h + 1, w, h, 'hide', seed)
    if band: hline(a, x, b - h + 2, w, g['acc'][2]); hline(a, x, b - h + 3, w, g['acc'][1])
    dome(a, x + w / 2, b - h, w / 2 + .5, w / 3.2, g['rroof'], seed, top=b - h + 1)
    put(a, x + w // 2, b - h - int(w / 3.2), C['wood'][1])
    rect(a, x + w // 2 - 1, b - 2, 2, 3, g['acc'][1])


def roofed(a, x, b, w, wh, g, seed, tier, win=(1, 2, 4, 3), dpos='c', shadow=True):
    rf = g['roof']; rp = g['rroof']
    m = g['wall'] if g['wall'] != 'hide' else 'planks'
    if rf == 'yurt':
        yurt(a, x, b, w, g, seed); return b - wh - w // 3
    rh = {'gable': max(3, w // 2), 'hip': max(3, w // 2), 'flat': 3, 'dome': 3, 'cone': max(4, w // 2 + 1), 'tiered': max(3, w // 2 - 1), 'thatch': max(3, w // 2)}[rf]
    base_roof = {'dome': 'flat', 'tiered': 'gable', 'cone': 'gable'}.get(rf, rf)
    top = block(a, x, b, w, wh, rh, m, base_roof, rp if base_roof != 'flat' else R['mud'] if m in ('mudw', 'adobe') else R['stone'], seed, win, .5, dpos,
                2 if w < 14 else 3, 3, 'arch' if rf in ('dome', 'cone') else 'sq', shadow=shadow, dcol=g['acc'][1])
    if rf == 'dome' and tier >= 2:
        dome(a, x + w / 2, top - 1, min(w / 3, 5) + .5, min(w / 3.4, 4.4), rp, seed); put(a, x + w // 2, top - int(min(w / 3.4, 4.4)) - 2, C['gold'])
    if rf == 'tiered' and tier >= 2:
        w2 = w - 6
        block(a, x + 3, top + 2, w2, 2, max(3, w2 // 2), m, 'gable', rp, seed + 9, None, 0, None, shadow=False)
        for xx in (x - 1, x + w): put(a, xx, top + rh - 2, rp[3])
    if rf == 'cone' and tier >= 3:
        roof_cone(a, x + w // 2 - 2, top - 7, 5, 8, rp)
    return top


def gen_house(a, x, b, g, tier, seed):
    x, b, seed = int(x), int(b), int(seed)
    rng = random.Random(seed)
    fx = []
    acc = g['acc']
    if tier == 0:
        w = rng.randint(6, 8)
        if g['nomad']:
            for i in range(w):
                hh = 4 - abs(i - w // 2) * 4 // w
                vline(a, x + i, b - hh, hh + 1, R['hide'][1 + (i % 2)])
            patch_roof(a, x, b - 4, w, 2, rng)
        else:
            m = 'mud' if g['wall'] in ('mudw', 'adobe', 'whitew', 'plaster') else 'planks' if g['wall'] != 'stone' else 'stone'
            wall(a, x, b - 2, w, 3, m, seed)
            for i in range(w + 2): put(a, x - 1 + i, b - 4, [R['tin'][2], R['reed'][2], C['wood'][1]][rng.randint(0, 2)]); put(a, x - 1 + i, b - 3, R['tin'][1])
            patch_roof(a, x, b - 5, w, 2, rng); rect(a, x + w // 2, b - 1, 2, 2, hx('#1e1610'))
        if rng.random() < .6: woodpile(a, x + w + 2, b)
        return fx
    if tier == 1:
        w = rng.randint(8, 10)
        top = roofed(a, x, b, w, rng.randint(4, 5), g, seed, 1, (1, 2, 4, 3), rng.choice('lcr'))
        if 'garden' in g['orn']: garden(a, x + w + 1, b - 3, 4, 4, rng)
        elif rng.random() < .5: laundry(a, x + w + 1, b - 5, 5, rng)
        return fx
    if tier == 2:
        w = rng.randint(11, 13)
        top = roofed(a, x, b, w, 7 if not g['nomad'] else 0, g, seed, 2, (2, 2, 4, 3))
        if g['nomad']: yurt(a, x + w + 1, b, 7, g, seed + 3, False)
        if 'awning' in g['orn']:
            for i in range(w - 2): put(a, x + 1 + i, b - 4, acc[3] if (i // 2) % 2 else hx('#f0ece0')); put(a, x + 1 + i, b - 3, acc[1])
        if 'garden' in g['orn']: garden(a, x + w + 1, b - 4, 5, 5, rng)
        if 'totem' in g['orn']: vline(a, x - 3, b - 9, 10, C['wood'][1]); rect(a, x - 4, b - 9, 3, 2, acc[2]); rect(a, x - 4, b - 6, 3, 2, acc[3])
        return fx
    if tier == 3:
        w = rng.randint(15, 18)
        if g['nomad']:
            yurt(a, x + 4, b, 14, g, seed); yurt(a, x - 3, b + 1, 8, g, seed + 1, False); yurt(a, x + 16, b + 1, 8, g, seed + 2, False)
            vline(a, x + 11, b - 18, 8, C['wood'][1]); banner(a, x + 12, b - 18, 4, acc)
            return fx
        top = roofed(a, x, b, w, 9, g, seed, 3, (2, 3, 4, 4))
        if g['tall']: tower(a, x + w - 2, b, 5, 16, g['wall'] if g['wall'] != 'hide' else 'stone', 'dome' if g['roof'] == 'dome' else 'cone', seed, g['rroof'])
        if 'banner' in g['orn']: banner(a, x + 2, b - 7, 3, acc); banner(a, x + w - 4, b - 7, 3, acc)
        if 'garden' in g['orn'] or 'awning' in g['orn']: garden(a, x - 6, b - 4, 5, 5, rng)
        if 'spire' in g['orn']: vline(a, x + w // 2, top - 9, 6, C['gold'])
        return fx
    # palace
    w = rng.randint(26, 30)
    if g['nomad']:
        yurt(a, x + 7, b, 18, g, seed)
        for k, xx in enumerate((x - 2, x + 25)): yurt(a, xx, b + 1, 9, g, seed + k, False)
        for xx in (x + 3, x + 29): vline(a, xx, b - 22, 12, C['wood'][1]); banner(a, xx + 1, b - 22, 6, acc)
        put(a, x + 16, b - 13, C['gold'])
        return fx
    m = g['wall'] if g['wall'] != 'hide' else 'stone'
    if 'spikes' in g['orn']:
        for i in range(-3, w + 3, 2): vline(a, x + i, b - 4, 5, C['wood'][2]); put(a, x + i, b - 5, C['wood'][1])
    roofed(a, x, b - 1, 8, 7, g, seed + 1, 2, (2, 2, 3, 3), None)
    roofed(a, x + w - 8, b - 1, 8, 7, g, seed + 2, 2, (2, 2, 3, 3), None)
    top = roofed(a, x + 6, b, w - 12, 11, g, seed, 4, (2, 3, 4, 4), 'c', shadow=True)
    if g['roof'] == 'dome': dome(a, x + w / 2, top - 2, 6, 5.4, g['rroof'], seed); put(a, x + w // 2, top - 9, C['gold'])
    if g['tall']:
        for tx in (x - 2, x + w - 3): tower(a, tx, b, 5, 20, m, 'dome' if g['roof'] == 'dome' else 'cone', seed + tx, g['rroof'])
    if 'spire' in g['orn']: vline(a, x + w // 2, top - 16, 8, C['gold'])
    if 'garden' in g['orn']: garden(a, x + 2, b + 2, w - 4, 2, rng)
    banner(a, x + 9, b - 8, 3, acc); banner(a, x + w - 11, b - 8, 3, acc)
    flag(a, x + w // 2, top - 3, acc, 7)
    return fx


def outfit_from(g, cls, gender):
    T3 = lambda rp: [rp[1], rp[2], rp[3]]
    m = gender == 'm'
    earth = [hx('#5e5040'), hx('#78684f'), hx('#94826a')]
    bot = g['garment'] if m else ('dress' if g['garment'] != 'kilt' else 'dress')
    if g['nomad']: bot = 'pants'
    if cls == 'poor':
        return dict(top=earth, bot=bot, brp=[hx('#4a3e32'), hx('#5e5040'), hx('#73644f')], shoes=None, head=g['head'] if m else g['fhead'],
                    hcol=earth, item='basket' if not m else 'bucket', ex=['patch'] + (['legwrap'] if bot == 'pants' else []), cape=None)
    if cls == 'middle':
        return dict(top=T3(g['acc']), bot=bot, brp=T3(g['acc2']) if bot != 'robe' else None, shoes=hx('#5a3e28'), head=g['head'] if m else g['fhead'],
                    hcol=T3(g['acc2']), item=None, ex=(['plaid'] if bot == 'kilt' else []) + (['belt_brass'] if bot == 'pants' else []), cape=None)
    if cls == 'rich':
        return dict(top=T3(g['acc2']), bot=bot, brp=T3(g['acc']), shoes=hx('#2a1e16'), head=g['head'] if m else g['fhead'],
                    hcol=T3(g['acc']), item=None, ex=['trim_gold' if g['gold'] else 'trim_silver', 'necklace' if g['gold'] else 'brooch'], cape=T3(g['acc']) if not m else None)
    return dict(top=T3(g['acc']), bot='robe' if bot in ('robe', 'dress') else bot, brp=T3(g['acc2']), shoes=hx('#c8a050'), head=g['crown'],
                hcol=T3(g['acc2']), item='sword' if 'MARTIAL' in g['values'] else 'crook', ex=['collar_gold' if g['gold'] else 'furcollar', 'trim_gold'],
                cape=T3(g['acc2']))
