# Stage 2 + 3 Report: World generation, terrain rendering, camera and touch

**Status: built, not yet verified on device.** Stages 2 and 3 ship in one build at the owner's request ("next build should be playable"). Each stage keeps its own exit criteria below.

## What was built
- `WorldSim.Core`: `TileData` (§4.1, 5 bytes), `FixedNoise` (Q16.16 gradient noise and fBm), `WorldGenerator` (§4.2 passes: continental height plus ridges, biome decision tree, edge refinement via domain warp and smooth threshold jitter, detail scatter of trees, rocks and ore) and `WorldHash`.
- `WorldSim.Simulation`: `WorldMapSystem` (ISystem). A `WorldGenRequest` triggers a Burst `IJobParallelFor` (tiles) and a Burst `IJob` (hash). The result is stored in the `WorldMap` singleton.
- `WorldSim.Presentation`:
  - `TerrainTexture`: Burst job painting 4×4 procedural pixels per tile.
  - `CameraRig`: clamped pan, pinch zoom anchored on the fingers, double-tap glide.
  - `GestureRecognizer`: pure C# touch state machine.
  - `WorldHud`: Canvas Scaler 1080×1920, safe area.
  - `WorldViewController`: ties it all together.
- `Tools/WorldPreview`: renders a world to PNG from the same Core sources (no Unity).
- CI: `ci/make_meta.py --check` fails the build if any Assets file lacks a committed `.meta`.

## Acceptance evidence
| Check | Status | Evidence |
|---|---|---|
| Stage 2: same seed gives the same hash across runs | **Verified (ARM64 .NET)** | `SameSeed_TwoRuns_IdenticalHash`, `TileOrder_DoesNotMatter` |
| Stage 2: hash identical across platforms | **Pending CI (x64) and device (IL2CPP+Burst)** | Golden hashes: `0x5EED` gives `0xB1999710960C6FA6`, `0xC0FFEE` gives `0x013F857F297A6D5B`, `0x1` gives `0x4828B520AF3E6CB6`. The app shows the hash for the default seed 0x5EED in its top bar. |
| Stage 3: pinch does not pan; release order never leaves it stuck | **Verified (unit tests)** | 8 `GestureRecognizerTests` |
| Stage 3: pinch, pan, tap, long-press manual test | **Pending device** | Owner to test on phone |
| All tests | **26/26 pass** | `dotnet test Tools/CoreTests` (C# 9, warnings as errors, overflow checking on) |

## Added on owner request (same build)
- **First-launch fiction notice** (plan A3): modal, must be accepted once, and can be reopened from the "Notice" button.
- **Map sizes Small 256 / Medium 512 / Large 1024** (plan A5), cycled by the "Size" button and used by the next "New world". Terrain is 4 px per tile up to 512 and 2 px per tile for 1024.
- **Feature sizes capped in absolute tiles** (continents 180, ridges 110, climate 130, warp 110/40, ocean border 48), so a large map gets more continents, ranges and lakes instead of the same world magnified. The caps sit above what a 256 map uses, so its golden hashes are unchanged. Reference timings (single-threaded .NET on the dev phone, no Burst): 256 = 0.2 s, 512 = 0.35 s, 1024 = 0.95 s.

## Found and fixed along the way
- `StableHash64.Add(uint)` relied on unchecked narrowing casts. It threw under overflow checking and was latent since Stage 1. The casts are now explicitly `unchecked`.

## Known deviations
See plan items 12–14: fixed-point gradient noise instead of OpenSimplex2, a CPU-painted terrain texture instead of the blend shader, and the Pixel Perfect Camera disabled during free zoom.
