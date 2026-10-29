# Validation report

Test date: October 28, 2026. Environment: macOS, Apple M5 GPU, Python 3.12.14, pygame-ce 2.5.8, ModernGL 5.13.0.

## Automated gameplay

**67 automated tests pass.** The updated unittest suite covers movement, buffering/coyote time, variable jumping, collision/animation independence, all enemy response definitions, projectiles, freezing/kicking/shattering/thawing, Cat climb exits, temporary overlays, reserve swapping, Penguin traction, Cape diving, Mega structure protection, complete progression, skip/reopen completion, snapshot rollback, unique scoring, corrupt saves/replays, remapping/mouse controls, secrets, red sets, practice isolation, fallback and layer protection.

`test_full_courses_and_both_checkpoint_retries_without_powerups` clears all four courses at three jump lead timings (0.27, 0.30, 0.34 seconds) without pickups: **12 full runs and 24 checkpoint continuations**. Red-route validation clears all eight optional platform routes against actual enemies and collects their three marked coins. These tests use actual movement and collision code, not geometric estimates alone.

The separate [course report](course-check.json) adds a timed final-pole double jump and confirms Gold is achievable in every world without abilities. Baseline traversal scores vary with timing and coin collection; this is intentional. The report records each score and duration. These automated policies are reproducible feasibility checks, not a substitute for subjective human difficulty testing.

## Native renderer

`tools/check_graphics.py` opened the native display and compiled the production shaders on **Apple M5**. All four worlds passed orientation/alpha comparison, unchanged HUD checks, enhanced-effect checks, heat protection, reduced-motion stability, resizing, and entering/leaving fullscreen. Final driver status: `GL_NO_ERROR`.

The recorded uncapped 120-frame sample measured **290.9 rendered frames/second** on this machine. The normal loop is capped at 60 FPS. This short controlled sample is not a universal or long-session performance guarantee. Full details: [graphics-check.json](graphics-check.json).

## Visual and package inspection

Rendered screenshots were inspected for menu readability, four-world distinction, ability silhouettes, route surfaces, settings, secret-room feedback and world results. Inspection caught and fixed a stale iris overlay on modal screens and a duplicate settings label. Frame alignment uses a stable foot anchor and collision body. The gameplay GIF contains 192 software-rendered frames (16 seconds at an average 12 FPS) produced by an automated input policy.

The release excludes virtual environments, Python caches, personal saves and ghost recordings. It includes the runtime assets, source, tests, pinned dependencies, launcher, documentation, screenshots and GIF. The archive is CRC checked and its extracted source is tested before delivery; the machine's existing dependency environment is reused for that extraction check. A first-time online installation on a clean second machine was not tested.

## Remaining limits

No browser port, executable bundler, online services or controller support was added. All forms preserve the collision body for safety. Ice blocks are nonblocking; Cat climbing and Penguin sliding are intentionally contextual. Human playtesting remains useful for audio preference, visual comfort, balance over longer sessions and accessibility needs beyond the tested controls/reduced-motion modes.
