# ArtGen: WorldSim art generators

Procedural pixel-art generators (Python 3.10+, `pip install -r requirements.txt`). Every sprite in `Assets/WorldSim/Resources/WorldSimArt` comes from here, so art stays consistent and can be regenerated or extended. Read `docs/art/ASSETS_GUIDE.md` and `docs/art/STYLE_GUIDE.md` first.

```bash
cd Tools/ArtGen
python export_all.py                        # all atlases -> ../../Assets/WorldSim/Resources/WorldSimArt (+ atlas_index.json)
python export_all.py people strategic       # only some: buildings houses people animals army air fx nature terrain ui strategic
python data_export.py                       # design rules -> ../../Assets/WorldSim/Resources/WorldSimData/*.json
WORLDSIM_ART_OUT=/tmp/art python export_all.py fx   # export somewhere else (WORLDSIM_DATA_OUT for data_export)
python strategicsheet.py                    # preview renderers (*sheet.py, airraid.py, anim.py, ui2.py, systems.py ...) write PNG/GIF next to the script
```
Some preview modules render as a side effect of being imported, so do not import them from export code. Output is deterministic (fixed seeds).

| Module | Draws |
|---|---|
| `lib.py` | palette ramps (`W`, `R`, `C`), shading (`dome`, `lit`), primitives, trees, rocks, 3×5 font, icons, panels |
| `buildings.py` | 60 era buildings + roofs/walls/props, `BUILD[era][category]` |
| `houses.py`, `culturegen.py` | culture genome (founders -> values -> creed, rule, look, names, clans) and genome-driven houses `gen_house` |
| `people.py` | paper-doll people `person2` (culture/genome, class, age, gender, era, states) |
| `animals.py` | 19 species, adult + young, walk frames |
| `weapons.py`, `army2.py` | soldiers, mounted units, war machines, attack FX |
| `air.py` | top-down aircraft, air defence, missiles, explosions, airbase |
| `strategic.py` | ballistic launcher, silo, missile defence, 5 missile types, re-entry, nuclear detonation, shockwave, crater, fallout, hazard marker |
| `terrain.py` | 24 biomes, props, 10-level elevation renderer |
| `ui2kit.py`, `ui2.py`, `systems.py` | UI kit (5×7 font, frames, buttons, icons) and the observer screens |
| `anim.py`, `nightcycle.py`, `airraid.py`, `featureboard.py`, `strategicsheet.py`, `*sheet.py`, `scenes.py`, `culturecity.py`, `ui.py`, `chars.py`, `catalog.py` | preview / sheet renderers (and older v1 helpers they reuse) |
| `xcore.py` | exporter core: alpha recovery (black/white passes), recolour masks, atlas packing, JSON |
| `export_all.py`, `data_export.py` | the full export |

To add art: write a drawer `fn(canvas, ctx)` (read palette regions from `ctx.v[...]`), then `atlas.add(key, fn, W, H, pivot, regions=(...), tags=..., anchors=...)` in `export_all.py`, re-run it, and commit the PNG/JSON (+ Unity metas).
