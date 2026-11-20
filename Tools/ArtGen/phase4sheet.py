import numpy as np, json, os
from PIL import Image
from lib import *
from phase1sheet import spr, paste, row, ART
import phase4 as P4
K = 'UI/Kingdoms/kingdom_colours'; I = 'UI/Icons/icons'; WX = 'FX/Weather/weather_fx'
W = 1000
bg = np.zeros((900, W, 3), np.uint8); bg[:] = hx('#151b25')
y = 8
text(bg, 8, y, 'WORLDSIM  PHASE 4  -  32 KINGDOM COLOURS, ICONS, PORTRAITS, WEATHER & DISASTERS', hx('#ffffff'), 2); y += 26
pal = P4.palettes()
for i, p in enumerate(pal):
    cx = 8 + (i % 16) * 61; cy = y + (i // 16) * 60
    paste(bg, spr(K, f'flag_{p["name"]}_swallow_1')[0], cx, cy)
    paste(bg, spr(K, f'banner_{p["name"]}')[0], cx + 16, cy)
    paste(bg, spr(K, f'capital_{p["name"]}')[0], cx + 28, cy)
    paste(bg, spr(K, f'badge_{p["name"]}')[0], cx + 2, cy + 18)
    paste(bg, spr(K, f'army_marker_{p["name"]}')[0], cx + 22, cy + 20)
    paste(bg, spr(K, f'war_tent_{p["name"]}')[0], cx + 40, cy + 20)
    text(bg, cx, cy + 44, p['name'].upper(), hx('#c8ccd2'), 1)
y += 128
meta = json.load(open(os.path.join(ART, I + '.json')))
names = [f['name'] for f in meta['frameList'] if f['name'].startswith('ic_') and f['name'].endswith('_32')]
x = 8
for n in names:
    if x > W - 40: x = 8; y += 36
    paste(bg, spr(I, n)[0], x, y); x += 34
y += 42
names = [f['name'] for f in meta['frameList'] if f['name'].startswith('portrait_') and f['name'].endswith('_32')]
x = 8
for n in names[::2][:140]:
    if x > W - 40: x = 8; y += 34
    paste(bg, spr(I, n)[0], x, y); x += 33
y += 40
sky = bg[y:y + 80]; sky[:] = hx('#3a5a7a')
x = 8
for k in ('wx_tornado_3', 'wx_volcano_4', 'wx_tsunami_3', 'wx_lightning_strike_1', 'wx_meteor_2', 'wx_wildfire_1', 'wx_quake_2', 'wx_aurora_1', 'wx_firework_e04a3a_3', 'wx_firework_6ac04a_4', 'wx_rain_tile_0', 'wx_snow_tile_0'):
    im = spr(WX, k)[0]; paste(bg, im, x, y + 78 - im.shape[0]); x += im.shape[1] + 4
y += 84
bg = bg[:y]
Image.fromarray(bg).resize((bg.shape[1] * 2, bg.shape[0] * 2), Image.NEAREST).save('out/14_phase4_colours_icons_weather.png'); print(bg.shape)
