# GodSim

A mobile-first pixel-art god simulator built on Unity 6.3 LTS with DOTS. This is original work inspired by the genre and contains no WorldBox code or assets.

- Plan, section map and flagged requirements: [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- Stage reports: [docs/stage-reports/](docs/stage-reports/)
- CI and Unity license setup: [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)

## Core tests without Unity

`GodSim.Core` (PRNGs, seeds, hashing) is plain C#, and its tests run on any machine with the .NET 8 SDK:

```
dotnet test Tools/CoreTests
```

## First open (Stage 1)

1. Install **Unity 6000.3.28f1** with Android Build Support (SDK, NDK, OpenJDK).
2. Open this folder in Unity Hub. If the Package Manager reports a URP or ugui version mismatch, accept the editor's bundled version and tell me which version it chose.
3. When the Input System asks to enable the new backend, choose **Yes**. Then check that **Project Settings > Player > Active Input Handling** is set to **Input System Package (New)**, not *Both*.
4. Create the URP asset: **Assets > Create > Rendering > URP Asset (with 2D Renderer)**. Assign it in **Project Settings > Graphics** and in **Quality** for every level.
5. Switch the platform to Android: **File > Build Profiles**.
6. Run **GodSim > Setup > Apply Android Project Settings**, then **GodSim > Setup > Create Boot Scene**.
7. Run the tests: **Window > General > Test Runner > EditMode > Run All**.
8. Build: **GodSim > Build > Android Release (IL2CPP ARM64)**.

To build from the command line:

```
Unity -batchmode -quit -projectPath . -buildTarget Android \
      -executeMethod GodSim.EditorTools.GodSimBuild.BuildReleaseCI -logFile build.log
```

The command exits with code 0 if the build succeeds and 1 if it fails.
