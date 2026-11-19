#!/usr/bin/env bash
# Codespace only. Installs the exact Unity Editor this project uses, from Unity's own download
# server, into /tmp and links it as /opt/unity (the path GameCI's licensing scripts expect).
#
# Why /tmp: the Editor is ~4.6 GB compressed and much larger extracted. /tmp in a codespace is a
# big temporary disk that does not count as codespace storage (Free plan: 15 GB-month), but it
# is wiped when the codespace stops, so up.sh calls this script again after each start
# (a few minutes: download + extract). The project and its Library stay in /workspaces.
#
# Version and changeset come from ProjectSettings/ProjectVersion.txt, so upgrading Unity there
# upgrades the codespace automatically.
set -euo pipefail
cd "$(dirname "$0")/../.."
line=$(sed -n 's/^m_EditorVersionWithRevision: //p' ProjectSettings/ProjectVersion.txt)  # "6000.3.28f1 (8f082d2fe476)"
VERSION=${line%% *}
CHANGESET=$(echo "$line" | sed -n 's/.*(\(.*\)).*/\1/p')
[ -n "$VERSION" ] && [ -n "$CHANGESET" ] || { echo "Can't read version/changeset from ProjectVersion.txt"; exit 1; }
DEST=/tmp/unity-$VERSION
URL="https://download.unity3d.com/download_unity/$CHANGESET/LinuxEditorInstaller/Unity-$VERSION.tar.xz"

if [ -x "$DEST/Editor/Unity" ] && [ "$(cat "$DEST/version" 2>/dev/null)" = "$VERSION" ]; then
  echo "Unity $VERSION already installed in $DEST."
else
  free_gb=$(df -BG --output=avail /tmp | tail -1 | tr -dc 0-9)
  [ "$free_gb" -ge 30 ] || { echo "Only ${free_gb} GB free in /tmp; need about 30."; exit 1; }
  echo "== Downloading Unity $VERSION ($CHANGESET) from download.unity3d.com"
  expected=$(curl -sIL "$URL" | tr -d '\r' | awk 'tolower($1)=="content-length:" {n=$2} END {print n}')
  rm -rf "$DEST" "$DEST.partial"; mkdir -p "$DEST.partial"
  # Stream download straight into tar: no 4.6 GB archive kept on disk. xz -t style integrity is
  # covered by tar/xz failing on a truncated or corrupt stream; the byte count is checked too.
  curl -fSL --retry 3 "$URL" | tee >(wc -c > "$DEST.partial.bytes") | tar -xJ -C "$DEST.partial"
  got=$(cat "$DEST.partial.bytes"); rm -f "$DEST.partial.bytes"
  if [ -n "$expected" ] && [ "$got" != "$expected" ]; then
    echo "Download size mismatch: got $got bytes, expected $expected."; rm -rf "$DEST.partial"; exit 1
  fi
  mv "$DEST.partial" "$DEST"
  echo "$VERSION" > "$DEST/version"
  echo "Installed: $(du -sh "$DEST" | cut -f1) in $DEST"
fi
[ -x "$DEST/Editor/Unity" ] || { echo "Editor binary missing in $DEST/Editor/Unity"; exit 1; }
sudo ln -sfn "$DEST" /opt/unity
echo "/opt/unity -> $DEST"
