#!/usr/bin/env bash
# One-time Codespace setup (postCreateCommand). Safe to re-run.
# Installs: uv, Claude Code, software OpenGL for rendering without a GPU, the Unity MCP package
# (locally only, never committed) and registers the Unity MCP server with Claude Code.
set -euo pipefail
cd "$(dirname "$0")/.."
STATE=/workspaces/.unity-state
MCP_VERSION=10.3.0 # CoplayDev/unity-mcp: Unity package tag and PyPI mcpforunityserver version
mkdir -p "$STATE"

say() { printf '\n== %s\n' "$*"; }

say "Unity version check"
want=$(sed -n 's/^m_EditorVersion: //p' ProjectSettings/ProjectVersion.txt)
have=$(cat "${UNITY_PATH:-/opt/unity}/version" 2>/dev/null || true) # GameCI images write the editor version here
echo "project: $want   image editor: ${have:-unknown}"
case "$have" in
  "$want"*) echo "OK" ;;
  *) echo "WARNING: the image does not match ProjectVersion.txt. Update the image tag in .devcontainer/devcontainer.json." ;;
esac

say "System packages (software OpenGL + virtual display for rendering without a GPU)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends tmux xvfb xauth libgl1-mesa-dri libglu1-mesa mesa-utils mesa-vulkan-drivers libvulkan1 curl ca-certificates jq >/dev/null
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
  2. Tools/Unity/up.sh # activate the Unity license and start the headless Editor
  3. claude            # work; Unity MCP tools are available
  4. Tools/Unity/down.sh  # ALWAYS before stopping: quits Unity and returns the license seat
EOF
