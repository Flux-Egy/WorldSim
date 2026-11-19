#!/usr/bin/env bash
# Codespace only. Started in the background by up.sh, stopped by down.sh.
#
# Why: when a codespace stops (idle timeout, default 30 min, or a manual stop), every process is
# killed at once and nothing runs on stop, so the Unity license seat would NOT be returned.
# Losing the phone's connection does not stop the codespace immediately; it idles until the
# timeout. This guard returns the seat first: when no terminal has been open for
# IDLE_MINUTES (default 15, below the 30-minute idle timeout), it runs down.sh.
#
# "Terminal open" = any pseudo-terminal in /dev/pts: an SSH session from Termux, a VS Code
# terminal, or a running claude session all count.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
STATE=/workspaces/.unity-state
IDLE_MINUTES="${IDLE_MINUTES:-15}"
echo $$ > "$STATE/idle-guard.pid"
idle=0
while true; do
  sleep 60
  # Unity gone and no license recorded: nothing left to protect.
  if [ ! -f "$STATE/activated-via" ] && ! pgrep -f "/opt/unity/Editor/Unity .*-projectPath" >/dev/null; then
    break
  fi
  terminals=$(find /dev/pts -maxdepth 1 -name '[0-9]*' 2>/dev/null | wc -l)
  if [ "$terminals" -gt 0 ]; then idle=0; else idle=$((idle + 1)); fi
  if [ "$idle" -ge "$IDLE_MINUTES" ]; then
    echo "$(date -u +%FT%TZ) no terminal for $IDLE_MINUTES min: returning the license" >> "$STATE/sessions.log"
    rm -f "$STATE/idle-guard.pid"
    exec "$PWD/Tools/Unity/down.sh" >> "$STATE/idle-guard.log" 2>&1
  fi
done
rm -f "$STATE/idle-guard.pid"
