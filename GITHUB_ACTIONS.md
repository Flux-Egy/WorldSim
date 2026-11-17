# GitHub Actions setup

The Unity Editor can't run on the ARM development machine, so GitHub Actions is the build server. The workflow is `.github/workflows/build.yml`.

| Job | Needs Unity credentials | What it does |
|---|---|---|
| `core-tests` | No | Compiles `GodSim.Core` with plain .NET 8 and runs the determinism tests |
| `license-check` | No | Checks whether `UNITY_EMAIL` and `UNITY_PASSWORD` exist. If not, the Unity job is **skipped** rather than failed |
| `build-android` | Yes | Pass 1 sets up the project headlessly. Pass 2 builds the Release APK (IL2CPP, ARM64, stripping High) |

## 1. Unity license: phone only, no license file

**No PC, no Unity Hub and no `.ulf` / `.alf` file are needed.**

Unity has removed manual (`.alf` → `.ulf`) activation for Personal licenses. game-ci's docs say: *"Unity no longer supports manual activation with `.alf` files, so the old personal license flow stopped working"*, and `game-ci/unity-request-activation-file` is marked "no longer maintained and should not be used". Instead, `game-ci/unity-builder` v6 runs the game-ci CLI, whose **`personal` licensing method** signs in with your Unity account. It requests a Personal seat from Unity's licensing service at the start of each Unity step and returns it at the end. (Source: `game-ci/cli`, `dist/platforms/ubuntu/steps/activate.sh` and `licensing_method.sh`.)

The CLI picks this method automatically when `UNITY_EMAIL` and `UNITY_PASSWORD` are set and **`UNITY_LICENSE` and `UNITY_SERIAL` are not**.

### 1a. Prepare the Unity account (phone browser)

1. Go to **https://id.unity.com**. Sign in, or create an account.
   - A **separate account just for CI** is recommended; game-ci's own error text says so too.
   - It must have a real **password**. An account you sign into with Google, Apple or Facebook has no password, so headless sign-in can't work.
2. **Turn off two-factor authentication** for that account. A CI runner can't answer a 2FA code or a "new device" email.
3. Make sure the account has a Personal license available. Unity normally grants this to any account that accepts the Personal terms. If the first run says "no available Personal seats", see Troubleshooting.

### 1b. Add the secrets

**Option A: from Termux.** This is the easiest: values are typed at a hidden prompt, so they don't end up in your shell history.

```bash
gh secret set UNITY_EMAIL    -R Flux-Egy/WorldSim-God   # type the email, press Enter
gh secret set UNITY_PASSWORD -R Flux-Egy/WorldSim-God   # type the password, press Enter
gh secret list -R Flux-Egy/WorldSim-God                 # should list both (values are never shown)
```

**Option B: from the phone browser.** Open https://github.com/Flux-Egy/WorldSim-God/settings/secrets/actions, then tap **New repository secret** twice:

| Name | Secret |
|---|---|
| `UNITY_EMAIL` | The Unity account's email |
| `UNITY_PASSWORD` | That account's password |

**Do not create `UNITY_LICENSE` or `UNITY_SERIAL`.** Either one switches the CLI away from personal mode.

### 1c. Start the build

```bash
gh workflow run build.yml -R Flux-Egy/WorldSim-God --ref main
gh run watch -R Flux-Egy/WorldSim-God        # pick the run; Ctrl+C stops watching, not the run
```

Or in the browser: **Actions > Build > Run workflow**.

### Troubleshooting licensing

| Log says | Meaning / fix |
|---|---|
| `Unity rejected the account credentials, or wants a second factor` | Wrong email or password, 2FA still on, or Unity emailed a "new device" confirmation (check the account's inbox and approve it). Hosted runners change IP every run. |
| `Unity reports no available Personal seats` | A previous run leaked its seat (killed job or crash), or two jobs ran at once. Release the seat at id.unity.com and re-run. The workflow never cancels a running build, to avoid this. |
| `UNITY_EMAIL / UNITY_PASSWORD secrets not set` (warning) | The secrets are missing or misspelled. |

### Paid (Plus or Pro) license, later

Add `UNITY_SERIAL` as well. The CLI then uses the serial method instead of personal.

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

- **Unity EditMode tests in CI.** `game-ci/unity-test-runner` v4.3.2 can't activate a Personal license from email and password alone; its activation script only accepts a serial, a license file or a license server. The current EditMode tests are the same Core tests `core-tests` already runs. Unity-only tests (Stage 2) will run through a unity-builder `buildMethod` instead.

- **Release signing.** In v6, unity-builder's `androidKeystore*` inputs are passed to the new game-ci CLI. I couldn't confirm how they reach a *custom* `buildMethod`, so the workflow doesn't use them yet. Until then the APK is debug-signed, which is fine for sideloading and testing but not for the Play Store. This gets added and verified before any store release.
- **Modder build.** It waits on Decision A (the mod loader) in `docs/IMPLEMENTATION_PLAN.md`. `GodSimBuild.BuildModderCI` already exists. Adding it is one more builder step.
- **`cliVersion`.** This is left at the default (`latest`). If a game-ci CLI update ever breaks a build, pin it on both `unity-builder` steps.
