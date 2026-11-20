# WorldSim Pixel Style Guide

## Grid & scale
* **Fine grid (2×)** is the only export resolution: 16 px = 1 Unity unit. Terrain, buildings and props are designed on the coarse world grid and upscaled ×2 (nearest); people, animals, units, FX and UI are drawn natively on the fine grid. Never mix other scales.
* Phone reference screen: 240 × 520 fine px (shown ×3). UI text: 5×7 font, world labels: 3×5 font.
* Typical sizes (fine px): adult person 16×28 box (≈13×27 visible), child ≈11×20, sheep ≈22×17, horse ≈32×30, house slum ≈16×10 → palace ≈64×60, era seat ≈70×70, fighter jet ≈30, bomber ≈45, ICBM ≈42, ballistic launcher ≈52×20, nuclear cloud up to 160×150.

## Light & shading
* Light comes from the **top-left**. Shapes use banded 5-step ramps with 2×2 Bayer dither at band edges (`dome()`), not smooth gradients.
* **No black outlines.** Separation comes from value contrast, a 1 px lighter top/left rim and a darker bottom/right edge. Exception: aircraft over busy ground may get a 55 % ink outline.
* Shadows fall **down-right**, 25–38 % dark, semi-transparent (exported with real alpha).
* Windows: lit (`#f2b65a`, highlight `#ffd98a`) vs dark (`#26303a`); at night lit pixels keep full brightness and glow.

## Palette
* Ramps live in `Tools/ArtGen/lib.py` (`W` walls ×3, `R` roofs ×5, `C` misc). Kingdom colour = `R['K']` (terracotta default) → recolour region TEAM.
* Culture colours are generated (HSV ramps) and applied with the recolour shader; never bake a final culture colour into new art — draw it with the region's ramp.
* UI: ink `#0b0e13`, panels `#151b25/#1e2633/#28323f`, text `#f3e6c8`, dim `#8f99a8`, accent `#e8b46a`, good `#7cc46a`, bad `#e06a55`, cyan `#5fe0e8`, gold rail `#9a7030 → #e6c47a`.

## Animation
* Walk cycles: 4 frames, 6 fps, 1 px body bob on frames 1 & 3, arms swing opposite to legs.
* Rotors 16 fps, fire 8 fps, explosions 10 fps non-loop (4 frames), smoke rise 6 fps.
* Hit = full white flash for 1–2 frames (shader `_Flash`), never gore. Deaths: people lie down, animals legs-up, graves for the dead.
* Era progress must be **visible**: materials, roofs, lights at night, vehicles, clothing.

## Readability rules for phones
* Every unit/role must be identifiable by silhouette + one colour cue at 1× (helmet shape, weapon, mount).
* Status always shown with a bubble icon above the head, hp bars 12×3.
* Labels sit on 80 % dark plates; never put text directly on the map.

## Symbols & content rules
* No real-world religious symbols or buildings (no crosses, crescents, stars of real faiths, halos); creeds are fictional and their marks are abstract (axe, scale, tree, hearth, eye, sun, leaf, horn, gear, wave, peak).
* No real-world hazard/organisation emblems: the radiation zone uses the original yellow/black hazard marker; medics wear a green heart, not a cross.
* Graves are plain rounded stones. Violence stays cartoon-clean: flashes, numbers, legs-up animals, no gore.
* Naming follows `CLAUDE.md`: player abilities are just "Powers".

## Originality
Learn principles from other games, never copy their sprites, icons, palettes or layouts.
