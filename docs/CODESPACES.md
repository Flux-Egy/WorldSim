# Unity workshop in GitHub Codespaces

The owner works from an Android phone only, so the Unity Editor can't run locally. This Codespace runs a **headless Unity Editor** (no screen; software OpenGL on a virtual display) with **Unity MCP**, so Claude can drive the Editor and see screenshots. It is for **planned work sessions**, not every change. See CLAUDE.md, "Where work happens".

Files: `.devcontainer/` (image, setup) and `Tools/Unity/up.sh` / `down.sh` (start and stop Unity, activate and return the license).

## Budget
- Machine: 4 cores / 16 GB RAM (`hostRequirements`). On the Free plan, 120 core-hours a month is **about 30 hours** on this machine. Storage: 15 GB-month free.
- Beyond that, GitHub bills per hour and per GB. Check the current prices at github.com/settings/billing; the owner is OK with roughly 10 USD a month if the sessions are worth it.
- Rule: about 2-3 sessions a week, about 3 hours each. Claude reports the hours used at the end of every session.
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
Tools/Unity/down.sh            # ALWAYS: quits Unity and returns the license seat
exit
gh codespace stop -c <name>
```
`up.sh --nographics` starts Unity without any rendering. It's faster, but there are no screenshots.

## License seats
A Personal Unity account has very few seats. The Actions jobs take one and return it per run, and this codespace takes one while Unity is up. `down.sh` returns it. If a codespace stops without `down.sh`, the seat may stay taken. `on-start.sh` keeps one stable machine id per codespace, so the next `up.sh` reuses that seat instead of taking another. If Actions fails with "no seat available", run `up.sh` then `down.sh` in the codespace, or release the activation at id.unity.com.

## What the codespace changes locally (never committed)
- `Packages/manifest.json` gets `com.coplaydev.unity-mcp` (pinned `v10.3.0`). `setup.sh` marks `manifest.json` and `packages-lock.json` as *skip-worktree*, so they aren't committed from here. **Change packages from the phone, not here.**
- Unity MCP is registered with Claude Code **inside the codespace only**. It is never registered on the phone.

## First-session spike (time box: 2 hours)
Goal: prove the setup before relying on it. Check each item and write the result into this file:
- [ ] The image matches `ProjectVersion.txt` (`setup.sh` prints this).
- [ ] `up.sh` activates the license.
- [ ] The Editor imports the project and the MCP bridge reports.
- [ ] `claude` lists the UnityMCP tools and can read the console.
- [ ] Enter Play Mode on `Boot`, and a Game view screenshot shows the world (software OpenGL).
- [ ] Run EditMode tests through MCP.
- [ ] `down.sh` returns the license, and the next Actions run still activates.
- [ ] Record the hours and storage used.

If rendering fails, record the error and fall back to `--nographics` (console, tests and scene/asset queries still work). Then decide with the owner whether the workshop is still worth it.
