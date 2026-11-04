# Workspace-Sense TOOLS_REF (2026-11-04) — exhaustive tool reference

DATATYPE PASS COUNTS: signatures typed 83/83 (S1–S83) · knobs typed 27/27 (K1–K27) · still-unknown 14 (U1–U14).
Tag legend: (S#) = typed signature (every param typed + return + units + defaults; symmetric index pairs share
one tag); (K#) = typed knob (attr type + unit + default); (U#) = still-unknown datatype item ([unknown] only —
[probable] counts as typed-with-caveat).

Claim tags: [verified] = proven by in-pack evidence/verifiers; [probable] = code-read,
consistent but not independently asserted; [theoretical] = inferred, no in-pack proof.

## Tool 1. pxr USD core — `Usd`, `UsdGeom`, `UsdPhysics`, `Gf` (in-sim)

DOES: Authors every drill scene (cubes, cylinders, ground planes, physics scenes,
joints, physics APIs) and reads authored-state pose, world bounds, physics flags,
and joint anchors off the live stage [verified: sense.py, drill_*.py, evidence/*].

Functions + full signatures (as used in-pack; S-tags — one tag per bullet, symmetric index pairs share a tag):
- (S1) `stage.Traverse() -> Usd.PrimRange` — no params; iterates every prim [verified: sense.py:93]
- (S2) `stage.GetPrimAtPath(path: Sdf.Path | str) -> Usd.Prim` — invalid prim if absent, never None;
  always guard `prim.IsValid()`; units n/a; no default (required) [verified: sense.py:31, drill_cube.py:11,
  dup_inventory.py:21, dup_detail.py:16 — all call sites pass `str`]
- (S3) `stage.RemovePrim(path: Sdf.Path | str) -> bool` — deletes prim subtree; True if removed
  [probable: return never checked in-pack]; no default [verified: drill_cube.py:13, drill_joint.py:16,
  drill03_setup.py:16, clean_slate.py:16 — all pass `str`]
- (S4) `prim.GetPath() -> Sdf.Path` — no params; `str()` it for JSON [verified: sense.py:95, dup_inventory.py:29]
- (S5) `prim.GetTypeName() -> Tf.Token` — no params; str-like (`"Joint" in tname`, `.startswith()`, `str()`
  all used); units n/a [verified: sense.py:96,145, dup_inventory.py:17, dup_detail.py:19]
- (S6) `prim.GetChildren() -> Iterable[Usd.Prim]` — no params; sibling range (wrap `list()` to count)
  [probable range type; verified iteration: dup_inventory.py:28,81, dup_detail.py:22]
- (S7) `prim.GetName() -> str` — no params; leaf name [verified: dup_inventory.py:81]
- (S8) `prim.IsValid() -> bool` — no params [verified: sense.py:32, drill_cube.py:12, dup_inventory.py:22, dup_detail.py:17]
- (S9) `prim.GetAttribute(name: str) -> Usd.Attribute` — invalid attr if absent; guard `.IsValid()`
  before `.Get()`; no default [verified: dup_inventory.py:100-101, dup_detail.py:40-41,61-62]
- (S10) `prim.GetRelationship(name: str) -> Usd.Relationship` — invalid rel if absent; guard `.IsValid()`;
  no default [verified: dup_detail.py:56-57]
- (S11) `prim.HasAPI(schema_cls: type) -> bool` — schema_cls is a USD schema class (`UsdPhysics.RigidBodyAPI`,
  `.CollisionAPI`, `.MassAPI`, `.ArticulationRootAPI`, `.DriveAPI`, `.RevoluteJoint`, `.FixedJoint`);
  no default [verified: sense.py:116,120,124,132, dup_inventory.py:61-63]
- (S12) `prim.GetAppliedSchemas() -> list[str]` — no params; token names (JSON via `default=str`); wrap
  `list()` [verified: dup_inventory.py:57, dup_detail.py:33]
- (S13) `stage.GetRootLayer() -> Sdf.Layer` — no params [verified: dup_inventory.py:11]
- (S14) `layer.GetIdentifier() -> str` — no params; stage URL [verified: dup_inventory.py:11]
- (S15) `Usd.TimeCode.Default() -> Usd.TimeCode` — no params; authored/default (unanimated) time; units:
  timecodes [verified: sense.py:83]
- (S16) `UsdGeom.XformCache(time: Usd.TimeCode = Usd.TimeCode.Default()) -> UsdGeom.XformCache` —
  no-arg `XformCache()` = default time, same effect [probable; verified calls: sense.py:84 with tcode,
  dup_inventory.py:46 / dup_detail.py:7 no-arg]
- (S17) `xcache.GetLocalToWorldTransform(prim: Usd.Prim) -> Gf.Matrix4d` — translations in m; no default
  [verified: sense.py:34,99, dup_inventory.py:49, dup_detail.py:10]
- (S18) `mat.ExtractTranslation() -> Gf.Vec3d` — no params; indexable `[0],[1],[2]`; units m
  [verified: sense.py:35,100, dup_inventory.py:50-51, dup_detail.py:11]
- (S19) `mat.ExtractRotation() -> Gf.Rotation` — no params; units n/a [verified: sense.py:36,101]
- (S20) `rot.GetQuaternion() -> Gf.Quath` — no params; unitless (w + xyz); quat flavor [probable:
  only `.GetReal()/.GetImaginary()` used in-pack] [verified calls: sense.py:36,101]
- (S21) `quat.GetReal() -> float` — no params; w component, unitless [verified: sense.py:38,104];
  `quat.GetImaginary() -> Gf.Vec3h | Gf.Vec3f` — no params; [x,y,z] unitless, indexable; exact vec flavor
  [probable: Quath→Vec3h, Quatf→Vec3f] [verified: sense.py:37,102,162,171]
- (S22) `UsdGeom.BBoxCache(time: Usd.TimeCode, purposes: Sequence[Tf.Token | str]) -> UsdGeom.BBoxCache` —
  both required in-pack (extra ctor params theoretical); purposes unitless token set; `"render"/"proxy"`
  pass as raw `str` [verified: sense.py:87]
- (S23) `bcache.ComputeWorldBound(prim: Usd.Prim) -> Gf.BBox3d` — bounds in m; no default
  [verified: sense.py:39,108]
- (S24) `bbox.ComputeAlignedRange() -> Gf.Range3d` — no params; axis-aligned box in m [verified: sense.py:39,108]
- (S25) `rng.GetMin() -> Gf.Vec3d` / `rng.GetMax() -> Gf.Vec3d` — no params; box corners in m, indexable
  [verified: sense.py:40,109-112]
- (S26) `UsdGeom.Cube.Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdGeom.Cube` — both required;
  in-pack `path` always `str` [verified: drill_cube.py:14, drill_joint.py:18, drill03_setup.py:27,33]
- (S27) `cube.GetSizeAttr() -> Usd.Attribute` (double, m) + `.Set(value: float) -> bool [probable]` —
  size IS edge length (1.0 → 1.0 m edge); no Set default [verified: drill_cube.py:15, drill_joint.py:19, drill03_setup.py:28,34]
- (S28) `UsdGeom.Cylinder.Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdGeom.Cylinder`
  [verified: drill_joint.py:25]
- (S29) `cyl.GetRadiusAttr() -> Usd.Attribute` (float, m) + `.Set(value: float)` [verified: drill_joint.py:26];
  `cyl.GetHeightAttr() -> Usd.Attribute` (float, m) + `.Set(value: float)` [verified: drill_joint.py:27];
  `cyl.GetAxisAttr() -> Usd.Attribute` (token) + `.Set(value: Tf.Token)` (`UsdGeom.Tokens.x`)
  [verified: drill_joint.py:28]
- (S30) `UsdGeom.Plane.Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdGeom.Plane`
  [verified: drill03_setup.py:22]
- (S31) `plane.CreateWidthAttr() -> Usd.Attribute` (double, m) + `.Set(value: float)`; called no-arg in-pack
  (optional `defaultValue`/`writeSparsely` params theoretical) [verified: drill03_setup.py:23];
  `plane.CreateLengthAttr() -> Usd.Attribute` (double, m) + `.Set(value: float)` [verified: drill03_setup.py:24]
- (S32) `schema.GetPrim() -> Usd.Prim` — no params; prim under a Cube/Cylinder/Plane/Joint/Scene handle
  [verified: drill_cube.py:16, drill_joint.py:20-23, drill03_setup.py:25,29-32]
- (S33) `UsdGeom.Xformable(prim: Usd.Prim) -> UsdGeom.Xformable`;
  `.AddTranslateOp(opSuffix: str = "" [probable], precision: UsdGeom.XformOp.Precision = double [probable]) -> UsdGeom.XformOp`;
  `xformOp.Set(value: Gf.Vec3d | Sequence[float], time: Usd.TimeCode = Default [probable]) -> bool [probable]` —
  value units m; pose authoring [verified: drill_cube.py:16, drill_joint.py:20,29, drill03_setup.py:29,35]
- (S34) `Gf.Vec3d(x: float = 0 [probable], y: float = 0 [probable], z: float = 0 [probable]) -> Gf.Vec3d` —
  in-pack always 3-arg; translates/positions in m [verified: drill_cube.py:16, drill_joint.py:20,29, drill03_setup.py:29,35];
  `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` — joint anchors in m, gravity dir unitless
  [verified: drill_joint.py:37,39, drill03_setup.py:19]
- (S35) `Gf.Quatf(real: float = 1.0 [probable], imaginary: Gf.Vec3f | Sequence[float] = (0,0,0) [probable]) -> Gf.Quatf` —
  unitless; `Gf.Quatf(1.0)` = identity [verified: drill_joint.py:38,40]
- (S36) `UsdPhysics.Scene.Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdPhysics.Scene`
  [verified: drill03_setup.py:18]
- (S37) `scene.CreateGravityDirectionAttr() -> Usd.Attribute` (vector3f, unitless direction) +
  `.Set(value: Gf.Vec3f | Sequence[float])` [verified: drill03_setup.py:19];
  `scene.CreateGravityMagnitudeAttr() -> Usd.Attribute` (float, m/s²) + `.Set(value: float)`
  [verified: drill03_setup.py:20]; both called no-arg in-pack (optional `defaultValue`/`writeSparsely` theoretical)
- (S38) `UsdPhysics.RigidBodyAPI.Apply(prim: Usd.Prim) -> UsdPhysics.RigidBodyAPI` — return unused in-pack
  [verified: drill_joint.py:21,30, drill03_setup.py:30,36];
  `UsdPhysics.RigidBodyAPI(prim: Usd.Prim) -> UsdPhysics.RigidBodyAPI` (bound handle) [verified: sense.py:125];
  `.GetKinematicEnabledAttr() -> Usd.Attribute` (bool) + `.Get() -> bool` [verified: sense.py:126]
- (S39) `UsdPhysics.CollisionAPI.Apply(prim: Usd.Prim) -> UsdPhysics.CollisionAPI` [verified: drill_joint.py:22,31,
  drill03_setup.py:25,31,37]
- (S40) `UsdPhysics.MassAPI.Apply(prim: Usd.Prim) -> UsdPhysics.MassAPI` (return chained for Set);
  `UsdPhysics.MassAPI(prim: Usd.Prim) -> UsdPhysics.MassAPI` (bound handle);
  `.GetMassAttr() -> Usd.Attribute` (float, kg [probable unit]) + `.Set(value: float)` / `.Get() -> float`
  [verified: drill_joint.py:23,32, drill03_setup.py:32,38, sense.py:133]
- (S41) `UsdPhysics.RevoluteJoint.Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdPhysics.RevoluteJoint`
  [verified: drill_joint.py:34]; `UsdPhysics.Joint(prim: Usd.Prim) -> UsdPhysics.Joint` base handle
  [verified: sense.py:146]
- (S42) `joint.GetBody0Rel() -> Usd.Relationship` / `joint.GetBody1Rel() -> Usd.Relationship` — no params
  [verified: drill_joint.py:35-36, sense.py:149,153]
- (S43) `rel.AddTarget(target: Sdf.Path | str) -> None [probable]` — in-pack `str` literals; no default
  [verified: drill_joint.py:35-36]; `rel.GetTargets() -> list[Sdf.Path]` — no params; `str()` each for JSON
  [verified: sense.py:149,153]; `rel.IsValid() -> bool` — no params [verified: dup_detail.py:57]
- (S44) `joint.GetLocalPos0Attr() -> Usd.Attribute` (point3f [probable role], m) /
  `joint.GetLocalPos1Attr() -> Usd.Attribute` (same) + `.Get() -> Gf.Vec3f` / `.Set(value: Gf.Vec3f | Sequence[float])`
  [verified: drill_joint.py:37,39, sense.py:158,167];
  `joint.GetLocalRot0Attr() -> Usd.Attribute` (quatf, unitless) / `joint.GetLocalRot1Attr() -> Usd.Attribute` (same) +
  `.Get() -> Gf.Quatf` / `.Set(value: Gf.Quatf)` [verified: drill_joint.py:38,40, sense.py:159,168]
- (S45) `UsdPhysics.RevoluteJoint(prim: Usd.Prim) -> UsdPhysics.RevoluteJoint` (bound handle, revolute-only);
  `.GetAxisAttr() -> Usd.Attribute` (token) + `.Get() -> Tf.Token` / `.Set(value: Tf.Token)` (`UsdPhysics.Tokens.x`)
  [verified: drill_joint.py:41, sense.py:175-178]
- (S46) `UsdPhysics.Scene(prim: Usd.Prim) -> UsdPhysics.Scene` — falsy unless prim IS a scene; truthiness test
  [verified: sense.py:139-140]
- (S47) `attr.Get(time: Usd.TimeCode = Default [probable]) -> Any` — type per attribute (float/bool/Vec3f/Quatf/Token);
  missing attrs raise → wrap try/except [verified: sense.py:126,133,158-159,167-168,178, dup_inventory.py:101, dup_detail.py:41,62];
  `attr.Set(value: Any, time: Usd.TimeCode = Default [probable]) -> bool [probable]` — value per attribute; return
  never checked in-pack [verified: all drill setups]; `attr.IsValid() -> bool` [verified: dup_inventory.py:101, dup_detail.py:41,62]
- (S48) `sense._site_of(stage: Usd.Stage, xcache: UsdGeom.XformCache, bcache: UsdGeom.BBoxCache, body_paths: list[str], anchor: Sequence[float] | None) -> str` —
  site label (`maxX+midY+midZ`, `rotated:`-prefixed, or `unknown*`); anchor units m; no defaults; in-pack helper
  (not USD API) [verified: sense.py:21-59, called sense.py:181-182]
- Probe-only reads via S9/S10/S11: `HasAPI` flags `ArticulationRootAPI`, `DriveAPI`, `RevoluteJoint`, `FixedJoint`
  [verified: dup_inventory.py:61]; attr reads `"drive:angular:physics:*"`, `"state:angular:physics:*"`,
  `"physics:excludeFromArticulation"` [verified: dup_inventory.py:98-103, dup_detail.py:38-43,61-64]; rel reads
  `"physics:body0"/"physics:body1"` [verified: dup_detail.py:54-59]
- Joint detection heuristic (not a USD signature): `"Joint" in tname and tname.startswith("Physics")` on the
  S5 token [verified: sense.py:145]
- Typed constants (unitless `Tf.Token`): `UsdGeom.Tokens.x`, `UsdGeom.Tokens.default_` (="default" [probable]),
  `UsdPhysics.Tokens.x` [verified: drill_joint.py:28,41, sense.py:87]

Knobs + effect-of-change (K-tags — every knob: attr type + unit + default):
- (K1) `BBoxCache` purposes: type `Sequence[Tf.Token | str]`, unitless token set; default: none (required S22
  arg; always explicit in-pack). `["default"]` alone → explicit render/proxy prims read EMPTY bbox (±FLT_MAX);
  `["default","render","proxy"]` → real bounds [verified: failures.md V1, sense.py:87]. Adding `"guide"` would
  include guide prims (excluded by design) [theoretical].
- (K2) `Cube.size`: attr type double, unit m edge length; default (U1) [unknown — always `.Set(1.0)` in-pack:
  drill_cube.py:15, drill_joint.py:19, drill03_setup.py:28,34]. 1.0 → size=[1,1,1] sensed [verified: verify_drill01].
- (K3) `Cylinder.radius`: float, m; default (U2) [unknown — always `.Set(0.25)`: drill_joint.py:26].
  `Cylinder.height`: float, m; default (U3) [unknown — always `.Set(1.0)`: drill_joint.py:27].
  `Cylinder.axis`: token enum {x,y,z}, unitless; default (U4) [unknown — always `.Set(Tokens.x)`: drill_joint.py:28];
  orients height axis; X used in Drill 02 [verified].
- (K4) `Plane.width`/`Plane.length`: double, m; defaults (U5) [unknown — always `.Set(20.0)`: drill03_setup.py:23-24].
- (K5) `GravityDirection`: vector3f, unitless direction; default (U6) [unknown — always `.Set((0,0,-1))`:
  drill03_setup.py:19]. `GravityMagnitude`: float, m/s²; default (U7) [unknown — always `.Set(9.81)`:
  drill03_setup.py:20]. (0,0,-1)/9.81 → vz in (-4.0,-3.1) after 20-24 steps [verified: verify_drill03b.py:89].
  Other magnitudes untested [unknown → theoretical].
- (K6) `MassAPI.mass`: float, kg [probable unit]; default (U8) [unknown — always `.Set()`: 2.0/1.0 drill_joint.py:23,32,
  1.0/5.0 drill03_setup.py:32,38]. 1.0/2.0/5.0 all sensed exactly ±1e-3 [verified: co_verify.py:55, verify_drill02.py:51].
  Mass 5.0 vs 1.0 falls identically (gap exactly 2.0) [verified: d3_senseB] — gravity-only fall is mass-independent [verified].
- (K7) `KinematicEnabled`: bool, unitless; default False [probable — never `.Set()` in-pack, only read].
  Emitted (`kinematic` field) but never asserted [verified: sense.py:124-130; no verifier reads it].
- (K8) Joint `localPos0/1`: point3f, m; default (0,0,0) [probable — always `.Set()` in-pack: drill_joint.py:37,39].
  `localRot0/1`: quatf, unitless; default identity [probable — always `.Set(Quatf(1.0))`: drill_joint.py:38,40].
  Revolute `axis`: token enum {x,y,z}, unitless; default (U14) [unknown — always `.Set(Tokens.x)`: drill_joint.py:41;
  read sense.py:178, asserted verify_drill02.py:43 / co_verify.py:107].
- (K9) Xform translate op value: `Gf.Vec3d`, m; default (0,0,0) [probable — always `.Set()` in-pack: drill_cube.py:16,
  drill_joint.py:20,29, drill03_setup.py:29,35].
- (K10) Drive/state attrs (read-only via S9, never Set/asserted in-pack): type float [probable] each;
  `drive:angular:physics:targetPosition` + `state:angular:physics:position` unit (U9) [unknown — deg vs rad unproven];
  `drive:angular:physics:targetVelocity` + `state:angular:physics:velocity` unit (U10) [unknown — deg/s vs rad/s];
  `drive:angular:physics:damping` unit/role (U11) [unknown]; `...:stiffness` (U12) [unknown];
  `...:maxForce` (U13) [unknown]; defaults all unproven (never authored in-pack)
  [verified reads: dup_inventory.py:98-103, dup_detail.py:38-43].
- (K11) `physics:excludeFromArticulation`: bool [probable], unitless; default False [probable — never authored in-pack]
  [verified read: dup_detail.py:61-64]. `physics:body0`/`physics:body1` rels: `list[Sdf.Path]`, unitless; no default
  [verified: dup_detail.py:54-59].
- (K12) Site-label tolerance `tol = max(1e-4, span*1e-3)`: type float, unit m (literals, no default);
  anchors within tol of face/mid get that tag, else `inX/Y/Z` [verified: sense.py:47-55, S48];
  rotation identity threshold 1e-3: float, unitless quat-component diff [verified: sense.py:38].

EKB rules:
- IF a prim's bbox reads ±FLT_MAX/empty THEN check its purpose — BBoxCache with purposes=["default"] excludes
  render/proxy prims — BECAUSE purpose filtering is per-query, not per-prim [verified: failures.md V1].
- IF sensing while playing THEN use RigidPrim tensors, never XformCache/BBoxCache — BECAUSE USD caches read
  AUTHORED state only during play [verified: sense.py docstring, d3_hot vs d3_sense0].
- IF you need a joint anchor's local position THEN read GetLocalPos0/1Attr, never ComputeLocalBound —
  BECAUSE ComputeLocalBound returns world-frame bounds on this Kit build [verified: sense.py:21-27];
  derive local range as world bbox minus body translation [verified].
- IF a body is rotated THEN prefix site labels `rotated:` and treat as approximate — BECAUSE world bboxes
  inflate under rotation [verified: sense.py:36-57].
- IF detecting joints THEN match `"Joint" in type and type.startswith("Physics")` — BECAUSE type names are
  PhysicsRevoluteJoint etc. [verified: sense.py:145]; axis attr exists only on RevoluteJoint — guard by
  exact type [verified: sense.py:175-180].
- IF an attr may not exist THEN wrap `.Get()` in try/except and emit None/error — BECAUSE missing attrs raise
  live (velocities, kinematic, mass paths all guarded) [verified: sense.py:106-137,200-204].
- IF placing assets with their own metersPerUnit THEN scale by mpu and order T*R*S (spatial-reasoning) —
  BECAUSE S*T scales the translation vector [probable: spatial-reasoning skill; no in-pack drill uses mpu].

LIMITS [verified unless noted]:
- BBoxCache ["default"] excludes render/proxy (V1; fixed in sense.py:87; covered by co_sense_p3).
- XformCache/BBoxCache are authored-state-only while playing (docstring v0.2; d3_hot tensor vs d3_sense0 null).
- ComputeLocalBound returns world-frame bounds on this Kit build (sense.py:21-27; co_sense_p3 site assertions pass on the workaround).
- Rotated bodies: inflated world bbox, approximate `rotated:` site label (sense.py:36-57).
- `"guide"` purpose excluded by design, effect unmeasured (sense.py:85-87; no drill covers guides).
- Per-prim failures are swallowed into `pose_error`/`bbox_error`/`errors[]` records, never raised [verified: sense.py:105-114,186-187] —
  so a passing snapshot can still carry partial errors; verifiers require `errors==[]` [verified: co_verify.py:82-83].

UNKNOWN (theoretical):
- Whether other Kit builds need more purpose tokens or fix ComputeLocalBound.
- Site-label accuracy for scaled/skewed/articulated bodies; `rotated:` path has no calibrated tolerance or drill assertion.
- Kinematic-enabled bodies and `mass=None` records are emitted but never asserted.
- `anchor*_quat` records emitted (sense.py:163,172) but never asserted by any verifier.
- Multi-scene stages: only last `UsdPhysics.Scene(prim)`-truthy prim is recorded (sense.py:139-140 overwrites) — single scene only [probable from code].

## Tool 2. `omni.usd` (in-sim)

DOES: Single entry point to the live stage for every in-sim script [verified: all in-sim scripts].

Functions + full signatures:
- (S49) `omni.usd.get_context() -> omni.usd.UsdContext` — no params; context typename [probable]
  [verified: sense.py:70, drill_cube.py:9, drill_joint.py:12, drill03_setup.py:9, clean_slate.py:4, dup probes]
- (S50) `ctx.get_stage() -> Usd.Stage | None` — no params; None when no stage open → guard (S50 None-branch
  verified: sense.py:71-74) [verified: sense.py:70, all in-sim scripts]
- No-stage guard: `if stage is None or not stage: out["errors"].append("no stage open"); print(json); return`
  [verified: sense.py:70-74]; dup probes instead record `stage_valid: bool` and continue [verified: dup_inventory.py:8].

Knobs: none — no parameters anywhere in-pack [verified].

EKB rules:
- IF `get_stage()` returns None/falsy THEN emit `{"errors": ["no stage open"]}` and exit cleanly —
  BECAUSE every downstream read would throw [verified: sense.py:70-74].
- IF writing a probe THEN print `PROBE_JSON:{...}` even on fatal (wrap all in try/except + traceback) —
  BECAUSE the bridge only captures stdout [verified: dup probes :120-122/:69-71].

LIMITS: none beyond the no-stage guard [verified].

UNKNOWN (theoretical): behavior with multiple open stages / non-`/World` roots — no drill covers it.

## Tool 3. `omni.timeline` (in-sim)

DOES: Reads or resets the play clock that gates live-vs-edit sensing [verified: sense.py:76-79, drill03_setup.py:39-42].

Functions + full signatures:
- (S51) `omni.timeline.get_timeline_interface() -> ITimeline` — no params; interface typename [probable]
  [verified: sense.py:77, drill03_setup.py:42, drill03_vel.py:19, dup_inventory.py:116]
- (S52) `tiface.get_current_time() -> float` — no params; units seconds; sense rounds to 3dp [verified: sense.py:79,
  dup_inventory.py:117]
- (S53) `tiface.set_current_time(time: float | Usd.TimeCode) -> None [probable]` — units seconds; no default;
  reset clock to edit state [verified: drill03_setup.py:42 passes `0.0`]
- (S54) `tiface.pause() -> None [probable]` — no params [verified: drill03_vel.py:19]
- (S55) `tiface.is_playing() -> bool` / `tiface.is_stopped() -> bool` / `tiface.is_paused() -> bool` — no params;
  `is_stopped`/`is_paused` guarded by `hasattr` in probes (may not exist per build) [verified: dup_inventory.py:117];
  sense.py does NOT use them (uses app_utils.is_playing) [verified: sense.py:78]

Knobs + effect-of-change (K-tags):
- (K13) Clock `t`: type float, unit seconds (S52, rounded 3dp); default 0.0 = edit state. Gates `live`: t=0 (edit) →
  `live=null`; t>0 + not playing → `source="rest"`; playing → `source="tensor"`
  [verified: sense.py:190-193; d3_sense0=null, d3_senseB/C=rest, d3_hot=tensor; verify_drill03b Phases 1-2].

EKB rules:
- IF resetting a scene for a deterministic drill THEN call `app_utils.stop()` AND `set_current_time(0.0)` —
  BECAUSE stop alone may leave clock>0, which sense would report as `rest` instead of edit-null [verified: drill03_setup.py:41-42, sense.py:191].
- IF reading is_stopped/is_paused THEN guard with `hasattr(..., "n/a" fallback)` — BECAUSE the interface
  varies by build [verified: dup_inventory.py:117].
- IF sensing flight THEN read tensors while playing; IF sensing rest THEN stop first and read after —
  BECAUSE `rested = (not playing) and t>0` [verified: sense.py:190-193].

LIMITS [verified]: `live=null` at clock=0; `source="rest"` when stopped with clock>0; `source="tensor"` while
playing (sense.py:190-193; evidence d3_sense0/B/C/hot).

UNKNOWN (theoretical): paused-mid-play vs stopped-with-clock>0 tensor semantics — `rested` treats any
non-playing clock>0 as rest; paused-state tensor freshness unproven. (Note: drill03_vel.py pauses then
immediately stops, so no evidence reads tensors while paused.)

## Tool 4. `isaacsim.core.experimental.utils.app` as `app_utils` (in-sim)

DOES: Play-state queries, transport control (play/stop), and fallback physics stepping [verified].

Functions + full signatures:
- (S56) `app_utils.is_playing() -> bool` — no params; timeline `playing` flag [verified: sense.py:78]
- (S57) `app_utils.stop() -> None [probable]` — no params; reset to edit [verified: drill03_setup.py:41, drill03_vel.py:20]
- (S58) `app_utils.play() -> None [probable]` — no params; start playing [verified: drill03_vel.py:12]
- (S59) `await app_utils.update_app_async(steps: int, ...) -> None [probable]` — `steps`: physics-step count
  (frames), unitless, no default (required kwarg in-pack; extra params theoretical); coroutine, must await —
  scripts using `await` run in the bridge's async context [probable: top-level await in drill03_step.py:20,
  drill03_vel.py:13] [verified: drill03_step.py:20 `steps=int(STEPS)`, drill03_vel.py:13 `steps=20`]

Knobs + effect-of-change (K-tags):
- (K14) `steps`: type int, unit physics steps (frames); default: none (required S59 kwarg). drill03_vel uses exactly
  20 → deterministic z in (1.15,1.6) m, vz in (-4.0,-3.1) m/s [verified: verify_drill03b.py:87-90]. drill03_step takes
  STEPS via `--arg` (20 → in-flight, +100 → rested z=0.5 m) [verified: verify_drill03.py:60-73].

EKB rules:
- IF `SimulationContext.step` is unavailable THEN fall back to `await update_app_async(steps)` and print a
  `STEP-FALLBACK` marker — BECAUSE the sim-context path can fail live in-sim [verified: drill03_step.py:10-20].
- IF stepping for a velocity proof THEN play + step exactly 20 with no real-time wait — BECAUSE wall-clock
  play races the read; fixed steps are deterministic [verified: drill03_vel.py docstring + Phase 3 gate].
- IF a drill needs a clean clock THEN `stop()` before setup ends [verified: drill03_setup.py:41].

LIMITS [verified]: SimulationContext path can be unavailable in-sim; scripts fall back to update_app_async
with a `STEP-FALLBACK` marker (drill03_step.py:10-20).

UNKNOWN (theoretical): numerical equivalence of `sim.step(render=True)` vs `update_app_async` stepping —
verifiers accept either via the `via=` tag without comparing.

## Tool 5. `isaacsim.core.experimental.prims.RigidPrim` (in-sim)

DOES: Tensor source of SIMULATED world poses and velocities for all rigid bodies [verified: sense.py:195-216,
drill03_step.py, drill03_vel.py].

Functions + full signatures:
- (S60) `RigidPrim(paths: str | Sequence[str]) -> RigidPrim` — `paths`: prim path(s), unitless, no default
  (required kwarg in-pack); multi-body `paths=[...]` (sense.py:196) and single-path `paths="/World/LiveCube"`
  (drill03_step.py:8, drill03_vel.py:10-11) both work [verified]
- (S61) `rp.get_world_poses() -> tuple[pos: Tensor[N,3] float m, quat: Tensor[N,4] float w,x,y,z unitless]` —
  no params; row i ↔ paths[i]; dtype float32 [probable] [verified: sense.py:197-199,206-210;
  drill03_step.py:21 reads `[0].numpy()[0][2]` = z of first body]
- (S62) `tensor.numpy() -> numpy.ndarray` — no params; tensor owner `torch.Tensor` [probable: `.numpy()` +
  `[i][j]` float indexing only]; same shapes/units as S61/S63 [verified: sense.py:198-199,202, drill03_step.py:21,23]
- (S63) `rp.get_velocities() -> tuple[linvel: Tensor[N,3] float m/s, angvel: Tensor[N,3] float rad/s [probable unit]]` —
  no params; row i ↔ paths[i]; CAN RAISE live → catch and emit `linvel/angvel=None` [verified: sense.py:200-204,
  drill03_step.py:22-25 emits vz=nan, drill03_vel.py:15-18]
- (S64) `sense._f(x: Any, n: int = 4) -> float | None` — `x`: any float-able (units passthrough);
  `n`: decimal digits, unitless, default 4; None on failure; in-pack helper (not Isaac API)
  [verified: sense.py:14-18, used sense.py:103-104,110-112,208-214]

Knobs + effect-of-change (K-tags):
- (K15) `paths` shape: type `str | Sequence[str]`, unitless; default: none (required S60 arg). Single str still
  returns batched tensors indexed `[0]` [verified: drill03_step.py:21]. Two independent `RigidPrim` instances over
  the same path agree to 1e-6 m/s (instdiff gate) [verified: drill03_vel.py:17-18, verify_drill03b.py:91-92].
- (K16) Rounding `n`: type int, unit decimal digits; default 4 (S64). sense emits 4dp [verified: sense.py:14-18];
  truth markers use z=%.4f (m) vz=%.4f (m/s) instdiff=%.6f (m/s) [verified: drill03_step.py:26, drill03_vel.py:21].

EKB rules:
- IF reading simulated pose/velocity THEN construct RigidPrim AFTER play starts (or at rest with clock>0) —
  BECAUSE tensors only carry simulated state then; at clock=0 sense reports live=null [verified: sense.py:189-193].
- IF `get_velocities()` raises THEN keep the pose and emit null velocities — BECAUSE pose reads succeed
  independently [verified: sense.py:200-204].
- IF proving determinism THEN read through TWO independent RigidPrim instances and diff — BECAUSE
  instance disagreement reveals stale/shared state [verified: drill03_vel.py:10-18].
- IF comparing sense-live z to truth z THEN tolerance 1e-3 suffices (exact tensor match) [verified: verify_drill03.py:64,70];
  IF comparing rested z THEN tolerance 0.05-0.1 (settle variance) [verified: verify_drill03b:77, verify_drill03.py:68].

LIMITS [verified]:
- `get_velocities()` can raise live; pose-only fallback (sense.py:200-204; vz=nan in drill03_step.py:22-25).
- Two-body same-fall agreement to 1e-6 (d3_senseB gap exactly 2.0); rested z=0.5±0.05 (d3_senseC);
  in-flight VEL-REPORT z/vz/instdiff proven (d3_vel) — all in verify_drill03b Phases 2-3.
- v1 gate additionally proves: A.z≈2.0 just-played, B.z falls below A.z-0.1, B.vz<-1 in flight,
  C.z≈0.5 rested with |vz|<0.3 [verified: verify_drill03.py:60-73].

UNKNOWN (theoretical): conditions under which `get_velocities()` raises (pose-only fallback trigger)
uncharacterized; tensor reads while paused (not stopped, not playing) unproven.

## Tool 6. `isaacsim.core.api.simulation_context.SimulationContext` (in-sim)

DOES: Preferred Drill 03 stepper — `sim.step(render=True)` × N, stays playing [verified: drill03_step.py:11-17].

Functions + full signatures:
- (S65) `SimulationContext.instance() -> SimulationContext | None` — no params (classmethod [probable]);
  existing context or None [verified: drill03_step.py:12]
- (S66) `SimulationContext() -> SimulationContext` — no-arg constructor fallback when instance() is None;
  other ctor params theoretical [verified: drill03_step.py:14]
- (S67) `sim.step(render: bool = True [probable]) -> None [probable]` — `render`: unitless flag; advance one
  physics step; only `render=True` is drilled [verified: drill03_step.py:16]

Knobs + effect-of-change (K-tags):
- (K17) `render`: type bool, unitless; default True [probable — always explicit `True` in-pack]. `render=True` is
  the only drilled value; render=False effect unproven [verified usage drill03_step.py:16 / theoretical effect].
- (K18) `STEPS` injected global: type `str` as injected → `int(STEPS)` at use, unit physics steps (frames);
  default: none (required by drill03_step.py:15,20). 20 → in-flight z≈1.3-1.5 m; +100 → rested z=0.5 m
  [verified: verify_drill03.py:60-73].

EKB rules:
- IF `instance()` returns None THEN construct `SimulationContext()` — BECAUSE the stepper needs a live
  context either way [verified: drill03_step.py:12-14].
- IF any of this raises THEN print `STEP-FALLBACK <exc>` and use `await update_app_async(steps)` —
  BECAUSE the whole block is wrapped [verified: drill03_step.py:10-20].
- IF reporting which path ran THEN print `via=sim.step|update_app_async` in LIVE-TRUTH — BECAUSE
  verifiers parse it (though they accept either) [verified: drill03_step.py:26, verify_drill03.py:28-33].

LIMITS: none live-verified beyond the fallback path itself [verified: drill03_step.py:10-20].

UNKNOWN (theoretical): when `instance()` returns None vs an existing context; when the constructor path
itself fails (only the fallback marker is observed); effect of `render=True/False` on sensed state.

## Tool 7. Bridge transport — `isaacsim_send.py` + evidence envelope (CLI/JSON)

DOES: Ships in-sim scripts to Isaac Sim and captures printed markers/JSON into `evidence/*.json` as
`{status, output}` [verified: 27 evidence files; verifiers parse them].

Functions + full signatures (as observed in-pack; script itself NOT in-pack — not found under workspace depth 3):
- (S68) `isaacsim_send.py --arg NAME=VALUE` (CLI) — `NAME: str`, `VALUE: str`; in-pack only `STEPS=N` drilled:
  injected as global `STEPS: str`, consumed as `int(STEPS)` (unit physics steps, no default)
  [verified usage: drill03_step.py:1-4,15,20]
- Stdout markers parsed downstream (S-tags = typed payload contracts) [all verified in verifiers]:
  - (S69) `CLEAN-SLATE-OK removed=N` — `removed: int`, unit prims count; informational, parsed by nothing in-pack
    [probable; verified emitted: clean_slate.py:18]
  - (S70) `DRILL01-SETUP-OK ...` / `DRILL02-SETUP-OK ...` / `DRILL03-SETUP-OK ...` — free-form `str` suffix;
    informational setup markers [verified emitted: drill_cube.py:17, drill_joint.py:42, drill03_setup.py:43; no in-pack parser]
  - (S71) `LIVE-TRUTH z=%.4f vz=%.4f via=%s` — `z: float` m 4dp, `vz: float` m/s 4dp | literal `nan`,
    `via: str` enum {`sim.step`, `update_app_async`}; regex `LIVE-TRUTH z=([-\d.]+) vz=([-\dnan.]+) via=(\S+)`
    [verified: drill03_step.py:26 emits, verify_drill03.py:28-33 parses]
  - (S72) `VEL-REPORT z=%.4f vz=%.4f instdiff=%.6f` — `z: float` m 4dp, `vz: float` m/s 4dp,
    `instdiff: float` m/s 6dp; regex `VEL-REPORT z=([-\d.]+) vz=([-\d.]+) instdiff=([-\d.]+)`
    [verified: drill03_vel.py:21 emits, verify_drill03b.py:80-81 parses]
  - (S73) `PROBE_JSON:{...}` — `{...}: dict` as JSON `str` (stdout-wrapped snapshot; `default=str` for non-JSON
    scalars); no in-pack local parser, consumed externally/cross-pack
    [verified emitted: dup_inventory.py:120-122, dup_detail.py:69-71; probable: no parser in-pack]
  - (S74) `STEP-FALLBACK <exc>` — `<exc>: str` (`repr(exc)`); informational fallback marker
    [verified: drill03_step.py:19]
  - (S75) sense.py prints BARE JSON (no marker) — `output: str` = full snapshot object parsed via
    `json.loads(env["output"])` [verified: sense.py:219, co_verify.py:27]
- (S76) Envelope: `env: dict` with `env["status"]: str` (`"ok"` = parse output, else fail fast) +
  `env["output"]: str` (stdout text); parse = `json.loads(env["output"]) -> dict` [verified: co_verify.py:23-28,
  verify_drill03b.py:24-28, verify_drill01.py:25-29, verify_drill02.py:20-24, verify_drill03.py:19-23].
- Multi-encoding loader S80: try `utf-8-sig`, `utf-16`, then `utf-8` [verified: identical `_load` in all 5 verifiers].

Knobs + effect-of-change (K-tags):
- (K19) `--arg STEPS=N`: type `str` on CLI → `int` at use (`int(STEPS)`), unit physics steps; default: none
  (required by drill03_step.py:15,20); sets loop count [verified]; other arg names/types undocumented [theoretical].
- (K20) Evidence encoding order: type `tuple[str,str,str]` = (`utf-8-sig`, `utf-16`, `utf-8`), unitless; no default
  (fixed fallback chain in S80). Bridge output varies (BOM/UTF-16 seen live) — loader order matters, utf-8-sig first
  [verified: needed by real evidence files].

EKB rules:
- IF loading any evidence file THEN try encodings (utf-8-sig, utf-16, utf-8) in order — BECAUSE bridge
  output encoding varies live [verified: all 5 verifiers' `_load`].
- IF `env.status != "ok"` THEN fail fast with the status (never parse output) — BECAUSE output is
  untrustworthy on failed sends [verified: every verifier].
- IF a script needs parameters THEN read injected globals (e.g. bare `STEPS`) — BECAUSE `--arg` injects
  them, no import exists [verified: drill03_step.py].
- IF emitting machine output THEN use a greppable marker prefix (LIVE-TRUTH/VEL-REPORT/PROBE_JSON) or bare
  JSON for full snapshots — BECAUSE verifiers regex stdout, not return values [verified].
- IF vz is unreadable THEN print literal `nan` — BECAUSE the LIVE-TRUTH regex explicitly accepts `[-\dnan.]`
  [verified: verify_drill03.py:28-33].

LIMITS [verified]: bridge output encoding varies; loader tries utf-8-sig/utf-16/utf-8 (all verifiers;
needed by real evidence/*.json).

UNKNOWN (theoretical): full bridge CLI surface (timeouts, retries, arg types beyond STEPS, failure `status`
values) — nothing in-pack documents it; verifiers only handle `status != "ok"` as fatal. `isaacsim_send.py`
source itself is outside this pack (not found in workspace).

## Tool 8. Local verifier harness — stdlib `json`/`sys`/`re` (local)

DOES: Offline assertions over evidence envelopes; exit 0 + `*-PASS` or exit 1 + `*-FAIL` with diff lines [verified: all 5 verifiers].

Functions + full signatures:
- (S77) `json.load(fh: TextIO) -> dict` / `json.loads(s: str) -> dict` — `fh`: open text file (K20 encoding);
  `s`: JSON text; units n/a; envelope + snapshot parse [verified: every verifier]
- (S78) `sys.exit(code: int) -> NoReturn` — `code`: 0 pass / 1 fail (exit-code contract); `main() -> int`
  in every verifier; no default [verified: every verifier's last line + `return 0/1`]
- (S79) `re.search(pattern: str, string: str) -> re.Match | None` — marker extraction (S71 LIVE-TRUTH, S72
  VEL-REPORT); units n/a; None = marker missing → FAIL [verified: verify_drill03.py:28, verify_drill03b.py:80]
- (S80) `_load(path: str) -> dict` — `path`: evidence file path, unitless, no default; multi-encoding open
  (K20 order; falls through to plain `utf-8`); returns envelope dict; in-pack helper, identical in all 5 verifiers
  [verified: co_verify.py:13, verify_drill01.py:14, verify_drill02.py:9, verify_drill03.py:9, verify_drill03b.py:14]
- (S81) `_snap(name: str) -> dict` — `name`: evidence filename e.g. `"co_sense_p1.json"`, no default;
  envelope→snapshot (`status` gate + `json.loads(env["output"])`); raises RuntimeError on non-ok
  [verified: co_verify.py:23, verify_drill03.py:19, verify_drill03b.py:24]
- (S82) `_truth(name: str) -> tuple[z: float, vz: float, via: str]` — `name`: evidence filename, no default;
  `z` in m, `vz` in m/s (literal `nan`→`float('nan')`), `via` S71 enum; raises RuntimeError if no marker
  [verified: verify_drill03.py:26-33]
- (S83) `_close(a: float, b: float) -> bool = abs(a-b) <= TOL` with `TOL: float = 1e-3` (module const, unitless;
  units passthrough of compared quantity); `close(a: float, b: float) -> bool` same shape in verify_drill01;
  verify_drill02 inlines `abs(g-w) > TOL` with `TOL=1e-3` [verified: co_verify.py:10,30-31, verify_drill01.py:7,10-11,
  verify_drill02.py:6,41,51]

Knobs + effect-of-change (K-tags; per-verifier gates — every expectation: type + unit + tolerance):
- (K21) `TOL: float = 1e-3`, unitless const (units passthrough: m for pose/size/z, kg for mass); tensor-agreement
  1e-6 (m for gap, m/s for instdiff — literals, no const); rested-settle 0.05-0.1 m (literals)
  [verified: co_verify.py:10, verify_drill01.py:7, verify_drill02.py:6, verify_drill03.py:64-72, verify_drill03b.py:74-77,91].
- (K22) `verify_drill01.py` (D1): SenseCube `pos: list[float]` m == [2,-1,0.5] ±1e-3, `size: list[float]` m ==
  [1,1,1] ±1e-3, `rigid: bool` is False; prints prim/joint/error counts + full record [verified: full read].
- (K23) `verify_drill02.py` (D2): joint `type: str` exact, `body0/body1: list[str]` exact; `anchor*_pos: list[float]`
  m ±1e-3; `axis: str` lower=="x"; `anchor*_site: str` maxX+midY+midZ / minX+midY+midZ exact; cube `rigid: bool`
  True + `mass: float` kg == 2.0 ±1e-3 [verified: full read].
- (K24) `verify_drill03.py` (D3 v1): A.z≈2.0 m ±0.05; B.z<A.z-0.1 m; B.z==truth±1e-3 m; B.vz<-1 m/s; C.z≈0.5 m ±0.1
  and ==truth±1e-3 m; |C.vz|<0.3 m/s [verified: full read]. NOT superseded-removed — still present and complements
  v2 (v1 checks truth-agreement + vz gates; v2 checks edit-null + two-body + instdiff) [probable: both read fully, gates differ].
- (K25) `verify_drill03b.py` (D3 v2): Phase 1 hot tensor (`source: str`=="tensor", z m in [0.4,2.05], no errors);
  Phase 2 edit-null + B/C two-body (B sources rest, B z-ranges m, gap==2.0 m ±1e-6, C z=0.5 m ±0.05); Phase 3
  VEL-REPORT (z m range, vz m/s in (-4.0,-3.1), instdiff m/s ≤1e-6) [verified: full read].
- (K26) `co_verify.py` (P1-P4): `physics_scene: str`=="/World/PhysicsScene" + `errors: list`==[] for all 4;
  per-body `pos: list[float]` m ±1e-3 / `rigid: bool` / `mass: float` kg ±1e-3 / `collision: bool`; static rigid
  False + collision True; P3 hinge type/bodies exact, `anchor*_pos` m ±1e-3, axis z, sites exact [verified: full read].
- (K27) `EXPECT` tables: type `dict`, module-level, unitless container of typed expectations
  (co_verify.py:34-42, verify_drill01.py:6) — edit here to re-target; no default [verified].

EKB rules:
- IF any probe `errors[]` is non-empty THEN fail the drill — BECAUSE partial snapshots are untrustworthy
  [verified: co_verify.py:82-83, verify_drill03b.py:49].
- IF comparing floats THEN use TOL=1e-3 for authored/pose/mass, 1e-6 for tensor-agreement (gap, instdiff),
  0.05-0.1 for rested-settle z — BECAUSE each tolerance matches its noise source [verified: across verifiers].
- IF a joint axis is compared THEN lowercase it first — BECAUSE token case varies (`str(v).lower()`) [verified: co_verify.py:107, verify_drill02.py:43].
- IF printing results THEN print human-readable values BEFORE the PASS/FAIL line — BECAUSE every verifier
  logs values first for debugging [verified: all 5].
- IF FAILing on missing data THEN return 1 immediately (verify_drill02/03 early-return) vs accumulate-then-report
  (co_verify/03b fails-list) — both patterns in-pack [verified].

LIMITS [verified]: verifiers require zero probe `errors[]` (co_verify.py:82-83, verify_drill03b.py:49);
any `live:` capture failure fails the drill.

UNKNOWN (theoretical): none remaining for v1 verifiers — verify_drill01/02/03 now FULLY read (prior TOOLS.md
"skimmed" note resolved this pass). Cross-pack dup-probe output has no in-pack local parser — its consumer is external.
