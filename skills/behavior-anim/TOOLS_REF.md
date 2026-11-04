# Behavior-Anim TOOLS_REF (FULL-TOOL-MASTERY, 2026-11-04)

Deep reference companion to TOOLS.md. Claim tags: [verified] = drill-proven
in this pack (script + evidence/verify gate); [probable] = strongly implied
by repeated pack usage but never directly gated; [theoretical] = inferred
from API names/general USD knowledge, NOT proven here.

Coverage: 12 tools, 67 functions (67 typed), 35 knobs (35 typed),
29 limits, 14 unknowns. DATATYPE pass: every signature carries exact
param types + return type + units + defaults; call-site-grounded types
cite script:line, ungrounded slots marked [probable]/[theoretical].
Scripts fully read: 18/18 (b1/b2/b3/b4/v10 build+run, probe_time,
probe_cmd, probe_cmd2, verify_b1/b2/b3/b4/v10). No SKILL.md exists in
this pack; README.md is the pack root doc.

---

## 1. omni.usd (UsdContext) — live stage access

DOES: Returns the live USD stage inside Isaac Sim; every build/run
script starts here [verified].

FUNCTIONS (7, all typed):
- `omni.usd.get_context()` -> `omni.usd.UsdContext` [verified: all
  13 in-sim scripts, e.g. b1_build.py:9, b1_run.py:11, probe_time.py:3].
  SIG: `get_context() -> UsdContext`. No params. Returns singleton.
- `ctx.get_stage()` where `ctx: UsdContext` -> `pxr.Usd.Stage`
  [verified: all 13 in-sim scripts, e.g. b1_build.py:9, b1_run.py:11].
  SIG: `UsdContext.get_stage() -> Usd.Stage`. No params.
- `stage.GetPrimAtPath(path: str)` -> `pxr.Usd.Prim` [verified:
  b1_build.py:11, b1_run.py:19, b2_build.py:10, b3_build.py:11,
  b4_build.py:11, v10_build.py:11, b4_run.py:24, v10_run.py:24].
  SIG: `GetPrimAtPath(path: str) -> Usd.Prim`. `path`: prim-path
  string, unit n/a, required positional (no default observed).
  Returns prim or INVALID prim (never None/raises) when missing
  [verified: every build guards with `if o and o.IsValid()`].
- `stage.DefinePrim(path: str, typeName: str)` -> `pxr.Usd.Prim` [verified].
  SIG: `DefinePrim(path: str, typeName: str = "" [theoretical])
  -> Usd.Prim`. `path`: prim-path string, n/a, required. `typeName`:
  USD schema name string, n/a; default "" never observed (both args
  always passed positionally). Used only as
  `DefinePrim("/World/<Bot>", "Xform")` for arm roots [verified:
  b3_build.py:15, b4_build.py:21, v10_build.py:26].
- `stage.RemovePrim(path: str)` -> `bool` [probable return: never checked
  at any call site; True-on-removed per USD convention].
  SIG: `RemovePrim(path: str) -> bool`. `path`: prim-path string,
  n/a, required. Used only for idempotent rebuild teardown
  [verified: b1_build.py:13, b2_build.py:12, b3_build.py:13,
  b4_build.py:13, v10_build.py:14].
- `stage.GetTimeCodesPerSecond()` -> `float` [verified].
  SIG: `GetTimeCodesPerSecond() -> float`. No params. Units:
  timecodes/second. Value 60.0 here. The ONLY time base drills use
  [verified: README, probe_time.py:4, b1_run.py:18].
- `stage.GetFramesPerSecond()` -> `float` [verified].
  SIG: `GetFramesPerSecond() -> float`. No params. Units:
  frames/second. Value 24.0 here. Read once in probe_time.py:4;
  NEVER used in any drill computation [verified: zero refs in bN/v10
  run scripts].

KNOBS (2, both typed):
- `path: str` (prim-path string, unit n/a, required positional, no
  default). Values: "/World/B1Box", "/World/B2Box", "/World/B3Bot",
  "/World/B4Slider", "/World/B4Bot", "/World/V10Gate", "/World/V10Bot"
  [verified: per-build]. EVERY drill hardcodes its own /World/<Name>
  path; changing it requires changing build+run+verify together
  [verified]. Effect-of-change: mismatch => GetPrimAtPath returns
  invalid prim => downstream Xformable/Articulation reads fail
  [probable].
- `typeName: str` (USD schema type name, unit n/a, default ""
  [theoretical: never omitted]). Only value ever passed: "Xform"
  [verified: b3_build.py:15, b4_build.py:21, v10_build.py:26]. Other
  schema type names untested [theoretical-unknown].

EKB RULES:
- IF script runs in-sim THEN first two lines are get_context/get_stage
  BECAUSE no stage handle means no prim access [verified: 13/13].
- IF rebuilding THEN RemovePrim-if-valid before Define BECAUSE stale
  prims keep old samples/joints and corrupt gates [verified: 5/5 builds].
- IF converting time THEN multiply by GetTimeCodesPerSecond, never
  FramesPerSecond, BECAUSE TCPS=60/FPS=24 mismatch is drill-proven
  and every gate runs off timecodes [verified: discovery.md].

LIMITS (2, cited):
- L1: GetPrimAtPath on a missing path yields an invalid prim, not an
  exception; every build checks IsValid [verified: b1_build.py:11-13].
- L2: No other UsdContext helpers (selection, layers, edit targets)
  are used anywhere in this pack [verified-absence: grep of 18 scripts].

UNKNOWN (1):
- U1 [theoretical]: whether selection/layer helpers work mid-play.

## 2. omni.timeline — live sim clock

DOES: Reads the live playhead time during play [verified].

FUNCTIONS (3, all typed):
- `omni.timeline.get_timeline_interface()` -> timeline interface
  object (exact class `ITimeline` [probable: never introspected])
  [verified: b1_run.py:12, b2_run.py:14, b4_run.py:17, v10_run.py:16,
  probe_time.py:5].
  SIG: `get_timeline_interface() -> TimelineInterface [probable]`.
  No params.
- `tl.get_current_time()` where `tl: TimelineInterface` -> `float`
  [verified: b1_run.py:17, b2_run.py:19, b4_run.py:22, v10_run.py:22,
  probe_time.py:6].
  SIG: `get_current_time() -> float`. No params. Units: SECONDS
  (NOT timecode). Live timecode = `now * stage.GetTimeCodesPerSecond()`
  [verified: b1_run.py:18, b2_run.py:20, b4_run.py:23, v10_run.py:23].
- `tl.is_playing()` -> `bool` [verified: probe_time.py:6 prints it].
  SIG: `is_playing() -> bool`. No params. NEVER used in any drill
  decision [verified-absence in bN/v10 runs].

KNOBS (1, typed):
- TCPS multiplier `TCPS: float` in `Usd.TimeCode(now_s * TCPS)`
  (units: timecodes/second, value 60.0 = stage TCPS, not a function
  default — stage property) [verified: b1_run.py:18, b2_run.py:20,
  b4_run.py:23, v10_run.py:23]. Effect-of-change: wrong multiplier
  => reads samples at the wrong time => gates fail by the time-scale
  ratio [probable].

EKB RULES:
- IF reading animated state THEN tc = get_current_time() * TCPS
  BECAUSE get_current_time returns seconds while samples are keyed in
  timecodes [verified: identical line in 4 run scripts].
- IF sampling world state THEN build a fresh Usd.TimeCode per read
  BECAUSE the playhead advances between chunks [verified: _read/_x/_gate
  helpers all recompute tc inside the function].

LIMITS (2, cited):
- L1: `stop()` (via app_utils) resets playhead to 0; t0=0.000 gated
  [verified: README "Verified facts", verify_b1 "playhead reset"].
- L2: get_current_time resolution is chunk-granular in practice;
  trigger lands within one step-chunk of theory, never exact
  [verified: discovery.md "Trigger", verify_b4 tol 0.25s].

UNKNOWN (1):
- U2 [theoretical]: play/pause/step/set_current_time via the timeline
  interface are never called here; behavior unproven in this pack.

## 3. isaacsim.core.experimental.utils.app (app_utils) — sim loop driver

DOES: Drives play/stop/stepped-advance from in-sim scripts [verified].

FUNCTIONS (3, all typed):
- `app_utils.stop()` -> `None` [verified: b1_run.py:28, b2_run.py:32,
  b3_run.py:30, b4_run.py:35, v10_run.py:35].
  SIG: `stop() -> None`. No params. Resets playhead to 0 [verified:
  README].
- `app_utils.play(commit: bool)` -> `None` [verified: b1_run.py:31,
  b2_run.py:34, b3_run.py:32, b4_run.py:37, v10_run.py:37].
  SIG: `play(commit: bool = <unknown> [theoretical]) -> None`.
  `commit`: bool, n/a; ALWAYS passed as `commit=True` (kw); bare
  play() and commit=False never used [verified: 5/5 runs], so the
  default value is unproven.
- `await app_utils.update_app_async(steps: int)` -> `None` (coroutine)
  [verified: b1_run.py:29/32/34, b2_run.py:33/35/37, b3_run.py:31/33/38,
  b4_run.py:36/38/42, v10_run.py:36/38/43, probe_cmd.py:4, probe_cmd2.py:8].
  SIG: `update_app_async(steps: int) -> Coroutine[None]`. `steps`:
  int, unit sim-steps (~1/60 s each [probable]), required kw (no
  default observed; always passed as `steps=N`). N values used: 5
  (settle), 10 (settle/chunk), 12 (V10 chunk), 30 (B1/B2 half-second
  legs), 60 (B3 phases, probe_cmd2 soak) [verified: per-script].

KNOBS (2, both typed):
- `commit: bool` (unit n/a, default unknown [theoretical-unknown]):
  invariant value True across the pack [verified: 5/5 runs].
  Effect-of-change: commit=False or omitted is UNTESTED here; do not
  vary it.
- `steps: int` (unit sim-steps, ~1/60 s each [probable]; required kw,
  no default observed): chunk size. Values 5/10/12/30/60 [verified].
  Small (5-12) = sense/react granularity for triggers and zone
  control; large (30-60) = traverse-to-checkpoint or let a position
  drive settle [verified: B4/V10 chunks vs B3 phases].
  Effect-of-change: bigger chunk => coarser trigger/switch timing
  (lands within one chunk) but fewer loop iterations [verified:
  discovery.md "Trigger"]; too-small settle (<5) untested [theoretical].

EKB RULES:
- IF starting a run THEN stop() + settle-chunk (5-10 steps) + play()
  BECAUSE stop resets the playhead to a known t0 [verified: 5/5 runs].
- IF closed-loop sensing THEN chunked play (10-12 steps) + sense per
  chunk BECAUSE one long play() gives no mid-flight reads [verified:
  B4 20x10, V10 20x12].
- IF commanding a joint THEN soak 60 steps per phase BECAUSE the
  position drive (stiffness 100/damping 10) needs settle time to hit
  <0.002 error [verified: B3 STEPS=60].

LIMITS (3, cited):
- L1: stop() resets playhead to 0 [verified: README, b1_run.py:28-30].
- L2: Sim crashed 3x during this skill (run-send connection resets
  #5-7); recovery = relaunch windowed + bridge poll + rebuild
  [verified: discovery.md "Session notes"].
- L3: Trigger/switch timing is chunk-granular, not exact
  [verified: discovery.md, verify_b4 tol 0.25, verify_v10 tol 0.3].

UNKNOWN (1):
- U3 [theoretical]: wall-clock vs step-count determinism of
  update_app_async chunk sizes is unproven.

## 4. pxr UsdGeom — animated transforms (author + read)

DOES: Authors time-sampled translate/rotate ops and reads them back at
live time, both as raw op values and composed world matrices [verified].

FUNCTIONS (15, all typed; last bullet holds 2 methods):
- `UsdGeom.Cube.Define(stage: Usd.Stage, path: str)` -> `UsdGeom.Cube` schema
  [verified: b1_build.py:15, b2_build.py:14, b3_build.py:17/26,
  b4_build.py:15/23/32, v10_build.py:16/28/37].
  SIG: `Cube.Define(stage: Usd.Stage, path: str) -> UsdGeom.Cube`.
  Both required positional (no defaults observed). Binds a Cube
  schema at path (creates prim).
- `cube.GetSizeAttr().Set(size: float)` -> `None` [verified: b1_build.py:16,
  b2_build.py:15, b3_build.py:18/27, b4_build.py:16/24/33,
  v10_build.py:17/29/38].
  SIG: `GetSizeAttr() -> Usd.Attribute` (no params); then
  `Attribute.Set(size: float, time: Usd.TimeCode =
  Usd.TimeCode.Default() [probable]) -> bool [probable return:
  never checked]`. `size`: float, unit m (cube edge, stage units =
  meters [probable]); `time` never passed here (static default).
  Sizes: 0.5 (B1/B2 boxes), 0.4 (B4 slider, V10 gate), 0.15 (arm
  base), 0.2 (arm link) [verified: per-build].
- `UsdGeom.Xformable(prim: Usd.Prim)` -> `UsdGeom.Xformable` wrapper [verified:
  b1_build.py:17, b1_run.py:23, b2_build.py:16, b2_run.py:22,
  b3_build.py:16, b4_run.py:25, v10_run.py:25, v10_build.py:56].
  SIG: `Xformable(prim: Usd.Prim) -> UsdGeom.Xformable`. Single
  required positional prim; no other args observed.
- `xf.AddTranslateOp()` -> `UsdGeom.XformOp` [verified:
  b1_build.py:17, b2_build.py:17, b3_build.py:16/19/28,
  b4_build.py:17/22/25/34, v10_build.py:19/27/30/39].
  SIG: `AddTranslateOp() -> UsdGeom.XformOp`. No args passed at any
  call site (optional USD opSuffix/precision params [theoretical],
  never used).
- `xf.AddRotateYOp()` -> `UsdGeom.XformOp` [verified:
  b2_build.py:20, v10_build.py:22].
  SIG: `AddRotateYOp() -> UsdGeom.XformOp`. No args passed (optional
  USD params [theoretical], never used). Only rotation axis ever
  authored [verified].
- `xop.Set(value: Gf.Vec3d)` (no TimeCode) -> static default [verified:
  arm-root offsets b3_build.py:16, b4_build.py:22, v10_build.py:27;
  base/link offsets b3_build.py:19/28, b4_build.py:25/34,
  v10_build.py:30/39].
  SIG: `XformOp.Set(value: Gf.Vec3d, time: Usd.TimeCode =
  Usd.TimeCode.Default() [probable]) -> bool [probable return]`.
  Only Gf.Vec3d translate values observed (unit m [probable]);
  static rotate Set unobserved [theoretical]. Distinct from
  time-sampled Set below.
- `xop.GetAttr()` -> `pxr.Usd.Attribute` [verified: b1_build.py:18,
  b2_build.py:18/21, b4_build.py:18, v10_build.py:20/23].
  SIG: `XformOp.GetAttr() -> Usd.Attribute`. No params.
- `attr.Set(value: Gf.Vec3d | float, time: Usd.TimeCode)` -> time sample write [verified].
  SIG: `Attribute.Set(value: Gf.Vec3d | float, time: Usd.TimeCode)
  -> bool [probable return]`. Both required positional (no defaults
  observed). Translate takes Gf.Vec3d (unit m [probable]) [verified:
  b1_build.py:19-20, b2_build.py:18-19, b4_build.py:18-19,
  v10_build.py:20-21]; rotateY takes float (unit DEGREES) [verified:
  b2_build.py:21-22, v10_build.py:23-24]; `time`: TimeCode, unit
  timecodes.
- `attr.GetTimeSamples()` -> `list[float]` [verified: b1_build.py:21,
  b2_build.py:26-27, b4_build.py:52, v10_build.py:58-59].
  SIG: `Attribute.GetTimeSamples() -> list[float]`. No params.
  Elements: float, unit timecodes. Always 2 samples here.
- `xf.GetOrderedXformOps()` -> `list[UsdGeom.XformOp]`, authoring
  order [verified: b2_build.py:23, b1_run.py:23, b2_run.py:22,
  b4_run.py:25, v10_run.py:25, v10_build.py:56; discovery.md "Time
  sampling"].
  SIG: `GetOrderedXformOps() -> list[XformOp]`. No params observed.
- `op.GetOpType()` -> `pxr.Tf.Token` (str-like) [verified:
  b2_build.py:23 reports op types; values never gated beyond ops=2
  count].
  SIG: `XformOp.GetOpType() -> Tf.Token`. No params.
- `op.Get(time: Usd.TimeCode)` -> authored value at tc (interp'd) [verified:
  b1_run.py:24, b2_run.py:23-24, b4_run.py:26, v10_run.py:26].
  SIG: `XformOp.Get(time: Usd.TimeCode) -> Gf.Vec3d | float`.
  `time`: TimeCode, unit timecodes, required positional. Translate
  -> Gf.Vec3d (m [probable]); rotateY -> float (deg). Linear interp
  exact [verified].
- `UsdGeom.XformCache(time: Usd.TimeCode)` -> `UsdGeom.XformCache` [verified:
  b1_run.py:20, b2_run.py:25].
  SIG: `XformCache(time: Usd.TimeCode) -> UsdGeom.XformCache`.
  Single required positional TimeCode (unit timecodes).
- `cache.GetLocalToWorldTransform(prim: Usd.Prim)` -> `Gf.Matrix4d` [verified:
  b1_run.py:21, b2_run.py:25].
  SIG: `GetLocalToWorldTransform(prim: Usd.Prim) -> Gf.Matrix4d`.
  `prim`: Usd.Prim, required positional. Matrix translation part in
  m [probable]. NOTE: `GetLocalToWorld` does NOT exist in this USD
  build (AttributeError) [verified: failures.md R1].
- `matrix.ExtractTranslation()` -> `Gf.Vec3d` (unit m [probable])
  [verified: b1_run.py:21-22]; `matrix.ExtractRotation()` ->
  `Gf.Rotation` (angle read in deg via GetAngle) [verified:
  b2_run.py:26].
  SIG: `ExtractTranslation() -> Gf.Vec3d`; `ExtractRotation() ->
  Gf.Rotation`. No params on either.

KNOBS (6, all typed):
- Cube `size: float` (unit m = stage length unit [probable]; USD Cube
  default 1.0 [theoretical: always Set here, never defaulted]).
  Values 0.15/0.2/0.4/0.5 [verified: per-build]. Visual/collision
  scale only; no gate depends on it [probable: sizes vary with
  identical gate shapes].
- Sample `value`s: translate `Gf.Vec3d` (unit m [probable]) /
  rotateY `float` (unit deg); required args, no defaults. Define the
  motion; x 0->2.0, y 0->2.4, ry 0->90/45 [verified]. Effect: gates
  compare against these exact endpoints [verified: verify scripts].
- Sample `timecodes: float` (unit timecodes @60 tc/s, so
  0/60/120/144 => 0s/1.0s/2.0s/2.4s; required args, no defaults)
  [verified: b1_build.py:19-20, b4_build.py:18-19,
  v10_build.py:20-21/23-24]. Effect: doubling span halves apparent
  speed; trigger/switch theory times shift 1:1 [verified].
- Op authoring order: `call-order -> list[XformOp]` (type = sequence
  convention, unit n/a, no default — order = Add* call order).
  Translate first, rotate second [verified: b2_build.py:17-22,
  v10_build.py:19-24]. GetOrdered callers unpack positionally
  (`tops, rops = ...`) [verified: b2_run.py:22, v10_run.py:25].
  Effect-of-change: reordering breaks positional unpack
  [verified-rule: discovery.md "unpack positionally only when you
  authored both"].
- Static `Set(value: Gf.Vec3d)` on arm offsets (unit m [probable];
  default = unvarying transform): default (unvarying) transform
  [verified: b3_build.py:16/19/28]. Effect: moves whole arm; no gate
  reads it back [probable].
- Read index `i: int` (`[0]`/`[1]` into Vec3d op values; unit n/a =
  axis selector, no default): [0]=x, [1]=y component [verified:
  b1_run.py:22/24 x, v10_run.py:26 y]. Effect: wrong index reads the
  wrong axis [verified by construction].

EKB RULES:
- IF authoring motion THEN attr.Set(value, Usd.TimeCode(tc)) with >=2
  samples BECAUSE single-sample gives no interpolation [verified].
- IF reading world state THEN prefer op.Get(tc) for the authored value
  AND XformCache world matrix as the independent cross-check BECAUSE
  the two agreeing to 1e-6 proves the composition path [verified:
  B1 gate "mid op==world", B2 axis/angle cross-check].
- IF multi-op prim THEN unpack GetOrderedXformOps positionally ONLY
  when you authored the ops in that order BECAUSE order = authoring
  order, not semantic order [verified: discovery.md].
- IF composing rotation reads THEN ExtractRotation -> GetAxis/GetAngle
  BECAUSE it is independent of the authored op value [verified: B2].

LIMITS (5, cited):
- L1: No `GetLocalToWorld`; use `GetLocalToWorldTransform`
  [verified: failures.md R1, b1_run.py:21].
- L2: Beyond the last sample the value HOLDS (B4 x_end=2.000 at
  t=3.4s, last sample 2.0s) [verified: discovery.md, verify_b4].
- L3: op.Get(tc) and XformCache agree to 1e-6 [verified: verify_b1
  "mid op==world", discovery.md].
- L4: Only LINEAR interpolation drill-proven [verified: README].
- L5: Only rotateY authored; other axes untested [verified-absence].

UNKNOWN (2):
- U4 [theoretical]: non-linear interpolation types (Bezier etc.).
- U5 [theoretical]: rotateX/Z and scale-op behavior.

## 5. pxr Gf — rotation math + vector values

DOES: Vector values for authored samples; axis/angle extraction from
world matrices [verified].

FUNCTIONS (4, all typed):
- `Gf.Vec3d(x: float, y: float, z: float)` -> `Gf.Vec3d` double vector [verified:
  b1_build.py:19-20, b2_build.py:18-19, b3_build.py:16/19/28,
  b4_build.py:18-19/22, v10_build.py:20-21/27].
  SIG: `Vec3d(x: float, y: float, z: float) -> Gf.Vec3d`. All three
  required positional (no defaults observed). Units: m when used as
  translate sample/offset [probable].
- `Gf.Vec3f(x: float, y: float, z: float)` -> `Gf.Vec3f` float vector [verified:
  b3_build.py:35-36, b4_build.py:41-42, v10_build.py:46-47].
  SIG: `Vec3f(x: float, y: float, z: float) -> Gf.Vec3f`. All three
  required positional. Units: m (joint local-pos) [probable].
- `rot.GetAxis()` where `rot: Gf.Rotation` -> `Gf.Vec3d` unit axis
  [verified: b2_run.py:27; gated as +Y within 0.05 per component in
  verify_b2.py:17-19].
  SIG: `Rotation.GetAxis() -> Gf.Vec3d`. No params. Unitless unit
  vector.
- `rot.GetAngle()` -> `float` DEGREES (45.0/90.0), NOT radians
  [verified: b2_run.py:29, failures.md R2, verify_b2 gates g1~45 g2~90].
  SIG: `Rotation.GetAngle() -> float`. No params. Units: degrees.

KNOBS (2, both typed):
- Vector components `x, y, z: float` (double for Vec3d, float for
  Vec3f; unit m [probable] for translate/local-pos uses; required
  positional, no defaults): position/offset values per drill
  [verified]. Effect: 1:1 with authored motion [verified].
- Rotation axis choice: authoring `axis: str` token ("Y" observed via
  CreateAxisAttr [verified: b3_build.py:34]); read `Gf.Vec3d` unit
  vector (GetAxis [verified: b2_run.py:27]). Unit n/a / unitless;
  no defaults observed. Always Y [verified]. Effect-of-change: other
  axes untested [theoretical].

EKB RULES:
- IF crossing a rotation boundary THEN convert units explicitly
  BECAUSE xformOp=degrees, DOF=radians, GetAngle=degrees [verified:
  failures.md R2 unit map].
- IF gating rotation THEN check axis AND angle (two signals) BECAUSE
  angle alone cannot catch a wrong-axis author [verified: verify_b2
  "axis +Y" + "angle 45deg"].

LIMITS (2, cited):
- L1: GetAngle returns degrees [verified: failures.md R2].
- L2: Unit map (op deg / DOF rad / GetAngle deg) is drill-proven and
  complete for this pack [verified: failures.md R2].

UNKNOWN (0): none; map is drill-proven.

## 6. pxr Usd / UsdPhysics — time + 1R arm authoring

DOES: TimeCode construction; rigid-body/joint/drive authoring for the
1R behavior arms (B3/B4/V10 share one pattern) [verified].

FUNCTIONS (18, all typed; joint bullets each hold 2+ methods):
- `Usd.TimeCode(tc: float)` -> `pxr.Usd.TimeCode` [verified: b1_build.py:19-20,
  b2_build.py:18-19/21-22, b1_run.py:18, b2_run.py:20, b4_build.py:18-19,
  b4_run.py:23, v10_build.py:20-21/23-24, v10_run.py:23].
  SIG: `TimeCode(tc: float) -> Usd.TimeCode`. `tc`: float, unit
  timecodes (seconds * 60), required positional (no default observed).
- `UsdPhysics.RigidBodyAPI.Apply(prim: Usd.Prim)` -> `UsdPhysics.RigidBodyAPI`
  [verified: b3_build.py:20/29, b4_build.py:26/35, v10_build.py:31/40].
  SIG: `RigidBodyAPI.Apply(prim: Usd.Prim) -> RigidBodyAPI`. `prim`:
  Usd.Prim, required positional. Applied to base+link in 3/3 builds.
- `UsdPhysics.MassAPI.Apply(prim: Usd.Prim).GetMassAttr().Set(m: float)` [verified:
  b3_build.py:21/30, b4_build.py:27/36, v10_build.py:32/41].
  SIG: `MassAPI.Apply(prim: Usd.Prim) -> MassAPI` (prim required);
  `GetMassAttr() -> Usd.Attribute` (no params); `Set(m: float) ->
  bool [probable return: never checked]`. `m`: float, unit kg
  [probable]. Base m=2.0, link m=0.5, always [verified: 3/3 builds].
- `UsdPhysics.ArticulationRootAPI.Apply(prim: Usd.Prim)` ->
  `UsdPhysics.ArticulationRootAPI` [verified: b3_build.py:22,
  b4_build.py:28, v10_build.py:33].
  SIG: `ArticulationRootAPI.Apply(prim: Usd.Prim) ->
  ArticulationRootAPI`. `prim`: Usd.Prim (the Base prim),
  required positional. Applied to Base, the Articulation() path root.
- `UsdPhysics.FixedJoint.Define(stage: Usd.Stage, path: str)` -> `UsdPhysics.FixedJoint`
  [verified: b3_build.py:23, b4_build.py:29, v10_build.py:34].
  SIG: `FixedJoint.Define(stage: Usd.Stage, path: str) ->
  UsdPhysics.FixedJoint`. Both required positional. RootFixed welds
  /World/Bot -> /World/Bot/Base [verified: 3/3].
- `UsdPhysics.RevoluteJoint.Define(stage: Usd.Stage, path: str)` ->
  `UsdPhysics.RevoluteJoint` [verified: b3_build.py:31, b4_build.py:37,
  v10_build.py:42].
  SIG: `RevoluteJoint.Define(stage: Usd.Stage, path: str) ->
  UsdPhysics.RevoluteJoint`. Both required positional. Hinge1,
  Base -> Link [verified: 3/3].
- `joint.CreateBody0Rel().SetTargets(paths: list[str])` /
  `joint.CreateBody1Rel().SetTargets(paths: list[str])` [verified:
  b3_build.py:24-25/32-33, b4_build.py:30-31/38-39,
  v10_build.py:35-36/43-44].
  SIG: `CreateBody0Rel() -> Usd.Relationship` (no params);
  `CreateBody1Rel() -> Usd.Relationship` (no params);
  `Relationship.SetTargets(paths: list[str]) -> bool [probable
  return: never checked]`. `paths`: list of prim-path strings
  (single-element observed), n/a, required positional. Fixed
  (Bot,Base); Hinge (Base,Link) [verified: 3/3].
- `hinge.CreateAxisAttr(value: str)` ("Y" observed) -> `Usd.Attribute` [verified:
  b3_build.py:34, b4_build.py:40, v10_build.py:45].
  SIG: `CreateAxisAttr(value: str = <unknown> [theoretical]) ->
  Usd.Attribute`. `value`: axis token string ("X"|"Y"|"Z"
  [probable set; only "Y" ever passed]), n/a. Always passed
  positionally, so the default is unproven. Only "Y" ever used.
- `hinge.CreateLocalPos0Attr(value: Gf.Vec3f)` (= (0,0,0.075) here) /
  `hinge.CreateLocalPos1Attr(value: Gf.Vec3f)` (= (0,0,-0.1) here) -> `Usd.Attribute`
  [verified: b3_build.py:35-36, b4_build.py:41-42, v10_build.py:46-47].
  SIG: `CreateLocalPos0Attr(value: Gf.Vec3f) -> Usd.Attribute`;
  `CreateLocalPos1Attr(value: Gf.Vec3f) -> Usd.Attribute`. `value`:
  Gf.Vec3f, unit m [probable], required positional (no defaults
  observed). Identical values in 3/3 builds.
- `UsdPhysics.LimitAPI.Apply(prim: Usd.Prim, name: str)` ("rotY" observed) ->
  `UsdPhysics.LimitAPI` [verified: b3_build.py:37, b4_build.py:43,
  v10_build.py:48].
  SIG: `LimitAPI.Apply(prim: Usd.Prim, name: str) -> LimitAPI`.
  `prim`: hinge prim, required; `name`: instance-name string
  ("rotY" observed), n/a, required positional.
- `lim.CreateLowAttr(value: float)` (-170.0) / `lim.CreateHighAttr(value: float)` (+170.0) ->
  `Usd.Attribute` [verified: b3_build.py:38-39, b4_build.py:44-45,
  v10_build.py:49-50].
  SIG: `CreateLowAttr(value: float) -> Usd.Attribute`;
  `CreateHighAttr(value: float) -> Usd.Attribute`. `value`: float,
  unit DEGREES, required positional. Identical +-170 in 3/3 builds.
- `UsdPhysics.DriveAPI.Apply(prim: Usd.Prim, name: str)` ("angular" observed) ->
  `UsdPhysics.DriveAPI` [verified: b3_build.py:40, b4_build.py:46,
  v10_build.py:51].
  SIG: `DriveAPI.Apply(prim: Usd.Prim, name: str) -> DriveAPI`.
  `prim`: hinge prim, required; `name`: drive-name string
  ("angular" observed), n/a, required positional.
- `drv.CreateTypeAttr(value: str)` ("position" observed) -> `Usd.Attribute` [verified:
  b3_build.py:41, b4_build.py:47, v10_build.py:52].
  SIG: `CreateTypeAttr(value: str) -> Usd.Attribute`. `value`: drive
  type token string ("position" observed; "velocity"/"force"
  [theoretical]), n/a, required positional. Only type used.
- `drv.CreateTargetPositionAttr().Set(v: float)` (0.0 degrees, pre-play
  authoring) [verified: b3_build.py:42, b4_build.py:48, v10_build.py:53].
  SIG: `CreateTargetPositionAttr() -> Usd.Attribute` (no params);
  `Attribute.Set(v: float) -> bool [probable return: never checked]`.
  `v`: float, unit DEGREES (pre-play authoring). Works as INITIAL
  target; mid-play USD rewrites do NOT propagate [verified:
  failures.md R3].
- `drv.CreateStiffnessAttr(value: float)` (100.0) / `drv.CreateDampingAttr(value: float)` (10.0) ->
  `Usd.Attribute` [verified: b3_build.py:43-44, b4_build.py:49-50,
  v10_build.py:54-55].
  SIG: `CreateStiffnessAttr(value: float) -> Usd.Attribute`;
  `CreateDampingAttr(value: float) -> Usd.Attribute`. `value`:
  float, required positional. Units: stiffness = torque/angle,
  damping = torque/angular-velocity [theoretical: exact unit
  convention unproven here]. Identical 100.0/10.0 in 3/3 builds.
- `prim.IsValid()` -> `bool` [verified: b1_build.py:12/22,
  b2_build.py:11/24, b3_build.py:12/45-46, b4_build.py:12/51-53,
  v10_build.py:12/57-59].
  SIG: `Usd.Prim.IsValid() -> bool`. No params. Every build/run
  validity gate.
- `schema.GetPrim()` -> `pxr.Usd.Prim` (Cube/Joint .GetPrim())
  [verified: b1_build.py:17, b2_build.py:16, b3_build.py:19-23/27-31,
  b4_build.py:17/23, v10_build.py:18/28].
  SIG: `UsdSchema.GetPrim() -> Usd.Prim`. No params. Used to pass
  prims into Xformable/Physics APIs.

KNOBS (8, all typed):
- Masses `m: float` (unit kg [probable]; USD default mass unproven
  [theoretical: always Set]): 2.0 (base) / 0.5 (link), invariant
  [verified: 3/3 builds]. Effect-of-change: untested; heavier link
  likely needs longer soak or stiffer drive [theoretical].
- Axis `value: str` token (unit n/a; default unproven [theoretical]):
  "Y" invariant [verified: 3/3]. Other axes untested [theoretical].
- LocalPos `value: Gf.Vec3f` (unit m [probable]; default unproven
  [theoretical]): (0,0,0.075)/(0,0,-0.1) hinge frame offsets,
  invariant [verified: 3/3]. Effect: hinge pivot placement [probable].
- Limits `value: float` (unit deg; default unproven [theoretical]):
  +-170deg, never approached (max |q|=0.6 rad ~ 34deg) [verified:
  b4_run.py:18]. Effect: commands beyond limits untested [theoretical].
- Drive type `value: str` token (unit n/a; default unproven
  [theoretical]): "position" invariant [verified: 3/3].
  "velocity"/"force" untested [theoretical].
- Stiffness `value: float` / damping `value: float` (units torque/
  angle and torque/angular-velocity [theoretical]; defaults unproven
  [theoretical]): 100 / 10 invariant; B3 hits <0.002 error with
  60-step soaks [verified: b3_run.py:15]. Effect: softer drive =>
  longer settle or steady-state error [theoretical].
- Initial target `v: float` (unit deg; USD default target unproven
  [theoretical: always Set]): 0.0, pre-play authoring works
  [verified: b3_build.py:42, b4_build.py:48, v10_build.py:53].
  Effect: arm starts at 0 before first tensor command [probable].
- TimeCode `tc: float` (unit timecodes = s * 60; required arg, no
  default): values 0/60/120/144 [verified]. See UsdGeom sample-time
  knob [verified].

EKB RULES:
- IF building an arm THEN copy the B3 pattern verbatim (masses, axis,
  frames, limits, drive) BECAUSE B4/V10 reuse it byte-identically and
  all gates pass [verified: 3/3 builds].
- IF commanding mid-play THEN use the tensor API, NEVER USD drive
  sets, BECAUSE USD sets need stop/play re-parse per waypoint
  [verified: failures.md R3, discovery.md].
- IF authoring pre-play targets THEN USD DriveAPI Set works BECAUSE
  builds use it and runs start from it [verified: builds + B3 HOME].
- IF applying ArticulationRoot THEN apply to the prim you will pass
  to Articulation(path) BECAUSE the tensor handle roots there
  [verified: Base in 3/3 builds, Articulation(".../Base") in runs].

LIMITS (3, cited):
- L1: Runtime USD `drive:angular:physics:targetPosition` sets do NOT
  propagate mid-play without stop/play re-parse [verified:
  failures.md R3, discovery.md, b3_run docstring].
- L2: DriveAPI angular targets authored in degrees [verified:
  failures.md R2].
- L3: Pre-play USD authoring DOES work (builds set initial 0.0)
  [verified: b3/b4/v10 builds].

UNKNOWN (2):
- U6 [theoretical]: whether USD drive sets propagate for
  non-articulation or non-playing cases.
- U7 [theoretical]: multi-joint arms, other axes/limits/drives.

## 7. isaacsim.core.experimental.prims.Articulation — runtime joint I/O

DOES: Mid-play joint command + readback in radians; the ONLY working
runtime command path [verified: failures.md R3].

FUNCTIONS (4, all typed):
- `Articulation(path: str)` ("/World/<Bot>/Base") -> `Articulation` handle
  [verified: b3_run.py:34, b4_run.py:39, v10_run.py:39, probe_cmd.py:5,
  probe_cmd2.py:6].
  SIG: `Articulation(path: str) -> Articulation`. `path`: prim-path
  string, n/a, required positional (extra kwargs like device
  [theoretical], never passed). Constructed AFTER play starts (after
  play() + 5-10 settle steps) [verified: 3/3 runs]; fresh handle per
  run is safest [verified: discovery.md Skill 5 R3].
- `robot.set_dof_position_targets(targets: np.ndarray)` (float32 rad, shape (1,))
  -> `None` [verified: b3_run.py:37, b4_run.py:46-47, v10_run.py:41/
  48-49, probe_cmd2.py:7].
  SIG: `set_dof_position_targets(targets: np.ndarray[float32,
  shape (1,)]) -> None`. `targets`: float32 1-element ndarray, unit
  RADIANS, required positional. Values: B3 +0.5/-0.5/0.0, B4 +0.6,
  V10 +-0.4, probe_cmd2 +0.5. Applies mid-play, single session
  [verified: B3 q=0.4991/-0.4982/-0.0009].
- `robot.get_dof_positions()` -> `wp.array | np.ndarray` [verified:
  b3_run.py:19, b4_run.py:30, v10_run.py:30, probe_cmd2.py:9].
  SIG: `get_dof_positions() -> wp.array | np.ndarray`. No params.
  Units: radians; shape (1,) single-DOF [verified]. Scalar via
  `float(np.asarray(q, dtype=float).flatten()[0])` [verified].
- `robot.get_dof_position_targets()` -> `wp.array | np.ndarray`
  [verified: _e helper b3_run.py:24-27; gated EXACT to 1e-6].
  SIG: `get_dof_position_targets() -> wp.array | np.ndarray`. No
  params. Units: radians (echoed targets); shape (1,) [verified].

KNOBS (3, all typed):
- Root `path: str` (prim-path string, unit n/a, required positional,
  no default): always ".../Base" (the ArticulationRoot prim)
  [verified: 5/5 uses: b3_run.py:34, b4_run.py:39, v10_run.py:39,
  probe_cmd.py:5, probe_cmd2.py:6]. Effect: wrong path => no/invalid
  handle [probable].
- Target values `tgt: float` elements in float32 ndarray (unit rad;
  required arg, no default): +-0.4/0.5/0.6/0.0 used [verified].
  Effect: 1:1 with settled q within <0.002 (B3) [verified].
- Handle timing: `ordering constraint` (type = call-order convention,
  unit n/a, no default): construct after play() + 5-10 settle steps,
  invariant [verified: 3/3 runs]. Effect-of-change: constructing
  pre-play untested here [theoretical].

EKB RULES:
- IF commanding joints mid-play THEN Articulation.set_dof_position_
  targets with float32 radians BECAUSE it is the only path that
  propagates without re-parse [verified: failures.md R3].
- IF reading q THEN handle both wp.array (.numpy()) and ndarray
  BECAUSE readback type varies across builds [verified: identical
  _q/_e pattern in 4 scripts].
- IF discovering API THEN probe `dir(obj: object)` (= `dir(art: Articulation)`, probe_cmd.py:6) filtered live (Skill 6 R3
  rule) BECAUSE guessed method names fail (cf. R1) [verified:
  probe_cmd.py].
- IF gating a phase THEN check q AND echoed target AND sign flips
  (three independent signals) BECAUSE echo proves the command landed
  while q proves the physics followed [verified: discovery.md "State
  machine", verify_b3].

LIMITS (4, cited):
- L1: Mid-play commands MUST use this API [verified: failures.md R3].
- L2: Construct AFTER play starts; fresh handle per run safest
  [verified: discovery.md].
- L3: B3 accuracy <0.002 error, echo exact to 1e-6 [verified:
  README dataset, verify_b3].
- L4: Only single-DOF (1R, flatten()[0]) drill-proven [verified].

UNKNOWN (1):
- U8 [theoretical]: multi-DOF indexing/ordering.

## 8. warp (wp) — tensor-array interop

DOES: Type-check + conversion for Articulation readbacks [verified].

FUNCTIONS (2, both typed):
- `isinstance(obj: wp.array | np.ndarray, cls: type)` (= (q, wp.array)) -> `bool` (Python builtin) [verified:
  b3_run.py:20/26, b4_run.py:31, v10_run.py:31, probe_cmd2.py:10].
  SIG: `isinstance(obj: wp.array | np.ndarray, cls: type = wp.array)
  -> bool`. `obj`: DOF readback of either container type; `cls`:
  always the wp.array class here. The branch guard.
- `q.numpy()` where `q: wp.array` -> `np.ndarray` [verified: same
  sites]. SIG: `wp.array.numpy() -> np.ndarray`. No params. Dtype/
  shape float/(1,) here [probable: never asserted, only flattened].
  Only called on the wp.array branch.

KNOBS (0): pure interop pattern; no tunable values [verified].

EKB RULES:
- IF reading DOFs THEN `q.numpy() if isinstance(q, wp.array) else
  np.asarray(q)` BECAUSE readbacks arrive as either type [verified:
  5 identical sites across 4 scripts].

LIMITS (1, cited):
- L1: Nothing drill-proven beyond the isinstance/numpy pattern
  [verified-absence: no other wp.* call in 18 scripts].

UNKNOWN (1):
- U9 [theoretical]: whether readbacks are always wp.array vs ndarray
  across builds; pack handles both.

## 9. numpy (np) — target vectors + scalar reads

DOES: Command-target construction (float32 radians) and scalar
extraction from readbacks [verified].

FUNCTIONS (4, all typed):
- `np.array(object: list[float], dtype: np.dtype)` (= ([tgt], float32)) -> command vector [verified:
  b3_run.py:37, b4_run.py:46-47, v10_run.py:41/48-49, probe_cmd2.py:7].
  SIG: `np.array(object: list[float], dtype: np.dtype = np.float32)
  -> np.ndarray[float32, shape (1,)]`. `object`: 1-element list,
  unit radians; `dtype`: always np.float32 here (numpy default
  float64 [theoretical: never relied on]). ALWAYS float32,
  single-element [verified: 5/5 command sites].
- `np.asarray(a: wp.array | np.ndarray, dtype: type | None)` -> `np.ndarray`
  [verified: b3_run.py:20-21/26-27, b4_run.py:31-32, v10_run.py:31-32,
  probe_cmd2.py:10-11].
  SIG: `np.asarray(a: wp.array | np.ndarray, dtype: type | None =
  None [probable default: preserves input]) -> np.ndarray`. `a`:
  DOF readback of either container type; `dtype`: float in _q/_e
  helpers, omitted in probe_cmd2.py:11 (input dtype preserved
  [probable]).
- `.flatten()[0]` -> first scalar [verified: b3_run.py:21/27,
  b4_run.py:32, v10_run.py:32, probe_cmd2.py:11].
  SIG: `ndarray.flatten(order: str = "C" [theoretical: never passed])
  -> np.ndarray` (no args passed); then `[i: int = 0]` (int axis
  index, n/a, literal 0 observed) -> numpy scalar (radians here).
  Single-DOF assumption baked in [verified].
- `float(x: np.scalar | float)` -> `float` Python scalar for reports [verified: same
  sites: b3_run.py:21/27, b4_run.py:32, v10_run.py:32, probe_cmd2.py:11].
  SIG: `float(x: np.scalar | float) -> float`. `x`: single numpy
  scalar from flatten()[0]; units follow context (radians for q/e).
- NOTE: b2_run.py imports `math` but never calls it (dead import)
  [verified: full read of b2_run.py].

KNOBS (2, both typed):
- `dtype: np.dtype` (unit n/a; numpy default float64 [theoretical]):
  invariant value np.float32 on commands [verified: 5/5 sites].
  Effect-of-change: float64 untested [theoretical-unknown].
- Target list `[tgt]: list[float]` (elements float, unit radians;
  required arg, no default): single-element [verified: b3_run.py:37,
  b4_run.py:47, v10_run.py:41/49, probe_cmd2.py:7]. Effect:
  multi-element untested (single-DOF pack) [theoretical].

EKB RULES:
- IF commanding THEN wrap target as float32 single-element array
  BECAUSE every passing command uses exactly that shape [verified].
- IF reading THEN asarray/flatten/[0]/float chain BECAUSE readbacks
  are 1-element arrays of uncertain container type [verified].

LIMITS (2, cited):
- L1: Targets must be float32 radians (B3 exact <0.002) [verified:
  failures.md R3, b3_run.py:37].
- L2: Scalar reads assume single-DOF flatten()[0] [verified].

UNKNOWN (1):
- U10 [theoretical]: whether float64 targets are accepted.

## 10. omni.graph.core (og) — graph toggle (probe-only)

DOES: Enables/disables an OmniGraph graph around a command probe
[verified: probe_cmd2.py only use in pack].

FUNCTIONS (2, both typed):
- `og.get_graph_by_path(path: str)` ("/World/V9Graph") -> graph object (exact
  class `og.Graph` [probable: never introspected]) [verified:
  probe_cmd2.py:5/12]. Only graph path ever referenced.
  SIG: `get_graph_by_path(path: str) -> Graph [probable]`. `path`:
  graph prim-path string, n/a, required positional.
- `graph.set_disabled(disabled: bool)` -> `None` [probable return: never
  checked] [verified: probe_cmd2.py:5 (True), probe_cmd2.py:12 (False)].
  SIG: `set_disabled(disabled: bool) -> None [probable]`. `disabled`:
  bool, n/a, required positional (no default observed). Disabled
  before the command soak, re-enabled after [verified: probe_cmd2].

KNOBS (2, both typed):
- Graph `path: str` (prim-path string, unit n/a, required positional,
  no default): "/World/V9Graph" only [verified: probe_cmd2.py:5/12].
  Other graphs untested [theoretical].
- Disabled flag `disabled: bool` (unit n/a, no default observed —
  always passed): True during probe, False after [verified:
  probe_cmd2.py:5/12]. Effect-of-change: probe outcome with graph
  enabled untested [theoretical-unknown].

EKB RULES:
- IF probing a raw command THEN disable the owning graph first
  BECAUSE the pack's only probe does so (cause unproven, follow the
  ritual) [verified-pattern, theoretical-cause].

LIMITS (1, cited):
- L1: Single probe usage; graph behavior itself is not this pack's
  drill [verified: TOOLS.md, probe_cmd2.py].

UNKNOWN (1):
- U11 [theoretical]: WHY the graph had to be disabled for the probe.

## 11. isaacsim_send.py bridge — in-sim execution transport

DOES: Sends build/run scripts into the live Isaac Sim session
[verified-convention: README "Tools", every script docstring "runs
INSIDE Isaac Sim"].

FUNCTIONS (0 in-pack): no bridge source or CLI invocation appears in
any of the 18 scripts or 4 docs [verified-absence].

KNOBS (0): no invocable surface in this pack [verified-absence].

EKB RULES:
- IF a script docstring says "runs INSIDE Isaac Sim" THEN it must go
  via the bridge, never run locally (omni/pxr/isaacsim imports only
  exist in-sim) [verified: 13/13 in-sim scripts import omni or pxr].
- IF the bridge resets mid-run THEN relaunch windowed + bridge poll +
  rebuild BECAUSE that recovery worked for all 3 crashes [verified:
  discovery.md "Session notes"].

LIMITS (2, cited):
- L1: 3 run-send connection resets during this skill [verified:
  discovery.md "Session notes"].
- L2: Bridge CLI flags/invocation form appear nowhere in this pack
  [verified-absence].

UNKNOWN (1):
- U12 [theoretical]: exact bridge CLI form and flags.

## 12. verify_bN / verify_v10 — local evaluators

DOES: Local pass/fail evaluation of drill reports: loads
evidence/bN_build.json + evidence/bN_run.json, regex-extracts the
*-REPORT/*-OK line fields, checks tolerances, prints PASS/FAIL per
check + overall line [verified: full read of all 5].

FUNCTIONS (5, all typed):
- `json.load(open(".../evidence/<drill>_<build|run>.json"))["output"]`
  -> captured stdout string [verified: verify_b1.py:4-5,
  verify_b2.py:4-5, verify_b3.py:4-5, verify_b4.py:4-5, verify_v10.py:4-5].
  SIG: `open(file: str, mode: str = "r" [theoretical: never passed])
  -> TextIO`; `json.load(fp: TextIO) -> dict[str, Any]`; then
  `["output"]: str key -> str`. `file`: evidence JSON path string,
  required positional. 5/5 verifiers.
- `re.search(pattern: str, string: str)` via helper `f(pat: str, s: str, i: int = 1)` -> float or NaN on
  miss [verified: verify_b1.py:7-9, verify_b2.py:7-9, verify_b4.py:7-9,
  verify_v10.py:7-9; verify_b3.py:7-9 binds s=R with f(pat, i=1)].
  SIG: `f(pat: str, s: str, i: int = 1) -> float`. `pat`: regex
  string (required); `s`: haystack string (required, except verify_b3
  closes over module R); `i`: match-group index int, default 1
  (always defaulted — never passed explicitly [verified: 5/5]).
  `re.search(pattern: str, string: str) -> Match | None`; miss ->
  `float("nan")`. Patterns use `([-\d.]+)` capture [verified].
- `checks` dict: name -> bool; `ok = all(checks.values())`
  [verified: all 5 verifiers, e.g. verify_b1.py:11/22].
  SIG: `checks: dict[str, bool]`; `dict.values() ->
  ValuesView[bool]`; `all(it: Iterable[bool]) -> bool`; `ok: bool`.
- Per-check `print(("PASS " if v else "FAIL ") + k)` [verified: all 5,
  e.g. verify_b1.py:23-24].
  SIG: `print(*objects: str, sep: str = " " [theoretical], end: str =
  "\n" [theoretical]) -> None`. Single str arg observed (`v: bool`
  selects prefix, `k: str` check name); sep/end never passed.
- Overall `print("B<N>-" + ("PASS" if ok else "FAIL"))` where
  `ok: bool` -> `None`; exit 0 conventionally on pass (no sys.exit
  call; success = printed PASS) [verified: no exit() in any
  verifier, e.g. verify_b1.py:25].
  SIG: same `print` SIG as above; `ok: bool` selects PASS/FAIL.
- Check counts: b1=9, b2=10, b3=9, b4=8, v10=9 (44 total) [verified].
- Stdlib only: json + re (+ math imported in verify_b2 but unused
  there too) [verified].

KNOBS (7 tolerance families, all typed; each is a `float` (or `str`)
comparison literal — required constant, no default): effect-of-change
for ALL: tightening below process noise (chunk granularity ~0.08-0.2s,
drive settle ~0.002) causes false FAILs; loosening hides regressions
[probable].
- Time gates `tol: float` (unit s): 0.1 (t0 reset), 0.15 (B1/B2
  mid/end), 0.25 (B4 trig), 0.3 (V10 switch) [verified: verify_b1.py:
  14/16/19, verify_b4.py:16, verify_v10.py:17].
- Position gates `tol: float` (unit m [probable]): 0.05 (x0 start),
  0.15 (mid/end/slider/gate), 0.25 (trig x), 0.3 (switch y)
  [verified: verify_b1.py:15/17/20, verify_b4.py:17/19,
  verify_v10.py:16/19].
- Joint q gates `tol: float` (unit rad): 0.1 (B3 phases, B4/V10 ends)
  vs achieved <0.002 (B3) — gates are ~50x looser than demonstrated
  accuracy [verified: verify_b3.py:14/16/18, verify_b4.py:18,
  verify_v10.py:18].
- Echo gates `tol: float` (unit rad): 1e-6 EXACT (B3 three phases)
  [verified: verify_b3.py:15/17/19].
- Op==world gate `tol: float` (unit m [probable]): 1e-6 EXACT (B1
  mid) [verified: verify_b1.py:18].
- Degree gates `tol: float` (unit deg; axis tol unitless): 5.0 (ry op
  reads), 3.0 (GetAngle world), 0.05/component (axis) [verified:
  verify_b2.py:16/20/17-19/22-23, verify_v10.py:20].
- String gates `sub: str` (exact substring, unit n/a): "valid=True",
  "samples=2", "ops=2", "trig=1", "nsw=1", "bot=True", "hinge=True"
  [verified: all 5 verifiers].

EKB RULES:
- IF evaluating THEN run the matching verify locally against
  evidence/*.json BECAUSE verifiers never touch the sim [verified:
  docstrings "runs LOCALLY", stdlib-only].
- IF a time gate fails by <1 chunk THEN suspect chunk granularity,
  not the behavior, BECAUSE triggers land within one chunk of theory
  [verified: discovery.md "Trigger"].
- IF echo gate fails THEN the command never landed (transport/API
  fault), while q-only failure means physics didn't settle (soak
  fault), BECAUSE echo and q are independent signals [verified:
  verify_b3 structure].

LIMITS (2, cited):
- L1: Evaluators, not sim APIs; they assert on captured stdout only
  [verified: json+regex over evidence files].
- L2: Exact thresholds live per-script (see KNOBS above) [verified:
  full reads].

UNKNOWN (1):
- U13 [theoretical]: evidence/*.json capture format ({"output": ...})
  is consumed but its producer (bridge log wrapper) is not in-pack.
- U14 [theoretical]: cross-val x10_live.py + verify_x10.py cited by
  README ("co-validation snapshot", 11/11) but NOT present in
  scripts/ — claimed tool with no source [verified-absence].

## Unverified index (carried from TOOLS.md, now tagged)

- behavior-tree-generation library skill: needs NVIDIA_API_KEY + AEDG
  app; ruled unsuitable for deterministic drills [verified-ruling:
  discovery.md "Session notes"]. Not a pack tool.
- USD drive targetPosition sets outside mid-play: pre-play authoring
  works (builds); only mid-play propagation disproven [verified].
- Multi-DOF Articulation ordering [theoretical: U8].
- update_app_async wall-clock determinism [theoretical: U3].
- og disable/enable necessity [theoretical: U11].
- isaacsim_send.py CLI form [theoretical: U12].
- x10_live.py + verify_x10.py missing sources [verified-absence: U14].

