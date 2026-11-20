"""Phase 1 preview: pulls sprites straight from the exported atlases (what Unity will load)."""
import json, os, sys
import numpy as np
from PIL import Image
from lib import *
ART = os.environ.get('WORLDSIM_ART_OUT')
_cache = {}


def atlas(rel):
    if rel not in _cache:
        meta = json.load(open(os.path.join(ART, rel + '.json')))
        pages = [np.array(Image.open(os.path.join(ART, os.path.dirname(rel), p['image'])).convert('RGBA')) for p in meta['pageList']]
        _cache[rel] = ({f['name']: f for f in meta['frameList']}, pages)
    return _cache[rel]


def spr(rel, key):
    fr, pages = atlas(rel)
    f = fr[key]; p = pages[f['page']]
    return p[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']], f


def paste(bg, img, x, y):
    h, w = img.shape[:2]
    H, W = bg.shape[:2]
    if x >= W or y >= H: return
    img = img[:max(0, H - y), :max(0, W - x)]
    h, w = img.shape[:2]
    al = img[..., 3:4] / 255.
    bg[y:y + h, x:x + w] = (bg[y:y + h, x:x + w] * (1 - al) + img[..., :3] * al).astype(np.uint8)


def row(bg, rel, keys, x, y, gap=4, ground=True):
    for k in keys:
        try: im, f = spr(rel, k)
        except KeyError: print('missing', k); continue
        piv_y = int(f['h'] * (1 - f['pivotY']))
        paste(bg, im, x, y - piv_y)
        x += im.shape[1] + gap
    return x


W, H = 1280, 1500
bg = grass_ground(W, H, 4)
y = 10
text(bg, 10, y, 'WORLDSIM  PHASE 1  -  CREATURES, MAGIC, TITANS, SPELLS  (from the exported atlases)', hx('#ffffff'), 2, shadow=hx('#1a1a1a')); y += 30
F = 'Characters/Fauna/fauna_land'
for sp in ['wolf', 'lion', 'elephant', 'tiger', 'rhino', 'giraffe']:
    text(bg, 10, y + 18, sp.upper(), hx('#ffffff'), 1, shadow=hx('#1a1a1a'))
    ks = [f'a_{sp}_adult_walk_{i}' for i in range(4)] + [f'a_{sp}_adult_run_1', f'a_{sp}_adult_eat_0', f'a_{sp}_adult_attack_1', f'a_{sp}_adult_attack_2', f'a_{sp}_adult_sleep_0',
                                                      f'a_{sp}_adult_hurt', f'a_{sp}_adult_dead', f'a_{sp}_adult_remains', f'a_{sp}_adult_burnt', f'a_{sp}_adult_frozen', f'a_{sp}_young_walk_0']
    row(bg, F, ks, 90, y + 40, 6); y += 48
text(bg, 10, y + 4, 'POSES: WALK x4  RUN  EAT  ATTACK  SLEEP  HURT  DEAD  EATEN REMAINS  BURNT  FROZEN  YOUNG', hx('#ffe27a'), 1, shadow=hx('#1a1a1a')); y += 18
import animals as AN, bestiary as BS
BS.install(); BS.install_magic()
allq = [n for n in AN.SP if not n.startswith('_')]
x = 10; yy = y + 34
for n in allq:
    im, f = spr(F, f'a_{n}_adult_idle_0')
    if x + im.shape[1] > W - 10: x = 10; yy += 40
    paste(bg, im, x, yy - int(f['h'] * (1 - f['pivotY']))); x += im.shape[1] + 5
y = yy + 14
C = 'Characters/Fauna/fauna_critters'
text(bg, 10, y, 'BIRDS, CRITTERS, BIOME CREATURES', hx('#ffe27a'), 1, shadow=hx('#1a1a1a')); y += 10
names = list(BS.BIRDS) + list(BS.GROUND_BIRDS) + list(BS.SPECIAL) + list(BS.BIOME_SPECIAL)
x = 10; yy = y + 40
for n in names:
    k = f'c_{n}_adult_fly_1' if n in BS.BIRDS else f'c_{n}_adult_walk_1'
    try: im, f = spr(C, k)
    except KeyError: im, f = spr(C, f'c_{n}_adult_walk_0')
    if x + im.shape[1] > W - 10: x = 10; yy += 46
    paste(bg, im, x, yy - int(f['h'] * (1 - f['pivotY']))); x += im.shape[1] + 6
y = yy + 16
# sea strip on water
sea = np.zeros((70, W, 3), np.uint8); sea[:] = hx('#2a5a8a')
bg[y:y + 70] = sea
S = 'Characters/Fauna/fauna_sea'
x = 10
for n in BS.SEA:
    im, f = spr(S, f's_{n}_adult_swim_1')
    if x + im.shape[1] > W - 10: break
    paste(bg, im, x, y + 35 - int(f['h'] * (1 - f['pivotY']))); x += im.shape[1] + 6
text(bg, 10, y + 2, 'SEA LIFE', hx('#ffffff'), 1, shadow=hx('#1a1a1a'))
y += 76
M = 'Characters/Magic/beings'
import beings as BE
text(bg, 10, y, 'SUPERNATURAL BEINGS  (IDLE / ATTACK / CAST / DEATH)', hx('#ffe27a'), 1, shadow=hx('#1a1a1a'))
x = 10; yy = y + 70
for n in BE.B:
    ks = [f'm_{n}_idle_0', f'm_{n}_cast_2']
    for k in ks:
        im, f = spr(M, k)
        if x + im.shape[1] > W - 10: x = 10; yy += 66
        paste(bg, im, x, yy - int(f['h'] * (1 - f['pivotY']))); x += im.shape[1] + 2
    x += 6
yy += 66
x = row(bg, M, [f'm_jinn_possess_{i}' for i in range(4)], 10, yy, 4)
row(bg, M, [f'm_demon_death_{i}' for i in range(4)] + [f'm_jinn_death_{i}' for i in range(4)], x + 10, yy, 4)
y = yy + 10
T = 'Characters/Titans/titans'
text(bg, 10, y, 'TITANS  -  GRAB A HUMAN / STOMP / BREATH / SINK', hx('#ffe27a'), 1, shadow=hx('#1a1a1a'))
yy = y + 180
x = row(bg, T, ['t_colossus_grab_3', 't_abyss_lord_grab_2', 't_elder_wyrm_breath_2', 't_behemoth_stomp_2', 't_hill_giant_attack_2'], 10, yy, 8)
sea2 = bg[yy - 150:yy + 12, x:W].copy(); bg[yy - 60:yy + 12, x:W] = hx('#2a5a8a')
row(bg, T, ['t_kraken_grab_2', 't_sea_serpent_grab_2'], x + 4, yy + 4, 6)
y = yy + 20
SP = 'FX/Spells/spells'
text(bg, 10, y, 'SPELLS (40)', hx('#ffe27a'), 1, shadow=hx('#1a1a1a')); y += 12
import spells as SPL
x = 10
for n in SPL.SPELLS:
    im, f = spr(SP, f'icon_spell_{n}_32')
    paste(bg, im, x, y); x += 34
y += 40
x = 10
for k in ['sp_fireball_proj_0_1', 'sp_fireball_impact_1', 'sp_fireball_impact_3', 'sp_frost_nova_nova_4', 'sp_thunder_storm_storm_2', 'sp_plague_cloud_zone_2',
          'sp_raise_dead_circle_4', 'sp_demon_gate_circle_7', 'sp_fire_wall_wall_4', 'sp_heal_aura_front_2', 'sp_tidal_wave_nova_5', 'sp_blizzard_storm_3']:
    im, f = spr(SP, k)
    paste(bg, im, x, y + 70 - im.shape[0]); x += im.shape[1] + 6
bg = bg[:y + 80]
Image.fromarray(bg).resize((bg.shape[1] * 2, bg.shape[0] * 2), Image.NEAREST).save('out/11_phase1_creatures.png')
print(bg.shape)
