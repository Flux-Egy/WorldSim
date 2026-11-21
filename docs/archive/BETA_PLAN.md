# WorldSim Beta — scope and milestones

Owner request (2026-11-18): "finish the game and ship a clean Beta that is ready to publish, in one batch; take the time it needs." This file defines what that Beta contains. It's the working order from here on. Each milestone ends with a CI build that is installed and checked on the owner's phone (screenshot plus logcat) before the next one starts.

Ground rules (unchanged): original code and art only (§16, no reverse engineering of any other game); no "God" anywhere; creeds fully fictional (A3); fiction notice on first launch; Arabic replies to the owner, English in the repo.

## In the Beta

| # | Milestone | Content | Plan refs |
|---|---|---|---|
| B1 | **A world that looks alive** | 16+ biomes (temperate/birch/dense forest, jungle, savanna, desert, swamp, taiga, tundra, snow, beach, plus fictional ones: crystal fields, giant-mushroom grove, ember wastes, glimmerwood); decoration sprite layer (many tree, bush, flower, cactus, rock and reed types); soft biome edges; water depth bands plus animated waves; 8 px per tile at close zoom; bottom toolbar with tabs and pixel icons; speed buttons | §4, §7, A5 |
| B2 | **Shape the world** | Brushes: raise/lower land, paint any biome, water, sand, forest, mountain, plant/clear decoration; brush sizes; blank-world editor mode; map-generation sliders (land %, mountains, climate, islands) | §2.2, §6.3 |
| B3 | **Life** | Animals (herbivores, predators, birds, fish) with procedural sprites and walk animation; 4 fictional sapient races; needs plus utility AI (§5.2); coarse-grid A* (§5.3); birth, aging, death; **deep traits**: random at birth, inherited with mutation, editable by the player (A4); names; spawn powers | §5, A4 |
| B4 | **Civilizations** | Villages that grow into cities; buildings that change by era; kingdoms with names, banners, rulers and dynasties; borders; resources and simple economy; diplomacy, war and combat with **era weapons**; research and **open-ended eras** (Stone to modern to future to "Beyond") (A1); fictional creeds (A3); chronicle of events | §5.4, §11, A1, A3 |
| B5 | **Powers and disasters** | Meteor, earthquake, tornado, fire, acid rain, lightning, heal, bless/curse traits, possess unit (basic) | §6 |
| B6 | **Time and watching history** | Pause to 50× (macro simulation at high speed), skip to next era, timeline, graphs, unit/kingdom inspector | A2 |
| B7 | **Save / load** | Binary + GZip saves, 3 slots, rotating autosave, exact round-trip test | §10 |
| B8 | **Polish** | Settings screen (frame rate, render scale, particles, sim rate), thermal fallback, performance pass on the owner's phone, sounds (procedural), tutorial hints, crash-safe startup | §2.1, §12, §13 |
| B9 | **Release prep** | Release signing key in GitHub secrets, AAB for Play, versioning, store text, privacy policy, content-rating notes, `RELEASE.md` checklist | §15 |

## After the Beta (1.0 and later)
Magic system, mod loader (HybridCLR, Decision A), Huge/Titanic maps with chunked rendering, Arabic UI (needs an Arabic text-shaping component), multiplayer/sharing worlds.

## Honest expectations
- Art is generated procedurally in code (no artist). It will be far richer than the Stage 2 placeholders, but not hand-painted quality. Any CC0 asset pack (licence checked per pack) or commissioned art can replace it later without code changes.
- "Ready to publish" means the build and the documents are ready. Uploading to Google Play needs the owner's Play Console account (25 USD one-time fee), store screenshots and the content-rating questionnaire, which only the owner can submit.
