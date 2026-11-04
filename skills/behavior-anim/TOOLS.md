# Behavior-Anim Tool Knowledge (2026-11-04)

Deep reference: TOOLS_REF.md (12 tools, 67 functions, 35 knobs, 29 limits, 14 unknowns; 18/18 scripts fully read).

## Tools

### omni.usd (UsdContext)
- DOES: Provides live stage access inside Isaac Sim.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()`
  - `stage.GetPrimAtPath(path)`, `stage.DefinePrim(path, "Xform")`, `stage.RemovePrim(path)`
  - `stage.GetTimeCodesPerSecond()` (time base = 60)
- LIMITS-live-verified:
  - None drill-proven in this pack beyond usage above.
- UNKNOWN:
  - Whether other UsdContext helpers (selection, layers) work mid-play; not drill-proven here.

### omni.timeline (timeline interface)
- DOES: Reads live sim time during play.
- FUNCTIONS USED:
  - `omni.timeline.get_timeline_interface()`
  - `tl.get_current_time()` (seconds; x TimeCodesPerSecond = live timecode)
- LIMITS-live-verified:
  - `stop()` resets playhead to 0 (README: t0=0.000 verified).
- UNKNOWN:
  - play/pause/step via timeline interface not used here (pack uses app_utils); set_current_time behavior not drill-proven.

### isaacsim.core.experimental.utils.app (app_utils)
- DOES: Drives the sim loop (play/stop/step) from in-sim scripts.
- FUNCTIONS USED:
  - `app_utils.stop()`
  - `app_utils.play(commit=True)`
  - `await app_utils.update_app_async(steps=N)` (5/10/12/30/60-step chunks across drills)
- LIMITS-live-verified:
  - stop() resets playhead to 0 (README verified fact).
  - Sim crashed 3x during this skill (run-send connection resets); recovery = relaunch windowed + bridge poll + rebuild (discovery.md "Session notes").
- UNKNOWN:
  - Exact wall-clock/step determinism of update_app_async chunk sizes; trigger lands within one chunk, not exact (discovery.md "Trigger").

### pxr UsdGeom (Xformable / XformCache / Cube)
- DOES: Authors and reads animated transforms (time-sampled translate/rotate).
- FUNCTIONS USED:
  - `UsdGeom.Cube.Define(stage, path)`, `GetSizeAttr().Set(...)`
  - `UsdGeom.Xformable(prim).AddTranslateOp()`, `.AddRotateYOp()`, `.Set(...)`
  - `op.GetAttr().Set(value, Usd.TimeCode(tc))`, `op.GetAttr().GetTimeSamples()`
  - `UsdGeom.Xformable(prim).GetOrderedXformOps()`, `op.Get(tc)`
  - `UsdGeom.XformCache(tc).GetLocalToWorldTransform(prim)`, `.ExtractTranslation()`, `.ExtractRotation()`
- LIMITS-live-verified:
  - `XformCache` has NO `GetLocalToWorld` in this USD build — use `GetLocalToWorldTransform` (failures.md R1).
  - `GetOrderedXformOps()` order = authoring order; unpack positionally only when you authored both ops (discovery.md "Time sampling").
  - Beyond the last sample the value HOLDS (B4 x_end=2.000 at t=3.4s, last sample 2.0s) (discovery.md).
  - op.Get(tc) and XformCache world value agree to 1e-6 (B1 gate) (discovery.md).
- UNKNOWN:
  - Non-linear interpolation types; only linear interp drill-proven (README).

### pxr Gf (Rotation / Vec types)
- DOES: Rotation math + vector values for authored samples.
- FUNCTIONS USED:
  - `Gf.Vec3d(...)`, `Gf.Vec3f(...)`
  - `rot.GetAxis()`, `rot.GetAngle()`
- LIMITS-live-verified:
  - `Gf.Rotation.GetAngle` returns DEGREES (45.0/90.0), not radians (failures.md R2).
  - Unit map: xformOp rotate = degrees; DOF = radians; GetAngle = degrees — convert at every boundary (failures.md R2).
- UNKNOWN:
  - Nothing further; map is drill-proven.

### pxr Usd / UsdPhysics (stage time + articulation scene graph)
- DOES: TimeCode construction; rigid-body / joint / drive authoring for 1R arms.
- FUNCTIONS USED:
  - `Usd.TimeCode(tc)`
  - `UsdPhysics.RigidBodyAPI.Apply(prim)`, `UsdPhysics.MassAPI.Apply(prim).GetMassAttr().Set(...)`
  - `UsdPhysics.ArticulationRootAPI.Apply(prim)`
  - `UsdPhysics.FixedJoint.Define(...)`, `UsdPhysics.RevoluteJoint.Define(...)`
  - `CreateBody0Rel()/CreateBody1Rel().SetTargets([...])`, `CreateAxisAttr("Y")`
  - `CreateLocalPos0Attr/CreateLocalPos1Attr(...)`
  - `UsdPhysics.LimitAPI.Apply(prim, "rotY")`, `CreateLowAttr/CreateHighAttr(...)` (degrees)
  - `UsdPhysics.DriveAPI.Apply(prim, "angular")`, `CreateTypeAttr("position")`, `CreateTargetPositionAttr().Set(0.0)`, `CreateStiffnessAttr(100.0)`, `CreateDampingAttr(10.0)`
- LIMITS-live-verified:
  - Runtime USD `drive:angular:physics:targetPosition` sets do NOT propagate mid-play without stop/play re-parse — never command mid-play loops through USD (failures.md R3; discovery.md).
  - DriveAPI angular targets are authored in degrees (failures.md R2).
- UNKNOWN:
  - Whether USD drive sets propagate for NON-articulation or non-playing cases; only the mid-play failure is drill-proven.

### isaacsim.core.experimental.prims.Articulation (tensor API)
- DOES: Mid-play joint command + readback in radians (the only working runtime command path).
- FUNCTIONS USED:
  - `Articulation("/World/.../Base")` (constructed AFTER play starts)
  - `robot.set_dof_position_targets(np.array([tgt], dtype=np.float32))` (radians)
  - `robot.get_dof_positions()`, `robot.get_dof_position_targets()` (radians; warp array or ndarray)
- LIMITS-live-verified:
  - Mid-play joint commands MUST use this API; USD sets need stop/play re-parse per waypoint (failures.md R3).
  - Handle: construct AFTER play starts; fresh handle per run is safest (discovery.md).
  - B3 accuracy: q=0.4991/-0.4982/-0.0009 exact, 3 phases <0.002 error (failures.md R3; README dataset).
- UNKNOWN:
  - Multi-DOF indexing/ordering; only single-DOF (1R, flatten()[0]) drill-proven here.

### warp (wp)
- DOES: Tensor-array interop for Articulation readbacks.
- FUNCTIONS USED:
  - `isinstance(q, wp.array)` check, `q.numpy()` conversion to numpy
- LIMITS-live-verified:
  - None drill-proven beyond the isinstance/numpy pattern used in every _q/_e helper.
- UNKNOWN:
  - Whether readbacks are always wp.array vs ndarray across builds; pack handles both.

### numpy (np)
- DOES: Target-vector construction + scalar extraction for DOF commands/reads.
- FUNCTIONS USED:
  - `np.array([tgt], dtype=np.float32)` (command targets)
  - `np.asarray(q, dtype=float).flatten()[0]` (scalar reads)
- LIMITS-live-verified:
  - Targets must be float32 radians (B3 exact to <0.002) (failures.md R3).
- UNKNOWN:
  - Whether float64 targets are accepted; only float32 drill-proven.

### omni.graph.core (og)
- DOES: Enables/disables an OmniGraph graph around a command probe.
- FUNCTIONS USED:
  - `og.get_graph_by_path("/World/V9Graph").set_disabled(True/False)` (probe_cmd2.py only)
- LIMITS-live-verified:
  - None in this pack (single probe usage; graph behavior itself is not this pack's drill).
- UNKNOWN:
  - Why the graph had to be disabled for the command probe; cause not drill-proven here.

### isaacsim_send.py bridge
- DOES: Sends build/run scripts into the live Isaac Sim session for execution.
- FUNCTIONS USED:
  - Pack convention: bN_build/bN_run/v10_build/v10_run/probe_* all "run INSIDE Isaac Sim" via the bridge (README "Tools").
- LIMITS-live-verified:
  - 3 run-send connection resets during this skill; recovery = relaunch + bridge poll + rebuild (discovery.md "Session notes").
- UNKNOWN:
  - Bridge CLI flags / invocation form not shown anywhere in this pack.

### verify_bN / verify_v10 (local evaluators)
- DOES: Local pass/fail evaluation of drill reports (json + regex on *-REPORT lines).
- FUNCTIONS USED:
  - `json`, `re` (+ `math` in verify_b2) stdlib only; exit 0 on pass.
- LIMITS-live-verified:
  - None; evaluators, not sim APIs.
- UNKNOWN:
  - Exact per-drill thresholds live in the verify scripts themselves (skimmed, not fully read).

## Unverified

- behavior-tree-generation library skill (needs NVIDIA_API_KEY + AEDG app; ruled unsuitable for deterministic drills — discovery.md "Session notes"). Not a pack tool; listed so nobody reaches for it here.
- Cross-val x10_live.py + verify_x10.py cited by README ("co-validation snapshot") but NOT present in scripts/ — claimed tool with no source in this pack.
- USD drive targetPosition sets outside mid-play (pre-play authoring works — builds use it; propagation without re-parse only disproven mid-play).
- Multi-DOF Articulation ordering; only 1R single-joint proven.
- update_app_async wall-clock determinism; chunk-granular trigger only.
- og graph disable/enable necessity in probe_cmd2 (single unexamined use).
- isaacsim_send.py exact CLI form (no invocation in pack).

## Sources-read

- action-reasoner/skills/behavior-anim/README.md (FULL; no SKILL.md in pack)
- action-reasoner/skills/behavior-anim/failures.md (FULL)
- action-reasoner/skills/behavior-anim/discovery.md (FULL)
- action-reasoner/skills/behavior-anim/scripts/b3_run.py (FULL)
- action-reasoner/skills/behavior-anim/scripts/b4_run.py (FULL)
- action-reasoner/skills/behavior-anim/scripts/v10_run.py (FULL)
- action-reasoner/skills/behavior-anim/scripts/b1_run.py (FULL)
- action-reasoner/skills/behavior-anim/scripts/b2_run.py (FULL)
- action-reasoner/skills/behavior-anim/scripts/b4_build.py (FULL)
- action-reasoner/skills/behavior-anim/scripts/probe_cmd2.py (FULL)
- action-reasoner/skills/behavior-anim/scripts/v10_build.py (FULL)
- Skimmed by name + imports only (10): b1_build.py, b2_build.py, b3_build.py, probe_cmd.py, probe_time.py, verify_b1.py, verify_b2.py, verify_b3.py, verify_b4.py, verify_v10.py
