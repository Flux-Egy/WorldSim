# Credits

WorldSim's base art, audio and code are made for this project. Licensed third-party assets, code and audio are allowed under [docs/ORIGINALITY.md](docs/ORIGINALITY.md); every one is listed below (name, author, source, link, licence, where used) and shown in the game's credits.

## Third-party assets
| Name | Author | Source / link | Licence | Used in WorldSim |
|---|---|---|---|---|
| (none yet) | | | | |

## Engine and libraries
- Unity 6.3 LTS and Unity packages (URP, Entities, Burst, Collections, Mathematics, Input System, Adaptive Performance), under the Unity Companion License / Unity Terms of Service.
- Build pipeline: [game-ci](https://game.ci) unity-builder (MIT).

## Tools used in development (not shipped)
- [Unity MCP](https://github.com/CoplayDev/unity-mcp) (MIT): Unity package added inside the Codespace only, never committed.
- [Aseprite](https://www.aseprite.org) (built from source for personal use) and [aseprite-mcp](https://github.com/diivi/aseprite-mcp) (MIT): art tools on the owner's phone.

## Borrowed code and techniques
Every open-source snippet or technique we adapt is listed here with its licence.

| What | Where in WorldSim | Source | Licence |
|---|---|---|---|
| Headless Unity licensing in a container: run GameCI's `activate.sh` / `return_license.sh` directly, with a stable machine id | `Tools/Unity/up.sh`, `Tools/Unity/down.sh`, `.devcontainer/on-start.sh` | [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) `tools/ci_unity_license.py`; scripts from [game-ci/cli](https://github.com/game-ci/cli) v0.1.76 (downloaded at run time, not vendored) | MIT |
