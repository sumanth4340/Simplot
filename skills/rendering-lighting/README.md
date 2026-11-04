# Skill 6 RENDERING & LIGHTING — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0.0 / Kit 110, RTX RealTimePathTracing, Windows.
Co-validated with graduated skills (X6 gauntlet, 9/9).

## Verified facts (do not guess these)
- Capture: RtxCamera (pose kwargs) + CameraSensor (resolution as LIST
  [H, W]) + play + settle + get_data("rgb") unwrap-[0]-numpy (R3/R4).
- Installed 6.0.0 API lags skill sketches: no aux_output_level; probe
  signatures live before trusting examples (R3).
- Dome 100->400: 1.30x pixels. filmIso 100->400: 1.49x pixels.
  DistantLight 3x: ~1.07x (OPEN, see R5).
- During-play light sets apply live; re-parse legs add nothing.
- Captures are bit-deterministic; pin exposure per drill (R4/V6).

## Dataset (evidence/, replayable)
- R1 authoring: dome 400, sun 1500, cube 1.0, focal 24, cam at eye.
- R2 capture: 240x320x3, mean 143.6, max 203, 33KB PNG.
- R3 dome ratio: 110.2->143.4 = 1.302.
- R4 filmIso ratio: 143.6->213.2 = 1.485.
- V6 exam (new scene): 10/10, mean 184.5, 40KB PNG.
- X6 cross-val: 9/9 across stage/model/sense/rig/render lenses.

## Tools (scripts/, in-sim via isaacsim_send.py unless noted)
- r1_build, r2_cap, r3_light, r4_expo, v6_build/v6_cap: execution.
- verify_rN/verify_v6: local evaluators, exit 0 on pass.
- cross-val x6_live.py + verify_x6.py: co-validation snapshot.

## Eval
Suite: R1 R2 R3 R4 V6 (5/5 green) + X6 co-val (9/9) at graduation.

## Failure catalog
See failures.md (R1-R5, R5 open).
