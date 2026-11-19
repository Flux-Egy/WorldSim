#!/usr/bin/env bash
# Codespace only. Run this BEFORE killing a Unity Editor that looks stuck (CLAUDE.md, "Unity seems
# stuck"). Captures what a human would see and what the Editor is doing:
#   - a screenshot of the Xvfb virtual display(s) Unity runs on (a dialog nobody can see: Safe
#     Mode, project upgrade, package errors...). Note: in -batchmode Unity normally shows no
#     dialogs, so a blank or black screen is the usual, healthy result.
#   - how long ago the Editor log was written, whether the project finished loading, and its tail
#   - CPU use and thread states of the Unity processes (all idle + "Loading completed" = waiting
#     for commands, which is normal; a recent log + CPU = still working)
# Output: /workspaces/.unity-state/diagnose-<time>/
set -uo pipefail
STATE=/workspaces/.unity-state
OUT="$STATE/diagnose-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"

echo "== Virtual display screenshots"
for sock in /tmp/.X11-unix/X*; do
  [ -e "$sock" ] || continue
  d=":${sock##*/X}"
  if import -display "$d" -window root "$OUT/display${d#:}.png" 2>/dev/null; then
    echo "  $d -> $OUT/display${d#:}.png ($(identify -format '%wx%h, %k colours' "$OUT/display${d#:}.png" 2>/dev/null))"
  else
    echo "  $d: capture failed"
  fi
done

echo "== Editor log"
LOG="$STATE/editor.log"
if [ -f "$LOG" ]; then
  echo "  last written $(( $(date +%s) - $(stat -c %Y "$LOG") )) s ago, size $(du -h "$LOG" | cut -f1)"
  grep -q "Loading completed" "$LOG" && echo "  project finished loading (an idle Editor after this is normal)"
  grep -n -iE "safe mode|error CS|Package Manager|failed to resolve|would you like|upgrade|license" "$LOG" | tail -10 > "$OUT/log-flags.txt"
  [ -s "$OUT/log-flags.txt" ] && { echo "  flagged lines:"; sed 's/^/    /' "$OUT/log-flags.txt" | cut -c1-180; }
  tail -40 "$LOG" > "$OUT/log-tail.txt"
fi

echo "== Unity processes (CPU %, elapsed, thread states)"
for p in $(pgrep -x Unity); do
  echo "  pid $p: $(ps -o pcpu=,etime= -p "$p")  threads: $(awk '{print $3}' /proc/"$p"/task/*/stat 2>/dev/null | sort | uniq -c | tr '\n' ' ')"
done
pgrep -x Unity >/dev/null || echo "  no Unity process"
echo "Saved to $OUT"
