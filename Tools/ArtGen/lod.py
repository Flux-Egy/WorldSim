"""Far-zoom art: per-biome map colours, 16/8 px LOD tiles, settlement / army / monster / event markers (TEAM recolour)."""
import os, json, re
import numpy as np
from PIL import Image
from lib import *
from animals import R5
from xcore import Atlas

def load(art, rel):
    m = json.load(open(os.path.join(art, rel + '.json'))); d = os.path.dirname(rel)
    pages = [np.array(Image.open(os.path.join(art, d, p['image'])).convert('RGBA')) for p in m['pageList']]
    return {f['name']: pages[f['page']][f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']] for f in m['frameList']}


def down(img, s):
    """box-average to s x s, then snap to a 4-level palette of the tile itself (keeps it pixel-art)."""
    rgb = img[..., :3].astype(float); H = rgb.shape[0]; k = H // s
    small = rgb.reshape(s, k, s, k, 3).mean(axis=(1, 3))
    lum = small.mean(axis=2); qs = np.quantile(lum, [.25, .5, .75])
    out = np.zeros_like(small)
    for i, (lo, hi) in enumerate(zip([-1] + list(qs), list(qs) + [999])):
        m = (lum > lo) & (lum <= hi)
        if m.any(): out[m] = small[m].mean(axis=0)
    return np.dstack([out.astype(np.uint8), np.full((s, s), 255, np.uint8)])


def marker(a, kind, rp):
    ink = hx('#0b0e13'); gold = hx('#e8c040'); w = hx('#f3e6c8')
    def disc(r, col):
        for y in range(16):
            for x in range(16):
                if (x - 7.5) ** 2 + (y - 7.5) ** 2 <= r * r: put(a, x, y, col)
    if kind in ('village', 'town', 'city', 'capital'):
        disc(7.2, ink); disc(6.2, rp[2]); disc(4.8, rp[3])
        n = {'village': 1, 'town': 2, 'city': 3, 'capital': 3}[kind]
        for i in range(n):
            x = 7 - (n - 1) * 2 + i * 4
            rect(a, x - 1, 7, 3, 4, w); put(a, x, 6, w)
        if kind == 'capital':
            for i, h in enumerate((2, 3, 2)): vline(a, 5 + i * 3, 2 - h // 2 + 1, h, gold)
            hline(a, 5, 3, 7, gold)
    elif kind == 'army':
        disc(7.2, ink); disc(6.2, rp[2])
        for i in range(8): put(a, 4 + i, 4 + i, w); put(a, 11 - i, 4 + i, w)
    elif kind == 'unit_dot':
        rect(a, 6, 6, 4, 4, ink); rect(a, 7, 7, 2, 2, rp[3])
    elif kind == 'monster':
        disc(7.2, ink); disc(6.2, hx('#7a1e2a'))
        dome(a, 7.5, 8, 4, 3.5, R5('#3a1010', '#5a1a1a', '#7a2a2a', '#9a3a3a', '#ba5a50'), 1)
        put(a, 6, 7, hx('#ffd34a')); put(a, 9, 7, hx('#ffd34a')); put(a, 4, 4, w); put(a, 11, 4, w)
    elif kind == 'wonder':
        disc(7.2, ink); disc(6.2, hx('#3a2e5a'))
        for i in range(5): hline(a, 7 - i, 4 + i * 2, 2 * i + 2, gold)
    else:   # events
        col = {'fire': '#f4602a', 'flood': '#3a8ad8', 'quake': '#a88a5a', 'plague': '#7ac04a', 'war': '#d8342e', 'nuke': '#ffd34a', 'storm': '#8a9aa8'}[kind]
        for y in range(16):     # diamond sign
            for x in range(16):
                d = abs(x - 7.5) + abs(y - 7.5)
                if d <= 7.5: put(a, x, y, ink if d > 6.3 else hx(col))
        glyph = {'fire': ["..#..", ".###.", "##.##", "#...#", ".###."], 'flood': [".....", "#.#.#", ".#.#.", "#.#.#", "....."], 'quake': ["#....", ".#.#.", "..#.#", ".#...", "#...."],
                 'plague': [".###.", "#.#.#", "#####", ".#.#.", "....."], 'war': ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"], 'nuke': [".###.", "#.#.#", "##.##", "#.#.#", ".###."],
                 'storm': [".##..", "####.", "..#..", ".#...", "#...."]}[kind]
        for j, row in enumerate(glyph):
            for i, c in enumerate(row):
                if c == '#': put(a, 5 + i, 5 + j, ink)


def export(art, out_data, done):
    at = Atlas('lod', os.path.join(art, 'Terrain'))
    colors = {}
    for rel in ('Terrain/terrain_tiles', 'Terrain/biomes_extra'):
        fr = load(art, rel)
        for name, img in fr.items():
            m = re.fullmatch(r't_([a-z_]+?)_(\d)(?:_\d)?', name)
            if not m or img.shape[0] != 64 or img.shape[1] != 64: continue
            b, v = m.group(1), int(m.group(2))
            if name.count('_') > 2 and name.split('_')[-2] in ('spring', 'autumn', 'winter'): continue
            if rel.endswith('biomes_extra') and b == 'lava' and not name.endswith('_0'): continue
            if v == 0 and b not in colors: colors[b] = '#%02x%02x%02x' % tuple(int(c) for c in img[..., :3].reshape(-1, 3).mean(axis=0))
            for s in (16, 8):
                key = f't_{b}_{v}_lod{s}'
                if key not in [it[0] for it in at.items]: at.add_array(key, down(img, s), (0, 0), {'biome': b, 'variant': v, 'lod_px': s, 'use': f'zoomed out ({64 // s}x); same 16x16 cell grid'})
    for k in ('village', 'town', 'city', 'capital', 'army', 'unit_dot'):
        at.add(f'mk_{k}', lambda a, ctx, k=k: marker(a, k, ctx.v.get('TEAM') or R['K']), 16, 16, (8, 8), regions=('TEAM',), keep_canvas=True, tags={'marker': k, 'recolor': 'TEAM'})
    for k in ('monster', 'wonder', 'fire', 'flood', 'quake', 'plague', 'war', 'nuke', 'storm'):
        at.add(f'mk_{k}', lambda a, ctx, k=k: marker(a, k, R['K']), 16, 16, (8, 8), regions=(), keep_canvas=True, tags={'marker': k})
    done('lod', at)
    json.dump({'map_colors': colors, 'zoom_levels': {
        'near': 'full sprites + animation (zoom stations x2..x4)',
        'mid': 'full sprites, animation at half rate, hide decals/particles, people as sprites (zoom x1)',
        'far': 'terrain t_*_lodN (16 px at 1/4, 8 px at 1/8); hide people/animals/props; show mk_* markers at constant screen size; kingdom territory = TEAM colour overlay ~35% + border_<colour> strips',
        'map': 'flat map_colors per cell + territory overlay + mk_city/capital/army/monster/event markers'}},
        open(os.path.join(out_data, 'lod.json'), 'w'), indent=1)
