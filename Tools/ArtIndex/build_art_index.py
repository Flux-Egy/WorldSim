#!/usr/bin/env python3
"""Build the compact binary art index (art_index.bytes) from the art pack's atlas JSON files.

Why: WorldSimArtDB used to parse every atlas JSON (~9 MB) and load every texture page at startup
(~288 MiB as RGBA32). The index lets the game find any frame or animation by name in a few
microseconds, without parsing JSON or touching a texture; pages then load per atlas on demand.

Usage (from the repo root; stdlib only):
  python3 Tools/ArtIndex/build_art_index.py           # (re)write the index
  python3 Tools/ArtIndex/build_art_index.py --check   # CI: fail if the committed index is stale

Run it after every art regeneration (docs/art/ASSETS_GUIDE.md, section 6).
Reader: Assets/WorldSim/Runtime/Render/Art/ArtIndex.cs (format documented there; keep in sync).
"""
import json
import os
import struct
import sys

ART = os.path.join("Assets", "WorldSim", "Resources", "WorldSimArt")
OUT = os.path.join(ART, "art_index.bytes")
MAGIC, VERSION = b"WSAI", 1
CLAMPED = []  # events moved to their animation's last frame (reported, see main)
FNV_OFFSET, FNV_PRIME, MASK64 = 0xCBF29CE484222325, 0x100000001B3, (1 << 64) - 1


def fnv1a64(s):
    h = FNV_OFFSET
    for b in s.encode("utf-8"):
        h = ((h ^ b) * FNV_PRIME) & MASK64
    return h


class Strings:
    """Interned UTF-8 strings: one blob plus (offset, length) per id."""
    def __init__(self):
        self.ids, self.items = {}, []

    def id(self, s):
        if s not in self.ids:
            self.ids[s] = len(self.items)
            self.items.append(s)
        return self.ids[s]

    def pack(self):
        blob, table = bytearray(), bytearray()
        for s in self.items:
            b = s.encode("utf-8")
            table += struct.pack("<IH", len(blob), len(b))
            blob += b
        return struct.pack("<I", len(self.items)) + bytes(table) + struct.pack("<I", len(blob)) + bytes(blob)


def build(root=ART):
    atlases = json.load(open(os.path.join(root, "atlas_index.json"), encoding="utf-8"))["atlases"]
    strings = Strings()                                  # names of frames/anims/anchors/events, paths
    frames, anims = [], []                               # collected before sorting
    atlas_bin = bytearray(struct.pack("<I", len(atlases)))
    for ai, path in enumerate(atlases):
        j = json.load(open(os.path.join(root, path + ".json"), encoding="utf-8"))
        folder = os.path.dirname(path)
        pages = j["pageList"]
        atlas_bin += struct.pack("<IHH", strings.id(path), int(j.get("ppu") or 16), len(pages))
        for pg in pages:
            image = (folder + "/" if folder else "") + os.path.splitext(pg["image"])[0]
            mask = (folder + "/" if folder else "") + os.path.splitext(pg["mask"])[0] if pg.get("mask") else ""
            atlas_bin += struct.pack("<IIHH", strings.id(image), strings.id(mask) if mask else 0xFFFFFFFF, pg["w"], pg["h"])
        for f in j["frameList"]:
            frames.append((fnv1a64(f["name"]), f["name"], ai, f))
        for a in j.get("animList") or []:
            anims.append((fnv1a64(a["name"]), a["name"], a))

    frames.sort(key=lambda t: (t[0], t[1]))
    anims.sort(key=lambda t: (t[0], t[1]))
    for kind, items in (("frame", frames), ("animation", anims)):
        for a, b in zip(items, items[1:]):
            if a[0] == b[0]:
                raise SystemExit(f"{kind} name hash collision or duplicate: {a[1]!r} / {b[1]!r}")
    frame_id = {name: i for i, (_, name, _, _) in enumerate(frames)}

    anchors = bytearray()
    anchor_count = 0
    frame_bin = bytearray(struct.pack("<I", len(frames)))
    frame_bin += b"".join(struct.pack("<Q", h) for h, _, _, _ in frames)
    for _, name, ai, f in frames:
        first = anchor_count
        for an in f.get("anchors") or []:
            anchors += struct.pack("<Ihh", strings.id(an["name"]), an["x"], an["y"])
            anchor_count += 1
        flags = 1 if f.get("recolor") else 0
        frame_bin += struct.pack("<IHBBHHHHffIH", strings.id(name), ai, f["page"], flags,
                                 f["x"], f["y"], f["w"], f["h"], float(f["pivotX"]), float(f["pivotY"]),
                                 first, anchor_count - first)

    anim_frames, events = bytearray(), bytearray()
    nf = ne = 0
    anim_bin = bytearray(struct.pack("<I", len(anims)))
    anim_bin += b"".join(struct.pack("<Q", h) for h, _, _ in anims)
    for _, name, a in anims:
        f0, e0 = nf, ne
        for fr in a["frames"]:
            if fr not in frame_id:
                raise SystemExit(f"animation {name!r} references missing frame {fr!r}")
            anim_frames += struct.pack("<i", frame_id[fr]); nf += 1
        last = len(a["frames"]) - 1
        for ev in a.get("events") or []:
            frame = ev["frame"]
            if frame > last:  # art-pack bug: event on a frame the animation doesn't have (would never fire)
                CLAMPED.append(f"{name}: {ev['name']} @ {frame} -> {last}")
                frame = last
            events += struct.pack("<HI", frame, strings.id(ev["name"])); ne += 1
        anim_bin += struct.pack("<IfBIHIH", strings.id(name), float(a["fps"]), 1 if a.get("loop") else 0, f0, nf - f0, e0, ne - e0)

    out = bytearray(MAGIC + struct.pack("<I", VERSION))
    out += strings.pack()
    out += atlas_bin
    out += frame_bin
    out += struct.pack("<I", anchor_count) + anchors
    out += anim_bin
    out += struct.pack("<I", nf) + anim_frames
    out += struct.pack("<I", ne) + events
    return bytes(out), len(atlases), len(frames), len(anims)


def main():
    data, na, nf, nanim = build()
    if CLAMPED:
        print(f"WARNING: {len(CLAMPED)} animation events pointed past their animation's last frame and were moved to it "
              "(fix in Tools/ArtGen, then rebuild). First ones:", file=sys.stderr)
        for line in CLAMPED[:5]:
            print("  " + line, file=sys.stderr)
    if "--check" in sys.argv:
        old = open(OUT, "rb").read() if os.path.exists(OUT) else b""
        if old != data:
            raise SystemExit(f"{OUT} is stale: run python3 Tools/ArtIndex/build_art_index.py and commit it")
        print(f"art index up to date ({na} atlases, {nf} frames, {nanim} animations, {len(data)} bytes)")
        return
    with open(OUT, "wb") as fh:
        fh.write(data)
    print(f"wrote {OUT}: {na} atlases, {nf} frames, {nanim} animations, {len(data)} bytes")


if __name__ == "__main__":
    main()
