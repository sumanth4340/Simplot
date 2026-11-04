# Behavior & Animation — Discovery Notes (live-verified, 6.0.0)

## Time sampling
- Stage: TimeCodesPerSecond=60, FramesPerSecond=24 (mismatched;
  drive everything off timecodes, not frames).
- Author: UsdGeom.Xformable(prim).AddTranslateOp() /
  AddRotateYOp(); attr.Set(value, Usd.TimeCode(tc)).
- Multi-op prims: GetOrderedXformOps() order = authoring order;
  unpack positionally only when you authored both.
- Beyond the last sample the value HOLDS (B4 x_end=2.000 at
  t=3.4s with last sample at 2.0s).

## Reading animated state
- Live timecode: omni.timeline.get_timeline_interface()
  .get_current_time() x stage.GetTimeCodesPerSecond().
- op.Get(tc) for the authored value; UsdGeom.XformCache(tc)
  .GetLocalToWorldTransform(prim).ExtractTranslation() /
  .ExtractRotation() (-> GetAxis/GetAngle-in-degrees) for the
  composed world value. The two agree to 1e-6 (B1 gate).

## Commanding joints at runtime
- Articulation(root).set_dof_position_targets(np.float32 rad)
  applies mid-play in one session; echo via
  get_dof_position_targets (B3: 3 phases, <0.002 error).
- Articulation handle: construct AFTER play starts; fresh
  handle per run is safest (Skill 5 R3).
- USD drive:angular:physics:targetPosition sets at runtime do
  NOT propagate without stop/play re-parse (M3 R4) — never
  command mid-play loops through USD.

## Behavior patterns
- State machine (B3): phase list + fixed step budgets, single
  play session; gate per-phase q AND echoed target AND sign
  flips (three independent signals).
- Trigger (B4): chunked play (10 steps), sense per chunk,
  latch-once flag; trigger lands within one chunk of theory.
- Zone control (V10): command only on zone CHANGE; counts
  transitions (nsw=1) to prove no chatter.

## Session notes
- Sim crashed 3x this skill (run-send connection resets #5-7);
  recovery unchanged: relaunch windowed + bridge poll + rebuild.
- behavior-tree-generation library skill needs NVIDIA_API_KEY +
  AEDG app: unsuitable for deterministic drills; Skill 10 stays
  with scripted behaviors.
