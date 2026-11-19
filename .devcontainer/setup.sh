#!/usr/bin/env bash
# One-time Codespace setup (postCreateCommand). Safe to re-run.
# Installs: Unity's system libraries, software OpenGL + Xvfb, tmux, uv, Claude Code, the Unity MCP
# package (locally only, never committed) and registers the Unity MCP server with Claude Code.
# The Unity Editor itself is installed by Tools/Unity/install-editor.sh (called by up.sh) into /tmp.
set -euo pipefail
cd "$(dirname "$0")/.."
STATE=/workspaces/.unity-state
MCP_VERSION=10.3.0 # CoplayDev/unity-mcp: Unity package tag and PyPI mcpforunityserver version
mkdir -p "$STATE"

say() { printf '\n== %s\n' "$*"; }

say "System packages: Unity's runtime libraries (list from GameCI's Ubuntu 24.04 base image),"
say "software OpenGL/Vulkan + Xvfb virtual display (rendering without a GPU), tmux"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq --no-install-recommends \
  ca-certificates libasound2t64 libc6-dev libcap2 libglu1-mesa libgtk-3-0t64 libncurses6 libnotify4 \
  libnss3 libvulkan1 mesa-vulkan-drivers libgl1-mesa-dri mesa-utils libxtst6 libxss1 cpio lsb-release \
  python3 xvfb xauth xz-utils curl git jq unzip tmux >/dev/null
echo "OK"

say "uv (runs the Unity MCP server)"
if ! command -v uv >/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
uv --version

say "Claude Code"
if ! command -v claude >/dev/null; then
  curl -fsSL https://claude.ai/install.sh | bash
fi
export PATH="$HOME/.local/bin:$PATH"
claude --version

say "Unity MCP package (local only: manifest changes are hidden from git)"
python3 - "$MCP_VERSION" <<'EOF'
import json, sys, collections
p = 'Packages/manifest.json'
d = json.load(open(p), object_pairs_hook=collections.OrderedDict)
url = f"https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v{sys.argv[1]}"
if d['dependencies'].get('com.coplaydev.unity-mcp') != url:
    d['dependencies']['com.coplaydev.unity-mcp'] = url
    open(p, 'w').write(json.dumps(d, indent=2) + "\n")
    print("added", url)
else:
    print("already present")
EOF
# Keep the codespace-only package out of commits. Undo with: git update-index --no-skip-worktree <file>
git update-index --skip-worktree Packages/manifest.json Packages/packages-lock.json
echo "manifest.json and packages-lock.json are skip-worktree here: change packages from the phone, not in this codespace."

say "Register Unity MCP with Claude Code (this codespace only)"
claude mcp remove UnityMCP -s user >/dev/null 2>&1 || true
claude mcp add UnityMCP -s user -e DISABLE_TELEMETRY=1 -e UNITY_MCP_DISABLE_TELEMETRY=1 \
  -- uvx --from "mcpforunityserver==$MCP_VERSION" mcp-for-unity --transport stdio
# Warm the uv cache so the first Claude session starts fast.
uvx --from "mcpforunityserver==$MCP_VERSION" mcp-for-unity --help >/dev/null 2>&1 || true

say "Done"
cat <<'EOF'
Next (see docs/CODESPACES.md):
  1. claude            # first time: log in, then exit
  2. Tools/Unity/up.sh # installs the Editor if needed (~10 min after each start), license, Editor with rendering
  3. claude            # work; Unity MCP tools are available
  4. Tools/Unity/down.sh  # ALWAYS before stopping: quits Unity and returns the license seat
EOF
