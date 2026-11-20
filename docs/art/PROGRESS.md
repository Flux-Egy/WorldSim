# Asset library – progress checkpoint (2026-11-20)

| Phase | Content | Status |
|---|---|---|
| 1 | 64 land species (+young), 18 birds, 17 critters/biome specials, 25 sea, 31 supernatural beings, 11 titans, 40 spells | done |
| 2 | 35 actions + 12 death types for human/elf/orc/dwarf (adult + child), 13 soldier types x 4 species | done |
| 3 | walls/keeps per era, bridges, docks, farms (8 crops x 8 stages), roads/rails autotile, 12 wonders, 33 creed sanctums, ships & vehicles x 8 dirs, seasonal/swaying/choppable trees, seasonal terrain, blend + shore masks | done |
| 4 | 32 kingdom colours (data + baked flags/banners/markers/buttons), ~120 icons x2 sizes, ~230 portraits, weather & disaster FX | done |
| 5 | 201 SFX + 24 ambient + 12 music loops, interactions.json (blast zones, building states, 222 rules), creatures.json (174), animation_events.json, anim events in C#, WorldSimAudioDB, docs | done |
| 5c | v3.1 review fixes: no gore, child fade deaths, shader building states (−8.3k sprites, −~140 MiB), seer, emblems, kingdom colours, audio levels, Burn/Frost/Overgrown in shader | done |
| 5b | Disaster states for every building (hit, burning, burnt, flooded, collapse, frozen, overgrown), knocked/blinded/vaporized for people & soldiers, decals & particles | done |

Sprites: 28,047 · animations: 6,121 · audio clips: 237 (see Assets/WorldSim/Resources/WorldSimArt/export_stats.json).
Regenerate everything: `cd Tools/ArtGen && WORLDSIM_ART_OUT=<path>/Resources/WorldSimArt python export_all.py`
Not verified yet: import inside real Unity (needs CI / the phone build).
