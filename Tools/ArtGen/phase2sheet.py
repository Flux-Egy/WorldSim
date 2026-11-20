import os, numpy as np
from PIL import Image
from lib import *
import phase1sheet as PS   # helpers (re-renders phase 1 sheet on import; cheap)
from phase1sheet import spr, paste, row
import humans as HU, export_humans as EH
P_ = 'Characters/People/people_actions'; S_ = 'Units/Soldiers/soldiers_actions'
W, H = 1280, 1260
bg = grass_ground(W, H, 9)
y = 10
text(bg, 10, y, 'WORLDSIM  PHASE 2  -  PEOPLE ACTIONS, WORK, COMBAT, 12 DEATH TYPES  (from the atlases)', hx('#ffffff'), 2, shadow=hx('#1a1a1a')); y += 34
for base, label in [('h_human_m_medieval', 'HUMAN'), ('h_elf_f_medieval', 'ELF'), ('h_orc_m_tribal', 'ORC'), ('h_dwarf_m_medieval', 'DWARF'), ('h_human_f_modern', 'HUMAN MODERN')]:
    text(bg, 10, y + 14, label, hx('#ffffff'), 1, shadow=hx('#1a1a1a'))
    ks = [f'{base}_{a}_{min(1, HU.ACTIONS[a] - 1)}' for a in HU.ACTIONS]
    row(bg, P_, ks, 80, y + 36, 3); y += 44
text(bg, 10, y, ' '.join(a.upper() for a in HU.ACTIONS), hx('#ffe27a'), 1, shadow=hx('#1a1a1a')); y += 14
x = 10; yy = y + 36
for sp in ('human', 'dwarf'):
    for g in 'mf':
        paste_keys = [f'h_{sp}_{g}_child_{a}_0' for a in ('idle', 'run', 'cheer', 'flee', 'cower', 'carry')]
        x = row(bg, P_, paste_keys, x, yy, 3) + 10
y = yy + 10
text(bg, 10, y, 'DEATHS (EVERY SPECIES, EVERY SOLDIER):', hx('#ffe27a'), 1, shadow=hx('#1a1a1a')); y += 8
for i, (kind, nf) in enumerate(HU.DEATHS.items()):
    col = i % 2; r = i // 2
    xx = 10 + col * 640; yy = y + 40 + r * 42
    text(bg, xx, yy - 26, kind.upper(), hx('#ffffff'), 1, shadow=hx('#1a1a1a'))
    row(bg, P_, [f'h_human_m_medieval_death_{kind}_{f}' for f in range(nf)], xx + 90, yy, 4)
y = y + 40 + 6 * 42
text(bg, 10, y, 'SOLDIERS x 13 TYPES x 4 SPECIES  (IDLE / ATTACK / HURT / DEATH)  - TEAM COLOUR IS RECOLOURED AT RUNTIME', hx('#ffe27a'), 1, shadow=hx('#1a1a1a'))
x = 10; yy = y + 40
for st, (lk, atk, era) in EH.SOLDIERS.items():
    for sp in ('human',):
        ks = [f'sol_{sp}_{st}_idle_0', f'sol_{sp}_{st}_{atk}_1', f'sol_{sp}_{st}_{atk}_2']
        if x > W - 120: x = 10; yy += 44
        x = row(bg, S_, ks, x, yy, 2) + 12
yy += 44
x = 10
for sp in HU.SPECIES:
    x = row(bg, S_, [f'sol_{sp}_knight_melee_2', f'sol_{sp}_archer_shoot_bow_1', f'sol_{sp}_rifle_shoot_gun_1', f'sol_{sp}_battlemage_cast_2'], x, yy, 3) + 14
bg = bg[:yy + 14]
Image.fromarray(bg).resize((bg.shape[1] * 2, bg.shape[0] * 2), Image.NEAREST).save('out/12_phase2_people.png'); print(bg.shape)
