# WorldSim — Master Prompt: Vision, Goals, Decisions and Final Version

Use this as the single source of truth for the game. It merges the original production prompt with every decision and feature request made since (2026-11-17 → 2026-11-18).

---

## 1. What WorldSim is

A **mobile-first pixel-art world-simulation sandbox** for Android. The player shapes a living world and watches life, peoples and civilizations emerge, grow, fight, evolve through history **and keep advancing into the future**. The player can intervene with tools and powers, or simply observe.

Core promises:
1. **A world that looks alive**: rich biomes, plants, creatures, weather, motion.
2. **Total creative control**: build any map by hand or generate one with settings.
3. **Deep life**: every creature has traits, needs, a life story; peoples have names, families, kingdoms and history.
4. **Unbounded progress**: civilizations never stop at one era. They go from the Stone Age to today and beyond, into invented future eras with no ceiling.
5. **Time in the player's hands**: pause, slow down, fast-forward up to 50×, skip to the next era, and read the history.
6. **Runs well on a strong phone**: hundreds to thousands of agents without stutter.

## 2. Ground rules (non-negotiable)

- **Original work only; learning is welcome, taking is not.** All code, art, audio and UI are created for WorldSim, and no ready-made asset packs are shipped. Studying open-source projects, tutorials, references and genre conventions is encouraged; reusing permissively licensed code is fine when credited in CREDITS.md. Never use anything decompiled or ripped from another game (including WorldBox), even renamed or edited. Full policy: docs/ORIGINALITY.md.
- **No word "God"** anywhere: product, code, UI, docs, assets. The game is "WorldSim"; package `com.fluxegy.worldsim`. "God powers" are just **Powers**.
- **Beliefs are fully fictional** (see §6.6). A **fiction notice** is shown on first launch: every creed, belief, ritual, kingdom, name and character is invented and refers to no real religion, belief, people or place.
- **Deterministic simulation**: the same seed + settings + inputs give the same world and history on every device (integer/fixed-point math in simulation; floats only in presentation).
- **Honesty in reporting**: never claim something works without evidence (tests, CI logs, on-device screenshot/logcat).

## 3. Platform and technology (pinned)

| Item | Choice |
|---|---|
| Engine | Unity **6000.3.28f1** (Unity 6.3 LTS) |
| Rendering | URP 17.3.0, 2D Renderer, a Global Light2D at runtime (no global light = black sprites) |
| Simulation | DOTS: Entities 1.5.0, Burst 1.8.31, Collections 2.7.1, Mathematics 1.3.3 |
| Input | Input System 1.20.1, EnhancedTouch (legacy input disabled) |
| UI | uGUI 2.0.0 built in code, Canvas Scaler 1080×1920, safe area; built-in `LegacyRuntime.ttf` (Arabic shaping needs a dedicated component later) |
| Build | Android, **IL2CPP, ARM64**, stripping High, Vulkan + GLES3 |
| Build server | **GitHub Actions only** (owner has no PC): `game-ci/unity-builder@v6` with `cliVersion: v0.1.76`, two passes (headless `WorldSimCI.Bootstrap`, then `WorldSimBuild.BuildReleaseCI`), per-step timeouts, never cancel running builds (Personal seat leaks) |
| Licence | Unity Personal via secrets `UNITY_EMAIL` + `UNITY_PASSWORD` only (2FA off). Unity removed `.alf/.ulf` manual activation |
| Signing | Committed **test** key `ci/worldsim-test.keystore` so updates install over each other; a separate store key via GitHub secrets for release |
| Device testing | The owner's phone is rooted: install with `pm install`, launch with `am start`, verify with `screencap` + `logcat`, before telling the owner a build works |
| Mods | **HybridCLR + first-party loader** (single IL2CPP build); public `WorldSim.ModAPI.dll`; data-driven registries (terrain, species, traits, weapons, techs, powers); mod code never runs inside Burst jobs |

**Assemblies:** `WorldSim.Core` (pure, deterministic, tested in plain .NET), `WorldSim.Render` (pure pixel-art painter, same code in game and preview tool), `WorldSim.Simulation` (ECS), `WorldSim.ModAPI`, `WorldSim.Modding`, `WorldSim.Presentation` (MonoBehaviour glue, UI), `WorldSim.Editor` (CI/build tooling), tests. `Tools/CoreTests` (dotnet test) and `Tools/WorldPreview` (renders worlds, sprites, icons to PNG) run on the phone without Unity.

**Performance budgets (60 FPS):** simulation ≤ 8 ms, rendering ≤ 6 ms, UI ≤ 1 ms, 0 B GC alloc per frame in steady state. AI LOD, budgeted pathfinding, macro simulation at high speeds, thermal throttling fallback.

## 4. Visual direction

- Top-down pixel art with a slight front tilt; light from the top-left; 1-px dark outlines on objects; hard pixels.
- **Zoom-dependent detail (owner request):** far zoom = calm, clean map (no sprites, no shimmer); mid = full detail; near = full detail **plus animation** (waves, swaying trees, glowing lava, creature animation). Animation cost only for what is visible.
- Owner-provided art (generated to `docs/ASSET_SPEC.md`: 16 px per tile, 4-frame walks, neutral-grey clothes tinted per kingdom, 5 building eras per people) replaces procedural art file by file; anything missing stays procedural.

## 5. World

- **Generation:** layered integer noise (continents, ridges, domain warp, smooth edge jitter, climate), **19 biomes** (ocean, shallows, beach, grass, temperate/birch/dense forests, jungle, savanna, desert, swamp, taiga, tundra, snow, mountains, lava, and invented ones: crystal fields, mushroom grove, ember wastes, glimmerwood), **24 decoration types** (trees, bushes, berries, flowers, grass, cacti, reeds, rocks, crystals, mushrooms), resources (wood, stone, gold, gems).
- **Settings before generation:** land amount (islands ↔ continents), climate (ice age ↔ hot), mountains, blank worlds (empty ocean, flat land).
- **Map sizes:** Small 256², Medium 512², Large 1024² (bigger maps get more continents, not magnified ones); **Huge 2048² and Titanic 4096²** with chunked terrain rendering and macro simulation.
- **Map editor / shaping:** brushes in several sizes: raise, lower, flatten, paint any biome, plant trees, clear; changes repaint only the edited area; edits are deterministic and saved.

## 6. Life, peoples and civilizations

### 6.1 Species and creatures
Many species: peoples (Human, Elf, Orc, Dwarf, plus more, and mod-added) and animals (herbivores, predators, birds, fish, more over time, including invented and legendary creatures). Food chains, habitats (land/water/air), needs (hunger, thirst, fatigue, happiness), aging, birth, death.

### 6.2 Brain (utility AI)
Every N ticks each creature scores actions (eat, drink, sleep, flee, hunt, mate, socialize, work, build, worship/perform ritual, fight, trade…) with curves over its state, **weighted by traits, culture and creed**, plus small deterministic noise.

### 6.3 Traits — deep, inherited, editable (A4)
Dozens of traits in exclusive groups (genius/smart/dull, strong/weak, brave/coward, kind/aggressive, healthy/frail, fertile, long-lived, fast/slow, charismatic, lucky/clumsy, glutton/hardy, curious/lazy, and more, including traits **earned during life**: veteran, survivor, traveller…). Every newborn gets **random traits** if the player doesn't choose: inheritance from parents, spontaneous chance, rare mutations, life circumstances. The player can **add or remove any trait** on a unit or an area. Traits change behaviour, stats, research and history.

### 6.4 Characters that grow
Names, age stages (child → adult → elder), families and lineages, friends and rivals, skills and experience, a readable **biography**, memories that affect behaviour, and **legends** (heroes with titles remembered by history). Possess a unit for direct control.

### 6.5 Kingdoms
Villages grow into cities with **walls**, buildings that **change by era**, territory borders, banners and colours, rulers and **dynasties**, laws, culture, diplomacy (peace, alliance, war, vassals), trade caravans and ships, economy (resources, coins), revolts and civil wars, collapse and successor states.

### 6.6 Beliefs and rituals — fully fictional (A3)
Procedurally generated **Creeds** with invented syllable names, abstract emblems and tenets that are game modifiers. They revere only things of this world (an ancient tree, a peak, a crater, a founder, a famous event). They spread and split, affect diplomacy and happiness, and have buildings that change by era (Monolith, Sanctum, Circle of Stones…). **Never** real religions, scriptures, figures, places, symbols, titles or practices.

### 6.7 Open-ended technology (A1)
Data-driven **tech tree and eras**: Stone, Bronze, Iron, Medieval, Gunpowder, Industrial, Modern, **Information (today)**, Near future, Far future, then **procedurally generated "Beyond" tiers forever**. Research from population, schools, universities, trade and **smart/genius citizens**; **knowledge spreads** through contact, trade and conquest; collapse can set a kingdom back but knowledge survives in successors. **Weapons, armour, units, vehicles and buildings evolve per era** (clubs → swords → bows → muskets → rifles → tanks → aircraft → drones → energy weapons…), with varied weapon families per kingdom.

### 6.8 Magic
A fictional magic system tied to the world (mana crystals, places of power), schools (fire, water, earth, air, healing, illusion…), **magical talent as an inherited trait**, mages who learn and grow, and kingdoms that follow a magic path, a technology path, or both (magitech in later eras).

## 7. Powers and disasters
Terrain powers, spawn life, heal, lightning, **meteor, earthquake, tornado, fire, acid rain, floods, volcanoes**, plagues, blessings and curses (trait powers), weather (rain, snow, heat waves) that changes moisture, temperature, crops and fire risk. Disasters really affect terrain, units, buildings, economy and AI.

## 8. Time and watching history (A2)
Pause, 0.25×–50×, **skip to the next era or event**; macro simulation off-screen at high speed (same seed → same history at any speed). **Chronicle/timeline** of eras, inventions, wars, empires, collapses; **graphs** (population, tech level, territory per kingdom); **tech tree view**; kingdom and character inspectors; **observer mode** that follows the most interesting events.

## 9. Save, settings, polish
Binary + GZip saves with version header, exact round-trip (state hash), 3 slots + rotating autosave, missing-mod placeholders. Settings: frame rate (30/60/90/unlimited), render scale, particles, shadows, AA, simulation rate; persisted. Procedural sounds or owner audio. Tutorial hints. Crash-safe startup (UI first, visible errors). Arabic UI with proper text shaping after the Beta.

## 10. Milestones

| # | Milestone | Status (2026-11-18) |
|---|---|---|
| Stage 1 | Project, CI, Android ARM64 build | **Done, verified on device** |
| Stage 2+3 | Deterministic world + touch camera | **Done** (hash identical on ARM64 .NET, x64 CI and device) |
| B1 | World that looks alive (biomes, decorations, organic edges, water, toolbar, zoom LOD, waves) | **Built** (device check pending for the latest parts) |
| B2 | Shape the world (brushes, settings, blank worlds) | **Built** (device check pending) |
| B3 | Life: species, deep traits + genetics, utility AI, creatures on screen, Life tab | **Part 1 written** (not yet built) |
| B4 | Civilizations: villages→cities, kingdoms, dynasties, eras, weapons, creeds, economy, diplomacy, chronicle | next |
| B5 | Powers and disasters, trait editing | |
| B6 | Time control and history views | |
| B7 | Save/load | |
| B8 | Polish, settings, performance, sounds | |
| B9 | Release prep (store key, AAB, store texts) | |
| After Beta | Magic, mods (HybridCLR), Huge/Titanic maps, Arabic UI, more species and legendary creatures | |

Each milestone: write code + pure tests (plain .NET on the phone) → CI build → install, run, screenshot and read logcat on the owner's phone → report with evidence.

## 11. Working with the owner
- Explain everything to the owner **in Arabic** (code, paths, logs in English).
- During builds, send a short status with estimated time left **every 5 minutes**.
- Don't open the game on the owner's phone while they asked to wait.
