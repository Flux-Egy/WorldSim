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
sudo cp "$STATE/machine-id" /etc/machine-id
sudo mkdir -p /var/lib/dbus && sudo cp "$STATE/machine-id" /var/lib/dbus/machine-id

echo "$(date -u +%FT%TZ) codespace started ($(nproc) cores)" >> "$STATE/sessions.log"

# A codespace that stopped suddenly (idle timeout, manual stop) never ran down.sh, so its license
# seat may still be active. Return it now, in the background, with the same machine id it was
# activated with. Log: $STATE/return.log
if [ -f "$STATE/activated-via" ] && ! pgrep -f "/opt/unity/Editor/Unity" >/dev/null 2>&1; then
  echo "Unity license left active by a sudden stop: returning it in the background (see $STATE/return.log)."
  echo "$(date -u +%FT%TZ) auto-return after sudden stop" >> "$STATE/sessions.log"
  # The Editor (needed to return the seat) lives in /tmp, which was wiped: reinstall it first.
  REPO="$(cd "$(dirname "$0")/.." && pwd)"
  nohup bash -c "'$REPO/Tools/Unity/install-editor.sh' && '$REPO/Tools/Unity/down.sh'" >> "$STATE/auto-return.log" 2>&1 &
fi
