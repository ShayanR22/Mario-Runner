# Campaign upgrade checklist

Implemented and validated in the local project. The original four-world renderer and assets were extended in place. No runtime dependencies were added.

## 1. Baseline and campaign foundation

- [x] Established the original 33-test baseline.
- [x] New Game, overwrite confirmation, Continue, Settings, Records, Quit.
- [x] Sequential four-world campaign; campaign world selection removed.
- [x] Skill scoring, opportunity-aware combos, unique reward IDs, medals and records.
- [x] Explicit flagpole grab/slide/hop/walk state machine, skip, reduced motion, and automatic progression.
- [x] Commit-before-animation completion tokens, atomic saves, and legacy-score migration.
- [x] Midpoint and pre-finale checkpoint rollback of all gameplay subsystems.

## 2. Core abilities

- [x] Data-driven ability definitions and reusable activation, attack, update, damage, expiry, serialization.
- [x] Fire: bouncing projectiles, cooldown and active limit, explicit resistances.
- [x] Ice: freeze, kick, shatter, thaw, safe nonblocking frozen blocks.
- [x] Cat: claws, aerial dive, marked-wall climb and automatic safe exit.
- [x] Mushroom: growth presentation, one-hit absorption, fixed safe collision body.
- [x] Star: overlay timer, readable expiry warning and grace.
- [x] Tanooki: tail attack and hold-to-float with double jumping.
- [x] One equipped form and one reserve; keyboard/mouse equivalents.

## 3. Routes, secondary abilities, finales

- [x] Two optional elevated routes per world; actual landing collision and gently moving Sky platforms.
- [x] Route landing tested with the physics; all eight red routes traversed against actual enemies.
- [x] Boomerang: return path, unique hits, coin collection.
- [x] Cape: slower glide and contextual dive.
- [x] Penguin: ice shots, traction and contextual belly slide on the short ice section.
- [x] Mega: timed overlay and breakable ordinary obstacles; required structures preserved.
- [x] Two-encounter world finales reusing taught mechanics, with safe checkpoints and flag approaches.

## 4. Replay and presentation

- [x] Isolated pipe rooms and stable red-set rewards.
- [x] Optional clean-run, limited-use, red-set and flag challenges.
- [x] Medal/challenge cosmetics with preview and equip screen.
- [x] Versioned full-run best ghost, position/form/pose recording and corruption rejection.
- [x] Encounter-gated practice isolated from campaign scores, rewards and replay files.
- [x] Exported transformation and pickup art on the established pixel grid.
- [x] Local power-up/projectile lighting, world atmosphere, protected platforms and pickups.
- [x] Iris reveals, optional impact shake, score popups, reduced motion.
- [x] Separate music/SFX, synthesized music, persistent settings and remapping.
- [x] Gradual decorative quality adaptation.

## 5. Release validation

- [x] Gameplay, save corruption/migration, reward farming, controls, and renderer regression tests.
- [x] No-power-up full runs and both checkpoint retries for all four worlds at three timings.
- [x] Medal calibration: an achievable Gold route in every world using no abilities.
- [x] Native Apple M5 GPU checks, HUD alignment, reduced motion, resize and fullscreen restoration.
- [x] Visually inspected rendered menu, four worlds, Cat/Mushroom, settings, bonus room and results.
- [x] README, interaction table, asset provenance, screenshots and 16-second gameplay GIF.
- [x] Portable ZIP with pinned requirements; extracted package checked before delivery.

## Deliberate limits

- Stable player collision geometry is used across transformations; growth is visual and Mega changes attack interaction rather than blocking clearances.
- Frozen blocks are nonblocking to keep the only safe route open.
- Cat climbing is restricted to marked optional walls; Penguin's skid/slide behavior is confined to the short Underground ice section.
- Finales are compact encounter sequences rather than large bosses.
- A checkpoint-resumed run may set records but cannot replace a full-run ghost with a partial replay.
- Current course spacing favors individual stomps; the underlying aerial-chain scoring rule is supported, but no dedicated three-stomp encounter is advertised.
- Automated traversal and inspected frames establish feasibility and alignment; subjective difficulty and long-session balance still benefit from human playtesting.
