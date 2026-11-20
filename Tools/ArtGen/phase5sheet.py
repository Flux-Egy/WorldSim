import numpy as np, json
from PIL import Image
from lib import *
from phase1sheet import spr, paste
DH = 'Buildings/Disaster/disaster_houses'; P = 'Characters/People/people_actions'; S = 'Units/Soldiers/soldiers_actions'; T = 'Characters/Titans/titans'
DEC = 'FX/Decals/decals_particles'; FX = 'FX/fx'; ST = 'Units/strategic'
W, H = 1100, 420
bg = grass_ground(W, H, 21)
def burn_fx(im, k):   # same maths as the shader's _Burn
    im = im.copy(); l = im[..., :3].astype(float) @ np.array([.30, .59, .11])
    im[..., :3] = (im[..., :3] * (1 - k) + (l * .32 + 9)[..., None] * k).astype(np.uint8); return im
def put_s(rel, key, x, y, burn=0.0, fire=None):
    if '__burning' in key or '__burnt' in key or '__hit' in key:
        burn = .4 if '__burning' in key else 1.0 if '__burnt' in key else 0.0; fire = key.endswith(('_0', '_1', '_2')) and '__burning' in key
        key = key.split('__')[0]; rel = 'Buildings/houses_culture_kit'
    im, f = spr(rel, key); px = int(f['w'] * f['pivotX']); py = int(f['h'] * (1 - f['pivotY']))
    if burn: im = burn_fx(im, burn)
    paste(bg, im, x - px, y - py)
    if fire:
        roof = [a for a in f['anchors'] if a['name'] == 'roof'][0]
        tags = json.loads(f['tagsJson']); ov, fo = spr('Buildings/Disaster/building_overlays', f"ov_fire_{tags['w_class']}_1")
        paste(bg, ov, x - px + roof['x'] - ov.shape[1] // 2, y - py + roof['y'] - ov.shape[0] + 3)
        sm, _ = spr('Buildings/Disaster/building_overlays', 'ov_smoke_column_1'); paste(bg, sm, x - px + roof['x'] - 10, y - py + roof['y'] - 40)
text(bg, 8, 6, 'BOMB NEAR A TOWN:  ZONE 0 FIREBALL | 1 BLAST | 2 THERMAL | 3 SHOCKWAVE | 4 FLASH', hx('#ffffff'), 1, shadow=hx('#1a1a1a'))
cx, cy = 130, 230
put_s(DEC, 'decal_crater_xl_0', cx, cy); put_s(DEC, 'decal_scorch_xl_1', cx, cy + 4)
put_s(FX, 'boom_2_1', cx, cy - 6) if True else None
house = 'h_gable_logs_middle_0'
cols = [(240, ['__collapse_3', '__collapse_2'], ['death_vaporized_3', 'death_explosion_5', 'death_explosion_2']),
        (330, ['__collapse_1', '__burning_1'], ['death_explosion_4', 'death_burn_4', 'burning_1']),
        (420, ['__burning_0', '__burning_2'], ['burning_2', 'death_burn_5', 'hurt_0']),
        (510, ['', ''], ['knocked_0', 'knocked_1', 'knocked_3']),
        (600, ['', ''], ['blinded_0', 'blinded_1', 'cower_1'])]
for zi, (x, hs, ppl) in enumerate(cols):
    for j, st in enumerate(hs):
        put_s(DH if st else 'Buildings/houses_culture_kit', house + st, x + 10, 150 + j * 110)
    for j, a in enumerate(ppl):
        put_s(P, f'h_human_{"mf"[j % 2]}_medieval_{a}', x - 14 + j * 24, 320 + (j % 2) * 8)
    text(bg, x - 10, 365, f'ZONE {zi}', hx('#ffe27a'), 1, shadow=hx('#1a1a1a'))
for i in range(5):
    for t in np.linspace(0, 2 * np.pi, 220):
        rr = 60 + i * 90
        x, y = int(cx + rr * np.cos(t)), int(cy + rr * .45 * np.sin(t))
        if 0 <= x < 700 and 0 <= y < H and int(t * 30) % 3 == 0: bg[y, x] = (255, 230 - i * 30, 120)
# titan vs soldiers
text(bg, 720, 6, 'HUMANS VS A TITAN', hx('#ffffff'), 1, shadow=hx('#1a1a1a'))
put_s(T, 't_colossus_grab_3', 900, 300); put_s(T, 't_fx_stuck_arrows_2', 880, 210)
put_s(T, 't_fx_crack_2', 980, 310)
for i, (k, x, y) in enumerate([('sol_human_archer_shoot_bow_1', 740, 330), ('sol_dwarf_spearman_stab_2', 780, 350), ('sol_human_knight_melee_2', 820, 340),
                               ('sol_orc_club_flee_1', 1040, 345), ('sol_elf_archer_shoot_bow_2', 760, 380), ('sol_human_swordsman_death_crushed_3', 990, 330),
                               ('sol_human_knight_knocked_1', 1040, 380), ('sol_dwarf_hoplite_cower_1', 1070, 330)]):
    put_s(S, k, x, y)
Image.fromarray(bg).resize((W * 2, H * 2), Image.NEAREST).save('out/15_interactions_blast_titan.png')
