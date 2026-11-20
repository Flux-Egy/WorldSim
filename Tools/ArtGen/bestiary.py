"""Bestiary: 60+ land/air species, 25 sea creatures, 30 biome creatures.  Fine 2x grid, facing right, light top-left.
Quadrupeds reuse animals.quad (poses walk/idle/run/eat/attack/sleep); special bodies (birds, insects, snakes, crabs,
scorpions, spiders, worms, frogs, sea life) have their own drawers with the same pose names."""
import math, random
import numpy as np
from lib import *
import animals as AN
from animals import SP, R5, DARK, line, quad

GLOW = {'cyan': hx('#5fe0e8'), 'fire': hx('#ffb84a'), 'toxic': hx('#9ae04a'), 'violet': hx('#c87ae8'), 'ice': hx('#cfefff'), 'gold': hx('#ffd34a')}


# ------------------------------------------------------------------ extras (drawn after the head, get geometry dict g)
def ex_trunk(a, g):
    x, y = int(g['hcx'] + g['hrx'] * .6), int(g['hcy'] + g['hry'] * .2)
    curl = 1 if g['pose'] in ('eat', 'attack') else 0
    for i in range(int(g['hry'] * 2.4)):
        put(a, x + (i // 3 if curl else (1 if i > 4 else 0)), y + i, g['hrp'][2] if i % 3 else g['hrp'][1]); put(a, x + 1 + (i // 3 if curl else (1 if i > 4 else 0)), y + i, g['hrp'][1])
    put(a, x - 1, y + 2, hx('#f2ece0')); put(a, x - 2, y + 3, hx('#f2ece0'))   # tusk


def ex_bigears(a, g):
    dome(a, g['hcx'] - g['hrx'] * .6, g['hcy'] + 1, g['hrx'] * .8, g['hry'] * 1.1, [lit(c, -.08) for c in g['hrp']], 9)


def ex_horn_nose(a, g):
    x, y = int(g['hcx'] + g['hrx'] + g['sn'] * .6), int(g['hcy'] - g['hry'] * .3)
    for i in range(4): put(a, x - i // 2, y - i, hx('#e2d8c2') if i < 3 else hx('#c8bc9e'))
    put(a, x - 3, y - 1, hx('#c8bc9e'))


def ex_lionmane(a, g):
    if g['young']: return
    m = R5('#5a3418', '#7a4a20', '#9a6228', '#b87a30', '#d09440')
    dome(a, g['hcx'] - 1, g['hcy'] + .5, g['hrx'] * 1.55, g['hry'] * 1.6, m, g['seed'], rough=.4)
    dome(a, g['hcx'] + .5, g['hcy'], g['hrx'] * .9, g['hry'] * .9, g['hrp'], g['seed'] + 1)
    put(a, int(g['hcx'] + g['hrx'] * .3), int(g['hcy'] - g['hry'] * .3), DARK)
    put(a, int(g['hcx'] + g['hrx'] + 1), int(g['hcy']), DARK)


def ex_spikes(col):
    def f(a, g):
        for i in range(-2, 3):
            x = int(g['cx'] + i * g['rx'] * .35); y = int(g['cy'] - g['ry'])
            for k in range(3 + (i % 2)): put(a, x + k // 2, y - k, lit(col, .3 - k * .1))
    return f


def ex_glow_eye(col):
    def f(a, g):
        ex, ey = int(g['hcx'] + g['hrx'] * .3), int(g['hcy'] - g['hry'] * .3)
        if g['pose'] != 'sleep':
            put(a, ex, ey, col); blend_mask(a, ellipse_mask(a.shape[:2], ex, ey, 2, 2), col, .35)
    return f


def ex_cracks(col):
    def f(a, g):
        r = random.Random(g['seed'])
        for _ in range(5):
            x, y = g['cx'] + r.uniform(-g['rx'] * .7, g['rx'] * .7), g['cy'] + r.uniform(-g['ry'] * .3, g['ry'] * .5)
            for k in range(3): put(a, int(x + k), int(y + (k % 2)), col)
        blend_mask(a, ellipse_mask(a.shape[:2], g['cx'], g['cy'], g['rx'] * .8, g['ry'] * .6), col, .12)
    return f


def ex_mushrooms(a, g):
    for i, dx in enumerate((-.4, .1, .45)):
        x, y = g['cx'] + g['rx'] * dx, g['cy'] - g['ry'] - 1
        vline(a, int(x), int(y), 2, hx('#e8e0cc'))
        dome(a, x + .5, y - 1, 2.2, 1.6, [hx('#6a2a5a'), hx('#8a3a76'), hx('#a85a94'), hx('#c87ab4'), hx('#e8a8d8')], i)


def ex_moss(a, g):
    r = random.Random(g['seed'])
    for _ in range(int(g['rx'] * 3)):
        x, y = g['cx'] + r.uniform(-g['rx'] * .8, g['rx'] * .8), g['cy'] - g['ry'] * r.uniform(.4, 1.0)
        put(a, int(x), int(y), [hx('#4a7a34'), hx('#6a9a44'), hx('#8aba5a')][r.randint(0, 2)])


def ex_crystals(col):
    def f(a, g):
        for i, dx in enumerate((-.5, -.1, .3)):
            x, y = int(g['cx'] + g['rx'] * dx), int(g['cy'] - g['ry'] + 1)
            for k in range(4 + i % 2):
                put(a, x, y - k, lit(col, .25 - k * .08)); put(a, x + 1, y - k + 1, lit(col, -.15))
            put(a, x, y - 4 - i % 2, hx('#ffffff'))
    return f


def ex_stones(a, g):
    for i, dx in enumerate((-.5, 0, .4)):
        dome(a, g['cx'] + g['rx'] * dx, g['cy'] - g['ry'] + .5, 2.4, 1.8, R5('#4a4844', '#6a6660', '#8a857c', '#aaa498', '#c8c2b4'), i)


def ex_flames(a, g):
    for i, dx in enumerate((-.6, -.2, .2)):
        x, y = int(g['cx'] + g['rx'] * dx), int(g['cy'] - g['ry'])
        fl = (g['frame'] + i) % 3
        put(a, x, y - 1, hx('#d5452d')); put(a, x, y - 2 - fl % 2, hx('#f49a3c')); put(a, x + (fl == 1), y - 3 - fl % 2, hx('#ffd34a'))


def ex_frost(a, g):
    for i in range(-2, 3):
        x = int(g['cx'] + i * g['rx'] * .35); y = int(g['cy'] - g['ry'])
        put(a, x, y - 1, hx('#e8f6ff')); put(a, x, y - 2, hx('#bfe6f8')); put(a, x + 1, y - 1, hx('#9ad0f0'))


def ex_antlers_big(a, g):
    if g['young']: return
    ac = hx('#c9b48a'); ad = hx('#9a845e')
    x, y = g['ebx'] + 1, g['et']
    for (dx, dy) in [(0, -1), (0, -2), (-1, -3), (-2, -3), (-3, -3), (-4, -4), (-2, -4), (-3, -5), (1, -3), (2, -3), (3, -4), (2, -5), (4, -5), (-4, -2)]:
        put(a, x + dx, y + dy, ac if dx >= 0 else ad)


def ex_shell(col):
    def f(a, g):
        dome(a, g['cx'], g['cy'] - g['ry'] * .2, g['rx'] * 1.05, g['ry'] * 1.05, col, g['seed'])
        for i in range(-1, 2):
            for j in (0, 1):
                put(a, int(g['cx'] + i * g['rx'] * .5), int(g['cy'] - g['ry'] * .5 + j * g['ry'] * .6), lit(col[1], -.2))
    return f


def ex_pouch(a, g):
    put(a, int(g['cx'] + g['rx'] * .5), int(g['cy'] + g['ry'] * .6), lit(g['rp'][3], .1))


# ------------------------------------------------------------------ new quadruped species (added to animals.SP)
NEW_SP = {
    'elephant': dict(rx=11, ry=7, rp=R5('#5a5652', '#6e6a66', '#86827c', '#a09b94', '#bab5ad'), fur='short', head=(4.2, 4), neck=(0, 0), snout=0, ears='side',
                     legs=(7, 3), lcol=hx('#6e6a66'), tail='tuft', extras=(ex_bigears, ex_trunk), young=dict()),
    'mammoth': dict(rx=11, ry=7.5, rp=R5('#3a2618', '#5a3a22', '#7a5030', '#946640', '#ae7e52'), fur='shaggy', rough=.35, head=(4.2, 4), neck=(0, 0), snout=0, ears='round',
                    legs=(7, 3), lcol=hx('#4a3020'), tail='tuft', extras=(ex_trunk,)),
    'giraffe': dict(rx=7, ry=4.2, rp=R5('#9a6a2a', '#c48a3a', '#dca650', '#ecc270', '#f6dc98'), fur='spots', furx=dict(col=hx('#7a4a1e'), n=8), head=(2.2, 1.8),
                    neck=(5, 13), snout=2, ears='point', horns='small', legs=(12, 1), lcol=hx('#dca650'), hoof=DARK, tail='tuft'),
    'zebra': dict(rx=7.5, ry=4, rp=R5('#c8c4bc', '#dcd8d0', '#ecE8e0', '#f6f4ee', '#ffffff'), fur='stripes', furx=dict(p=3, col=hx('#1e1c1a')), head=(2.3, 2),
                  neck=(4, 5), snout=3, ears='point', mane=hx('#1e1c1a'), legs=(7, 2), lcol=hx('#dcd8d0'), hoof=DARK, tail='tuft'),
    'lion': dict(rx=7, ry=3.8, rp=R5('#a8783a', '#c4924a', '#d8aa60', '#e8c27a', '#f4d89a'), fur='short', head=(2.6, 2.3), neck=(1.5, 1.5), snout=1.6, ears='round',
                 legs=(5, 2), lcol=hx('#c4924a'), tail='tuft', mane=hx('#7a4a20'), extras=(ex_lionmane,)),
    'tiger': dict(rx=7.5, ry=3.6, rp=R5('#b0501e', '#d0682a', '#e8843a', '#f4a056', '#fcc080'), fur='stripes', furx=dict(p=4, col=hx('#1e1410'), skip=2), head=(2.5, 2.2),
                  neck=(1.5, 1.5), snout=1.6, ears='round', legs=(5, 2), lcol=hx('#d0682a'), tail='cat', bellyc=hx('#f4ece0'), front_belly=True),
    'leopard': dict(rx=6.5, ry=3.2, rp=R5('#a8803a', '#c8a050', '#dcb868', '#ecd086', '#f8e4a8'), fur='spots', furx=dict(col=hx('#3a2a1a'), n=10), head=(2.2, 1.9),
                    neck=(1.5, 1.5), snout=1.4, ears='round', legs=(5, 1), lcol=hx('#c8a050'), tail='cat'),
    'hyena': dict(rx=6.5, ry=3.6, rp=R5('#7a6a4e', '#948260', '#ae9a74', '#c4b08a', '#d8c6a2'), fur='spots', furx=dict(col=hx('#4a3a2a'), n=7), head=(2.4, 2.1),
                  neck=(2, 2.5), snout=2, ears='round', legs=(5, 1), lcol=hx('#948260'), tail='bushy', mane=hx('#3a2e22')),
    'rhino': dict(rx=9.5, ry=5.2, rp=R5('#5e5a56', '#76726c', '#8e8982', '#a8a29a', '#c0bab0'), fur='short', head=(3.4, 2.8), neck=(0, 0), snout=2.4, ears='point',
                  legs=(5, 3), lcol=hx('#76726c'), tail='stub', extras=(ex_horn_nose,)),
    'hippo': dict(rx=10, ry=6, rp=R5('#6a5058', '#84666e', '#9c7e84', '#b4989c', '#ccb2b4'), fur='short', head=(3.8, 3.2), neck=(0, 0), snout=2.6, scol=hx('#c49a9a'), disc=True,
                  ears='tiny', legs=(4, 3), lcol=hx('#84666e'), tail='stub'),
    'buffalo': dict(rx=9, ry=5, rp=R5('#2a2220', '#3e322c', '#54443a', '#6a584a', '#806c5c'), fur='shaggy', head=(2.8, 2.5), neck=(1, 0), snout=1.6, ears='side', horns='curl',
                    legs=(5, 2), lcol=hx('#3e322c'), hoof=DARK, tail='tuft'),
    'yak': dict(rx=9, ry=5.5, rp=R5('#2a2420', '#3a322c', '#4e443a', '#62574a', '#7a6c5c'), fur='shaggy', rough=.4, head=(2.6, 2.3), neck=(1, 0), snout=1.4, ears='side',
                horns='curl', legs=(5, 2), lcol=hx('#3a322c'), tail='bushy'),
    'moose': dict(rx=8.5, ry=4.6, rp=R5('#3a2a1e', '#4e3828', '#644832', '#7a5a40', '#946e50'), fur='short', head=(2.6, 2.2), neck=(3, 4), snout=3, ears='side',
                  legs=(8, 2), lcol=hx('#4e3828'), hoof=DARK, tail='stub', extras=(ex_antlers_big,)),
    'reindeer': dict(rx=7, ry=3.8, rp=R5('#6a5a4a', '#84725e', '#9c8a74', '#b8a68e', '#d4c4ae'), fur='short', head=(2.2, 1.9), neck=(3, 4), snout=2.4, ears='side',
                     antler=True, legs=(7, 1), lcol=hx('#84725e'), hoof=DARK, tail='white', bellyc=hx('#ece4d6')),
    'llama': dict(rx=6, ry=3.6, rp=R5('#c8b498', '#dccab0', '#ecdcc4', '#f6ecdc', '#ffffff'), fur='wool', head=(2, 1.8), neck=(3, 8), snout=1.8, ears='long',
                  legs=(7, 1), lcol=hx('#c8b498'), tail='stub'),
    'panda': dict(rx=7.5, ry=5, rp=R5('#c8c8c4', '#dcdcd8', '#ececea', '#f6f6f4', '#ffffff'), fur='short', head=(3, 2.8), neck=(1, .5), snout=1.2, ears='round',
                  hrp=R5('#c8c8c4', '#dcdcd8', '#ececea', '#f6f6f4', '#ffffff'), legs=(3, 3), lcol=hx('#1e1e20'), tail='stub', marks=('face', hx('#1e1e20'))),
    'polar_bear': dict(rx=8.5, ry=5.4, rp=R5('#c8ccc8', '#dce0dc', '#ecf0ec', '#f6f8f6', '#ffffff'), fur='shaggy', head=(3, 2.6), neck=(2, 1), snout=2, scol=hx('#d8dcd8'),
                       ears='round', legs=(4, 3), lcol=hx('#dce0dc'), tail='stub'),
    'raccoon': dict(rx=4.5, ry=3, rp=R5('#5a5a5e', '#727276', '#8a8a8e', '#a6a6aa', '#c2c2c6'), fur='short', head=(2.2, 1.9), neck=(1, 1), snout=1.2, ears='point',
                    legs=(3, 1), lcol=hx('#3a3a3e'), tail='bushy', marks=('face', hx('#1e1e20'))),
    'badger': dict(rx=5, ry=2.8, rp=R5('#4a4a4c', '#606064', '#78787c', '#929296', '#acacb0'), fur='bristle', head=(2.2, 1.8), neck=(0, 0), snout=1.8,
                   ears='tiny', legs=(2, 1), lcol=hx('#2a2a2c'), tail='stub', marks=('blaze', hx('#f0ece4'))),
    'squirrel': dict(rx=3, ry=2.2, rp=R5('#8a4a1e', '#a85e28', '#c47634', '#d89048', '#ecac66'), fur='short', head=(1.8, 1.6), neck=(1, 1.5), snout=.6, ears='point',
                     legs=(2, 1), lcol=hx('#a85e28'), tail='fox', hop=True, bellyc=hx('#f0e2c8')),
    'rat': dict(rx=3, ry=1.8, rp=R5('#4a443e', '#5e5650', '#746b63', '#8c8278', '#a49a8e'), fur='short', head=(1.6, 1.3), neck=(1, .5), snout=1.2, scol=hx('#c49a9a'),
                ears='round', legs=(1, 1), lcol=hx('#c49a9a'), tail='long', tcol=hx('#c49a9a')),
    'hedgehog': dict(rx=3.6, ry=2.6, rp=R5('#4a3a2a', '#5e4a36', '#766046', '#8e785a', '#a89070'), fur='bristle', head=(1.6, 1.4), neck=(0, 0), snout=1.4,
                     hrp=R5('#9a8064', '#b49a7e', '#ccb498', '#e0cab0', '#f0dec8'), ears='tiny', legs=(1, 1), lcol=hx('#5e4a36'), tail='stub'),
    'tortoise': dict(rx=6, ry=3, rp=R5('#5a6a3a', '#6e8048', '#849858', '#9cb06a', '#b6c886'), fur='short', head=(1.8, 1.5), neck=(2, 0), snout=.8, ears='tiny',
                     legs=(2, 2), lcol=hx('#6e8048'), tail='stub', extras=(ex_shell(R5('#4a3a22', '#64502e', '#7e683c', '#9a844e', '#b8a066')),)),
    'lizard': dict(rx=5, ry=1.8, rp=R5('#3a5a2a', '#4a7034', '#5e8a40', '#78a452', '#98c06a'), fur='spots', furx=dict(col=hx('#2a4a1e'), n=5), head=(1.8, 1.3),
                   neck=(1, 0), snout=1.6, ears='tiny', legs=(1, 1), lcol=hx('#4a7034'), tail='long', tcol=hx('#4a7034')),
    'kangaroo': dict(rx=5, ry=4, rp=R5('#8a5a3a', '#a8704a', '#c08a5e', '#d4a478', '#e6be96'), fur='short', head=(2, 1.8), neck=(2, 5), snout=1.6, ears='long',
                     legs=(4, 2), lcol=hx('#a8704a'), tail='long', tcol=hx('#a8704a'), hop=True, extras=(ex_pouch,)),
    'sauropod': dict(rx=12, ry=6.5, rp=R5('#3a5a3a', '#4a6e44', '#5e8650', '#7aa066', '#9aba82'), fur='spots', furx=dict(col=hx('#3a5030'), n=6), head=(2, 1.6),
                     neck=(9, 16), snout=1.6, ears='tiny', legs=(7, 3), lcol=hx('#4a6e44'), tail='long', tcol=hx('#4a6e44')),
    'ox': dict(rx=8.5, ry=4.8, rp=R5('#7a5a3a', '#94704a', '#ae885c', '#c4a072', '#d8b88c'), fur='short', head=(2.8, 2.3), neck=(1.5, 1), snout=2, scol=hx('#c49a8a'),
               ears='side', horns='small', legs=(5, 2), lcol=hx('#94704a'), hoof=DARK, tail='tuft'),
}

BIOME_SP = {   # strange creatures that live only in certain biomes (quad based)
    'thunder_hare': ('MEADOW', 'rabbit', dict(rp=R5('#4a5a8a', '#5e70a8', '#7a8cc4', '#9aaadc', '#c0ccf0'), extras=(ex_glow_eye(GLOW['cyan']),))),
    'moss_bear': ('FOREST', 'bear', dict(extras=(ex_moss,), eyec=hx('#e8c84a'))),
    'frost_elk': ('PINE TAIGA', 'moose', dict(rp=R5('#6a7a8a', '#8494a4', '#9eaebe', '#bccad6', '#dae4ec'), extras=(ex_antlers_big, ex_frost))),
    'shadow_panther': ('JUNGLE', 'leopard', dict(rp=R5('#141418', '#1e1e24', '#2a2a32', '#383842', '#4a4a56'), furx=dict(col=hx('#0a0a0e'), n=6), extras=(ex_glow_eye(GLOW['gold']),))),
    'bog_lurker': ('SWAMP', 'lizard', dict(rx=9, ry=3, rp=R5('#2a3a22', '#3a4e2c', '#4e6638', '#668046', '#80a05a'), extras=(ex_glow_eye(GLOW['toxic']), ex_moss))),
    'horned_strider': ('SAVANNA', 'giraffe', dict(rp=R5('#7a5a8a', '#946ea8', '#ae88c0', '#c8a6d6', '#e0c8ec'), furx=dict(col=hx('#3a2a4a'), n=8), extras=(ex_horn_nose,))),
    'sand_fox': ('DESERT DUNES', 'fox', dict(rp=R5('#c8a060', '#dcb876', '#ecce92', '#f6e2b2', '#fff2d4'), extras=(ex_bigears,))),
    'rock_tortoise': ('BADLANDS', 'tortoise', dict(rx=9, ry=4.5, extras=(ex_shell(R5('#7a3a22', '#94502e', '#ae6a3e', '#c48452', '#d8a06c')), ex_stones))),
    'steppe_ram': ('STEPPE', 'goat', dict(rx=7, ry=4.5, rp=R5('#8a7a5a', '#a8946e', '#c0ac86', '#d4c4a0', '#e8dcc0'), fur='wool')),
    'woolly_rhino': ('TUNDRA', 'rhino', dict(fur='shaggy', rough=.35, rp=R5('#4a3424', '#64462e', '#7e5a3a', '#987048', '#b08860'))),
    'ice_wolf': ('SNOW', 'wolf', dict(rp=R5('#9ab4c8', '#b4cadc', '#cadcea', '#e0ecf4', '#f6fbff'), extras=(ex_frost, ex_glow_eye(GLOW['cyan'])))),
    'tusk_seal': ('GLACIER', 'hippo', dict(rx=8, ry=4, rp=R5('#5a6670', '#707e8a', '#8a98a4', '#a6b2bc', '#c2ccd4'), legs=(1, 3), extras=(ex_trunk,))),
    'cliff_lynx': ('ROCKY HIGHLAND', 'cat', dict(rx=6, ry=3.4, rp=R5('#8a7a64', '#a8967c', '#c0b096', '#d6c8b0', '#eae0cc'), furx=dict(p=5, skip=1))),
    'stone_ram': ('MOUNTAIN', 'goat', dict(rx=7, ry=4.5, rp=R5('#5a5a5c', '#727274', '#8c8c8e', '#a8a8aa', '#c4c4c6'), extras=(ex_stones,))),
    'lava_salamander': ('VOLCANIC', 'lizard', dict(rx=7, ry=2.4, rp=R5('#3a1a14', '#5a2418', '#7a3020', '#a04028', '#c85a34'), extras=(ex_cracks(GLOW['fire']), ex_glow_eye(GLOW['fire'])))),
    'ember_hound': ('VOLCANIC', 'wolf', dict(rp=R5('#1e1614', '#2e2220', '#3e302c', '#504038', '#665248'), extras=(ex_flames, ex_glow_eye(GLOW['fire'])))),
    'spore_boar': ('FUNGAL GROVE', 'boar', dict(rp=R5('#3a2a4a', '#4e3a62', '#644c7c', '#7c6294', '#967cae'), extras=(ex_mushrooms, ex_glow_eye(GLOW['violet'])))),
    'crystal_crawler': ('CRYSTAL CAVES', 'lizard', dict(rx=7, ry=2.6, rp=R5('#2a3450', '#3a4668', '#4e5c82', '#68769c', '#8694b8'), extras=(ex_crystals(GLOW['cyan']),))),
    'mutant_boar': ('IRRADIATED WASTE', 'boar', dict(rp=R5('#3a4a22', '#4e622c', '#647c38', '#7e9846', '#9ab45a'), extras=(ex_cracks(GLOW['toxic']), ex_glow_eye(GLOW['toxic'])))),
    'giant_rat': ('FARMLAND', 'rat', dict(rx=5.5, ry=3.2, head=(2.4, 2))),
    'salt_crawler': ('SALT FLATS', 'lizard', dict(rp=R5('#a8a49c', '#c0bcb4', '#d6d2ca', '#e8e4dc', '#f8f6f0'), extras=(ex_crystals(hx('#ffffff')),))),
    'glimmer_deer': ('FLOWER FIELD', 'deer', dict(rp=R5('#5a7a8a', '#7094a4', '#8aaebe', '#a8c8d6', '#c8e0ec'), extras=(ex_glow_eye(GLOW['cyan']), ex_crystals(GLOW['cyan'])))),
}


def install():
    SP.update(NEW_SP)
    for name, (biome, base, over) in BIOME_SP.items():
        s = dict(SP[base]); s.update(over)
        s.pop('young', None)
        SP[name] = s


# ------------------------------------------------------------------ special bodies
def bird(a, x, y, spec, pose='fly', frame=0, young=False):
    """flying / perched bird. spec: body ramp, wing ramp, beak colour, size, tail."""
    k = (.7 if young else 1.0) * spec.get('size', 1.0)
    rp, wp, bk = spec['rp'], spec['wp'], spec['beak']
    if pose == 'fly':
        cx, cy = x + 14, y + 12 + [0, -1, 0, 1][frame % 4]
        shadow_ell(a, cx + 2, y + 30, 5 * k, 1, .18)
        dome(a, cx, cy, 5 * k, 2.6 * k, rp, 3)
        dome(a, cx + 5 * k, cy - 1, 2.2 * k, 2 * k, spec.get('hp', rp), 4)
        put(a, int(cx + 6 * k), int(cy - 1.5), DARK)
        for i in range(int(2 * k) + 1): put(a, int(cx + 7 * k + i), int(cy - .5), bk)
        for i in range(int(4 * k)): put(a, int(cx - 5 * k - i), int(cy + i // 2), rp[1])
        wy = [-7, -3, 2, -2][frame % 4] * k
        for i in range(int(9 * k)):
            u = i / (9 * k)
            put(a, int(cx - 1 - i * .3), int(cy - 1 + wy * u), wp[3 if u < .5 else 2])
            put(a, int(cx - i * .3), int(cy - 1 + wy * u), wp[2])
            put(a, int(cx - 2 - i * .3), int(cy - 1 + wy * u + (1 if wy > 0 else -1) * 0), wp[1])
        if spec.get('glow'): blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 8 * k, 5 * k), spec['glow'], .25)
        return
    # perched / walking / attack (peck) / sleep
    g = y + 22
    shadow_ell(a, x + 13, g + 1, 5 * k, 1.2, .28)
    hop = [0, -1][frame % 2] if pose == 'walk' else 0
    cx, cy = x + 12, g - 6 * k + hop
    for lx in (cx - 1, cx + 1): vline(a, int(lx), int(cy + 2 * k), int(g - cy - 2 * k) + 1, bk)
    dome(a, cx, cy, 4.5 * k, 3.4 * k, rp, 3)
    hx_, hy_ = cx + 4 * k, cy - 3 * k
    if pose == 'attack': hx_ += 2; hy_ += 3 * (frame % 2)
    if pose == 'sleep': hx_ -= 3; hy_ += 2
    dome(a, hx_, hy_, 2.2 * k, 2 * k, spec.get('hp', rp), 4)
    if pose != 'sleep':
        put(a, int(hx_ + 1), int(hy_ - .5), DARK)
        for i in range(int(2 * k) + 1): put(a, int(hx_ + 2.5 * k + i), int(hy_), bk)
    dome(a, cx - 1, cy, 3.4 * k, 2.2 * k, wp, 5)
    for i in range(int(3 * k)): put(a, int(cx - 4 * k - i), int(cy + 1 - i // 2), wp[1])
    if spec.get('crest'): put(a, int(hx_), int(hy_ - 2.5 * k), spec['crest']); put(a, int(hx_ - 1), int(hy_ - 3 * k), spec['crest'])


BIRDS = {
    'eagle': dict(rp=R5('#3a2618', '#5a3a22', '#7a5030', '#946640', '#ae7e52'), wp=R5('#2a1a10', '#3e2818', '#563a24', '#6e4c30', '#86603e'),
                  hp=R5('#c8c4bc', '#dcd8d0', '#ecE8e0', '#f6f4ee', '#ffffff'), beak=hx('#e8b030'), size=1.25),
    'crow': dict(rp=R5('#141418', '#1e1e24', '#2a2a32', '#383842', '#4a4a56'), wp=R5('#0e0e12', '#18181e', '#22222a', '#2e2e38', '#3c3c48'), beak=hx('#3a3a40'), size=.9),
    'owl': dict(rp=R5('#5a4a3a', '#74604a', '#8e785e', '#a89276', '#c2ac90'), wp=R5('#4a3a2a', '#5e4a36', '#766046', '#8e785a', '#a89070'), beak=hx('#e8b030'), size=1.0),
    'parrot': dict(rp=R5('#2a6a2a', '#3a8a34', '#4eaa40', '#6ac454', '#8ade70'), wp=R5('#1e3a8a', '#2a50a8', '#3a6ac4', '#5a88dc', '#80a8f0'),
                   hp=R5('#a82a2a', '#c83a34', '#e05040', '#ec7058', '#f49478'), beak=hx('#3a3430'), size=.9),
    'seagull': dict(rp=R5('#b4bcc4', '#ccd2d8', '#e2e6ea', '#f2f4f6', '#ffffff'), wp=R5('#6a747e', '#848e98', '#a0a8b0', '#bcc2c8', '#d4d8dc'), beak=hx('#e8b030'), size=1.0),
    'flamingo': dict(rp=R5('#c85a7a', '#dc7896', '#ec96ae', '#f6b4c6', '#fcd4de'), wp=R5('#a83a5a', '#c84e70', '#dc6a8a', '#ec88a4', '#f6aac0'), beak=hx('#1e1c1a'), size=1.1),
    'bat': dict(rp=R5('#2a2228', '#3a3036', '#4a3e46', '#5c4e58', '#706070'), wp=R5('#1e161c', '#2a2026', '#382c34', '#463a42', '#564852'), beak=hx('#c49a9a'), size=.8),
    'bloom_moth': dict(rp=R5('#8a4a8a', '#a85ea8', '#c47ac4', '#da9ada', '#ecbcec'), wp=R5('#c8a030', '#dcb840', '#ecd058', '#f6e27a', '#fff2a8'), beak=hx('#3a2a3a'), size=.7, glow=GLOW['gold']),
    'cave_bat': dict(rp=R5('#2a2a3a', '#3a3a4e', '#4c4c64', '#60607c', '#767696'), wp=R5('#1e1e2a', '#2a2a3a', '#36364a', '#44445c', '#545470'), beak=hx('#5fe0e8'), size=1.0, glow=GLOW['cyan']),
    'ash_crow': dict(rp=R5('#3a3634', '#4e4a46', '#64605a', '#7c7770', '#968f86'), wp=R5('#2a2624', '#3a3532', '#4c4642', '#5e5852', '#726a62'), beak=hx('#d5452d'), size=1.0),
    'giant_eagle': dict(rp=R5('#4a3a2a', '#64503a', '#7e684c', '#988060', '#b29a78'), wp=R5('#3a2a1e', '#4e3a2a', '#644c36', '#7a6044', '#927654'),
                        hp=R5('#d8c8a8', '#e8dcc0', '#f2e8d4', '#faf4e8', '#ffffff'), beak=hx('#e8b030'), size=1.9),
    'mesa_vulture': dict(rp=R5('#3a2a24', '#4e3a32', '#664c42', '#7e6052', '#987664'), wp=R5('#2a1e1a', '#3a2a24', '#4c3830', '#5e463c', '#72564a'),
                         hp=R5('#c47a6a', '#d8927e', '#e8aa96', '#f2c2b0', '#fad8cc'), beak=hx('#d8c8a0'), size=1.3),
}
GROUND_BIRDS = {
    'penguin': dict(rp=R5('#1e1e24', '#2a2a32', '#383842', '#4a4a56', '#5c5c6a'), wp=R5('#14141a', '#1e1e24', '#2a2a32', '#383842', '#4a4a56'), beak=hx('#e8902a'), size=1.1, crest=None),
    'ostrich': dict(rp=R5('#1e1a18', '#2e2824', '#3e3630', '#50463e', '#62564c'), wp=R5('#c8c4bc', '#dcd8d0', '#ece8e0', '#f6f4ee', '#ffffff'), beak=hx('#c89a7a'), size=1.6),
    'peacock': dict(rp=R5('#1e3a8a', '#2a50a8', '#3a6ac4', '#5a88dc', '#80a8f0'), wp=R5('#1e5a3a', '#2a7a4e', '#3a9a64', '#5ab47e', '#80cc9c'), beak=hx('#c8b080'), size=1.1, crest=hx('#5aa4e8')),
}


def snake(a, x, y, spec, pose='walk', frame=0, young=False):
    k = .7 if young else 1.0
    rp = spec['rp']
    g = y + 20
    L = int(26 * k)
    ph = frame * 1.2
    pts = []
    for i in range(L):
        u = i / L
        yy = g - 3 - (math.sin(u * 6 + ph) * 2 * k if pose != 'sleep' else 0)
        pts.append((x + 2 + i, yy))
    if pose == 'attack':
        pts = pts[:-6] + [(pts[-7][0] + j, pts[-7][1] - j * (1 + frame % 2)) for j in range(1, 7)]
    if pose == 'sleep':
        pts = [(x + 12 + 7 * k * math.cos(t), g - 3 + 3 * k * math.sin(t)) for t in np.linspace(0, 4 * math.pi, L)]
    shadow_ell(a, x + 15, g, 12 * k, 1.2, .22)
    for i, (px, py) in enumerate(pts):
        w = 1 + (1 if 3 < i < L - 3 else 0)
        for t in range(w + 1):
            c = rp[3] if t == 0 else rp[2] if t == 1 else rp[1]
            if spec.get('band') and (i // 3) % 2: c = lit(spec['band'], .1 - t * .1)
            put(a, int(px), int(py + t), c)
    hx_, hy_ = pts[-1]
    dome(a, hx_ + 1, hy_ + .5, 2.2 * k, 1.6 * k, rp, 3)
    if pose != 'sleep': put(a, int(hx_ + 1), int(hy_), DARK)
    if pose == 'attack' and frame % 2: put(a, int(hx_ + 3), int(hy_ + 1), hx('#d5452d')); put(a, int(hx_ + 4), int(hy_ + 2), hx('#d5452d'))


def crab(a, x, y, spec, pose='walk', frame=0, young=False):
    k = (.7 if young else 1.0) * spec.get('size', 1.0)
    rp = spec['rp']
    g = y + 20
    cx, cy = x + 14, g - 4 * k
    shadow_ell(a, cx + 1, g + 1, 7 * k, 1.2, .28)
    for s_ in (-1, 1):
        for i in range(3):
            lx = cx + s_ * (3 + i * 2) * k
            off = (1 if (i + frame) % 2 else 0) if pose == 'walk' else 0
            line(a, cx + s_ * 2 * k, cy, lx, g - off, rp[1])
    dome(a, cx, cy, 6 * k, 3.4 * k, rp, 3)
    for s_ in (-1, 1):
        clx = cx + s_ * 7 * k + (s_ * 2 if pose == 'attack' and frame % 2 else 0)
        dome(a, clx, cy - 3 * k, 2.2 * k, 1.8 * k, rp, 4)
        put(a, int(clx + s_), int(cy - 4 * k), rp[0])
    for s_ in (-1, 1): vline(a, int(cx + s_ * 2), int(cy - 5 * k), 2, rp[1]); put(a, int(cx + s_ * 2), int(cy - 5 * k), DARK)


def scorpion(a, x, y, spec, pose='walk', frame=0, young=False):
    k = (.7 if young else 1.0) * spec.get('size', 1.0)
    rp = spec['rp']
    g = y + 22
    cx, cy = x + 12, g - 3 * k
    shadow_ell(a, cx + 2, g + 1, 9 * k, 1.2, .28)
    for i in range(4):
        off = (1 if (i + frame) % 2 else 0) if pose == 'walk' else 0
        line(a, cx - 2 + i * 2, cy, cx - 3 + i * 3, g - off, rp[1]); line(a, cx - 2 + i * 2, cy, cx - 1 + i * 2, g, rp[0])
    dome(a, cx, cy, 6 * k, 2.4 * k, rp, 3)
    # tail arcing over the back
    strike = pose == 'attack' and frame % 2
    pts = [(cx - 6 * k - i * .8, cy - i * 1.6) for i in range(5)] + [(cx - 9 * k + i * 1.5 + (4 if strike else 0), cy - 8 * k - i * .3 + (3 if strike else 0)) for i in range(4)]
    for (px, py) in pts: dome(a, px, py, 1.3 * k, 1.3 * k, rp, 5)
    put(a, int(pts[-1][0] + 2), int(pts[-1][1] + 1), spec.get('sting', hx('#d5452d')))
    for s_ in (0, 1):
        dome(a, cx + 7 * k + (2 if pose == 'attack' else 0), cy - 1 + s_ * 2, 2 * k, 1.3 * k, rp, 6 + s_)


def spider(a, x, y, spec, pose='walk', frame=0, young=False):
    k = (.7 if young else 1.0) * spec.get('size', 1.0)
    rp = spec['rp']
    g = y + 22
    cx, cy = x + 14, g - 5 * k
    shadow_ell(a, cx, g + 1, 10 * k, 1.4, .3)
    for s_ in (-1, 1):
        for i in range(4):
            off = (1 if (i + frame) % 2 else 0) if pose == 'walk' else 0
            kx, ky = cx + s_ * (4 + i * 2) * k, cy - 4 * k - off
            line(a, cx + s_ * 2, cy, kx, ky, rp[1]); line(a, kx, ky, kx + s_ * 2 * k, g, rp[0])
    dome(a, cx - 3 * k, cy - 1, 5 * k, 4 * k, rp, 3)
    dome(a, cx + 3 * k, cy, 3 * k, 2.6 * k, rp, 4)
    for i in range(3): put(a, int(cx + 3 * k + i), int(cy - 1), spec.get('eyes', hx('#d5452d')))
    if spec.get('mark'): put(a, int(cx - 3 * k), int(cy - 2), spec['mark']); put(a, int(cx - 3 * k), int(cy - 1), spec['mark'])
    if pose == 'attack' and frame % 2: put(a, int(cx + 6 * k), int(cy + 1), hx('#f2ece0')); put(a, int(cx + 6 * k), int(cy + 2), hx('#f2ece0'))


def worm(a, x, y, spec, pose='walk', frame=0, young=False):
    """sand worm: rises out of the ground."""
    k = (.7 if young else 1.0) * spec.get('size', 1.0)
    rp = spec['rp']
    g = y + 40
    rise = {'walk': [8, 12, 16, 12], 'idle': [6, 7], 'attack': [18, 24, 26], 'sleep': [3, 3], 'run': [10, 14, 18, 14], 'eat': [14, 15]}.get(pose, [8])[frame % len({'walk': 4, 'idle': 2, 'attack': 3, 'sleep': 2, 'run': 4, 'eat': 2}.get(pose, 1) * [0]) if False else 0]
    rise = {'walk': [8, 12, 16, 12], 'idle': [6, 7], 'attack': [18, 24, 26], 'sleep': [3, 3], 'run': [10, 14, 18, 14], 'eat': [14, 15]}[pose][frame % {'walk': 4, 'idle': 2, 'attack': 3, 'sleep': 2, 'run': 4, 'eat': 2}[pose]]
    rise = int(rise * k)
    blend_mask(a, ellipse_mask(a.shape[:2], x + 16, g, 10 * k, 3 * k), hx('#a88a5a'), .8)
    for i in range(rise):
        w = (5 - i * .05) * k
        lean = int(i * .15)
        for xx in range(int(x + 16 - w + lean), int(x + 16 + w + lean) + 1):
            c = rp[3] if xx < x + 16 - w / 3 + lean else rp[2] if xx < x + 16 + w / 3 + lean else rp[1]
            if i % 4 == 0: c = lit(c, -.15)
            put(a, xx, g - i, c)
    top = g - rise
    mo = 3 if pose == 'attack' else 1
    dome(a, x + 16 + int(rise * .15), top, 5 * k, 2.4 * k, rp, 3)
    m = ellipse_mask(a.shape[:2], x + 17 + int(rise * .15), top - .5, 3.2 * k, mo * .8 * k)
    a[m] = hx('#3a1a1a')
    for t in range(6): put(a, int(x + 17 + rise * .15 + 3 * k * math.cos(t)), int(top + mo * .7 * math.sin(t)), hx('#f2ece0'))
    if pose in ('walk', 'run'):
        for i in range(4): put(a, x + 4 + i * 7 + frame, g + 1 - (i % 2), hx('#c8a46a'))


def frog(a, x, y, spec, pose='walk', frame=0, young=False):
    k = (.6 if young else 1.0) * spec.get('size', 1.0)
    rp = spec['rp']
    g = y + 20
    jump = [0, -4, -6, -2][frame % 4] * k if pose in ('walk', 'run') else 0
    cx, cy = x + 12, g - 3 * k + jump
    shadow_ell(a, cx + 1, g + 1, 4 * k, 1, .26)
    dome(a, cx, cy, 4.4 * k, 3 * k, rp, 3)
    for s_ in (-1, 1): dome(a, cx + 2 * k + s_ * 1.5 * k, cy - 3 * k, 1.4 * k, 1.4 * k, rp, 4)
    put(a, int(cx + 3 * k), int(cy - 3 * k), DARK) if pose != 'sleep' else None
    rect(a, int(cx - 4 * k), int(cy + 1), int(3 * k) + 1, 2, rp[1])
    if pose == 'attack' and frame % 2:
        for i in range(8): put(a, int(cx + 4 * k + i), int(cy), hx('#d87a8a'))
    if spec.get('spots'):
        for (dx, dy) in [(-2, -1), (1, -2), (-1, 1)]: put(a, int(cx + dx * k), int(cy + dy * k), spec['spots'])


def insect(a, x, y, spec, pose='walk', frame=0, young=False):
    """beetle (walks) or butterfly/bee (flies)."""
    rp = spec['rp']
    if spec.get('fly'):
        cx, cy = x + 8, y + 8 + [0, -1, 0, 1][frame % 4]
        up = frame % 2 == 0
        for s_ in (-1, 1):
            dome(a, cx - 1, cy - (3 if up else 1) * 1, 3, 2.4 if up else 1.4, spec['wp'], 2 + s_)
        rect(a, cx - 2, cy, 5, 2, rp[1]); put(a, cx + 3, cy, DARK)
        if spec.get('glow'): blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 6, 5), spec['glow'], .3)
        return
    k = spec.get('size', 1.0) * (.7 if young else 1)
    g = y + 14
    cx, cy = x + 8, g - 2 * k
    for i in range(3):
        off = (1 if (i + frame) % 2 else 0) if pose == 'walk' else 0
        line(a, cx - 2 + i * 2, cy, cx - 3 + i * 3, g - off, DARK)
    dome(a, cx, cy, 3.6 * k, 2.2 * k, rp, 3)
    put(a, int(cx + 3.6 * k), int(cy), rp[0]); put(a, int(cx + 4.6 * k), int(cy - 1), DARK)
    if spec.get('glow'): blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, 5 * k, 3 * k), spec['glow'], .35)


SPECIAL = {
    'snake': (snake, dict(rp=R5('#3a5a2a', '#4a7034', '#5e8a40', '#78a452', '#98c06a'), band=hx('#c8a040'))),
    'cobra': (snake, dict(rp=R5('#4a3a22', '#64502e', '#7e683c', '#9a844e', '#b8a066'))),
    'crab': (crab, dict(rp=R5('#8a2a1e', '#a83a28', '#c45034', '#d86a48', '#ec8a66'))),
    'frog': (frog, dict(rp=R5('#2a5a2a', '#3a7434', '#4e8e40', '#6aaa54', '#8ac46e'), spots=hx('#2a3a1a'))),
    'beetle': (insect, dict(rp=R5('#1e2a3a', '#2a3a50', '#3a4e68', '#4e6482', '#687e9c'))),
    'butterfly': (insect, dict(rp=R5('#2a2a2a', '#3a3a3a', '#4a4a4a', '#5a5a5a', '#6a6a6a'), wp=R5('#c86a1e', '#e0842a', '#f0a03e', '#f6bc5e', '#fcd88a'), fly=True)),
    'bee': (insect, dict(rp=R5('#3a2a0e', '#6a5014', '#c8a020', '#e8c040', '#f6dc70'), wp=R5('#b4c8d4', '#c8d8e2', '#dce8ee', '#ecf4f8', '#ffffff'), fly=True)),
}
BIOME_SPECIAL = {
    'dune_scorpion': ('DESERT DUNES', scorpion, dict(rp=R5('#8a6a3a', '#a8844a', '#c49e5e', '#d8b878', '#ecd29a'), size=1.2)),
    'sand_worm': ('DESERT DUNES', worm, dict(rp=R5('#8a6a4a', '#a8845e', '#c09e76', '#d6b890', '#e8d0ac'), size=1.1)),
    'giant_spider': ('JUNGLE', spider, dict(rp=R5('#1e1a1a', '#2e2626', '#3e3434', '#504444', '#645656'), mark=hx('#d5452d'), size=1.2)),
    'cave_spider': ('CRYSTAL CAVES', spider, dict(rp=R5('#2a2a3a', '#3a3a4e', '#4c4c64', '#60607c', '#767696'), eyes=GLOW['cyan'], size=1.0)),
    'giant_crab': ('BEACH', crab, dict(rp=R5('#6a1e1e', '#8a2a24', '#a83a2e', '#c4523e', '#dc7058'), size=1.8)),
    'salt_crab': ('SALT FLATS', crab, dict(rp=R5('#a8a49c', '#c0bcb4', '#d6d2ca', '#e8e4dc', '#f8f6f0'), size=1.1)),
    'mire_toad': ('SWAMP', frog, dict(rp=R5('#3a3a22', '#4e4e2c', '#64643a', '#7e7e4a', '#9a9a5e'), spots=GLOW['toxic'], size=1.8)),
    'glow_roach': ('IRRADIATED WASTE', insect, dict(rp=R5('#2a2a14', '#3e3e1c', '#545426', '#6c6c32', '#868640'), glow=GLOW['toxic'], size=1.3)),
    'fungal_crawler': ('FUNGAL GROVE', insect, dict(rp=R5('#3a2a4a', '#4e3a62', '#644c7c', '#7c6294', '#967cae'), glow=GLOW['violet'], size=1.6)),
    'ice_beetle': ('GLACIER', insect, dict(rp=R5('#5a7a9a', '#7094b4', '#8aaecc', '#a8c8e0', '#cae2f2'), glow=GLOW['ice'], size=1.4)),
}


# ------------------------------------------------------------------ sea life
SEA = {
    # name: (body ramp, length, height, fin colour, pattern, kind)
    'carp': (R5('#8a6a2a', '#a8843a', '#c49e4e', '#d8b866', '#ecd286'), 12, 5, None, None, 'fish'),
    'tuna': (R5('#1e3a5a', '#2a4e74', '#3a6690', '#5a86ac', '#80a8c8'), 16, 6, hx('#e8c84a'), None, 'fish'),
    'salmon': (R5('#8a5a5a', '#a87070', '#c48a88', '#dca8a4', '#f0c6c0'), 14, 5, None, 'spots', 'fish'),
    'clownfish': (R5('#c85a1e', '#e0742a', '#f08e3e', '#f6aa5e', '#fcc88a'), 8, 4, None, 'bands', 'fish'),
    'angelfish': (R5('#c8b020', '#dcc430', '#ecd84a', '#f6e670', '#fff4a0'), 8, 7, hx('#2a4a8a'), 'bands', 'fish'),
    'pufferfish': (R5('#8a8a5a', '#a4a470', '#bcbc8a', '#d2d2a6', '#e6e6c4'), 9, 7, None, 'spots', 'fish'),
    'catfish': (R5('#3a3a32', '#4e4e44', '#64645a', '#7c7c72', '#96968c'), 14, 4, None, None, 'fish'),
    'piranha': (R5('#5a6a7a', '#748494', '#8e9eae', '#aab8c4', '#c6d2da'), 9, 5, hx('#d5452d'), None, 'fish'),
    'eel': (R5('#2a3a2a', '#3a4e3a', '#4e664e', '#668066', '#809a80'), 22, 2.4, None, None, 'eel'),
    'swordfish': (R5('#2a3a6a', '#3a4e88', '#4e66a4', '#6a86c0', '#8eaad8'), 18, 5, None, None, 'fish'),
    'shark': (R5('#5a6670', '#707e8a', '#8a98a4', '#a6b2bc', '#c2ccd4'), 26, 7, None, None, 'shark'),
    'hammerhead': (R5('#5a6a70', '#70828a', '#8a9ca4', '#a6b6bc', '#c2d0d4'), 24, 6, None, None, 'shark'),
    'whale': (R5('#2a3a4a', '#3a4e62', '#4e667c', '#668098', '#829cb2'), 46, 13, None, None, 'whale'),
    'orca': (R5('#141418', '#1e1e24', '#2a2a32', '#383842', '#4a4a56'), 32, 9, None, 'orca', 'whale'),
    'dolphin': (R5('#5a6a7a', '#748494', '#8e9eae', '#aab8c4', '#c6d2da'), 22, 6, None, None, 'whale'),
    'manta': (R5('#2a2e3a', '#3a3e4e', '#4c5064', '#60667c', '#787e96'), 18, 12, None, None, 'ray'),
    'jellyfish': (R5('#a86aa8', '#c482c4', '#da9ada', '#ecb6ec', '#f8d2f8'), 8, 6, None, None, 'jelly'),
    'octopus': (R5('#8a2a3a', '#a83a4a', '#c4505e', '#d86a76', '#ec8a94'), 10, 8, None, None, 'octopus'),
    'squid': (R5('#c8a8a8', '#dcbcbc', '#ecd0d0', '#f6e2e2', '#fff2f2'), 14, 5, None, None, 'squid'),
    'seahorse': (R5('#c8901e', '#dca82a', '#ecc03e', '#f6d65e', '#ffea8a'), 6, 10, None, None, 'seahorse'),
    'sea_turtle': (R5('#3a5a3a', '#4a7044', '#5e8a52', '#78a464', '#98c07c'), 16, 6, None, None, 'turtle'),
    'lobster': (R5('#8a2a1e', '#a83a28', '#c45034', '#d86a48', '#ec8a66'), 14, 4, None, None, 'lobster'),
    'anglerfish': (R5('#2a2a30', '#3a3a42', '#4c4c56', '#60606c', '#767684'), 12, 7, None, 'lure', 'fish'),
    'coral_serpent': (R5('#a83a5a', '#c44e70', '#da6a8a', '#ec88a4', '#f6aac0'), 30, 3, None, 'bands', 'eel'),
    'kraken_spawn': (R5('#3a2a4a', '#4e3a62', '#644c7c', '#7c6294', '#967cae'), 14, 10, None, None, 'octopus'),
}


def sea(a, x, y, name, pose='swim', frame=0, young=False):
    rp, L, H, fin, pat, kind = SEA[name]
    k = .55 if young else 1.0
    L, H = L * k, H * k
    cx, cy = x + L / 2 + 6, y + 14 + [0, -1, 0, 1][frame % 4] * (0 if pose == 'sleep' else 1)
    fl = [0, 1, 0, -1][frame % 4]
    if pose == 'attack': cx += [0, 3][frame % 2]
    if kind in ('fish', 'shark', 'whale', 'eel'):
        tail = cx - L / 2
        for i in range(int(H * .9) + 2):
            put(a, int(tail - i * .7), int(cy - i * .7 + fl), rp[1]); put(a, int(tail - i * .7), int(cy + i * .7 + fl), rp[0])
        if kind == 'eel':
            for i in range(int(L)):
                yy = cy + math.sin(i / 4 + frame) * 2 * k
                for t in range(int(H) + 1): put(a, int(cx - L / 2 + i), int(yy + t), rp[3 if t == 0 else 2 if t == 1 else 1])
                if pat == 'bands' and (i // 3) % 2: put(a, int(cx - L / 2 + i), int(yy + 1), hx('#f6e6ee'))
            dome(a, cx + L / 2, cy, 2.2 * k + 1, 1.8 * k + .5, rp, 3); put(a, int(cx + L / 2 + 1), int(cy - 1), DARK)
            return
        dome(a, cx, cy, L / 2, H / 2, rp, 3)
        put(a, int(cx), int(cy - H / 2 - 1), fin or rp[1]); put(a, int(cx - 1), int(cy - H / 2 - 2), fin or rp[1])
        if kind == 'shark':
            for i in range(int(H * .8)): put(a, int(cx - i * .4), int(cy - H / 2 - i), rp[1 if i % 2 else 2])
            hline(a, int(cx + L / 4), int(cy + H / 4), int(L / 5), hx('#e8eef2'))
            if name == 'hammerhead': vline(a, int(cx + L / 2 - 1), int(cy - H / 2 - 1), int(H) + 2, rp[1])
        if kind == 'whale':
            hline(a, int(cx - L / 3), int(cy + H / 3), int(L * .6), lit(rp[4], .2))
            if pat == 'orca':
                rect(a, int(cx + L / 4), int(cy - H / 4), 3, 2, hx('#f6f6f6')); hline(a, int(cx - L / 4), int(cy + H / 3), int(L / 2), hx('#f6f6f6'))
            if name == 'whale' and pose == 'idle':
                for i in range(4): put(a, int(cx + L / 4), int(cy - H / 2 - 2 - i * 2), hx('#d6eef6'))
        if pat == 'spots':
            for (dx, dy) in [(-.2, -.2), (.1, .1), (-.1, .2), (.2, -.1)]: put(a, int(cx + dx * L), int(cy + dy * H), lit(rp[1], -.2))
        if pat == 'bands':
            for dx in (-.25, .1): vline(a, int(cx + dx * L), int(cy - H / 2 + 1), int(H) - 1, hx('#f6f2ea'))
        if pat == 'lure':
            put(a, int(cx + L / 2), int(cy - H / 2 - 2), rp[1]); put(a, int(cx + L / 2 + 2), int(cy - H / 2 - 3), GLOW['gold'])
            blend_mask(a, ellipse_mask(a.shape[:2], cx + L / 2 + 2, cy - H / 2 - 3, 3, 3), GLOW['gold'], .4)
        if name == 'swordfish':
            for i in range(int(8 * k)): put(a, int(cx + L / 2 + i), int(cy - 1), rp[3])
        ex = int(cx + L / 2 - 2 - (1 if L > 20 else 0)); put(a, ex, int(cy - H / 6), DARK if pose != 'sleep' else rp[1])
        if pose == 'attack' and frame % 2:
            for i in range(3): put(a, int(cx + L / 2 - 1 - i), int(cy + H / 6), DARK); put(a, int(cx + L / 2 - 1 - i), int(cy + H / 6 + 1), hx('#f2ece0') if i % 2 else DARK)
    elif kind == 'ray':
        wing = [-2, 0, 2, 0][frame % 4]
        for i in range(int(L)):
            u = abs(i - L / 2) / (L / 2)
            h = H / 2 * (1 - u * .7) + (wing * u if pose != 'sleep' else 0)
            for j in range(-int(h), int(h) + 1): put(a, int(cx - L / 2 + i), int(cy + j * .5), rp[3 if j < 0 else 2 if j < h / 2 else 1])
        for i in range(int(L * .6)): put(a, int(cx - L / 2 - i), int(cy), rp[1])
        put(a, int(cx + L / 2 - 2), int(cy - 1), DARK)
    elif kind == 'jelly':
        pulse = [0, 1, 2, 1][frame % 4]
        dome(a, cx, cy, L / 2 + pulse * .5, H / 2 - pulse * .3, rp, 3)
        for i in range(-2, 3):
            for t in range(int(6 * k) + pulse):
                put(a, int(cx + i * 1.5 + math.sin(t / 2 + frame) * .8), int(cy + H / 3 + t), rp[2] if t % 2 else rp[3])
        blend_mask(a, ellipse_mask(a.shape[:2], cx, cy, L / 2 + 2, H / 2 + 2), rp[4], .2)
    elif kind in ('octopus', 'squid'):
        dome(a, cx, cy - (2 if kind == 'octopus' else 0), H / 2 if kind == 'octopus' else L / 3, H / 2.2, rp, 3)
        for i in range(-3, 4):
            for t in range(int(H * .8)):
                put(a, int(cx + i * (1.4 if kind == 'octopus' else .8) + math.sin(t / 2 + frame + i) * 1.2), int(cy + H / 3 + t * (1 if kind == 'octopus' else .6)), rp[2] if t % 2 else rp[1])
        put(a, int(cx + 1), int(cy - 2), DARK); put(a, int(cx - 2), int(cy - 2), DARK)
        if pose == 'attack': blend_mask(a, ellipse_mask(a.shape[:2], cx - 6, cy + 4, 5, 4), hx('#1e1a24'), .7 * (frame % 2))
    elif kind == 'seahorse':
        for i in range(int(H)):
            put(a, int(cx + math.sin(i / 3) * 1.5), int(cy - H / 2 + i), rp[2]); put(a, int(cx + 1 + math.sin(i / 3) * 1.5), int(cy - H / 2 + i), rp[1])
        dome(a, cx + 1, cy - H / 2, 2, 1.6, rp, 3); hline(a, int(cx + 2), int(cy - H / 2), 2, rp[1]); put(a, int(cx + 1), int(cy - H / 2 - 1), DARK)
    elif kind == 'turtle':
        for s_ in (-1, 1):
            put(a, int(cx + L / 4), int(cy + s_ * (H / 2 + 1 + (fl if s_ > 0 else -fl))), rp[2]); put(a, int(cx - L / 4), int(cy + s_ * (H / 2 + 1)), rp[2])
        dome(a, cx, cy, L / 2.5, H / 2, R5('#4a3a22', '#64502e', '#7e683c', '#9a844e', '#b8a066'), 3)
        dome(a, cx + L / 2.5 + 1, cy, 2, 1.6, rp, 4); put(a, int(cx + L / 2.5 + 2), int(cy - 1), DARK)
    elif kind == 'lobster':
        for i in range(int(L)): put(a, int(cx - L / 2 + i), int(cy), rp[2]); put(a, int(cx - L / 2 + i), int(cy + 1), rp[1])
        dome(a, cx + L / 4, cy, L / 4, H / 2, rp, 3)
        for s_ in (-1, 1): dome(a, cx + L / 2 + 2 + (2 if pose == 'attack' and frame % 2 else 0), cy + s_ * 2, 2, 1.4, rp, 4)
        for i in range(6): put(a, int(cx + L / 2 + i), int(cy - 3 - i // 2), rp[1])


# ------------------------------------------------------------------ registry for export
def install_all():
    install()


POSES = {'walk': 4, 'idle': 2, 'run': 4, 'eat': 2, 'attack': 3, 'sleep': 2}
SEA_POSES = {'swim': 4, 'idle': 2, 'attack': 2}
BIRD_POSES = {'fly': 4, 'walk': 2, 'idle': 2, 'attack': 2, 'sleep': 1}


# ------------------------------------------------------------------ magic beasts (quad rig + wings / horns / flames)
def ex_wings(rp, kind='bat'):
    def f(a, g):
        import beings
        up = {'walk': [1, .3, -.3, .3], 'run': [1, -.2, 1, -.2], 'attack': [.8, 1, .2], 'idle': [.3, .4], 'eat': [.1, .1], 'sleep': [-.6, -.6]}[g['pose']][g['frame'] % {'walk': 4, 'run': 4, 'attack': 3, 'idle': 2, 'eat': 2, 'sleep': 2}[g['pose']]]
        beings._wing(a, g['cx'] + g['rx'] * .2, g['cy'] - g['ry'] * .6, g['rx'] * 1.5, up, rp, kind)
    return f


def ex_unihorn(a, g):
    x, y = int(g['hcx'] + g['hrx'] * .5), int(g['hcy'] - g['hry'])
    for i in range(6): put(a, x + i // 2, y - i, hx('#ffe9a0') if i % 2 else hx('#f6f2ea'))


def ex_beak(a, g):
    x, y = int(g['hcx'] + g['hrx']), int(g['hcy'])
    for i in range(3): put(a, x + i, y - 1 + i // 2, hx('#e8b030')); put(a, x + i, y + i // 2, hx('#c88a20'))
    dome(a, g['hcx'], g['hcy'] - 1, g['hrx'] * 1.05, g['hry'], R5('#c8c4bc', '#dcd8d0', '#ece8e0', '#f6f4ee', '#ffffff'), 3)
    put(a, int(g['hcx'] + g['hrx'] * .4), int(g['hcy'] - g['hry'] * .4), DARK)


def ex_flamemane(a, g):
    for i in range(6):
        fl = (g['frame'] + i) % 3
        x, y = int(g['hcx'] - 2 - i * 1.2), int(g['hcy'] - g['hry'] + i * .6)
        put(a, x, y - 1 - fl, hx('#ffd34a')); put(a, x, y - fl, hx('#f49a3c')); put(a, x, y + 1, hx('#d5452d'))


def ex_backcrest(col):
    def f(a, g):
        for i in range(-3, 4):
            x = int(g['cx'] + i * g['rx'] * .25); y = int(g['cy'] - g['ry'])
            vline(a, x, y - 2 + abs(i) // 2, 2, col)
    return f


MAGIC_SP = {
    'dragon': ('lizard', dict(rx=12, ry=5.5, head=(3.2, 2.4), neck=(4, 6), snout=3, legs=(6, 3), rp=R5('#3a0e14', '#5a1820', '#7a2a2c', '#9a4038', '#ba5a48'),
                             horns='curl', extras=(ex_wings(R5('#2a0a10', '#4a1418', '#6a2424', '#8a3a30', '#a8543e')), ex_backcrest(hx('#e2d8c2')), ex_glow_eye(GLOW['gold'])))),
    'wyvern': ('lizard', dict(rx=9, ry=4, head=(2.6, 2), neck=(3, 4), snout=2.6, legs=(5, 2), rp=R5('#1e3a2a', '#2a5038', '#3a6a4a', '#52845e', '#6ea078'),
                             extras=(ex_wings(R5('#14281e', '#1e3a2a', '#2a5038', '#3a6a4a', '#52845e')), ex_backcrest(hx('#c8a040'))))),
    'griffin': ('lion', dict(extras=(ex_wings(R5('#3a2618', '#5a3a22', '#7a5030', '#946640', '#ae7e52'), 'feather'), ex_beak))),
    'unicorn': ('horse', dict(rp=R5('#c8c4cc', '#dcd8e0', '#ece8f0', '#f6f4fa', '#ffffff'), mane=hx('#c8a8e8'), lcol=hx('#dcd8e0'), hoof=hx('#c8a040'), extras=(ex_unihorn,))),
    'pegasus': ('horse', dict(rp=R5('#c8c4cc', '#dcd8e0', '#ece8f0', '#f6f4fa', '#ffffff'), mane=hx('#e8e0c8'), lcol=hx('#dcd8e0'), hoof=hx('#8a8a94'), extras=(ex_wings(R5('#b4b8c4', '#c8ccd6', '#dce0e8', '#eef0f4', '#ffffff'), 'feather'),))),
    'hellhound': ('wolf', dict(rp=R5('#140c0c', '#24140e', '#341c14', '#46261a', '#5a3222'), extras=(ex_flames, ex_glow_eye(GLOW['fire'])))),
    'nightmare': ('horse', dict(rp=R5('#0e0a10', '#18121a', '#241c28', '#322636', '#423446'), mane=hx('#d5452d'), lcol=hx('#241c28'), extras=(ex_flamemane, ex_glow_eye(GLOW['fire'])))),
    'basilisk': ('lizard', dict(rx=10, ry=3.2, head=(2.8, 2), rp=R5('#2a3a1a', '#3a5022', '#4e682c', '#668238', '#829e4a'), extras=(ex_backcrest(hx('#c83a3a')), ex_glow_eye(GLOW['toxic'])))),
    'chimera': ('lion', dict(rp=R5('#7a4a2a', '#965e36', '#b07444', '#c48c58', '#d8a670'), extras=(ex_lionmane, ex_wings(R5('#3a1a14', '#5a2418', '#7a3020', '#9a4028', '#b85232')), ex_horn_nose))),
}
MAGIC_BIRDS = {
    'phoenix': dict(rp=R5('#a82a10', '#d0461a', '#f07a2a', '#ffb04a', '#ffe27a'), wp=R5('#c43a14', '#e8601e', '#ff9a3a', '#ffc860', '#fff0a0'), beak=hx('#ffe27a'), size=1.6, glow=GLOW['fire']),
    'thunderbird': dict(rp=R5('#1e2a4a', '#2a3c66', '#3a5284', '#5a72a4', '#84a0c8'), wp=R5('#14203a', '#1e2e52', '#2a426e', '#46608e', '#6a86b0'), beak=hx('#ffd34a'), size=1.9, glow=GLOW['cyan']),
    'roc': dict(rp=R5('#4a3a2a', '#64503a', '#7e684c', '#988060', '#b29a78'), wp=R5('#3a2a1e', '#4e3a2a', '#644c36', '#7a6044', '#927654'), beak=hx('#e8b030'), size=2.6),
}


def install_magic():
    for name, (base, over) in MAGIC_SP.items():
        s = dict(SP[base]); s.update(over); s.pop('young', None)
        if 'extras' in over and 'extras' in SP[base] and base not in ('lion',): s['extras'] = tuple(SP[base].get('extras', ())) + tuple(over['extras'])
        SP[name] = s
    BIRDS.update(MAGIC_BIRDS)
