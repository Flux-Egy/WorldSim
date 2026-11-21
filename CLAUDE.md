# CLAUDE.md: working on WorldSim

WorldSim is a mobile-first pixel-art world-simulation sandbox: Unity 6000.3 LTS, URP 2D, DOTS (Entities/Jobs/Burst), Android IL2CPP ARM64. Current plan and progress: `PROGRESS.md` (Playable Alpha). All owner decisions: `docs/DECISIONS.md`. Project status snapshot: `docs/STATUS_REPORT.md` (branch `status/report`). Older vision/plan docs are in `docs/archive/` (history only).

## Talking to the owner
- **Explain everything in Arabic** (Egyptian is fine). Code, commands, paths, logs and commit messages stay in English.
- The owner works **only from an Android phone** (Termux + a chroot Ubuntu, rooted). There is no PC. Give phone-friendly steps.
- **Reports are honest.** Say what was verified and how (tests, CI run id, device screenshot), and what was not verified. Never call something working until it has been checked.
- During CI builds, send a status update with the estimated time left **every ~5 minutes**.

## Hard rules
- **Never use the word "God"** anywhere: names, UI, docs, code or commits (the owner's religious reasons). Use "WorldSim", "powers", "world simulation sandbox". Beliefs in the game are fully **fictional creeds**; never use real religions, symbols or scriptures.
  - **Exception (approved by the owner, 2026-11-20):** the supernatural beings **jinn, afreet, marid and demon**, and the **possession** mechanic, may use those names in art, data, code and UI. Nothing else changes: no real religions, symbols, scriptures or prophets, and never the word "God".
- **Originality** (`docs/ORIGINALITY.md`, updated 2026-11-21): style, ideas and mechanics from any game (WorldBox included) may be imitated. Ready-made assets/code/audio are allowed **only** with a licence that permits it (CC0, CC-BY, MIT, OGA-BY...): check the licence first, keep its text in the repo, add a row to `CREDITS.md` (name, author, source, link, licence, where used), show credits in game, never claim it as ours. Never rip or decompile any commercial game (WorldBox included) and no unpaid paid assets; a credit is not a permission. Our pack (WorldSimArt) stays the base. Reference images/videos stay outside the repo.
- **Secrets:** Unity credentials live only in GitHub secrets (`UNITY_EMAIL`, `UNITY_PASSWORD`; Codespaces secrets for the codespace). Never print, log or commit them. Don't add `UNITY_LICENSE`/`UNITY_SERIAL`. The repo is **public**: no personal data in commits or docs.
- **Never cancel a running Unity step in Actions.** A killed job can leak a Personal license seat. Cancelling before Unity starts is fine.
- **Verify before using.** Check package versions, action inputs and APIs against the primary source (registry, `action.yml`, release source) before relying on them. Pin versions.

## How to work (owner, 2026-11-21)
- Work autonomously; stop for the owner only at the review points (⛳) in `PROGRESS.md`.
- Small, frequent commits, pushed often. Nothing stays uncommitted at the end of a session.
- Reports to the owner: Egyptian Arabic, short: ✔️ done / ❌ not yet / ⏳ in progress, **with pictures from the phone itself**, not from the preview tool (preview pictures only for design choices, labelled as such).
- Before sending any picture, look at it as a player. If it looks flat, washed out or unreadable, fix it first.
- Every decision goes into `docs/DECISIONS.md`.
- No merge into `main` without the owner's approval.
- Before using the owner's phone for a capture (install, launch, screenshot), ask the owner to leave it untouched and wait for "تم"; abort if another app is in front, and never keep a screenshot of anything but the game.

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
- **Unity seems stuck in the codespace:** don't kill it straight away. First run `Tools/Unity/diagnose.sh`, which screenshots the Xvfb display (a hidden dialog such as Safe Mode, a project upgrade or package errors), checks the log age and "Loading completed", and shows CPU and thread states. A quiet log after "Loading completed" is normal: the Editor is waiting for commands. **Time-box: 30 min.** If it isn't solved by then, run `Tools/Unity/down.sh` (return the seat), stop the codespace (`gh codespace stop`) to save hours, and report what you found to the owner.
- Anything started from a shell, tmux or `postStartCommand` that must keep running needs `setsid` (otherwise it dies with that session). `postStartCommand` kills even `setsid` background jobs, so do that work in the foreground.

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
# New terrain look (rebuild): the real art pack, far + near zoom, optional near crops (cellX cellY cells)
dotnet run -c Release --project Tools/WorldPreview -- pack <seedHex> <size> <outDir> [cx cy n ...]
# CI
gh run list -L 3
gh run download <run-id> -n WorldSim-android-release
# Codespace only
Tools/Unity/up.sh           # license + Editor with rendering (Xvfb) + MCP bridge + idle guard
Tools/Unity/remote.sh       # up.sh + claude --remote-control in tmux (owner drives from the Claude app)
Tools/Unity/render-check.sh # proves real rendering works (first session, or when in doubt)
Tools/Unity/usage.sh        # disk + core-hours: report them to the owner after every session
Tools/Unity/diagnose.sh     # before killing a stuck Editor: display screenshot, log age, CPU/threads
Tools/Unity/down.sh         # ALWAYS before stopping: quit Unity, return the license seat
```
The device check (owner's rooted phone, from the chroot) is `pm install -r <apk>`, `am start -n com.fluxegy.worldsim/com.unity3d.player.UnityPlayerGameActivity`, then `screencap -p` and `logcat -s Unity`.

## Code layout and conventions
- `Assets/WorldSim/Runtime/Core`: **pure C#** (`noEngineReferences`), deterministic, integer and fixed-point only (Q16.16, SplitMix64, PCG32, FNV-1a hashes). Golden world hashes are in the tests; never change generation output silently.
- `Assets/WorldSim/Runtime/Render`: pure C# pixel painting (terrain, sprites, icons, `PngDecoder`), generic over struct interfaces so Burst and plain .NET share it.
- `Runtime/Simulation`: ECS (fixed 10 Hz `SimulationTickGroup`). `Runtime/Presentation`: views, camera, input, HUD (uGUI built in code). `Editor/`: CI bootstrap and build (`WorldSimCI`, `WorldSimBuild`).
- Tests: `Assets/WorldSim/Tests/EditMode` run in both `Tools/CoreTests` (.NET) and Unity (CI `unity-tests`). Add tests with every Core/Render change.
- CI: `.github/workflows/build.yml` and `GITHUB_ACTIONS.md`. The Unity version comes from `ProjectSettings/ProjectVersion.txt`. game-ci CLI is pinned to `v0.1.76`. The codespace installs the Editor from `ProjectVersion.txt` too (`Tools/Unity/install-editor.sh`), so upgrading Unity there is enough.
- Commits: on the working branch (now `rebuild/pack-foundation`), small and often, with a clear English message; `main` only after the owner approves a merge.
