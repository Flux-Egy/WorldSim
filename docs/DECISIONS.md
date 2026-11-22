# Decisions

Every owner decision, newest last. Add a row whenever a decision is taken (CLAUDE.md "How to work").
Sources: the owner's messages, CLAUDE.md, `docs/ORIGINALITY.md`, `docs/art/*`, and section 8 of the status report (`docs/STATUS_REPORT.md` on branch `status/report`).

## Platform, process and rules
| Date | Decision |
|---|---|
| 2026-11-17/18 | Engine and build: Unity 6000.3.28f1, URP 2D, DOTS (Entities/Burst), Android IL2CPP ARM64, package `com.fluxegy.worldsim`. GitHub Actions is the only build server (game-ci unity-builder v6, CLI pinned v0.1.76). Unity Personal via the `UNITY_EMAIL`/`UNITY_PASSWORD` secrets only. **Never cancel a running Unity step** (seat leak). |
| 2026-11-18 | Renamed to WorldSim. Naming rule: see CLAUDE.md hard rules. Beliefs are fully fictional (procedural creeds); fiction notice shown on first launch. |
| 2026-11-18 | Deterministic simulation (integer/fixed point); golden world hashes guard generation. |
| 2026-11-18 | Vision additions A1-A5: open-ended eras (Stone Age to beyond), deep editable inherited traits, time control up to 50x with history views, map sizes up to 4096. Original Beta scope B1-B9 (now archived). |
| 2026-11-18 | A test signing key is committed (`ci/worldsim-test.keystore`) so builds install over each other. Every Unity-side change is installed and checked on the owner's phone before it is reported as working. |
| 2026-11-19 | Three workshops: phone (pure C#, tests), Actions + device check (Unity side), Codespaces + Unity MCP (planned sessions; MCP is never registered on the phone). |
| 2026-11-20 | Exception to the naming rule: jinn, afreet, marid, demon and possession may be used. Still no real religions, symbols, scriptures or prophets. |
| 2026-11-21 | **Originality policy replaced** (`docs/ORIGINALITY.md`). Style, ideas and mechanics from any game (WorldBox included) may be imitated. Licensed ready-made assets, code and audio are allowed (CC0, CC-BY, MIT, OGA-BY...): check the licence, keep its text, add a row to CREDITS.md, show credits in game, never claim them as ours. No ripping or decompiling any commercial game; no unpaid paid assets; a credit is not a permission. Our pack stays the base. Reference media stays outside the repo. |
| 2026-11-21 | **Way of working:** autonomous work with stops only at ⛳ review points; small, frequent commits pushed often (nothing left uncommitted); short Egyptian-Arabic reports (✔️/❌/⏳) with pictures from the phone; look at every picture as a player before sending it; decisions recorded here; no merge into `main` without approval. |
| 2026-11-21 | **Next phase is the "Playable Alpha"** (`PROGRESS.md`): a good-looking world, people building villages, coloured kingdoms that grow and fight, and powers/disasters with visible results. No more improvements to preview tooling for its own sake: changes must be felt while playing. |
| 2026-11-21 | Clean-up: v3 renderer committed; old vision/plan docs moved to `docs/archive/`; branch `art/astc-test` deleted; from `wip/b4-other-agent` only the tested civ core (A*, names, rules) was kept. |

## Art and assets
| Date | Decision |
|---|---|
| 2026-11-20 | The owner's generated art pack (WorldSimArt) is the base art. No outlines. Disaster states via shader + overlays (collapse is baked). Children die only by fade + grave. Wonders resembling real landmarks are kept. |
| 2026-11-20 | Lazy art loader with a binary index (`art_index.bytes`, checked in CI). R8 recolour masks (lossless). All 237 audio clips approved. |
| 2026-11-20 | **Rebuild:** everything made before the pack is rebuilt on the pack in `rebuild/pack-foundation`. `main` stays untouched until approval; old code is deleted only after its replacement works on the phone. Golden hash changes are approved. |
| 2026-11-20 | Biomes: the pack's 24 + Lava, BirchForest, Glimmerwood, EmberWastes + water (all with their own tiles since patch v3.4.1). |
| 2026-11-20 | **Partial ASTC** on Android: terrain (except `Terrain/lod`), nature, buildings incl. disaster, FX. Uncompressed: UI, icons, portraits, font, people, animals, units. Masks stay R8; the LUT is never compressed. |
| 2026-11-20 | Camera: 4 zoom levels (near, mid, far, map) following `lod.json`. |

## Terrain look
| Date | Decision |
|---|---|
| 2026-11-21 | The old painter's look is rejected. Target: the clarity of the reference videos and the pack style demo. Send a same-seed picture before big visual steps. Never merge an unapproved look into main. |
| 2026-11-21 | Review 1 (done in v2): continuous cliffs, no texture repeats, clean snow, smooth borders and coasts, LOD tiles at far zoom, palms only on hot beaches and deserts. |
| 2026-11-21 | Review 2 (done in v3): no terraces or contour lines; cliff only at the coast; height through soft hillshade; rock darker and heavier with height; blue-grey shadow south of snow; white foam line; smooth island rims at far zoom; far zoom readable (forest density, `mk_*` markers in kingdom colour, roads, farms). |
| 2026-11-21 | **Look rules for the Alpha:** bright, clean ground colours with few small details (no camouflage blotches, no level lines); height by hillshade only, mountains clearly raised with stronger shading, snowy peaks with a blue-grey shadow; cliff only at the coast, then sand, then a thin foam line; water in 3 depths; smooth borders; mountains at most 15 % of the land. |
| 2026-11-21 | **Each zoom gets its own detail layer, never a shrunk copy:** Near = full tile + grass/flowers/pebbles, every tree with its shadow, bushes, full buildings with states, animated people. Mid = cleaner colour without small details, simplified tree crowns without bushes, simplified buildings, people as coloured dots. Far = biome colour + hillshade, forests as dark patches by density, small building clusters + kingdom borders in kingdom colour. Map = political kingdom colours, capitals + roads. |
| 2026-11-21 | **In-game terrain:** no shader that imitates the CPU composer. `TerrainComposer` itself is used as a runtime baker: 32x32-cell chunks baked on a background thread (Burst later) into Texture2D, re-baking only edited chunks, one layer per zoom, with a cache and release of far chunks. Default world size Medium (256) until bigger sizes are measured. |
| 2026-11-22 | Art-style candidates shown (A pack improved, B flat bright, C Kenney). **Decision: back to the v2 look** (`af635c8`: continuous cliffs, smooth borders, coast). Dropped: the smoky hillshade and Kenney. Take the grass and water shades of candidate B and apply them to v2. |
| 2026-11-22 | **Elevation detail fades with zoom:** Near = full cliffs (face + lit lip); Mid = only big cliffs (2+ levels), thin line at half contrast, small terraces gone; Far = no elevation lines, a very light hillshade on mountains only; Map = no elevation detail. Transitions between zooms fade, never jump. |
| 2026-11-22 | **Easy on the eye:** fewer terraces (patches under 40 cells merge); cliffs a dark shade of the same ground (never black), moderate contrast; calmer rock and snow texture; no grid or moiré at any zoom; vivid but not garish colours; no blur anywhere. Mountains (mountain + snow + glacier) at most 15 % of the land: now 14.0 % over 8 worlds. |
