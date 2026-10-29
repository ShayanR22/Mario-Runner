# Art generation record

Mode: built-in image generation. No CLI/API-key fallback was used.

## Implemented background atlas

The generated output is preserved at `assets/generated/biomes-source.png`. Runtime panels are `grass.png`, `cave.png`, `sky.png`, and `castle.png` in the same folder.

Prompt:

> Use case: stylized-concept. Asset type: four-biome background atlas for a 2D side-scrolling pixel-art game. A 1536x1024 canvas divided into exactly four equal rectangular panels in a 2x2 layout, with no gutters or labels. Top left: sunny green grasslands, turquoise sky, rounded green hills, small drifting white clouds, distant mountains. Top right: deep indigo underground cavern with purple rock strata, glowing cyan crystals and faint hanging roots. Bottom left: dreamy bright sky realm, blue sky, layered white cloud banks and small distant floating islands. Bottom right: dark volcanic castle interior, purple stone arches and columns, distant orange lava channels, warm amber windows. Every panel is environmental scenery only, no characters, no enemies, no icons, no text, no interface and no foreground floor. Side-on 2D game composition with distant scenery concentrated in the lower half and clear spacious upper regions. Cohesive hand-crafted 16-bit pixel art, sharp square pixels, restrained palettes, stepped shading and no smooth airbrushing. Each panel has matching left/right edge colors for scrolling. Polished readable game-ready environment art.

The returned atlas was visually inspected. It provides distinct settings and no interface or character content. Runtime panels are nearest-neighbor downscaled, then alternate with mirrored copies for continuous scrolling.

## Mario sheet attempts — no output used

The service rejected both attempts below. Actual Mario and enemy sheets were subsequently drawn through the editable pixel-art source and exported to PNG.

First prompt:

> Use case: stylized-concept. Asset type: production 2D pixel-art game character animation sprite sheet. Create a NEW, beautifully drawn recognizable Mario in red M cap, red shirt, blue overalls, white gloves, brown shoes and moustache. Exact 4-column by 4-row grid, 16 equally sized cells, square 1024x1024 canvas, TRANSPARENT background. No grid lines, labels, lettering, floor, shadows or scenery. Every cell contains exactly one full-body Mario facing RIGHT in side view; same body proportions, same size, generous transparent margins, feet on the same baseline within each cell. Crisp deliberate SNES-style pixel art, approximately 32x40 source pixels per character enlarged with clean nearest-neighbor edges, rich limited palette with dark navy outlines and 2-tone shading. Each character occupies about half the cell width and 70% of its height, centered horizontally, baseline at 88% cell height. Row 1 from left: idle neutral, idle breathing, running contact left leg forward, running recoil. Row 2: running passing, running high point, running contact right leg forward, running passing opposite. Row 3: jump takeoff fist raised, upward jump tuck, double-jump twist with arms wide (no effects), double-jump tuck facing right. Row 4: falling arms out, falling braced, landing crouch, damage recoiling. Keep every frame separate in its own cell, no overlapping neighboring frames. Recognizable cheerful Mario, professional animation keyframes, pure transparent empty space between frames.

Second prompt:

> Draw a cheerful, family-friendly pixel-art Mario animation sprite sheet for a 2D platform game. Mario wears his familiar red cap, red shirt, blue overalls, white gloves and brown shoes. Transparent background. Four columns and two rows of equal cells, eight separate full-body poses facing right: idle, running with left foot forward, running passing pose, running with right foot forward, jumping with fist up, double jumping with arms out, falling, landing crouch. Consistent character scale and side-view proportions, crisp retro pixel art and clean dark outlines. No text, no scenery, no grid lines. Leave generous transparent space around every sprite for easy extraction.

## Production sprite specification

The deterministic replacement uses 32×40 cells on an eight-column grid, the original base Mario frames (the current manifest also includes six additional three-frame ability/victory clips), and the animation durations documented in `ASSETS.md`. It uses dark navy outlines, red cap/shirt, blue overalls, cream gloves, brown shoes, gold buttons, and a compact side-view silhouette. Frames are assembled into shared canvases with a fixed (16,38) foot anchor.

Enemy and prop sheets use the same cell size and display scale. Automated validation checks every referenced frame for nonempty alpha, dimensions, and bounds. Gameplay collision bodies remain independent of changing limb silhouettes.
