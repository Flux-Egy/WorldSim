#!/usr/bin/env bash
# Codespace only. Activates the Unity Personal license and starts the Unity Editor headless,
# with the Unity MCP bridge, in the background. Stop it with Tools/Unity/down.sh.
#
#   Tools/Unity/up.sh              # DEFAULT and the normal way: real rendering through software
#                                  # OpenGL (Mesa llvmpipe) on an Xvfb virtual display. Needed for
#                                  # screenshots, which are the main reason to use the workshop.
#   Tools/Unity/up.sh --nographics # diagnostics only: no rendering at all, NO screenshots
#
# Licensing uses GameCI's own activate.sh / return_license.sh (the scripts our Actions builds
# already use), pinned to game-ci/cli v0.1.76. Approach adapted from Unity MCP's
# tools/ci_unity_license.py (MIT), see CREDITS.md.
set -euo pipefail
# Codespaces secrets are exported only in login shells: re-run in one if they're missing.
if [ -z "${UNITY_EMAIL:-}" ] && [ -z "${WORLDSIM_LOGIN_SHELL:-}" ]; then
  WORLDSIM_LOGIN_SHELL=1 exec bash -lc "$(printf '%q ' "$0" "$@")"
fi
cd "$(dirname "$0")/../.."
REPO="$PWD"
STATE=/workspaces/.unity-state
GAMECI_SHA=39868753b787468332a1f5a85aa151d02c8555c6 # game-ci/cli tag v0.1.76
MODE=graphics
[ "${1:-}" = "--nographics" ] && MODE=nographics

: "${UNITY_EMAIL:?UNITY_EMAIL is not set: add it as a Codespaces secret (docs/CODESPACES.md)}"
: "${UNITY_PASSWORD:?UNITY_PASSWORD is not set: add it as a Codespaces secret (docs/CODESPACES.md)}"

if pgrep -f "/opt/unity/Editor/Unity .*-projectPath" >/dev/null; then
  echo "Unity is already running (log: $STATE/editor.log)."; exit 0
fi

# The Editor lives in /tmp (wiped on every stop): install it if needed (a few minutes).
"$REPO/Tools/Unity/install-editor.sh"

mkdir -p "$STATE/activation" "$STATE/steps-$GAMECI_SHA"
STEPS="$STATE/steps-$GAMECI_SHA"
for f in activate.sh return_license.sh licensing_method.sh resolve_unity_path.sh; do
  [ -s "$STEPS/$f" ] || curl -fsSL -o "$STEPS/$f" \
    "https://raw.githubusercontent.com/game-ci/cli/$GAMECI_SHA/dist/platforms/ubuntu/steps/$f"
done

echo "== Activating Unity license (Personal, via account)"
STEPS_DIR="$STEPS" ACTIVATE_LICENSE_PATH="$STATE/activation" UNITY_LICENSE="" UNITY_LICENSE_FILE="" \
UNITY_LICENSING_SERVER="" HOME="$HOME" bash -c '
  set +eux
  unity-editor() { /opt/unity/Editor/Unity -batchmode -nographics "$@"; }
  export -f unity-editor
  source "$STEPS_DIR/activate.sh" || exit $?
  printf "%s" "${GAME_CI_ACTIVATED_VIA:-}" > "$ACTIVATE_LICENSE_PATH/activated-via"
' > "$STATE/activate.log" 2>&1 || { echo "Activation FAILED. Last lines:"; tail -25 "$STATE/activate.log"; exit 1; }
cp "$STATE/activation/activated-via" "$STATE/activated-via"
echo "License active (log: $STATE/activate.log)."
echo "$(date -u +%FT%TZ) license activated" >> "$STATE/sessions.log"
# Return the seat automatically if no terminal stays open for 15 min (see idle-guard.sh).
if ! { [ -f "$STATE/idle-guard.pid" ] && kill -0 "$(cat "$STATE/idle-guard.pid")" 2>/dev/null; }; then
  setsid nohup "$REPO/Tools/Unity/idle-guard.sh" >/dev/null 2>&1 < /dev/null &
  echo "Idle guard started: the license is returned after 15 min with no open terminal."
fi

# setsid: Unity must not belong to the terminal/tmux session that ran this script. In the spike,
# Unity died ~15 s after start when the tmux session running up.sh closed (session hang-up).
echo "== Starting Unity Editor ($MODE). First start imports the whole project: 10-20 min."
rm -f "$HOME"/.unity-mcp/unity-mcp-status-*.json 2>/dev/null || true
# McpCiBoot.StartStdioForCi is Unity MCP's own entry point for headless editors: it pins the
# stdio transport for this session (v10 defaults to HTTP) and starts the bridge. Without it the
# bridge never starts in batch mode (spike, 2026-11-19).
ARGS=(-batchmode -projectPath "$REPO" -logFile "$STATE/editor.log" -executeMethod MCPForUnity.Editor.McpCiBoot.StartStdioForCi)
if [ "$MODE" = nographics ]; then
  setsid nohup /opt/unity/Editor/Unity "${ARGS[@]}" -nographics >/dev/null 2>&1 < /dev/null &
else
  setsid nohup xvfb-run -a -s "-screen 0 1280x720x24" /opt/unity/Editor/Unity "${ARGS[@]}" -force-glcore >/dev/null 2>&1 < /dev/null &
fi
echo $! > "$STATE/editor.pid"

for i in $(seq 1 240); do # up to 20 minutes
  if ls "$HOME"/.unity-mcp/unity-mcp-status-*.json >/dev/null 2>&1; then
    echo "Unity MCP bridge is up after $((i * 5)) s."
    echo "== Graphics device (from the Editor log)"
    grep -E "GfxDevice|Renderer:|Version: *OpenGL|NullGfxDevice|-nographics" "$STATE/editor.log" | head -6 | sed 's/^/  /'
    if [ "$MODE" = nographics ]; then
      echo "NOTE: --nographics mode: no rendering, screenshots will NOT work."
    elif grep -qiE "NullGfxDevice|null device|Null graphics" "$STATE/editor.log"; then
      echo "WARNING: Unity started WITHOUT a graphics device: screenshots will NOT work."
      echo "Run Tools/Unity/render-check.sh to diagnose (docs/CODESPACES.md)."
    else
      echo "Rendering device present. Confirm with Tools/Unity/render-check.sh on the first session."
    fi
    echo "Start (or restart) claude to use Unity MCP."; exit 0
  fi
  if ! pgrep -f "/opt/unity/Editor/Unity .*-projectPath" >/dev/null; then
    echo "Unity exited early. Last log lines:"; tail -40 "$STATE/editor.log" 2>/dev/null; exit 1
  fi
  if [ $((i % 12)) -eq 0 ]; then
    age=$(( $(date +%s) - $(stat -c %Y "$STATE/editor.log" 2>/dev/null || date +%s) ))
    echo "  ... still starting ($((i * 5 / 60)) min). Editor log $(du -h "$STATE/editor.log" 2>/dev/null | cut -f1), last written ${age}s ago$(grep -q 'Loading completed' "$STATE/editor.log" 2>/dev/null && echo ', project loaded')"
  fi
  sleep 5
done
echo "Unity is running but the MCP bridge did not report in 20 min. Check $STATE/editor.log"
exit 1
