#!/usr/bin/env python3
"""Copies the art-pack pages the runtime terrain baker reads on the CPU into Resources as .bytes (TextAssets).

The baker (Render/Terrain/TerrainComposer, run in a background thread in the game) needs the pixels of the terrain,
LOD and nature pages. GPU textures can't be read back (ASTC on Android), so the PNG files themselves ship as raw bytes
and are decoded with PngDecoder. Output: Assets/WorldSim/Resources/WorldSimArt/Raw/<page path with / -> __>.bytes

  python3 Tools/ArtIndex/export_raw.py          # write
  python3 Tools/ArtIndex/export_raw.py --check  # CI: fail if a copy is missing or stale
"""
import os, sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "Assets", "WorldSim", "Resources", "WorldSimArt")
PAGES = [
    "Terrain/terrain_tiles.png", "Terrain/biomes_extra.png", "Terrain/lod.png", "Terrain/lod_mask.png",
    "Nature/nature_props.png", "mask_lut.png",
]

def main():
    check = "--check" in sys.argv
    out_dir = os.path.join(ROOT, "Raw")
    os.makedirs(out_dir, exist_ok=True)
    stale = []
    for p in PAGES:
        src = os.path.join(ROOT, p)
        dst = os.path.join(out_dir, p[:-4].replace("/", "__") + ".bytes")
        data = open(src, "rb").read()
        if not os.path.exists(dst) or open(dst, "rb").read() != data:
            stale.append(p)
            if not check:
                open(dst, "wb").write(data)
    if check and stale:
        raise SystemExit(f"raw art copies missing or stale: {stale}: run python3 Tools/ArtIndex/export_raw.py")
    print(f"raw art copies {'OK' if check else 'written'}: {len(PAGES)} pages ({len(stale)} updated)")

if __name__ == "__main__":
    main()
