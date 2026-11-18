# Stage 1 Report: Project skeleton

**Exit criterion:** "Project builds on Android ARM64". **PASSED on 2026-11-17** in CI run [44200906494](https://github.com/Flux-Egy/WorldSim/actions/runs/44200906494) (commit `a80952b`).

## What was built
- `ProjectSettings/ProjectVersion.txt` pins 6000.3.28f1. `Packages/manifest.json` lists Entities, Burst, Collections, Mathematics, Input System, URP, ugui, Adaptive Performance (+ Android provider) and Test Framework.
- Seven asmdefs with the dependency direction from the plan: Core ← Simulation ← Modding ← Presentation. ModAPI references neither Simulation nor Entities.
- `WorldSim.Core`: SplitMix64, PCG32, `WorldSeed` with stable `SeedStream` sub-seeds, and the `StableHash64` (FNV-1a) world hash. All are integer-only and Burst-callable.
- `WorldSim.Simulation`: `SimulationTickGroup` with a fixed 10 Hz rate that can be changed at runtime, plus the `SimulationClock` singleton and its Burst system.
- `WorldSim.Presentation`: `WorldSimBootstrap` (frame pacing, logs the build profile, errors if legacy input is enabled).
- `WorldSim.Editor`: the Android settings menu, the Boot scene generator (orthographic camera + Pixel Perfect Camera + Input System UI module), and Release/Modder build profiles that restore PlayerSettings afterwards and have command-line entry points.
- EditMode tests: known-answer tests for SplitMix64, PCG32, `WorldSeed.Derive` and FNV-1a.

## Acceptance evidence
| Check | Status | Evidence |
|---|---|---|
| Package versions exist | Verified | Queried packages.unity.com on 2026-11-17. URP 17.3.0 and ugui 2.0.0 are **not** verifiable there (core packages). |
| Test vectors correct | Verified | Independent Python implementations reproduce the reference outputs (PCG32 demo `0xA15C02B7…`, SplitMix64(0) `0xE220A8397B1DCDAF…`, FNV-1a("a") `0xAF63DC4C8601EC8C`). |
| WorldSim.Core compiles + tests pass (outside Unity) | **Verified 2026-11-17** | `dotnet test Tools/CoreTests`, .NET SDK 8.0.134 on ARM64: **6/6 passed**. Compiled as C# 9 with warnings-as-errors and overflow checking on. |
| All 7 WorldSim assemblies compile in Unity 6000.3.28f1 | **Verified** | CI run 44200906494. The Entities source generators and ILPP ran on Simulation/Presentation/Modding. |
| CI bootstrap (headless setup) | **Verified** | `activeInputHandler 0 -> 1`, URP 2D asset created (mirrors URP 17.3's Renderer2DMenus), Boot scene, Android settings, `[WorldSim CI] Bootstrap OK.` |
| Android ARM64 build | **Verified** | `Build Release: Succeeded`, 0 errors, 0 warnings, build time 13m31s. APK 35.0 MB, ABI `arm64-v8a` only, `libil2cpp.so` present, 0 managed DLLs (IL2CPP), minSdk 25, targetSdk 36, v2-signed with the Android Debug certificate. |
| Unity licensing from a phone-only setup | **Verified** | game-ci CLI `personal` method: `ASSIGN_SEAT` at start, `Successfully returned the entitlement license` at end of every Unity step. |
| EditMode tests inside Unity | **Not run** | unity-test-runner v4.3.2 cannot activate Personal from credentials. The same tests pass in plain .NET (x64 CI and ARM64 local). |
| App runs on a device | **Not yet tested** | First device install pending. |

## Known deviations
- 2026-11-18: renamed the project at the owner's request so the product and code contain no religious terms. Code is `WorldSim`, the app is "WorldSim" (`com.fluxegy.worldsim`), and the repo is `Flux-Egy/WorldSim`. File GUIDs were preserved (`.meta` files moved with their assets). Confirmation build 44269636318 passed just before the rename.
- The first APK (run 44200906494) has Unity's default identity `com.DefaultCompany.workspace` / "workspace". Fixed in the next commit: `com.fluxegy.worldsim` / "WorldSim".
- The Modder profile uses IL2CPP ARM64 (not Mono) until Decision A is made, because Mono on Android is, to my knowledge, ARMv7-only.
- Active Input Handling and URP asset creation are set headlessly by `WorldSimCI.Bootstrap` (verified in CI). The build still refuses to run if either is wrong.

## Open questions before Stage 2
- **A. Mod loader** (plan item 1): HybridCLR + first-party loader (recommended), or the literal §18.1 approach (Mono ARMv7 Modder build, data-only mods for players)?
- **B.** Can you run Unity 6.3 somewhere (a desktop or a CI runner) and send back the console log, Test Runner results and build log after step 8 of the README?
- **C.** Should I install a .NET SDK here (~0.7 GB of the 3 GB free) so I can compile and unit-test the `WorldSim.Core` code myself between your Unity runs?
