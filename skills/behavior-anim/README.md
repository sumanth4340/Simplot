# Skill 10 BEHAVIOR & ANIMATION — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0.0 / Kit 110, windowed GUI, Windows.
Co-validated with graduated skills (X10 gauntlet, 11/11).

## Verified facts (do not guess these)
- Time base: 60 timecodes/sec; samples via
  op.GetAttr().Set(value, Usd.TimeCode(tc)); linear interp exact.
- Read animated values at LIVE time: tc = tl.get_current_time()
  x TimeCodesPerSecond; op.Get(tc) + XformCache(tc)
  .GetLocalToWorldTransform (R1: no GetLocalToWorld here).
- Rotation units differ by layer: xformOp degrees, DOF radians,
  Gf.Rotation.GetAngle DEGREES (R2 unit map).
- Mid-play joint commands MUST use tensor API
  set_dof_position_targets(np radians); USD sets need stop/play
  re-parse per waypoint (R3, M3 R4 re-confirmed).
- Closed-loop pattern: play in N-step chunks, sense, latch
  triggers once; command only on zone change.
- stop() resets playhead to 0 (t0=0.000 verified).

## Dataset (evidence/, replayable)
- B1 translation: 9/9, x 0->1.0->2.0 exact at t 0/0.5/1.0s.
- B2 translate+rotate: 10/10, ry 45/90deg, axis +Y, angle deg.
- B3 state machine: 9/9, q +0.4991/-0.4982/-0.0009, echo exact.
- B4 trigger: 8/8, trig t=1.083 x=1.083, q=0.5991, x_end=2.0.
- V10 exam (gate Y-slide + two-zone arm): 9/9, 1 switch at
  y=t=1.283, q=0.3983, y_end=2.4, ry_end=45.
- X10 cross-val: 11/11 across stage/model/sense/physics/anim/
  behavior lenses.

## Tools (scripts/, in-sim via isaacsim_send.py unless noted)
- bN_build / bN_run (N=1..4), v10_build / v10_run; probe_time,
  probe_cmd, probe_cmd2: time-base + command API probes.
- verify_bN / verify_v10: local evaluators, exit 0 on pass.
- cross-val x10_live.py + verify_x10.py: co-validation snapshot.

## Eval
Suite: B1 B2 B3 B4 V10 (5/5 green) + X10 co-val (11/11).

## Failure catalog
See failures.md (R1-R3).
