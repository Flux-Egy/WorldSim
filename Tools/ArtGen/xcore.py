"""Asset export core: render -> RGBA (alpha recovered from black/white passes) + recolour mask, shelf-pack atlases, write JSON.

Recolour mask (PNG, same layout as the atlas page):
  R = region id * 36   (1 TEAM, 2 ACC, 3 ACC2, 4 ROOF, 5 SKIN, 6 HAIR) ; 0 = keep baked colour
  G = shade 0..255     (luminance the pixel had when that region was drawn with a neutral grey ramp)
  A = 255 where a region applies
The runtime shader replaces colour = Ramp[region].Evaluate(G/255) for masked pixels. Everything else stays as baked."""
import json, math, os, copy
import numpy as np
from PIL import Image
from lib import *
import people

REGIONS = ['TEAM', 'ACC', 'ACC2', 'ROOF', 'SKIN', 'HAIR']
GREY5 = [(40, 40, 40), (84, 84, 84), (128, 128, 128), (172, 172, 172), (216, 216, 216)]
ALT5 = [(120, 0, 90), (160, 0, 120), (200, 0, 150), (230, 40, 180), (250, 90, 210)]
DEFAULT = {'TEAM': list(R['K']), 'ACC': ramp('#1f4d4f', '#2b6a6a', '#3a8a86', '#5aaca4', '#8ccfc4'), 'ACC2': ramp('#6a2a5a', '#8a3a76', '#a85a94', '#c87ab4', '#e8a8d8'),
           'ROOF': list(R['K']), 'SKIN': hx('#c89a74'), 'HAIR': hx('#3a2618')}
GREY1, ALT1 = (128, 128, 128), (200, 0, 150)


class Ctx:
    """mutable palette the drawing closures read from."""
    def __init__(self): self.v = {k: (list(v) if isinstance(v, list) else v) for k, v in DEFAULT.items()}

    def apply(self):
        R['K'][:] = self.v['TEAM']
        people.OVERRIDE['skin'] = self.v['SKIN']; people.OVERRIDE['hair'] = self.v['HAIR']


_TEAM0 = list(R['K'])


def _restore():
    R['K'][:] = _TEAM0; people.OVERRIDE['skin'] = None; people.OVERRIDE['hair'] = None


def _render(fn, W, H, bg, ctx):
    a = np.zeros((H, W, 3), np.uint8); a[:] = bg
    ctx.apply()
    fn(a, ctx)
    return a.astype(np.int32)


def render(fn, W, H, regions=()):
    """fn(a, ctx) draws onto a W x H canvas. returns rgba (H,W,4) uint8 and mask (H,W,4) uint8."""
    try:
        ctx = Ctx()
        k = _render(fn, W, H, (0, 0, 0), ctx)
        w = _render(fn, W, H, (255, 255, 255), ctx)
        diff = (w - k).max(axis=2)
        alpha = np.clip(255 - diff, 0, 255)
        col = np.where(alpha[..., None] > 0, np.clip(k * 255 // np.maximum(alpha, 1)[..., None], 0, 255), 0)
        rgba = np.dstack([col, alpha]).astype(np.uint8)
        mask = np.zeros((H, W, 4), np.uint8)
        taken = np.zeros((H, W), bool)
        for rg in regions:
            rid = REGIONS.index(rg) + 1
            ctx_alt = Ctx(); ctx_alt.v[rg] = ALT5 if isinstance(DEFAULT[rg], list) else ALT1
            alt = _render(fn, W, H, (0, 0, 0), ctx_alt)
            ctx_g = Ctx(); ctx_g.v[rg] = GREY5 if isinstance(DEFAULT[rg], list) else GREY1
            gr = _render(fn, W, H, (0, 0, 0), ctx_g)
            mem = (np.abs(alt - k).sum(axis=2) > 6) & (alpha > 200) & ~taken
            mask[mem, 0] = rid * 36
            mask[mem, 1] = np.clip(gr[mem].mean(axis=1), 0, 255)
            mask[mem, 3] = 255
            taken |= mem
        return rgba, mask
    finally:
        _restore()


def crop(rgba, mask, pad=1):
    ys, xs = np.nonzero(rgba[..., 3] > 0)
    if not len(xs): return rgba[:1, :1], mask[:1, :1], (0, 0)
    y0, y1, x0, x1 = max(ys.min() - pad, 0), min(ys.max() + 1 + pad, rgba.shape[0]), max(xs.min() - pad, 0), min(xs.max() + 1 + pad, rgba.shape[1])
    return rgba[y0:y1, x0:x1], mask[y0:y1, x0:x1], (x0, y0)


class Atlas:
    """collects sprites, packs into pages, writes PNG + mask PNG + JSON."""
    def __init__(self, name, folder, page=2048, ppu=16):
        self.name, self.folder, self.page, self.ppu = name, folder, page, ppu
        self.items = []          # (key, rgba, mask, pivot(px from top-left), tags, anchors)
        self.anims = {}

    def add(self, key, fn, W, H, pivot, regions=(), tags=None, anchors=None, keep_canvas=False):
        rgba, mask = render(fn, W, H, regions)
        if keep_canvas: off = (0, 0); r2, m2 = rgba, mask
        else: r2, m2, off = crop(rgba, mask)
        pv = (pivot[0] - off[0], pivot[1] - off[1])
        an = {k: (v[0] - off[0], v[1] - off[1]) for k, v in (anchors or {}).items()}
        self.items.append((key, r2, m2, pv, tags or {}, an))
        return key

    def add_array(self, key, rgba, pivot, tags=None, mask=None):
        if mask is None: mask = np.zeros(rgba.shape[:2] + (4,), np.uint8)
        self.items.append((key, rgba, mask, pivot, tags or {}, {}))

    def anim(self, name, keys, fps=8, loop=True, events=None):
        """events: list of (frame_index, event_name) e.g. (2,'hit'), (1,'spawn_projectile'), (0,'sfx:roar')"""
        self.anims[name] = {'frames': keys, 'fps': fps, 'loop': loop, 'events': [{'frame': int(f), 'name': n} for f, n in (events or [])]}

    def save(self):
        os.makedirs(self.folder, exist_ok=True)
        for f_ in os.listdir(self.folder):
            if f_ == self.name + '.json' or (f_.startswith(self.name) and f_.endswith('.png') and f_[len(self.name):len(self.name) + 1] in ('.', '_')
                                             and (f_[len(self.name) + 1:].split('.')[0].replace('_mask', '').isdigit() or f_[len(self.name):] in ('.png', '_mask.png'))):
                os.remove(os.path.join(self.folder, f_))
        items = sorted(self.items, key=lambda t: -t[1].shape[0])
        pages, cur, x, y, rowh = [], [], 1, 1, 0
        P = self.page
        placed = []
        for it in items:
            h, w = it[1].shape[:2]
            if x + w + 1 > P: x, y, rowh = 1, y + rowh + 1, 0
            if y + h + 1 > P:
                pages.append(placed); placed = []; x, y, rowh = 1, 1, 0
            placed.append((it, x, y)); x += w + 1; rowh = max(rowh, h)
        if placed: pages.append(placed)
        meta_frames, files = {}, []
        for pi, pl in enumerate(pages):
            mh = max(yy + it[1].shape[0] for it, xx, yy in pl) + 1
            mw = max(xx + it[1].shape[1] for it, xx, yy in pl) + 1
            ph = 1 << math.ceil(math.log2(max(mh, 2))); pw = 1 << math.ceil(math.log2(max(mw, 2)))
            img = np.zeros((ph, pw, 4), np.uint8); msk = np.zeros((ph, pw, 4), np.uint8)
            has_mask = False
            for (key, rgba, mask, pv, tags, an), xx, yy in pl:
                h, w = rgba.shape[:2]
                img[yy:yy + h, xx:xx + w] = rgba; msk[yy:yy + h, xx:xx + w] = mask
                has_mask |= bool(mask[..., 3].any())
                meta_frames[key] = {'page': pi, 'x': xx, 'y': yy, 'w': w, 'h': h,
                                    'pivot_px': [int(pv[0]), int(pv[1])],
                                    'pivot_unity': [round(pv[0] / max(w, 1), 4), round(1 - pv[1] / max(h, 1), 4)],
                                    'anchors_px': {k: [int(v[0]), int(v[1])] for k, v in an.items()}, 'tags': tags,
                                    'recolor': bool(mask[..., 3].any())}
            fn = f'{self.name}_{pi}.png' if len(pages) > 1 else f'{self.name}.png'
            Image.fromarray(img, 'RGBA').save(os.path.join(self.folder, fn), optimize=True)
            mfn = None
            if has_mask:
                mfn = fn.replace('.png', '_mask.png'); Image.fromarray(msk, 'RGBA').save(os.path.join(self.folder, mfn), optimize=True)
            files.append({'image': fn, 'mask': mfn, 'w': pw, 'h': ph})
        frame_list = [{'name': k, 'page': v['page'], 'x': v['x'], 'y': v['y'], 'w': v['w'], 'h': v['h'], 'pivotX': v['pivot_unity'][0], 'pivotY': v['pivot_unity'][1],
                       'recolor': v['recolor'], 'anchors': [{'name': an, 'x': p[0], 'y': p[1]} for an, p in v['anchors_px'].items()], 'tagsJson': json.dumps(v['tags'])}
                      for k, v in meta_frames.items()]
        anim_list = [{'name': k, 'frames': v['frames'], 'fps': v['fps'], 'loop': v['loop'], 'events': v.get('events', [])} for k, v in self.anims.items()]
        page_list = [{'image': f['image'], 'mask': f['mask'] or '', 'w': f['w'], 'h': f['h']} for f in files]
        meta = {'atlas': self.name, 'ppu': self.ppu, 'filter': 'point',
                'pivot_note': 'x,y = top-left of the frame in the page (top-left origin); pivotX/Y normalised from the bottom-left (Unity); anchors in px from the frame top-left',
                'regions': {r: (i + 1) * 36 for i, r in enumerate(REGIONS)},
                'pageList': page_list, 'frameList': frame_list, 'animList': anim_list}
        with open(os.path.join(self.folder, self.name + '.json'), 'w') as fh: json.dump(meta, fh, separators=(',', ':'))
        return len(self.items), len(pages)


def up2(fn):
    """wrap a world-grid drawer so it is drawn at world scale then upscaled x2 into a fine canvas."""
    def g(a, ctx):
        H, W = a.shape[:2]
        w = np.zeros((H // 2, W // 2, 3), np.uint8); w[:] = a[0, 0]
        fx = fn(w, ctx)
        a[:] = upscale(w, 2)
        return fx
    return g
