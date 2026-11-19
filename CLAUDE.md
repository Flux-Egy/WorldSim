# CLAUDE.md: working on WorldSim

WorldSim is a mobile-first pixel-art world-simulation sandbox: Unity 6000.3 LTS, URP 2D, DOTS (Entities/Jobs/Burst), Android IL2CPP ARM64. The vision and all owner decisions are in `docs/GAME_VISION_PROMPT.md`, Beta scope in `docs/BETA_PLAN.md`, and design history in `docs/IMPLEMENTATION_PLAN.md`.

## Talking to the owner
- **Explain everything in Arabic** (Egyptian is fine). Code, commands, paths, logs and commit messages stay in English.
- The owner works **only from an Android phone** (Termux + a chroot Ubuntu, rooted). There is no PC. Give phone-friendly steps.
- **Reports are honest.** Say what was verified and how (tests, CI run id, device screenshot), and what was not verified. Never call something working until it has been checked.
- During CI builds, send a status update with the estimated time left **every ~5 minutes**.

## Hard rules
- **Never use the word "God"** anywhere: names, UI, docs, code or commits (the owner's religious reasons). Use "WorldSim", "powers", "world simulation sandbox". Beliefs in the game are fully **fictional creeds**; never use real religions, symbols or scriptures.
- **Originality** (`docs/ORIGINALITY.md`): learning from others is welcome, taking is not. All art is our own, and no ready-made asset packs are shipped. Never open or use anything decompiled or ripped from another game (WorldBox included), even if renamed, edited or "found online". Credit borrowed OSS code or techniques in `CREDITS.md`.
- **Secrets:** Unity credentials live only in GitHub secrets (`UNITY_EMAIL`, `UNITY_PASSWORD`; Codespaces secrets for the codespace). Never print, log or commit them. Don't add `UNITY_LICENSE`/`UNITY_SERIAL`. The repo is **public**: no personal data in commits or docs.
- **Never cancel a running Unity step in Actions.** A killed job can leak a Personal license seat. Cancelling before Unity starts is fine.
- **Verify before using.** Check package versions, action inputs and APIs against the primary source (registry, `action.yml`, release source) before relying on them. Pin versions.

## Where work happens (three workshops)
| Workshop | Use it for | Feedback time |
|---|---|---|
| **1. Phone** (default) | Everything in pure C# (`Core`, `Render`), world generation, simulation logic, art (Aseprite, Pillow), docs, CI config | seconds |
| **2. GitHub Actions + the owner's phone** | Every push: .NET tests, Unity EditMode tests, Android APK. Any change touching UnityEngine, ECS systems, Presentation, Editor scripts, packages or ProjectSettings must pass here **and be installed and checked on the phone** before it's reported as working | ~30 min |
| **3. Codespaces + Unity MCP** (`docs/CODESPACES.md`) | **Planned sessions** for Unity-side work where seeing the Editor helps: HUD/UI layout, ECS-to-rendering wiring, camera, sorting, lighting, feel tuning, Unity-only bugs | minutes (budgeted hours) |

How to choose:
- If it can be done and tested in pure C#, do it on the phone. Keep pushing logic into `Core`/`Render` so it stays testable here.
- Use Codespaces when the work is mostly Unity-side and needs many small try-and-look cycles, or when a Unity-only problem has failed twice in Actions. Plan the session's goal first, about 2-3 sessions of ~3 h a week, and report the hours used afterwards.
- The **phone is the final judge** of look, feel and performance. Editor screenshots (software rendering, no GPU) are not.
- UI, scenes and project settings are **built from code** (`WorldHud`, `WorldSimBootstrap`, `WorldSimCI.Bootstrap`), so CI can recreate them headlessly. Keep it that way: no hand-made scene or prefab edits that only the Editor can reproduce.
- In the codespace, Unity **always runs with real rendering** (Xvfb + software OpenGL, the `up.sh` default), because screenshots are the point of the workshop. `--nographics` is for diagnostics only. Look at every screenshot you rely on.
- Unity MCP is installed **only inside the codespace**. Never register it on the phone.

## Commands
```bash
# Phone: tests (.NET 8 SDK in /root/.dotnet; C# 9, warnings as errors, overflow checked)
dotnet test Tools/CoreTests
# Every file under Assets/ needs a committed .meta (CI checks this)
python3 ci/make_meta.py          # create missing .meta files
python3 ci/make_meta.py --check
# Render previews as PNG without Unity (worlds, crops, sprite and icon sheets)
dotnet run --project Tools/WorldPreview -- <seedHex> <size> <out.png> [cropX cropY tiles up]
dotnet run --project Tools/WorldPreview -- sprites|icons|creatures <out.png>
# CI
gh run list -L 3
gh run download <run-id> -n WorldSim-android-release
# Codespace only
Tools/Unity/up.sh           # license + Editor with rendering (Xvfb) + MCP bridge + idle guard
Tools/Unity/render-check.sh # proves real rendering works (first session, or when in doubt)
Tools/Unity/usage.sh        # disk + core-hours: report them to the owner after every session
Tools/Unity/down.sh         # ALWAYS before stopping: quit Unity, return the license seat
```
The device check (owner's rooted phone, from the chroot) is `pm install -r <apk>`, `am start -n com.fluxegy.worldsim/com.unity3d.player.UnityPlayerGameActivity`, then `screencap -p` and `logcat -s Unity`.

## Code layout and conventions
- `Assets/WorldSim/Runtime/Core`: **pure C#** (`noEngineReferences`), deterministic, integer and fixed-point only (Q16.16, SplitMix64, PCG32, FNV-1a hashes). Golden world hashes are in the tests; never change generation output silently.
- `Assets/WorldSim/Runtime/Render`: pure C# pixel painting (terrain, sprites, icons, `PngDecoder`), generic over struct interfaces so Burst and plain .NET share it.
- `Runtime/Simulation`: ECS (fixed 10 Hz `SimulationTickGroup`). `Runtime/Presentation`: views, camera, input, HUD (uGUI built in code). `Editor/`: CI bootstrap and build (`WorldSimCI`, `WorldSimBuild`).
- Tests: `Assets/WorldSim/Tests/EditMode` run in both `Tools/CoreTests` (.NET) and Unity (CI `unity-tests`). Add tests with every Core/Render change.
- CI: `.github/workflows/build.yml` and `GITHUB_ACTIONS.md`. The Unity version comes from `ProjectSettings/ProjectVersion.txt`. game-ci CLI is pinned to `v0.1.76`. When upgrading Unity, also update the image tag in `.devcontainer/devcontainer.json`.
- Commits: on `main` unless asked otherwise, with a clear English message.
