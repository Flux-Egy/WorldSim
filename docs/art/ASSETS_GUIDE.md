# WorldSim Art Pack: guide for Claude Code

> **للمالك:** الملف ده لـ Claude Code. بيقوله كل ملف بيتحط فين، وبيستخدمه في إيه جوه اللعبة، وإزاي الألوان بتتغير حسب المملكة والثقافة، وإزاي يعيد توليد أي رسمة أو يضيف رسمات جديدة.

The pack contains every generated sprite WorldSim needs for the first full build:
- **28,047 sprites and animation frames** in **34 atlases** (plus recolour masks), with **6,121 named animations** (many carry frame events);
- **237 audio clips** (OGG): sound effects, ambient loops and music;
- the design data they were generated from;
- a runtime loader and the recolour shader;
- the Python generators;
- all approved previews.

It mirrors the repo layout. Unzip it at the repo root and the files land where they belong.

This file supersedes the art parts of `docs/ASSET_SPEC.md` for generated art. That spec was written for an external image model. See §9 for the two decisions that differ.

---

## 1. Install (from the phone)

```bash
unzip -o ~/storage/downloads/WorldSim_ArtPack.zip -d ~/     # the zip has a top folder WorldSim_ArtPack/
cp -r ~/WorldSim_ArtPack/. ~/WorldSim/                         # overlay it on the repo root
cd ~/WorldSim
python3 ci/make_meta.py && python3 ci/make_meta.py --check
git add Assets/WorldSim/Resources Assets/WorldSim/Runtime/Presentation/Art Assets/WorldSim/Editor/WorldSimArtPostprocessor.cs* Tools/ArtGen docs/art
git commit -m "Art pack v2: generated atlases, runtime loader, recolour shader, ArtGen tools, art docs"
git push
```

- **Metas.** The pack already includes `.meta` files for every new folder and `.cs` file (made with `ci/make_meta.py`). PNG, JSON and shader metas are created by Unity on first import. Commit them from the codespace after one import to keep GUIDs stable. Loading goes through `Resources` paths, so GUIDs never matter at runtime.
- **CI.** The new C# touches `WorldSim.Presentation` (`Runtime/Presentation/Art/*`) and `WorldSim.Editor` (`WorldSimArtPostprocessor`). Per `CLAUDE.md`, that work must pass Actions and be checked on the phone before it is reported as working.
- **What was checked.** The C# was compiled here against API stubs with C# 9 and warnings as errors. It was **not** compiled against real Unity. If Unity rejects something, fix it on the Unity side and keep the API surface.

## 2. What is where

| Path | What | Used for |
|---|---|---|
| `Assets/WorldSim/Resources/WorldSimArt/atlas_index.json` | List of all atlases | `WorldSimArtDB.Load()` |
| `…/WorldSimArt/<Category>/<atlas>.json + .png (+ _mask.png)` | Atlas pages, frame rects, pivots, anchors, tags, animations | All sprites (§4) |
| `…/WorldSimArt/Shaders/WorldSimRecolor.shader` | `WorldSim/RecolorSprite` (unlit) | Kingdom, culture and person colours; hit flash; sickness; night tint |
| `Assets/WorldSim/Resources/WorldSimData/*.json` | Rules the art was generated from | Port to C#/ECS data (§5) |
| `Assets/WorldSim/Runtime/Presentation/Art/WorldSimArtDB.cs` | Runtime loader (`Sprite.Create`, no 2D Sprite package needed) | name → Sprite, masks, anchors, tags, animations |
| `…/Art/WorldSimPalette.cs`, `WorldSimRecolor.cs` | Palette ramp textures and the recolour component | Gives each renderer its owner's colours |
| `Assets/WorldSim/Editor/WorldSimArtPostprocessor.cs` | Import settings for the pack | Point filter, uncompressed, no mipmaps, masks linear |
| `Tools/ArtGen/` | Python generators (numpy + Pillow) | Regenerate or extend art (`python export_all.py`) |
| `docs/art/STYLE_GUIDE.md` | Pixel rules | Every new sprite follows it |
| `docs/art/previews/01…10` | Approved previews by topic | What the finished game should look like |

### Atlases

| Atlas | Content | Count |
|---|---|---|
| `Buildings/buildings_eras` | 6 eras × 10 categories (poor, rich, seat, commerce, industry, mine, research, energy, military, defense), seed variants. Every building also has `__construction`, `__damaged` and `__ruined` | 476 |
| `Buildings/houses_culture_kit` (2 pages) | Homes from slum to palace for 7 roof types × 8 wall materials, 2 variants each, plus yurts; each with the 3 states | 2,300 |
| `Characters/people` | Paper-doll people (`p_<age>_<gender>_<class>_<garment>_<head>_<frame>`), 4-frame walks, overlays `ov_bandage`, `ov_sling`, `ov_crutch`, `ov_sweat`, `ov_facepaint`, `ov_torch` | 1,350 |
| `Characters/animals` | 19 species, adult and young, 4-frame walk, `_dead` (legs up; for the 15 species that also live in fauna_land the old one is `_dead_classic`) | 190 |
| `Units/army` | 20 foot soldiers (`u_<kind>_<f>`), 4 mounted (`m_<kind>_<f>`), 15 machines (`x_<name>`) | 111 |
| `Units/aircraft` | 8 aircraft × 8 directions (`air_<type>_<deg>`), attack helicopter 8 directions × 4 rotor frames | 96 |
| `Units/air_defence` | SAM, radar, flak, CIWS, laser defence (animated), airbase | 15 |
| `Units/strategic` | Ballistic launcher (TEL), silo, missile-defence battery, 5 missiles × 16 directions × 2 frames, re-entry warhead, nuclear detonation (13 frames), shockwave, crater, fallout, radiation glow, hazard marker, grave marker | 197 |
| `FX/fx` | Explosions (3 sizes × 4), missiles and arrows (8 directions), smoke, fire, flame jet, laser, muzzle flash, tracer, bombs, flares, status bubbles, cough, flies, sparkle, hit, dust, splash, rain, snow, lightning, meteor | 76 |
| `Nature/nature_props` | Trees, pines (+ snow), palms, bushes, rocks, cacti, dead trees, reeds, ferns, mushrooms, crystals, corals, ice, lava pools, campfire, flowers | 53 |
| `Terrain/terrain_tiles` | 24 biomes × 4 seamless 64 px tiles, water depth ×3, shore foam ×2, cliff faces (earth, stone, snow × 1–4 levels) | 113 |
| `UI/ui_kit` | 9-slice frame, ribbon, 4 button styles, meter, gem, power icons (`picon_*`, 1× and 2×), menu and resource icons (`icon_*`), crest shields (4 splits) + crest symbols, reticle, selection ring | 125 |
| `UI/font_5x7` | 57 glyphs, white (tint in engine) | 57 |
| `Characters/Fauna/fauna_land` | 64 land species (animals, biome creatures, magic beasts) × adult/young × walk·idle·run·eat·attack·sleep + hurt, dead, remains, burnt, frozen (`a_<species>_<age>_<pose>_<f>`) | 3,212 |
| `Characters/Fauna/fauna_critters` | Birds (flying + ground, incl. phoenix, roc, thunderbird), snakes, frogs, crabs, insects, scorpions, spiders, sand worms (`c_…`) | 1,032 |
| `Characters/Fauna/fauna_sea` | 25 sea creatures × adult/young × swim·idle·attack + hurt, dead (belly-up), remains (`s_…`) | 550 |
| `Characters/Magic/beings` | 31 supernatural beings (demons, imp, afreet, jinn, marid, ghoul, wraith, lich, golems, elementals, treant…) idle·move·attack·cast·hurt·death; `m_jinn_possess_*`, `ov_possessed_*` | 518 |
| `Characters/Titans/titans` | 11 titans: idle·move·attack·grab (human struggling in hand)·stomp·roar·breath·hurt·death(+sink), remains, burnt, `t_fx_crack_*`, `t_fx_stuck_arrows_*` | 273 |
| `Characters/People/people_actions` | Human / elf / orc / dwarf × m/f × tribal/medieval/modern (+ children): 37 actions (work, combat, ride, swim, burning, knocked, blinded, possessed, grabbed…) + 13 death types for adults; children only `death_fade` (fade → grave stone) (`h_<species>_<g>_<outfit>_<action>_<f>`, `…_death_<type>_<f>`); recolour ACC/ACC2/SKIN/HAIR | 4,920 |
| `Units/Soldiers/soldiers_actions` | 13 soldier types × 4 species: idle·walk·run·attack·block·ride·flee·cower·knocked·blinded·burning + 13 deaths; TEAM recolour (`sol_<species>_<type>_…`) | 5,124 |
| `FX/Spells/spells` | 40 spells: projectiles ×8 dirs, impacts, novas, storms, beams, auras, zones, rune circles, walls, cast circles, icons (`sp_<spell>_<part>_<f>`) | 914 |
| `Buildings/world_structures` | Walls/gates/towers ×6 eras, keeps, bridges, docks, wells, markets, lamps, barns, pens, statues, fountain, 12 wonders, 33 fictional creed sanctums (+ states) | 736 |
| `Buildings/Disaster/disaster_*` | For EVERY building: the baked collapse sequence `__collapse_0..3`. Other states are shader + overlays (see §10) | 3,452 |
| `Buildings/Disaster/building_overlays` | `ov_fire_<s/m/l/xl>_0..2`, `ov_smoke_column_0..3`, `ov_flood_<cls>_0..1` | 24 |
| `Terrain/farms_roads` | 8 crops × 8 stages (plowed→ripe→harvested/withered/burnt/flooded), roads ×4 materials ×16-mask autotile, rails | 144 |
| `Terrain/terrain_seasonal` | Spring/autumn/winter tiles for green biomes, 16 biome blend masks, 16 shore masks | 140 |
| `Nature/nature_seasonal` | Trees/pines/palms/bushes × 4 seasons × 4 sway frames, fall (chopped) sequence, stump, burning, burnt, logs, ores with depletion | 427 |
| `Units/ships_vehicles` | 12 ships (6 eras, trade + war) × 8 dirs × 2 frames + sinking; 8 vehicles × 8 dirs + wrecks | 376 |
| `UI/Kingdoms/kingdom_colours` | 32 kingdom colours: animated flags (3 shapes), banner, capital marker, army marker, badge, buttons, selection ring, war tent, border strip | 672 |
| `UI/Icons/icons` | ~115 icons (resources, needs, status, jobs, war, disasters) at 16 & 32 px + portraits of every creature/being/titan/building | 698 |
| `FX/Weather/weather_fx` | Rain/snow/acid/hail/ash/blizzard/sandstorm tiles, fog, tornado, tsunami, volcano, lightning, meteor, wildfire, quake, aurora, rainbow, fireworks | 104 |
| `FX/Decals/decals_particles` | Scorch, crater (4 sizes), rubble, ash, puddle, footprints, 14 particle kinds, blast-zone rings (no blood: STYLE_GUIDE no gore) | 108 |

Scale is **16 px = 1 world unit** (`ppu` in every JSON). All art sits on one fine grid. Terrain, buildings and props were drawn on the coarse grid and upscaled ×2. Keep integer zoom steps with a Pixel Perfect Camera.

## 3. Using it in code

```csharp
using WorldSim.Presentation.Art;

var db = WorldSimArtDB.Instance;                       // reads only art_index.bytes; pages load on first use
var go = new GameObject("villager");
var sr = go.AddComponent<SpriteRenderer>();
var rc = go.AddComponent<WorldSimRecolor>();
rc.SetFrame("p_adult_f_middle_dress_scarf_0");          // sprite + mask + recolour material
rc.SetPalette(WorldSimPalette.BuildRampTexture(
    WorldSimPalette.RampFrom(kingdomColour),           // TEAM
    WorldSimPalette.RampFrom(culture.Acc),             // ACC
    WorldSimPalette.RampFrom(culture.Acc2),            // ACC2
    WorldSimPalette.RampFrom(culture.Roof),            // ROOF
    person.Skin, person.Hair));
if (db.TryGetAnim("walk_adult_f_middle_dress_scarf", out var walk)) { /* walk.Frames, walk.Fps, walk.Loop */ }
db.TryGetAnchor("u_rifle_0", "muzzle", out var muzzleLocal);    // where to spawn muzzle_flash
```

- **Frames without a mask.** These are animals, nature, terrain, FX and fonts. Use them with `db.GetSprite(name)` and the default sprite material, so 2D lights affect them.
- **Recoloured frames.** These use the unlit `WorldSim/RecolorSprite`. At night set its `_Night` colour to the same tint as the global light. Converting the shader to a Sprite-Lit Shader Graph later is fine. Keep the mask rules from §4.
- **Pool renderers** and fetch sprites by name. `Sprite.Create` runs once per frame name; the result is cached.
- **Sorting.** Y-sort by pivot. Pivots are the ground contact point: feet, or the base centre for buildings. Use `Transparency Sort Mode = Custom Axis (0,1,0)`.
- **Aircraft and missiles.** They sit on a higher sorting layer. Draw their shadow on the ground layer: the same sprite in 30 % black, offset `(+alt/3, +alt)` px.
- **Loading and memory.** Nothing loads at start except the index. A page loads the first time one of its frames is used, and its recolour mask loads separately, only when a mask is needed. Pages are uncompressed, about 4–16 MB each. Warm a category before showing it with `StartCoroutine(db.Preload("Buildings/houses_culture_kit"))`. Free one with `db.Release("Characters/Titans")`: atlases that are still shown (by an active SpriteRenderer or UI Image, including a recolour mask) or held by `db.Acquire(prefix)` are kept, and sprites made from released pages are destroyed.
- **Instanced rendering.** Use the int API: `db.TryGetFrameId(name, out id)`, `db.Frame(id)`, `db.UvRect(id)`, `db.GetPageTexture(atlas, page)` and `db.GetMaskTexture(atlas, page)`. Hold an `Acquire` lease for the atlases you draw.
- **Tags.** `GetTagsJson(name)` returns the tag object (era, category, roof, wall, tier, species, angle, frame…). Parse it once into lookup tables, for example `houses[(roof, wall, tier)]` and `aircraft[(type, angle)]`.

## 4. Recolour system (why cultures can be infinite)

Each atlas page may have a `_mask.png` with the same layout:
- **R** = region id × 36;
- **G** = the shade the pixel had when drawn with a neutral grey ramp (40/84/128/172/216);
- **A** = 255 where the pixel belongs to a region.

| Region | Set by | Typical pixels |
|---|---|---|
| 1 TEAM | Kingdom colour | Flags, banners, tabards, shields, era-building roofs, wing tips, missile bands, UI frame line |
| 2 ACC | Culture accent | Middle-class clothes, doors, shutters, awnings, crest field |
| 3 ACC2 | Culture second colour | Trousers and skirts, rich clothes, crest chevron |
| 4 ROOF | Culture roof | Gable, hip, dome, cone, tiered and yurt roofs of culture houses |
| 5 SKIN | Per person | Face and hands; `_Sick` tints it pale green |
| 6 HAIR | Per person | Hair and beards |

**Ramps.** `WorldSimPalette.BuildRampTexture` builds them; textures are cached per colour set. Culture colours follow `Tools/ArtGen/culturegen.py`:
- **ACC:** an HSV ramp on the creed hue ± 18°.
- **ACC2:** the hue shifted by 150–200°.
- **ROOF:** ACC for dome, cone and tiered roofs; otherwise one of {TEAM, shingle, turf, ACC}.

**Check.** `docs/art/previews/03_cultures/recolour_check.png` shows baked colours next to a recoloured version for a person, an era building, a soldier, a launcher and a house. It was produced with the shader maths in Python.

## 5. What each asset is for in the game

### Cultures → houses, people, crests
Port `WorldSimData/culture_rules.json`:
1. A new kingdom rolls 3 founders with 2 traits each. The leader's vote counts double.
2. The top 2 **values** decide:
   - the **creed** (fully fictional; it reveres a place, tree, river, crater, the founders or great works, never a real religion);
   - the rule and the town layout;
   - the roof type, ornaments and dress;
   - the crown, the crest symbol and the palette.
3. The birth biome decides the wall material and the skin and hair pools.
4. A phoneme set gives every culture its own sounding names, and the founders start 3 clans.

How the art follows from the genome:
- **Houses.** Pick `houses_culture_kit` frames whose tags match `roof`, `wall` and `tier` (0 slum … 4 palace). Prefer matching `ornaments` and `tall`. Nomadic cultures use `roof == yurt`. Apply the culture ramps.
- **People.** `p_<age>_<gender>_<class>_<garment>_<head>_<f>`. Garment and head come from the dress rules: men use `head`, women `fhead`, rulers `crown`. Class comes from wealth.
  - Martial cultures add `ov_facepaint`.
  - Stone-age night walkers add `ov_torch`.
  - The injured get `ov_bandage`, `ov_sling` and `ov_crutch`.
  - The sick get `_Sick` and `ov_sweat`.
- **Splits.** A child culture keeps the namer, so names sound related. It keeps about 78 % of the genes and mutates one visual gene, so its houses look different automatically.
- **Crests.** `crest_shield_<plain|pale|fess|chevron>` (ACC/ACC2) plus `crest_symbol_<sym>` at (3,2). Tint the symbol gold for GREEDY or GRANDEUR cultures. Clans reuse the parts with their own colours.

### Era buildings
`b_<era>_<category>_v<n>`:
- The **founding** phase of an era mixes previous-era buildings with the new breakthrough ones (`previews/02_eras_buildings/era_progression_*`).
- Building states:
  - `__construction` while building;
  - `__damaged` below 60 % HP (spawn `fire` and `smoke` at the `fx_*` anchors);
  - `__ruined` at 0 HP.
- At night, lit windows and the era's street lights are the visible sign of progress (`previews/02_eras_buildings/day_night_eras.png`). The lights per era:
  - torch stakes and torch-bearers;
  - torch poles;
  - gas lamps;
  - sodium lamps;
  - holo pylons.

### Life and death
- **Walks** play at 6 fps.
- **Combat feedback:** `_Flash` on hit, red damage numbers, a 12×3 hp bar, and `status_*` bubbles (alert, infected, sick, immune, food, heal).
- **Deaths:** people lie down (rotate 90°, 20 % grey), animals use `a_<species>_<age>_dead`, and the grave is `grave_marker`, a plain stone.
- **Disease** follows `life_and_powers.json`:
  - stages run healthy → infected → sick → severe → immune or dead;
  - contagion uses `cough` and proximity;
  - cures unlock by era: herbs → quarantine → vaccine.
- **Radiation sickness** uses the same stages, is not contagious, and shows `radiation_glow` under the person.

### Armies (`army_roster.json`)
36 unit types across 6 eras. Each unit has resource gates (`needs`): no iron means no knights, no oil means no tanks. Sprites are `u_*`, `m_*` and `x_*`.

| Unit type | Attack FX |
|---|---|
| Bows | `arrow_<deg>` |
| Guns | `muzzle_flash` + `tracer` + `smoke_*` |
| Artillery | `muzzle_flash` + `boom_1_*` at the target |
| Flamethrower | `flame_jet` |
| Laser | `laser_segment`, tiled |
| Catapult | Stone arc + `boom_0_*` |

### Air war (modern and future)
- **Aircraft:** `air_<type>_<deg>`, top-down. Pick the nearest of 8 directions. The transport drops paratroopers (people sprites). The helicopter rotor runs at 16 fps.
- **Air defence:**
  - `ad_sam` plays stowed → raise → ready → launch;
  - `ad_radar` has a detection ring and pings;
  - `ad_flak` fires airbursts;
  - `ad_ciws` fires tracers;
  - `ad_laser_ad` is for the future era.
- **Intercepts:** a homing missile → `boom_*` in the air → falling debris with a smoke trail → a ground hit.
- Reference: `previews/06_army_air/air_raid.gif`.

### Strategic weapons (`army_roster.json → strategic`)
- **Launchers:**
  - `st_tel_0..5`: travel → erect → vertical → ignition → lift-off;
  - `st_silo_0..3`: closed → opening → armed → launch;
  - `st_abm_battery_0..1`: the interceptor battery.
- **Missiles:** `st_<srbm|cruise|icbm|abm|hgv>_<deg×10>_<frame>` in 16 directions (deg × 10, so `225` means 22.5°). The exhaust is included in the sprite. Animate the 2 frames at 12 fps.
- **Flight:**
  1. Boost upward (`…_2700_*`).
  2. Arc across the map, picking the nearest direction every frame. Draw a dotted arc and show **LAUNCH DETECTED** to every nation that has radar.
  3. Show `st_reentry_*` over the target.
  4. Impact.
- **Nuclear detonation:**
  1. Play `nuke_0..12` at 5 fps (pivot = ground zero). Frames 0–1 also flash the screen white.
  2. Lay `shockwave_0..3` as a ground decal.
  3. Leave `crater_nuclear`, a drifting `fallout_*` overlay, `radiation_glow`, and `hazard_marker` props (an original yellow/black design, not a real-world symbol).
- **Rules** (`strategic.nuclear_detonation`):
  - the blast ruins buildings and the fire radius damages them;
  - cells inside the blast become the IRRADIATED WASTE biome;
  - fallout causes radiation sickness;
  - every nation remembers the strike (relations −60, AI deterrence);
  - 5 or more detonations in 10 years cause a nuclear winter.
- **Gates:** nuclear ICBMs need URANIUM, ENRICHMENT and ROCKETRY; hypersonic gliders are future-era only.
- Reference: `previews/10_strategic/nuke_strike.gif`.

### World
- **Tiles:** `t_<biome>_<0-3>`, seamless 64 px; randomise the variant per cell. The biome comes from height, moisture and temperature (`world_rules.json`).
- **Elevation, 10 levels:**
  - draw rows back to front;
  - the top face rises `level × 6 px`;
  - if the cell in front is lower, draw `cliff_<earth|stone|snow>_<diff>` (capped at 4; stack for more);
  - the water surface sits at level 3, with `water_depth_*` and animated `shore_foam_*`.
  - Gameplay: armies slow uphill, high ground sees further, rivers flow downhill.
- **Props:** scatter from each biome's `props` list.

### UI (observer first; English now, Arabic later)
- **Kit:** `frame_9slice` (8 px borders; TEAM = kingdom), `ribbon`, `button_ghost|primary|gold|on`, `meter_frame`, `gem`, `picon_*` power icons (including `nuke`, `missile`, `launch_alert`, `hazard`, `shield_dome`), `icon_*`, `font_5x7`, `reticle` (power targeting), `select_ring`.
- **Screens** (`previews/08_ui_systems`):
  - Watch;
  - Nation;
  - City + any person;
  - History;
  - Powers drawer;
  - Take Control (time keeps flowing; RELEASE returns to watching);
  - Culture tree;
  - Royal clan;
  - Plague card;
  - War front;
  - Legend;
  - "Why?" cause chain.
- **Dock:** WATCH · NATIONS · HISTORY · FOLLOW · POWERS.

## 6. Regenerating and extending art

```bash
cd Tools/ArtGen && pip install numpy pillow
python export_all.py                     # everything, straight into Assets/WorldSim/Resources/WorldSimArt (+ atlas_index.json)
python export_all.py strategic army      # only some: buildings houses people animals army air fx nature terrain ui strategic
python data_export.py                    # Assets/WorldSim/Resources/WorldSimData/*.json
cd ../.. && python3 Tools/ArtIndex/build_art_index.py   # REQUIRED after any art change: rebuilds Resources/WorldSimArt/art_index.bytes
python strategicsheet.py                 # example preview renderer (sheets / GIFs), writes PNGs next to the script
```

- **Rebuild the index after every regeneration.** The game finds frames and animations through `Resources/WorldSimArt/art_index.bytes`, not the atlas JSON. Run `python3 Tools/ArtIndex/build_art_index.py` from the repo root and commit the result. CI runs it with `--check` and fails if the index doesn't match the atlases. It also fails if an animation event sits past the animation's last frame (such an event would never fire).
- **Adding a sprite.** Write a drawer `fn(canvas, ctx)` that reads palette regions from `ctx.v[...]`, then call `atlas.add(key, fn, W, H, pivot, regions=(...), tags=..., anchors=...)` in `export_all.py`.
- **Alpha.** It is recovered from two passes (black and white background), so shadows and glows export as real semi-transparency.
- **Masks.** They come from re-rendering with a probe colour for each region.
- Always follow `docs/art/STYLE_GUIDE.md`.

## 7. Suggested build order
1. Commit the pack. Make one house and one person show correct colours on the phone through CI.
2. Terrain renderer (biomes, 10 elevation levels, water), prop scatter, and zoom LOD (far = map colours and dots).
3. Culture genome in C#, then a village that picks houses and people from the genome, with names from the namer.
4. Simulation: needs, families and clans, eras and resource gates, building states, day and night.
5. Life and death: hunting, predators, injury, disease, contagion.
6. Armies and war fronts, then air war, then strategic weapons for the modern and future eras.
7. Observer UI screens, history, the "Why?" chain, powers, Take Control.
8. Backlog features (`feature_backlog.json`) in vote order.

## 8. Rules that apply to this art
- **Words.** Follow the naming rule in `CLAUDE.md`: the player abilities are just "Powers".
- **Creeds** are fully fictional, with no real religious names, buildings, symbols or iconography. Crest symbols, hazard marks and grave markers were checked for this. Keep it that way in new art.
- **Originality.** Original art only; never copy WorldBox or any other game. Reference videos stay out of the repo (`.local-reference/`).
- **Secrets.** No credentials in files or chat.

## 9. Owner decisions to confirm
1. **Outlines.** `docs/ASSET_SPEC.md` and `GAME_VISION_PROMPT.md §4` say 1-px dark outlines. The approved previews and this pack use **no outlines**: value contrast, a lit top-left rim and darker bottom-right edges. If the owner wants outlines, add a 1-px `#1C1820` outline pass in `xcore.render`, then re-export.
2. **Tinting.** `ASSET_SPEC` asks for neutral-grey clothes tinted per kingdom. This pack bakes default colours and adds **recolour masks** instead, which tint per region (kingdom, culture, person).

## 10. Library v3 additions (creatures, interactions, disasters, audio)

### Everything a person can interact with has sprites
- **Hunting / being hunted.** Predators use `<species>_adult_attack` then `_eat`; the victim plays `hurt` then `dead`/`remains`. Humans killed by animals use `h_*_death_eaten`.
- **Titans.** Soldiers attack with their attack animation. The titan plays `t_<name>_hurt`, and `t_fx_stuck_arrows_*` sits on its `hit` anchor. It answers with `stomp` (`t_fx_crack_*` + `h_*_death_crushed`), `grab` (a struggling human is drawn inside the sprite; the real unit is hidden while grabbed) or `breath` (sets tiles on fire).
- **Jinn possession.** `m_jinn_possess_*`, then the victim keeps `h_*_possessed` with `ov_possessed_*` on top.
- **Bombs and missiles near houses.** `interactions.json → blast_zones` gives the radius per weapon for zones 0–4. `zone_effects` gives what happens in each zone:

| Zone | Name | People | Buildings | Trees |
|---|---|---|---|---|
| 0 | Fireball | vaporized | collapse to rubble | removed |
| 1 | Blast | explosion death | collapse | fall |
| 2 | Thermal | burning, then burn death | burning, then burnt | burning |
| 3 | Shockwave | knocked down, hurt | hit, then damaged | fall |
| 4 | Flash / fallout | blinded, sick later | intact | intact |

  The sound changes with distance too: `extra_blast_near`, `extra_blast_mid`, `extra_blast_far`, plus `extra_shockwave_pass` and `extra_ear_ring`.
- **Building states** (v3.1, after the review, to save ~150 MB of texture memory):
  - **baked:** `__damaged`, `__ruined`, `__construction` and the one-shot `__collapse_0..3` (events `building_crack`, `building_collapse`, `dust`, `rubble`).
  - **shader** (`WorldSimRecolor.SetBuildingState(burn, frost, overgrown)` and `Hit()`):
    - burning = `_Burn` 0.4 + `ov_fire_<w_class>` on the `roof` anchor + `ov_smoke_column`;
    - burnt = `_Burn` 1;
    - frozen = `_Frost` 1 (blue tint + snow on top edges);
    - overgrown = `_Overgrown` 0.6;
    - hit = `_Flash`.
  - **overlay:** flooded = `ov_flood_<w_class>` drawn at the building pivot.
  - Every building frame now has a `roof` anchor and a `w_class` tag (s ≤ 40 px, m ≤ 64, l ≤ 96, xl).
  - The team colour stays visible while a building burns.
- **No gore** (STYLE_GUIDE): no blood pools, no red remains. Eaten people end as a plain grave stone, eaten animals as pale bone remains; hits show cartoon impact stars.
- **Children** never show a violent death: any cause → `h_<species>_<g>_child_death_fade_0..3` (fade, poof, grave stone). Owner decision.
- **Deaths.** There are 13 types: weapon, arrow, explosion, burn, freeze, electric, poison, drown, crushed, eaten, dissolve, irradiated and vaporized. `interactions.json → death_by_damage` maps each damage type to its animation, and `corpse_by_death` gives the corpse that stays behind.

### Data files (`Resources/WorldSimData`)
| File | Use |
|---|---|
| `creatures.json` | 174 creatures: category, habitat/biome, diet, size, hp, damage, speed, hostile, tameable, ridable, produce, abilities, available poses |
| `interactions.json` | 222 rules: attacker → victim → animations, damage type, death, FX, SFX, outcome. Also blast zones, building states and naming patterns |
| `animation_events.json` | Every animation that has frame events (`hit`, `spawn_projectile`, `spawn_spell`, `grab_victim`, `corpse`, `sfx:<key>`…) |
| `kingdom_palettes.json` | 32 kingdom colours (team ramp + accent); feed the TEAM region |
| `asset_report.json` | Counts and sizes |

`WorldSimArtDB.TryGetAnim(name, out anim)` now exposes `anim.Events`. When the player reaches an event frame, call `WorldSimAudioDB.Instance.ResolveEventSfx(evt.Name)` for `sfx:` events. Handle the other events in gameplay.

### Audio (`Resources/WorldSimAudio`, OGG Vorbis, 22 kHz mono)
- `SFX/` has 201 clips: `ui_*`, `combat_*`, `body_*` (hurt, scream, deaths, cheer, panic), `creature_*`, `magic_*`, `world_*` (work, vehicles, missiles, nuke, siren), `disaster_*`, `building_*` (fire, crack, collapse, glass, flood…), `extra_*` (blast by distance, war drums/horn, battle, crowds, nature, monsters) and `event_*` / `sting_*` (kingdom founded or fallen, war, peace, era, victory, defeat).
- `Ambient/` has 24 seamless loops: biomes, weather, burning city, battle, underwater, harbour, wasteland…
- `Music/` has 12 seamless loops: one per era (stone, ancient, medieval, industrial, modern, future) and one per mood (war, peace, apocalypse, title, exploration, magic).
- Levels are matched by category (RMS targets: UI −22 dB, ambient −24, music −20, others −18; peak ≤ −3 dBFS). No clip clips after Vorbis encoding (decoded and checked). Everything is synthesised by `Tools/ArtGen/audio.py`. There are no samples and nothing is copied. **Not listened to by a human yet.** Only automatic checks were run (no NaN, not silent, seamless loop crossfade). Treat it as a first pass, and replace any clip you dislike with the same file name.

### Sizes
- Art: 18.0 MB (≈ 288 MiB of textures if every page and mask were loaded at once: load per atlas)
- Audio: 7.2 MB
- Data: 0.6 MB
- Code and tools: 0.9 MB

### Owner decisions after the review (2026-11-20)
| Topic | Decision |
|---|---|
| Outlines | **None.** The owner left it to us; the reviewer and the art side both recommend no outline. `docs/ASSET_SPEC.md` now says so (repo commit 1bccc8c). |
| Building disaster states | Shader + overlays; only the collapse stays baked. |
| Children's deaths | Fade + grave stone only. |
| Wonders that resemble real landmarks (colonnaded library, ziggurat, stepped pyramid, torch-bearing colossus) | **Keep as they are** (owner). |
| Names demon / jinn / afreet / marid and possession | Approved by the owner in the art chat ("عادي مش مشكلة… استخدم نفس الأسامي"). Added to `CLAUDE.md` (2026-11-20). |
| Gore, a real-religion title, cross-like emblems, close kingdom colours, clipped audio | Fixed (rule violations). The title was renamed "seer"; the `tree` and `scale` emblems were redrawn; the 32 kingdom colours were re-picked (min CIE Lab ΔE 11 → 21). |
