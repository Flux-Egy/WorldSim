# GitHub Actions setup

The Unity Editor can't run on the ARM development machine, so GitHub Actions is the build server. The workflow is `.github/workflows/build.yml`.

| Job | Needs a Unity license | What it does |
|---|---|---|
| `core-tests` | No | Compiles `GodSim.Core` with plain .NET 8 and runs the determinism tests |
| `license-check` | No | Checks whether a Unity license secret exists. If none does, the Unity jobs are **skipped** rather than failed |
| `unity-editmode-tests` | Yes | Runs the EditMode tests inside Unity 6000.3.28f1 |
| `build-android` | Yes | Pass 1 sets up the project headlessly. Pass 2 builds the Release APK (IL2CPP, ARM64, stripping High) |

## 1. Unity license secrets

This follows game-ci's own activation guide (game.ci, "Activation"). The variable names below are the ones `game-ci/unity-builder` v6 reads.

### Personal license (free)

You need **any desktop computer** (Windows, macOS or Linux x64) **once**, only to create the license file. Licenses aren't tied to an OS, so a file made on Windows works on the Ubuntu CI runners.

1. Install **Unity Hub** and sign in with the Unity account CI should use.
2. Go to **Unity Hub > Preferences > Licenses > Add > Get a free personal license**. Click **Add** even if a license already shows; that is what writes the file.
3. Find the license file:
   - Windows: `C:\ProgramData\Unity\Unity_lic.ulf`
   - macOS: `/Library/Application Support/Unity/Unity_lic.ulf`
   - Linux: `~/.local/share/unity3d/Unity/Unity_lic.ulf`
4. In GitHub, open **your repo > Settings > Secrets and variables > Actions > New repository secret** and add:

   | Secret | Value |
   |---|---|
   | `UNITY_LICENSE` | The **entire contents** of `Unity_lic.ulf` (XML text) |
   | `UNITY_EMAIL` | Your Unity account email |
   | `UNITY_PASSWORD` | Your Unity account password |

5. **Sign out of Unity Hub** on that computer. For Personal licenses, Hub 3.7+ has no "Return license" button; signing out is how the seat is returned, so the desktop doesn't keep it.

### Plus or Pro license

Add `UNITY_SERIAL` (your serial key), `UNITY_EMAIL` and `UNITY_PASSWORD`. Return the license in Unity Hub on your desktop first, so you don't use two seats at once.

Secrets are masked in logs and are never passed to workflows triggered from forks.

## 2. First run (bootstrap)

The repository doesn't yet contain the files Unity generates, such as `ProjectSettings/*.asset`, `.meta` files, the Boot scene and the URP asset, because they can't be written by hand reliably. Until they're committed:

1. Pass 1 (`GodSim.EditorTools.GodSimCI.Bootstrap`) generates them in the runner's workspace on every run.
2. The run uploads them as the **`project-bootstrap-files`** artifact.
3. Download that artifact once, copy its contents over the repo root and commit:
   ```
   gh run download <run-id> -n project-bootstrap-files -D .
   git add ProjectSettings Packages/packages-lock.json Assets
   git commit -m "Commit Unity-generated project files from CI bootstrap"
   ```
   After this, the `.meta` GUIDs stay stable between builds. Pass 1 keeps running, but it only fixes settings that drift.

**Check on the first run:** read the "Unity bootstrap" step log for `[GodSim CI] Bootstrap OK.` Two pieces of `GodSimCI.cs` couldn't be tested without an Editor:
- the serialized setting name `activeInputHandler`. The step fails with a clear message if it's wrong.
- creating the 2D renderer from a script. If sprites render **magenta** on the device, create the URP asset once on a desktop (**Assets > Create > Rendering > URP Asset (with 2D Renderer)**) and commit it; pass 1 then leaves it alone.

## 3. Getting the APK

Open **Actions > Build > (run) > Artifacts > `GodSim-android-release`**, or run:
```
gh run download <run-id> -n GodSim-android-release
adb install -r GodSim-release.apk
```
The APK is debug-signed (see "Not yet covered").

## 4. Costs and limits

- **Public repos:** standard GitHub-hosted runners are free. **Private repos:** they use your plan's Actions minutes (the Free plan includes 2,000 Linux minutes a month). Expect the first Android build to be slow: it pulls the Unity Android image and imports packages, then later runs reuse the `Library` cache.
- The disk-cleanup step is there because the Unity Android image plus the `Library` folder can fill a hosted runner's disk.

## 5. Not yet covered (deliberately)

- **Release signing.** In v6, unity-builder's `androidKeystore*` inputs are passed to the new game-ci CLI. I couldn't confirm how they reach a *custom* `buildMethod`, so the workflow doesn't use them yet. Until then the APK is debug-signed, which is fine for sideloading and testing but not for the Play Store. This gets added and verified before any store release.
- **Modder build.** It waits on Decision A (the mod loader) in `docs/IMPLEMENTATION_PLAN.md`. `GodSimBuild.BuildModderCI` already exists. Adding it is one more builder step.
- **`cliVersion`.** This is left at the default (`latest`). If a game-ci CLI update ever breaks a build, pin it on both `unity-builder` steps.
