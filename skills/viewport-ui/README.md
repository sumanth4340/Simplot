# Skill 8 VIEWPORT & UI — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0.0 / Kit 110, windowed GUI, Windows.
Co-validated with graduated skills (X8 gauntlet, 8/8).

## Verified facts (do not guess these)
- Viewport shots: library viewport_screenshot.py + output_path;
  1280x720 RGBA in GUI and headless alike.
- Viewport camera: library camera_control.py (look_at eye/target,
  get pose); active cam is /OmniverseKit_Persp.
- Selection: library select_prim.py set/get round-trips exactly.
- App shots: full window incl. UI (size follows window).
- No local PIL: verify via scripts/pngstats.py (stdlib decode).
- Compare views by mean-abs-diff pixels, not means (R2).

## Dataset (evidence/, replayable)
- W1 viewport shot: 1280x720, 172KB, mean 185.1.
- W2 look-at: pose exact, frames differ, std 3.0->21.5.
- W3 app shot + select: 958x981, selection round-trips.
- W4 two views: both valid, pixel-diff 7.59.
- V8 exam (new scene): 9/9, vp 80KB + app 216KB.
- X8 cross-val: 8/8 across stage/model/sense/rig/shot lenses.

## Tools (scripts/, in-sim via isaacsim_send.py unless noted)
- w1_build, v8_build: scene authorship.
- Library scripts (reused via --arg): viewport_screenshot,
  app_screenshot, camera_control, select_prim.
- pngstats.py: stdlib PNG stats + pixel diff (local lib).
- verify_wN/verify_v8: local evaluators, exit 0 on pass.
- cross-val x8_live.py + verify_x8.py: co-validation snapshot.

## Eval
Suite: W1 W2 W3 W4 V8 (5/5 green) + X8 co-val (8/8) at graduation.

## Failure catalog
See failures.md (R1-R2).
