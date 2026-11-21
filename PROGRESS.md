# Playable Alpha: plan and progress

**Goal (owner, 2026-11-21):** an APK that opens on the owner's phone to:
- a good-looking world in the WorldBox style;
- people who live and build villages;
- coloured kingdoms whose borders grow and who go to war;
- powers and disasters the owner can use and whose results are visible.

The goal is a difference the owner feels while playing, not improvements to preview tools.

**Rules:**
- Work autonomously and stop only at ⛳.
- Commit small and often, and push.
- Short Egyptian-Arabic reports with pictures from the phone.
- Every decision goes into `docs/DECISIONS.md`.
- Merge into `main` only with the owner's approval.

**Branch:** `rebuild/pack-foundation`.

Legend: `[x]` done · `[~]` in progress · `[ ]` not started · ⛳ owner review point.

## Step 0: clean-up
- [x] Commit and push renderer v3 (`cbcc705`).
- [x] `docs/DECISIONS.md` from section 8 of the status report plus today's decisions; old vision/plan docs moved to `docs/archive/`.
- [x] Originality policy updated (`CLAUDE.md`, `docs/ORIGINALITY.md`, `CREDITS.md`).
- [x] Delete branch `art/astc-test`.
- [x] `wip/b4-other-agent` reviewed: kept the tested civ core (`Core/Civ`: AStarGrid, CivNames, CivRules + 10 tests). Dropped the unbuilt ECS parts and deleted the branch.

## Step 1: lock the art style (most important)
Problem today: the look is dull and washed out, and details don't change with zoom (the same drawing just shrinks).
- [ ] Compare 2-3 terrain options for the same place:
  1. our pack, improved (brighter, calmer texture);
  2. a bright, flat WorldBox-like style;
  3. an open-licence top-down pack (Kenney or OpenGameArt; licence checked and credited).
  ⛳ The owner picks one.
- [ ] Look rules:
  - bright, clean ground with few small details, no blotches and no level lines;
  - height from hillshade only; stronger shading on mountains; snow caps with a blue-grey shadow;
  - cliff only at the coast, then sand, then a thin foam line; water in 3 depths;
  - smooth borders;
  - mountains at most 15 % of the land (measured).
- [ ] One detail layer per zoom (see `docs/DECISIONS.md`): Near / Mid / Far / Map.
  ⛳ One picture with the same place at all four zooms side by side.

## Step 2: the new look inside the game
- [ ] Runtime baker: `TerrainComposer` bakes 32x32-cell chunks on a background thread into Texture2D. Only edited chunks re-bake. One layer per zoom, with a cache and release of far chunks.
- [ ] Creatures drawn with pack sprites (`CreatureArt`) with animation and animation events; the old procedural creature art is removed.
- [ ] A new world starts with animals and people automatically.
- [ ] Default world size 256x256 until bigger maps are measured.
- [ ] HUD developer counters: FPS, memory, draw calls.
  ⛳ Phone pictures (Near/Mid/Far) + FPS + memory + draw calls.

## Step 3: the game becomes playable (the heart of the Alpha)
- [ ] **People:**
  - jobs: gather wood and food, farm, hunt, chop trees (tree falls, then stump, then logs);
  - build houses, farms and roads with pack sprites (`houses_culture_kit`, `farms_roads`);
  - birth, growing up, death (grave marker; children only fade).
- [ ] **Villages and kingdoms:**
  - a village grows into a city;
  - a kingdom has a name, a palette colour and a banner;
  - coloured borders grow with its cities;
  - two kingdoms meet, then tension, then war: soldiers (`soldiers_actions`), combat, attacks on cities, surrender or peace.
- [ ] **Powers** (one-handed powers bar):
  - spawn people and animals; the terrain brush (exists);
  - fire, rain, meteor, bomb/missile with blast zones 0-4 from `interactions.json`: vaporise, explode, burn, knock down, blind;
  - buildings: burnt, then collapse_0..3, then ruins; flooding with the overlay;
  - at least one titan attacks a city and the army fights it.
- [ ] **Audio:** SFX from animation events, biome ambience, a music loop; sounds fade with far zoom.
- [ ] **UI:**
  - tap a person, city or kingdom for an info panel;
  - time control: pause, x1, x2, x5, x10;
  - simple save/load + autosave.
  ⛳ A short video or GIF from the phone for each of the four points above.

## Step 4: performance
- [ ] Targets:
  - 60 FPS with 2,000 creatures on a 256 world;
  - never below 30 FPS with 10,000;
  - memory under 600 MB;
  - no allocations in hot paths;
  - creatures in instanced batches per atlas page.
  ⛳ Numbers from the phone.

## Done when
- [ ] The game opens and within 30 s shows a world that looks like WorldBox.
- [ ] Within 5 minutes a village grows into a kingdom with a colour and borders.
- [ ] A bomb next to a city: houses burn and collapse, people are affected by distance, graves afterwards, all with sound.
- [ ] Two kingdoms at war, visible at every zoom.
- [ ] 30 minutes of play without a crash.

## Log
- 2026-11-21: plan written; Step 0 done.
