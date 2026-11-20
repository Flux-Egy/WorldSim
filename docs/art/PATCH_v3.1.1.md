# Art pack patch v3.1.1: animation event frames

Fixes the bug Claude Code found: 151 animation events pointed past the last frame (100 in fauna_critters, 50 in fauna_sea, 1 in titans), so for example the eagle's attack never fired "hit".

- The data was fixed in place: each out-of-range event moved to the last frame of its animation, and duplicates were dropped. Only `events` changed. Frames, pages and every other field are byte-for-byte the same JSON layout.
- The generator was fixed: `Tools/ArtGen/xcore.py` `Atlas.anim()` now clamps events to the animation length, so re-exports stay correct. A fresh export of the three atlases gives identical `animList`, with 0 invalid events.
- `WorldSimData/animation_events.json` and `asset_report.json` were regenerated.

After copying: rebuild the art index (`Tools/ArtIndex`), because the CI checks it.
