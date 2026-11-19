#!/usr/bin/env bash
# Codespace only. Quits the headless Unity Editor and RETURNS the Unity license seat.
# Always run this before stopping the codespace: a seat left active can block the Actions
# builds (Personal accounts have very few seats).
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
STATE=/workspaces/.unity-state
GAMECI_SHA=39868753b787468332a1f5a85aa151d02c8555c6 # game-ci/cli tag v0.1.76
STEPS="$STATE/steps-$GAMECI_SHA"

# Stop the idle guard (when the guard itself runs this script it has already removed its pid file).
if [ -f "$STATE/idle-guard.pid" ]; then kill "$(cat "$STATE/idle-guard.pid")" 2>/dev/null || true; rm -f "$STATE/idle-guard.pid"; fi

echo "== Stopping Unity"
if pgrep -f "/opt/unity/Editor/Unity .*-projectPath" >/dev/null; then
  pkill -TERM -f "/opt/unity/Editor/Unity .*-projectPath"
  for _ in $(seq 1 30); do pgrep -f "/opt/unity/Editor/Unity .*-projectPath" >/dev/null || break; sleep 2; done
  pkill -KILL -f "/opt/unity/Editor/Unity .*-projectPath" 2>/dev/null || true
  echo "Unity stopped."
else
  echo "Unity was not running."
fi
rm -f "$STATE/editor.pid"

echo "== Returning the Unity license seat"
if [ ! -f "$STATE/activated-via" ]; then
  echo "No active license recorded. Nothing to return."; exit 0
fi
: "${UNITY_EMAIL:?UNITY_EMAIL is not set}"
: "${UNITY_PASSWORD:?UNITY_PASSWORD is not set}"
if STEPS_DIR="$STEPS" ACTIVATE_LICENSE_PATH="$STATE/activation" \
   GAME_CI_ACTIVATED_VIA="$(cat "$STATE/activated-via")" UNITY_LICENSE="" UNITY_LICENSE_FILE="" \
   UNITY_LICENSING_SERVER="" bash -c '
     set +eux
     unity-editor() { /opt/unity/Editor/Unity -batchmode -nographics "$@"; }
     export -f unity-editor
     source "$STEPS_DIR/return_license.sh" || exit $?
     exit "${RETURN_EXIT_CODE:-0}"
   ' > "$STATE/return.log" 2>&1; then
  rm -f "$STATE/activated-via"
  echo "$(date -u +%FT%TZ) license returned" >> "$STATE/sessions.log"
  echo "License returned. Safe to stop the codespace."
else
  echo "License return FAILED. Last lines:"; tail -25 "$STATE/return.log"
  echo "If it keeps failing, release the seat at https://id.unity.com (or wait for it to expire)."
  exit 1
fi
