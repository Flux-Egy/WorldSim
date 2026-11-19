# WorldSim — Art Asset Specification (for the asset generator)

Give this whole file to the image model. Every asset must follow it.

## 0. Originality (mandatory)
See docs/ORIGINALITY.md. Learning from references, tutorials and open-source projects is encouraged; shipping or editing someone else's art is not.
- **Original designs only.** Do **not** imitate, trace, recolour or "loosely copy" the sprites, characters, UI or overall look of any existing game (including WorldBox). The game's identity is its own.
- Generic genre conventions are fine: top-down pixel art, small readable characters, bright natural colours, dark outlines.
- No text, logos, real-world symbols, flags or religious symbols in any image.

## 1. Global style
- **Pixel art**, hard pixels: no anti-aliasing, no blur, no gradients except by dithering.
- **Top-down with a slight front tilt** ("3/4 view"): we see the tops of trees and the fronts of creatures.
- **Light comes from the top-left.** Lit side is 1–2 shades lighter; the bottom-right is 1–2 shades darker.
- **1-pixel outline** in a very dark, slightly purple-tinted colour `#1C1820` around every object (not around terrain tiles).
- **Transparent background** (PNG with alpha) for everything except terrain tiles.
- **Palette:** warm and saturated, but not neon. Reference colours already in the game (match them):

| Use | Hex |
|---|---|
| Grass | `#68AE40` |
| Forest floor | `#489036` |
| Sand / beach | `#E4D294` |
| Desert | `#E8C678` |
| Shallow water | `#468ED6` (deep: `#163E8C`) |
| Mountain rock | `#7C746C` |
| Snow | `#E8EEF6` |
| Lava | `#E24C18` |
| Crystal fields | `#96C4D6` |
| Mushroom grove | `#8C6A96` |
| Glimmerwood | `#42968E` |

## 2. Scale
- **1 tile = 16 × 16 pixels.**
- Objects stand on the **bottom-centre** of their image (the feet / trunk base touch the bottom edge, centred horizontally).
- Every frame of an animation has the **same canvas size** and the same anchor.

## 3. File format and naming
- PNG, RGBA, exact pixel sizes below (no scaling up). One image per object, or a horizontal strip of frames.
- Strips: frames left to right, same size, no gaps. Put the frame size in the name: `wolf_walk_16x16.png`.
- Lower-case, underscores, English: `<thing>_<variant>_<WxH>.png`.

Folder layout:
```
terrain/  trees/  plants/  rocks/  creatures/  buildings/  effects/  ui/  sounds/
```

## 4. Asset list

### 4.1 Terrain tiles (optional; the game already paints terrain)
- 16×16, **seamless** (tiles must repeat without visible seams), **4 variants** per biome.
- Biomes: ocean_deep, ocean_shallow, sand, grass, forest_floor, birch_floor, jungle_floor, savanna, desert, swamp, taiga, tundra, snow, mountain, lava, ember_wastes, crystal_fields, mushroom_grove, glimmerwood.

### 4.2 Trees and plants (3 variants each)
- Trees: **16×32** (trunk base at bottom centre). oak, pine, birch, palm, jungle, acacia, swamp, dead, snow_pine, glow (fictional: teal/pink glowing leaves).
- Small plants: **16×16**. bush, berry_bush, flowers (mixed colours), tall_grass, reeds, cactus, mushroom.
- Large fictional plants: **16×32**. giant_mushroom (red, purple, blue caps).
- Each tree also as a 2-frame **sway** strip (top leaves shifted 1 px): `oak_sway_16x32.png` (32×32 strip).

### 4.3 Rocks and minerals (3 variants)
- **16×16**: rock, boulder, ice_rock, ember_rock (dark rock with glowing orange cracks), crystal_cluster (cyan, violet, green), gold_vein, gem_vein.

### 4.4 Creatures — facing right, 16×16
Each: **4-frame walk strip** (64×16) + **1 idle** + **1 dead/lying** frame.
- Peoples (original designs, not taken from any game):
  - human; elf (pointed ears, slim); orc (green skin, small tusks, broad); dwarf (short, braided beard).
  - **Clothes in neutral light grey** (`#C8C8C8`) so the game can tint them with kingdom colours.
  - Each people also: **child** version (12×12 visual inside the 16×16 canvas).
- Animals: rabbit, sheep, deer (antlers), cow, wolf, bear, fox, bird (also a 2-frame flying strip), fish (2-frame swim strip).

### 4.5 Buildings (for kingdoms, coming in milestone B4)
- **32×32** each, door facing down, same perspective as trees.
- For each people, **5 eras** (stone, bronze/iron, medieval, industrial, modern), each with: house, farm, storage, workshop, watchtower, town_hall.
- Walls: wall_horizontal, wall_vertical, wall_corner, gate (16×16 each, per era).
- Shared: well, dock, boat (32×16), bridge (16×16).

### 4.6 Effects (strips, 8 frames)
- fire (16×16), smoke (16×16), explosion (32×32), lightning_strike (16×48), meteor (16×16 + trail), rain_drop (4×8), snowflake (4×4), blood_hit (8×8, small, not gory), sparkle (8×8), level_up glow (16×16).

### 4.7 UI icons (32×32, same outline rule, transparent)
globe, resize, info, mountain, people, animal, storm, spark, castle, gear, pause, play, fast, brush, eraser, tree, water, clock, raise, lower, flatten, plus one icon per species and per biome.

### 4.8 Sounds (optional; OGG, mono, short)
ui_click, ui_open, brush_paint, raise_land, lower_land, splash, footstep_grass, birth_chime, death_soft, sword_hit, arrow, explosion, thunder, rain_loop, wind_loop, ocean_loop, forest_loop.

## 5. Quality checklist (check every file)
- [ ] Exact size, transparent background (except terrain).
- [ ] Hard pixels, no blur, no anti-aliasing.
- [ ] 1-px dark outline; light from the top-left.
- [ ] Anchored bottom-centre; frames aligned.
- [ ] Original design, not resembling any specific existing game.
