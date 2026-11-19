# Unity workshop in GitHub Codespaces

The owner works from an Android phone only, so the Unity Editor can't run locally. This Codespace runs the Unity Editor **with real rendering** on an Xvfb virtual display (software OpenGL, since there is no GPU) plus **Unity MCP**, so Claude can drive the Editor and **see screenshots of the game**. Seeing the game is the main reason this workshop exists, so rendering is a requirement, not an extra. It is for **planned work sessions**, not every change. See CLAUDE.md, "Where work happens".

Files: `.devcontainer/` (image, setup), `Tools/Unity/up.sh` / `down.sh` (start and stop Unity with rendering, activate and return the license) and `Tools/Unity/render-check.sh` (proves rendering works, without MCP).

## Budget
- Machine: 4 cores / 16 GB RAM (`hostRequirements`). On the Free plan, 120 core-hours a month is **about 30 hours** on this machine. Storage: 15 GB-month free.
- Beyond that, GitHub bills per hour and per GB. Check the current prices at github.com/settings/billing; the owner is OK with roughly 10 USD a month if the sessions are worth it.
- Rule: about 2-3 sessions a week, about 3 hours each. Claude reports the hours and storage used at the end of every session (`Tools/Unity/usage.sh`).
- Set the **idle timeout** to 30 minutes (github.com/settings/codespaces) so a forgotten codespace stops by itself. Run `Tools/Unity/down.sh` before it does (see "License seats").

## One-time setup (owner)
1. **Codespaces secrets.** Go to github.com/settings/codespaces > *Secrets* > *New secret*. Add `UNITY_EMAIL` and `UNITY_PASSWORD` (same values as the Actions secrets) and give the `Flux-Egy/WorldSim` repository access to both.
2. **Create the codespace** (from Termux): `gh codespace create -R Flux-Egy/WorldSim -b main`, then pick the **4-core** machine when asked. `hostRequirements` hides smaller machines. Or use the website: repo > *Code* > *Codespaces* > *+*. The first creation pulls a ~5 GB Unity image and runs `.devcontainer/setup.sh`, which takes 10-15 min.
3. **Open a shell** from Termux with `gh codespace ssh -c <name>`, then run `claude` once and log in (it prints a link to open on the phone).

## Every session
```bash
gh codespace ssh -c <name>     # from Termux
cd /workspaces/WorldSim
git pull
Tools/Unity/up.sh              # license + headless Editor (first start imports the project: 10-20 min)
claude                         # Unity MCP tools are available
# ... work, commit, push (Actions builds the APK as usual) ...
Tools/Unity/usage.sh           # disk and core-hours so far (report them to the owner)
Tools/Unity/down.sh            # ALWAYS: quits Unity and returns the license seat
exit
gh codespace stop -c <name>
```
`up.sh` always renders by default. `up.sh --nographics` exists **for diagnostics only**: it turns rendering off completely, so screenshots will not work.

## License seats (and sudden stops)
A Personal Unity account has very few seats. The Actions jobs take one and return it per run, and this codespace takes one while Unity is up. A seat that is never returned can make Actions fail with "no seat available".

**What happens when:**
| Situation | What happens to the seat |
|---|---|
| You run `down.sh` | Returned immediately. The normal way. |
| The phone loses its connection, or you close Termux | The codespace keeps running. After **15 min** with no open terminal, `idle-guard.sh` (started by `up.sh`) runs `down.sh` and returns the seat, before the codespace's own 30-min idle stop. |
| The codespace stops before the guard acts (manual stop, idle timeout set below 15 min, crash) | Nothing runs on stop, so the seat stays active. **The next time the codespace starts**, `on-start.sh` sees it and returns it automatically in the background (log: `/workspaces/.unity-state/auto-return.log`). It can do this because the codespace keeps the same machine id. |
| The codespace is **deleted** while the seat is active | Nothing in the codespace can return it any more. See the manual steps below. |

Keep the codespace idle timeout at **30 min** (github.com/settings/codespaces), above the guard's 15 min.

**If a seat is stuck (manual steps for the owner):**
1. Start the codespace again: `gh codespace ssh -c <name>` starts it if it is stopped. The automatic return runs. Check it with `tail /workspaces/.unity-state/auto-return.log`, or run `Tools/Unity/down.sh` yourself.
2. If the codespace was deleted: sign in at id.unity.com and look for the account's activations or seats to release it. *The exact page is to be confirmed during the spike.* If it can't be released there, Unity support can release it.
3. Re-run the failed Actions job.

## What the codespace changes locally (never committed)
- `Packages/manifest.json` gets `com.coplaydev.unity-mcp` (pinned `v10.3.0`). `setup.sh` marks `manifest.json` and `packages-lock.json` as *skip-worktree*, so they aren't committed from here. **Change packages from the phone, not here.**
- Unity MCP is registered with Claude Code **inside the codespace only**. It is never registered on the phone.

## First-session spike (time box: 2 hours)
Goal: prove the setup before relying on it. **The spike passes only if all MUST items pass.** Write the results (with the screenshots' paths) into this file.

**MUST (any failure means the spike fails):**
- [ ] The image matches `ProjectVersion.txt` (`setup.sh` prints this).
- [ ] `up.sh` activates the license.
- [ ] `Tools/Unity/render-check.sh` prints `RENDER_CHECK PASS` with a real OpenGL device (not Null), and `render-check.png` shows the lit cube on a blue background. Claude opens the PNG and looks at it.
- [ ] The WorldSim Editor starts **with rendering** (`up.sh` reports a graphics device, not Null), the project imports, and the MCP bridge reports.
- [ ] `claude` lists the UnityMCP tools and can read the Editor console.
- [ ] **A real game screenshot through MCP:** enter Play Mode on `Boot`, take a Game view screenshot through Unity MCP, and the image shows the generated world (terrain, not a blank or black frame). Claude opens the image and describes what it shows.
- [ ] `down.sh` returns the license, and the next Actions run still activates.
- [ ] **Sudden-stop test:** run `up.sh`, then stop the codespace from the phone *without* `down.sh` (`gh codespace stop -c <name>`). Start it again and confirm `auto-return.log` shows the license returned. Then confirm the next Actions run still activates.
- [ ] **Idle-guard test:** run `up.sh`, close every terminal, wait 16 min. `sessions.log` shows the license returned by the guard, and the codespace is still running.
- [ ] **Storage after setup:** `Tools/Unity/usage.sh` after the first full import (Library included). Record the disk used against the **15 GB-month** limit and what takes the space (image, Library, caches). If it's over about 12 GB, plan how to cut it before relying on the workshop.
- [ ] **Core-hours used by the spike:** from `usage.sh` (hours since start × 4 cores), and the official number from github.com/settings/billing the next day. Compare with the 120 core-hours a month (about 30 h on 4 cores).

**SHOULD (record, but not blocking):**
- [ ] Run EditMode tests through MCP.
- [ ] A screenshot that includes the HUD. Screen-space overlay UI may not appear in camera captures; record what does.
- [ ] Time per screenshot and Editor responsiveness under software rendering.

**If rendering fails:** the spike fails. Don't settle for `--nographics`. Record the exact error (`render-check.log`, `editor.log`) and try, in order: `-force-vulkan` instead of `-force-glcore`, a larger Xvfb screen or depth, and missing Mesa packages. If none of these work within the time box, stop and decide with the owner (for example, a cloud machine with a GPU, which costs more) before spending more hours.
