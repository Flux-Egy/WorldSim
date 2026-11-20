# Patch v3.3: the 4 simulation biomes missing from the pack

New atlas `Terrain/biomes_extra`: 170 sprites, 1 page, no recolour masks.

| Biome | Tiles (64 px, tileable, 4 variants) | Props |
|---|---|---|
| LAVA | `t_lava_<v>_<f>`, animated 4 frames (anim `t_lava_<v>`), tag `emissive` | `lava_rock_<v>` |
| BIRCH FOREST | `t_birch_forest_<v>` + `t_birch_forest_<spring/autumn/winter>_<v>` | `birch_<3-5>_<v>_<season>_sway_<0-3>` |
| GLIMMERWOOD | `t_glimmerwood_<v>` | `glimmer_<3-5>_<v>_<0-3>`: glowing, animated, `emissive` |
| EMBER WASTES | `t_ember_wastes_<v>` | `ember_vent_<0-3>` (smoking, anim), `charred_stump_<v>`, `ember_rock_<v>` |

The generator is `Tools/ArtGen/biomes_extra.py`; `export_all.py biomes_extra` runs it.

After copying:
1. Rebuild the art index.
2. Run the mask tool (this atlas has no mask, so it should be a no-op).
