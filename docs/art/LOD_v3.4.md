# Patch v3.4: far-zoom art (LOD)

New atlas `Terrain/lod`: 239 sprites. New data file `WorldSimData/lod.json`.

| Asset | Use |
|---|---|
| `t_<biome>_<v>_lod16`, `t_<biome>_<v>_lod8` | Every biome tile (all 28 biomes) shrunk to 16 px and 8 px, using the tile's own 4 colours. Draw these instead of the 64 px tiles when zoomed out ×4 / ×8, so the ground stays clean instead of turning into noise. |
| `mk_village`, `mk_town`, `mk_city`, `mk_capital`, `mk_army`, `mk_unit_dot` | Markers in the kingdom's colour (TEAM recolour), 16 px. |
| `mk_monster`, `mk_wonder`, `mk_fire`, `mk_flood`, `mk_quake`, `mk_plague`, `mk_war`, `mk_nuke`, `mk_storm` | Markers for things that must stay visible far out. |
| `lod.json → map_colors` | One colour per biome plus 3 water depths, for the far map / minimap. |
| `lod.json → zoom_levels` | Suggested near / mid / far / map behaviour. |

At far zoom, markers should be drawn at a constant screen size. Kingdom territory = a TEAM colour overlay (~35%) plus `border_<colour>` strips.

v3.4.1 adds the missing `Terrain/lod_mask.png` and `atlas_index.json` (= the v3.1 list + `Terrain/biomes_extra` + `Terrain/lod`, nothing removed).

After copying, rebuild the art index and run the mask tool.
