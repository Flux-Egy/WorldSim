import os, numpy as np
from PIL import Image
from lib import *
from phase1sheet import spr, paste, row
import structures as SR
from culturegen import SYMBOLS
B = 'Buildings/world_structures'; F = 'Terrain/farms_roads'; SV = 'Units/ships_vehicles'; N = 'Nature/nature_seasonal'; TS = 'Terrain/terrain_seasonal'
W, H = 1280, 1500
bg = grass_ground(W, H, 12)
y = 10
text(bg, 10, y, 'WORLDSIM  PHASE 3  -  WALLS, CASTLES, WONDERS, FARMS, ROADS, SHIPS, VEHICLES, SEASONS', hx('#ffffff'), 2, shadow=hx('#1a1a1a')); y += 30
yy = y + 80; x = 10
for e in range(6):
    x = row(bg, B, [f'wall_{e}_h', f'wall_{e}_corner', f'wall_{e}_gate_closed', f'wall_{e}_gate_open', f'wall_{e}_tower'], x, yy, 0) + 6
yy += 110; x = 10
for e in range(6): x = row(bg, B, [f'keep_{e}_big'], x, yy, 6) + 4
x = row(bg, B, ['keep_2_big__damaged', 'keep_2_big__ruined', 'keep_2_big__construction'], x + 10, yy, 6)
yy += 210; x = 10
for wn in SR.WONDERS: x = row(bg, B, [f'wonder_{wn}'], x, yy, 4)
yy += 90; x = 10
for i, sym in enumerate(SYMBOLS):
    x = row(bg, B, [f'sanctum_{sym}_{i % 3}'], x, yy, 4)
yy += 10
text(bg, 10, yy, 'FICTIONAL CREED SANCTUMS (EMBLEM = CULTURE CREST SYMBOL)   STATUES   WELLS   MARKETS   LAMPS', hx('#ffe27a'), 1, shadow=hx('#1a1a1a'))
yy += 60; x = 10
x = row(bg, B, [f'statue_{s}_{m}' for s, m in (('figure', 'bronze'), ('beast', 'stone'), ('obelisk', 'marble'), ('orb', 'gold'), ('rider', 'bronze'), ('abstract', 'stone'))], x, yy, 4)
x = row(bg, B, [f'well_{e}' for e in range(0, 6, 2)] + [f'market_{e}_0' for e in (1, 2, 4)] + [f'lamp_{e}_on' for e in range(6)] + ['fountain_1', 'pen_1', 'dock_2', 'dock_4', 'barn_2'], x + 10, yy, 4)
yy += 50; x = 10
x = row(bg, B, [f'bridge_{k}_h' for k in SR.BRIDGE] + [f'bridge_{k}_v' for k in SR.BRIDGE], x, yy, 4)
yy += 20
for i, crop in enumerate(SR.CROPS):
    for j, st in enumerate(SR.STAGES):
        im, f = spr(F, f'farm_{crop}_{st}')
        paste(bg, im[:, :64], 10 + j * 66 + (i % 2) * 560, yy + (i // 2) * 34)
yy += 4 * 34 + 6
x = 10
for kind in SR.ROADS:
    for m in (5, 10, 15, 3, 6, 7):
        im, f = spr(F, f'road_{kind}_{m}'); paste(bg, im, x, yy); x += 34
for m in (5, 10, 15, 3): im, f = spr(F, f'rail_{m}'); paste(bg, im, x, yy); x += 34
yy += 40
sea = np.zeros((90, W, 3), np.uint8); sea[:] = hx('#2a5a8a'); bg[yy:yy + 90] = sea
x = 10
for name in ('raft', 'trireme', 'galleon', 'ironclad', 'destroyer', 'stealth_frigate'):
    for d in (0, 90, 225):
        try: im, f = spr(SV, f'ship_{name}_{d}_0')
        except KeyError: continue
        paste(bg, im, x, yy + 45 - im.shape[0] // 2); x += im.shape[1] + 4
x = row(bg, SV, ['ship_galleon_sink_1', 'ship_galleon_sink_2'], x + 6, yy + 70, 4)
yy += 100; x = 10
for kind in SR.VEHICLES:
    for d in (0, 135, 270):
        im, f = spr(SV, f'veh_{kind}_{d}_0'); paste(bg, im, x, yy); x += im.shape[1] + 2
    x += 6
yy += 50; x = 10
for s in ('spring', 'summer', 'autumn', 'winter'):
    x = row(bg, N, [f'tree_5_0_{s}_sway_0', f'tree_4_1_{s}_sway_1', f'pine_4_0_{s}_sway_0', f'bush_0_1_{s}_sway_0'], x, yy + 50, 2) + 12
x = row(bg, N, [f'tree_5_0_fall_{i}' for i in range(5)] + ['tree_5_0_stump', 'tree_5_0_burning_1', 'tree_5_0_burnt', 'logs_2'] + [f'ore_gold_{i}' for i in range(4)], x, yy + 50, 3)
yy += 60; x = 10
for s in ('summer', 'spring', 'autumn', 'winter'):
    k = 't_meadow_0' if s == 'summer' else f't_meadow_{s}_0'
    try: im, f = spr(TS if s != 'summer' else 'Terrain/terrain_tiles', k)
    except Exception: continue
    paste(bg, im, x, yy); x += 66
for m in (1, 3, 7, 15): im, f = spr(TS, f'shore_{m}'); bg2 = bg[yy:yy + 64, x:x + 64]; bg2[:] = hx('#3277b0'); paste(bg, im, x, yy); x += 66
yy += 70
bg = bg[:yy]
Image.fromarray(bg).resize((bg.shape[1] * 2, bg.shape[0] * 2), Image.NEAREST).save('out/13_phase3_world.png'); print(bg.shape)
