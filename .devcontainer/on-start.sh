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
# seat may still be active. Return it now, with the same machine id it was activated with.
# This runs in the foreground on purpose: in the spike (2026-11-19) background jobs started from
# postStartCommand were killed when it finished, even with setsid. Startup takes ~5 min longer,
# but only when a seat was left active. Log: $STATE/auto-return.log
if [ -f "$STATE/activated-via" ] && ! pgrep -f "/opt/unity/Editor/Unity" >/dev/null 2>&1; then
  echo "Unity license left active by a sudden stop: returning it now (log: $STATE/auto-return.log)."
  echo "$(date -u +%FT%TZ) auto-return after sudden stop" >> "$STATE/sessions.log"
  REPO="$(cd "$(dirname "$0")/.." && pwd)"
  # The Editor (needed to return the seat) lives in /tmp, which a stop wipes: reinstall it first.
  if bash -lc "'$REPO/Tools/Unity/install-editor.sh' && '$REPO/Tools/Unity/down.sh'" >> "$STATE/auto-return.log" 2>&1 < /dev/null; then
    echo "Seat returned."
  else
    echo "Automatic return FAILED: run Tools/Unity/down.sh (see docs/CODESPACES.md)."
  fi
fi
