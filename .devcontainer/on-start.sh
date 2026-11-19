#!/usr/bin/env bash
# Runs on every Codespace start (postStartCommand).
# Unity binds its license to the machine id. Keep one stable id per codespace (stored under
# /workspaces, which survives stop/start and rebuilds), so a re-activation reuses the same seat
# instead of taking a new one.
set -euo pipefail
STATE=/workspaces/.unity-state
mkdir -p "$STATE"
if [ ! -s "$STATE/machine-id" ]; then
  cat /proc/sys/kernel/random/uuid | tr -d '-' > "$STATE/machine-id"
fi
cp "$STATE/machine-id" /etc/machine-id
mkdir -p /var/lib/dbus && cp "$STATE/machine-id" /var/lib/dbus/machine-id

if pgrep -f "/opt/unity/Editor/Unity" >/dev/null 2>&1; then
  echo "Unity is already running."
elif [ -f "$STATE/activated-via" ]; then
  echo "NOTE: the Unity license from the last session may still be active (the codespace stopped"
  echo "without Tools/Unity/down.sh). Run Tools/Unity/up.sh to reuse it, or down.sh to return it."
fi
