#!/usr/bin/env bash
# Codespace only. Started in the background by up.sh, stopped by down.sh.
#
# Why: when a codespace stops (idle timeout or a manual stop), every process is killed at once
# and nothing runs on stop, so the Unity license seat would NOT be returned. This guard returns
# the seat first, after IDLE_MINUTES (default 15) with NO work going on.
#
# "Work" is any of these, checked every minute:
#   1. terminal I/O: a /dev/pts device read or written recently. That covers SSH from Termux,
#      VS Code terminals, and claude running in tmux (Remote Control sessions started with
#      Tools/Unity/remote.sh), whose screen updates while it works. Linux updates a tty's
#      atime/mtime on input/output, the same signal `w` uses for IDLE.
#   2. claude or the Unity MCP server using CPU (more than 2 s in the last minute), for a claude
#      started without a terminal.
#   3. the Unity Editor log growing (MCP commands, imports, compiles, play mode).
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
STATE=/workspaces/.unity-state
IDLE_MINUTES="${IDLE_MINUTES:-15}"
TICK=$(getconf CLK_TCK)
echo $$ > "$STATE/idle-guard.pid"

cpu_ticks() { # total CPU ticks of claude and Unity MCP server processes
  local total=0 pid
  for pid in $(pgrep -f "claude|mcp-for-unity" 2>/dev/null); do
    [ -r "/proc/$pid/stat" ] || continue
    total=$((total + $(awk '{print $14 + $15}' "/proc/$pid/stat" 2>/dev/null || echo 0)))
  done
  echo "$total"
}
newest_tty_io() { # seconds since the most recent terminal I/O (large if no terminal)
  local now newest=0 t f
  now=$(date +%s)
  for f in /dev/pts/[0-9]*; do
    [ -e "$f" ] || continue
    t=$(stat -c '%X %Y' "$f" 2>/dev/null | awk '{print ($1 > $2) ? $1 : $2}')
    [ "${t:-0}" -gt "$newest" ] && newest=$t
  done
  [ "$newest" -eq 0 ] && echo 999999 || echo $((now - newest))
}

idle=0
last_cpu=$(cpu_ticks)
last_log=$(stat -c %s "$STATE/editor.log" 2>/dev/null || echo 0)
while true; do
  sleep 60
  if [ ! -f "$STATE/activated-via" ] && ! pgrep -f "/opt/unity/Editor/Unity .*-projectPath" >/dev/null; then
    break # nothing left to protect
  fi
  cpu=$(cpu_ticks); log=$(stat -c %s "$STATE/editor.log" 2>/dev/null || echo 0)
  busy=no
  [ "$(newest_tty_io)" -lt 90 ] && busy=yes
  [ $(( (cpu - last_cpu) / TICK )) -ge 2 ] && busy=yes
  [ "$log" -ne "$last_log" ] && busy=yes
  last_cpu=$cpu; last_log=$log
  if [ "$busy" = yes ]; then idle=0; else idle=$((idle + 1)); fi
  if [ "$idle" -ge "$IDLE_MINUTES" ]; then
    echo "$(date -u +%FT%TZ) no work for $IDLE_MINUTES min: returning the license" >> "$STATE/sessions.log"
    rm -f "$STATE/idle-guard.pid"
    exec "$PWD/Tools/Unity/down.sh" >> "$STATE/idle-guard.log" 2>&1
  fi
done
rm -f "$STATE/idle-guard.pid"
