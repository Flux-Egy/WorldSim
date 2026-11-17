# Stage 1 Report: Project skeleton

**Exit criterion:** "Project builds on Android ARM64". **Not yet verified.** It needs the Unity Editor, which can't run on this machine.

## What was built
- `ProjectSettings/ProjectVersion.txt` pins 6000.3.28f1. `Packages/manifest.json` lists Entities, Burst, Collections, Mathematics, Input System, URP, ugui, Adaptive Performance (+ Android provider) and Test Framework.
- Seven asmdefs with the dependency direction from the plan: Core ← Simulation ← Modding ← Presentation. ModAPI references neither Simulation nor Entities.
- `GodSim.Core`: SplitMix64, PCG32, `WorldSeed` with stable `SeedStream` sub-seeds, and the `StableHash64` (FNV-1a) world hash. All are integer-only and Burst-callable.
- `GodSim.Simulation`: `SimulationTickGroup` with a fixed 10 Hz rate that can be changed at runtime, plus the `SimulationClock` singleton and its Burst system.
- `GodSim.Presentation`: `GodSimBootstrap` (frame pacing, logs the build profile, errors if legacy input is enabled).
- `GodSim.Editor`: the Android settings menu, the Boot scene generator (orthographic camera + Pixel Perfect Camera + Input System UI module), and Release/Modder build profiles that restore PlayerSettings afterwards and have command-line entry points.
- EditMode tests: known-answer tests for SplitMix64, PCG32, `WorldSeed.Derive` and FNV-1a.

## Acceptance evidence
| Check | Status | Evidence |
|---|---|---|
| Package versions exist | Verified | Queried packages.unity.com on 2026-11-17. URP 17.3.0 and ugui 2.0.0 are **not** verifiable there (core packages). |
| Test vectors correct | Verified | Independent Python implementations reproduce the reference outputs (PCG32 demo `0xA15C02B7…`, SplitMix64(0) `0xE220A8397B1DCDAF…`, FNV-1a("a") `0xAF63DC4C8601EC8C`). |
| GodSim.Core compiles + tests pass (outside Unity) | **Verified 2026-11-17** | `dotnet test Tools/CoreTests`, .NET SDK 8.0.134 on ARM64: **6/6 passed**. Compiled as C# 9 with warnings-as-errors and overflow checking on. |
| Unity-dependent C# compiles (Simulation, Presentation, Editor) | **Not run** | Needs Unity. CI job `build-android` covers it. |
| EditMode tests pass | **Not run** | Needs Unity. |
| Android ARM64 build | **Not run** | Needs Unity + Android modules. |

## Known deviations
- The Modder profile uses IL2CPP ARM64 (not Mono) until Decision A is made, because Mono on Android is, to my knowledge, ARMv7-only.
- Active Input Handling and URP asset creation are manual steps. I'm not confident there is a stable public scripting API for them, so the build fails with a clear message when they are wrong instead of setting them silently.

## Open questions before Stage 2
- **A. Mod loader** (plan item 1): HybridCLR + first-party loader (recommended), or the literal §18.1 approach (Mono ARMv7 Modder build, data-only mods for players)?
- **B.** Can you run Unity 6.3 somewhere (a desktop or a CI runner) and send back the console log, Test Runner results and build log after step 8 of the README?
- **C.** Should I install a .NET SDK here (~0.7 GB of the 3 GB free) so I can compile and unit-test the `GodSim.Core` code myself between your Unity runs?
