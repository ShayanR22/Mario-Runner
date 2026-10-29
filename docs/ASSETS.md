# Artwork, credits and atlas specification

## New production art

- **Mario, enemies, coins, flags, crystals, ground tiles:** newly authored pixel drawings in `runner/pixelart.py`, exported by `tools/build_art.py`. The base drawings are the existing programmatic art. This upgrade adds attack, transformation, flag, climb, glide, and dive poses, plus form-specific palettes, ears, tails, capes, and other details in `runner/form_art.py`.
- **Distant environment atlas:** generated with the built-in image-generation tool for this project. Source: `assets/generated/biomes-source.png`. Its four panels are extracted and downscaled with nearest-neighbor sampling to 480 × 215 source pixels.
- **Procedural layers:** additional clouds, embers, shadows, UI, and particles drawn by the renderer.
- **Sounds:** synthesized sine-wave cues in `runner/audio.py`; original low-volume synthesized music loop; no third-party sound recordings.
- **Heading font:** user-supplied `SuperMario256(1).ttf`, stored as `assets/original/SuperMario256.ttf`. No font author/license information was supplied.
- **Body font:** bundled Pygame default font.

Mario sprite generation was attempted twice through the built-in image-generation tool and rejected by that service. No generated Mario output was used. The implemented sprites are deterministic pixel drawings with editable source. Exact art prompts are in [ART_PROMPTS.md](ART_PROMPTS.md).

## Sprite layout

`assets/sheets/manifest.json` is authoritative. Every sprite sheet uses:
- **Cell:** 32 × 40 pixels.
- **Grid:** 8 columns, row-major frame indices.
- **Foot anchor:** (16, 38) within a cell.
- **Display scale:** 2× nearest-neighbor; 64 × 80 display cells.
- **Transparency:** actual PNG alpha, no color-key background.
- **Collision:** fixed 32 × 60 display-pixel player torso; enemy masks cached from the relevant display frames.

All forms share the same source grid. Mega uses a cached enlarged presentation, while Small Mario has a shortened torso inside the same display cell; both retain the fixed collision body. Idle, running and landing soles meet the shared baseline; airborne pose changes remain inside that same canvas. The collision body does not expand with arms, wings, or damage animation.

| Mario clip | Frames | Seconds/frame | Playback |
| --- | --- | --- | --- |
| Idle | 4 | 0.18 | Loop |
| Run | 6 | 0.085 | Loop |
| Jump | 2 | 0.12 | Hold final |
| Double jump | 4 | 0.06 | Hold final |
| Fall | 2 | 0.14 | Loop |
| Land | 3 | 0.06 | Hold final |
| Damage | 3 | 0.12 | Hold final |

The enemy sheet provides four-frame clips at 0.13 seconds/frame for Goomba, Koopa, Buzzy Beetle, Paratroopa, Bullet Bill, Dry Bones, fire, pipe, shell, collapsed bones, and vent. Some static props intentionally repeat frames for a uniform atlas interface. The prop sheet provides six coin frames, four flag frames, four checkpoint frames, four crystal frames, and one cloud frame.

Ground tiles are 64 × 32 source pixels, displayed at 128 × 64. Their geometry repeats horizontally. Backgrounds alternate a normal and mirrored panel to join identical edge columns while scrolling; this avoids hard wrap seams without requiring an external image editor.

## Rebuild

```bash
python tools/build_art.py
```

This exports all pixel sheets, the JSON manifest, the four ground tiles, and the four runtime background panels. It uses only Pygame and Python's standard library. The existing generated source atlas is included, so this command makes no API calls.

## Campaign upgrade exports

`form-*.png` sheets use the Mario manifest's frame ordering and 32×40 cells. `powerups.png` is one row of 32×40 icons, ordered by `powerups.json`. Runtime variants and fallback icons are generated from the same editable source and cached once. Cosmetics recolor clothing only. Platforms, marked climbing walls, frozen-block overlays, projectiles, exit buildings, flagpoles, and HUD elements are programmatic geometric pixel art in `scene.py`.

Attack, transform, flag, climb, glide, and dive each add three frames at 0.10 seconds/frame. `manifest.json` remains authoritative for the total frame count and indices. No new image-generation service was used for this upgrade: the established code-drawn sprite system offered reliable alignment and consistent pixel density.

## Rights

This is an unofficial Mario fan project. Generated or newly drawn depictions do not transfer rights to Nintendo characters or trademarks. No license is claimed for the supplied font or old user-supplied artwork. The old image files may remain in the local working folder for reference, but the new release archive uses the new artwork and includes only the supplied font from that folder.
