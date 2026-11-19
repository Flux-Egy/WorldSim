#!/usr/bin/env bash
# Codespace only. Prints what this codespace is using against the Free plan limits:
# disk (15 GB-month storage) and core-hours (120 a month). These are local estimates. The
# official numbers are on https://github.com/settings/billing (updated with some delay).
set -uo pipefail
STATE=/workspaces/.unity-state
cores=$(nproc)
up_s=$(ps -o etimes= -p 1 | tr -d ' ')

echo "== Disk"
df -h / /workspaces 2>/dev/null | awk 'NR==1 || !seen[$1]++'
used_gb=$(df -B1 --output=used / | tail -1 | awk '{printf "%.1f", $1/1e9}')
echo "Used on the codespace disk: ${used_gb} GB (Free plan storage: 15 GB-month)"
for d in /workspaces/WorldSim/Library "$HOME/.cache/unity3d" "$HOME/.cache/uv" "$HOME/.local/share/claude" /opt/unity; do
  [ -e "$d" ] && printf '  %-40s %s\n' "$d" "$(du -sh "$d" 2>/dev/null | cut -f1)"
done

echo "== Compute"
awk -v s="$up_s" -v c="$cores" 'BEGIN { printf "Machine: %d cores. Running since this start: %.2f h, about %.2f core-hours.\n", c, s/3600, s*c/3600 }'
echo "Free plan: 120 core-hours a month, about $((120 / cores)) h on this machine."
if [ -f "$STATE/sessions.log" ]; then
  echo "== Session log ($STATE/sessions.log, last 10)"
  tail -10 "$STATE/sessions.log"
fi
echo "Official usage: https://github.com/settings/billing (Codespaces compute and storage)."
