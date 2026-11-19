#!/usr/bin/env bash
# Codespace only. Starts a work session the owner drives from the phone with Claude Remote
# Control (claude.ai/code or the Claude app), with no terminal kept open on the phone.
#
#   Tools/Unity/remote.sh          # Unity up (if needed) + claude --remote-control in tmux
#   tmux attach -t worldsim        # optional: watch it from a terminal (detach: Ctrl-b d)
#
# claude runs inside tmux, so it survives the SSH connection closing, and its screen updates go
# to a real terminal. That terminal output is what keeps the session "active" for the idle guard
# and, per GitHub's docs ("terminal activity, either input or output, resets the idle timeout"),
# should also keep the codespace from idling out. The first-session spike confirms the latter.
set -euo pipefail
cd "$(dirname "$0")/../.."
"$PWD/Tools/Unity/up.sh"
if tmux has-session -t worldsim 2>/dev/null; then
  echo "A worldsim tmux session already exists (tmux attach -t worldsim)."
else
  tmux new-session -d -s worldsim -c "$PWD" "claude --remote-control worldsim-codespace"
  echo "claude is running with Remote Control in tmux session 'worldsim'."
fi
echo "Open claude.ai/code or the Claude app on the phone and pick the session 'worldsim-codespace'."
echo "You can close this terminal now. When done, ask Claude to run Tools/Unity/down.sh (or run it yourself)."
