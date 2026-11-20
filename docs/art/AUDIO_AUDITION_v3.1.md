# Audio audition: pack v3.1 (owner, 2026-11-20)

The owner listened to all 237 clips on the phone (audition page with every clip, grouped, keep/replace/unsure).
**Result: 211 OK, 25 to replace, 1 unsure.** Replace clips under the same file name (`Resources/WorldSimAudio/...`), so code and events keep working.

## Replace (25)
| Group | Clips |
|---|---|
| Body | `body_cough`, `body_freeze`, `body_shatter` |
| Buildings | `building_collapse`, `building_crack`, `building_debris_rain`, `building_freeze_creak`, `building_metal_crash` |
| Combat | `combat_arrow_hit` |
| Creatures | `creature_bark`, `creature_caw`, `creature_flap`, `creature_laugh`, `creature_oink`, `creature_screech` |
| Disasters | `disaster_fireworks`, `disaster_meteor`, `disaster_quake`, `disaster_volcano` |
| Extra | `extra_crowd_angry`, `extra_crowd_cheer_big`, `extra_hail`, `extra_monkey_chatter`, `extra_snort` |
| World | `world_harvest` |

## Unsure (1)
`extra_dolphin_click`

## Notes for the regeneration
- All music (12) and ambient loops (24) passed the audition.
- The rejected clips are mostly impact/destruction sounds, animal voices and crowds: the hardest kinds to synthesise convincingly.
- After replacing, keep the loudness targets from v3.1 (UI −22 dB RMS, ambient −24, music −20, others −18, peak ≤ −3 dBFS).
