#!/usr/bin/env python3
"""Re-encode the art pack's recolour masks from RGBA32 (4 bytes/px) to one byte per pixel, losslessly.

Source masks (as exported by Tools/ArtGen): R = region id x 36 (1 TEAM, 2 ACC, 3 ACC2, 4 ROOF, 5 SKIN, 6 HAIR),
G = shade, A = 255 where the pixel has a region. The shader uses only:
  - regions 1-4: the ramp step clamp(round((G - 40) / 44), 0, 4)
  - regions 5-6: G itself (continuous lighting of skin and hair)
Every mask pixel is therefore one (region, value) pair. The pack uses ~130 distinct pairs, so each pixel stores a
code 0..255 (0 = no region) in an 8-bit grey PNG, and mask_lut.png (256 x 1, RGBA) maps code -> (R = region x 36,
G = value, A = 255): exactly what the shader decoded before. Codes are assigned in sorted order, so the output is
deterministic. Masks that are already 8-bit grey are decoded through the existing LUT first, so re-running is safe.

Usage (repo root; needs Pillow + numpy):
  python3 Tools/ArtIndex/encode_masks.py           # encode (after every art export, BEFORE build_art_index.py)
  python3 Tools/ArtIndex/encode_masks.py --check   # CI: masks are 8-bit, the LUT matches, nothing to re-encode
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

ART = os.path.join("Assets", "WorldSim", "Resources", "WorldSimArt")
LUT_PATH = os.path.join(ART, "mask_lut.png")


def load_lut():
    if not os.path.exists(LUT_PATH):
        return None
    return np.asarray(Image.open(LUT_PATH).convert("RGBA"))[0]          # 256 x 4


def to_pairs(path, lut):
    """(region, value) per pixel, region 0 = none."""
    im = Image.open(path)
    if im.mode == "L":                                                  # already encoded: decode via the LUT
        if lut is None:
            raise SystemExit(f"{path} is encoded but {LUT_PATH} is missing")
        codes = np.asarray(im).astype(np.int32)
        reg = lut[codes, 0].astype(np.int32) // 36
        g = lut[codes, 1].astype(np.int32)
        val = np.where(reg <= 4, (g - 40) // 44, g)        # regions 1-4: back from nominal grey to ramp step
        none = lut[codes, 3] == 0
        reg[none] = 0
        val[none] = 0
        return reg, val
    a = np.asarray(im.convert("RGBA")).astype(np.int32)
    if ((a[..., 0] % 36) != 0).any():
        raise SystemExit(f"{path}: R is not a multiple of 36")
    masked = a[..., 3] > 127
    reg = np.where(masked, a[..., 0] // 36, 0)
    g = a[..., 1]
    step = np.clip(np.floor((g - 40) / 44.0 + 0.5), 0, 4).astype(np.int32)   # = the shader's round()
    val = np.where(reg <= 4, step, g)
    val[reg == 0] = 0
    if (reg > 6).any():
        raise SystemExit(f"{path}: region id above 6")
    return reg, val


def main():
    check = "--check" in sys.argv
    lut_old = load_lut()
    masks = sorted(glob.glob(os.path.join(ART, "**", "*_mask.png"), recursive=True))
    decoded = {p: to_pairs(p, lut_old) for p in masks}

    pairs = set()
    for reg, val in decoded.values():
        m = reg > 0
        pairs.update(zip(reg[m].tolist(), val[m].tolist()))
    pairs = sorted(pairs)
    if len(pairs) > 255:
        raise SystemExit(f"{len(pairs)} distinct (region, value) pairs: more than 255 codes")
    code_of = {pr: i + 1 for i, pr in enumerate(pairs)}

    lut = np.zeros((1, 256, 4), np.uint8)
    for (reg, val), c in code_of.items():
        # regions 1-4 store the ramp step as its nominal grey (40 + 44 x step) so the shader's decode is unchanged
        g = 40 + 44 * val if reg <= 4 else val
        lut[0, c] = (reg * 36, g, 0, 255)

    stale = []
    for p, (reg, val) in decoded.items():
        codes = np.zeros(reg.shape, np.uint8)
        m = reg > 0
        key = reg[m] * 1000 + val[m]
        lookup = {r * 1000 + v: c for (r, v), c in code_of.items()}
        codes[m] = np.vectorize(lookup.__getitem__, otypes=[np.uint8])(key) if m.any() else codes[m]
        # verify: decoding through the new LUT gives back exactly the same (region, value)
        back_reg = lut[0, codes, 0].astype(np.int32) // 36
        back_g = lut[0, codes, 1].astype(np.int32)
        back_val = np.where(back_reg <= 4, (back_g - 40) // 44, back_g)
        back_reg[codes == 0] = 0
        back_val[codes == 0] = 0
        if not (np.array_equal(back_reg, reg) and np.array_equal(back_val, val)):
            raise SystemExit(f"{p}: lossless round-trip failed")
        im = Image.open(p)
        if im.mode != "L" or not np.array_equal(np.asarray(im), codes):
            stale.append(p)
            if not check:
                Image.fromarray(codes, "L").save(p, optimize=True)

    lut_stale = lut_old is None or not np.array_equal(lut_old, lut[0])
    if check:
        if stale or lut_stale:
            raise SystemExit(f"masks not encoded or LUT out of date ({len(stale)} masks): run python3 Tools/ArtIndex/encode_masks.py")
        print(f"masks OK: {len(masks)} one-byte masks, {len(pairs)} codes used of 255")
        return
    if lut_stale:
        Image.fromarray(lut, "RGBA").save(LUT_PATH, optimize=True)
    print(f"encoded {len(stale)} of {len(masks)} masks; {len(pairs)} codes; LUT {'written' if lut_stale else 'unchanged'}")


if __name__ == "__main__":
    main()
