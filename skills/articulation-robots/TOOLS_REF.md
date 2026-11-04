# Articulation-Robots TOOLS_REF — Exhaustive Tool Reference (2026-11-04)

Full-tool-mastery companion to TOOLS.md. 11 tools, 81 functions/symbols
(81 typed), 30 knobs (30 typed), 30 limits, 22 unknowns. Every script
below (14/14) read in full. DATATYPE pass: every signature carries exact
param types + return type + units + defaults; 21 still-unknown markers remain
(schema fallback defaults never authored in-pack, tensor exact class,
SITE_API literal, ROBOT_TYPE middle element).

Claim tags: [verified] = live evidence or in-script fact in this pack;
[probable] = strong inference from pack + sibling-pack evidence, not directly
drilled here; [theoretical] = untested hypothesis, do not act on without a drill.

Sources-read (all full): README.md, failures.md, discovery.md,
scripts/a1_build.py, scripts/a1_run.py, scripts/a2_build.py,
scripts/a2_run.py, scripts/a3_build.py, scripts/a3_run.py,
scripts/a4_schema.py, scripts/v4_build.py, scripts/v4_run.py,
scripts/verify_a1.py, scripts/verify_a2.py, scripts/verify_a3.py,
scripts/verify_a4.py, scripts/verify_v4.py; evidence/a1_run.json,
evidence/a2_run.json, evidence/a3_run.json, evidence/a4_run.json,
evidence/v4_run.json (values sampled).

---

## T1 — pxr.UsdPhysics: physics/USD joint + articulation authoring (26 functions, 13 knobs)

DOES: Authors the physics scene, rigid bodies, collisions, masses, joint
frames, angular drives, and articulation roots in USD [verified].

### Functions (typed signatures; units; defaults)

- F1 `UsdPhysics.Scene.Define(stage, path)` — sig:
  `Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdPhysics.Scene`;
  defaults: none (both required); units: n/a (prim path);
  e.g. "/World/PhysicsScene" [verified: a1_build.py:14].
- F2 `scene.CreateGravityDirectionAttr()` — sig:
  `CreateGravityDirectionAttr(defaultValue: Gf.Vec3f [probable] = <schema default> [unknown], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `vector3f`, unitless direction; observed call passes no args
  [verified: a1_build.py:15].
- F3 `scene.CreateGravityMagnitudeAttr()` — sig:
  `CreateGravityMagnitudeAttr(defaultValue: float [probable] = <schema default> [unknown], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `float`, m/s^2; observed no-arg call; `.Set(9.81)`
  [verified: a1_build.py:16].
- F4 `UsdPhysics.RigidBodyAPI.Apply(prim)` — sig:
  `Apply(prim: Usd.Prim) -> UsdPhysics.RigidBodyAPI`;
  defaults: none; units: n/a [verified: a1_build.py:25].
- F5 `UsdPhysics.CollisionAPI.Apply(prim)` — sig:
  `Apply(prim: Usd.Prim) -> UsdPhysics.CollisionAPI`
  [verified: a1_build.py:20,26].
- F6 `UsdPhysics.MassAPI.Apply(prim)` — sig:
  `Apply(prim: Usd.Prim) -> UsdPhysics.MassAPI` [verified: a1_build.py:27].
- F7 `mass_api.GetMassAttr()` — sig: `GetMassAttr() -> Usd.Attribute`
  holding `float`, kg [verified: a1_build.py:27].
- F8 `UsdPhysics.ArticulationRootAPI.Apply(prim)` — sig:
  `Apply(prim: Usd.Prim) -> UsdPhysics.ArticulationRootAPI`;
  prim MUST be the dynamic base-link prim, not the robot Xform
  [verified: a1_build.py:28].
- F9 `UsdPhysics.FixedJoint.Define(stage, path)` — sig:
  `Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdPhysics.FixedJoint`;
  e.g. "/World/A1Bot/RootFixed" [verified: a1_build.py:29].
- F10 `UsdPhysics.RevoluteJoint.Define(stage, path)` — sig:
  `Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdPhysics.RevoluteJoint`;
  e.g. "/World/A1Bot/Hinge" [verified: a1_build.py:42].
- F11 `joint.GetBody0Rel()` — sig: `GetBody0Rel() -> Usd.Relationship`
  (parent body) [verified: a1_build.py:30].
- F12 `joint.GetBody1Rel()` — sig: `GetBody1Rel() -> Usd.Relationship`
  (child body) [verified: a1_build.py:31].
- F13 `rel.AddTarget(path)` — sig:
  `AddTarget(path: Sdf.Path | str) -> None` (observed; canonical bool
  success [probable], call sites ignore return); adds one target
  [verified: a1_build.py:30-31].
- F14 `joint.GetLocalPos0Attr()` — sig:
  `GetLocalPos0Attr() -> Usd.Attribute` holding `point3f`, joint frame
  in body0 space, METERS [verified: a1_build.py:32].
- F15 `joint.GetLocalRot0Attr()` — sig:
  `GetLocalRot0Attr() -> Usd.Attribute` holding `quatf`, joint
  orientation in body0 space, unitless quaternion
  [verified: a1_build.py:33].
- F16 `joint.GetLocalPos1Attr()` — sig:
  `GetLocalPos1Attr() -> Usd.Attribute` holding `point3f`, METERS,
  body1 space [verified: a1_build.py:34].
- F17 `joint.GetLocalRot1Attr()` — sig:
  `GetLocalRot1Attr() -> Usd.Attribute` holding `quatf`, unitless,
  body1 space [verified: a1_build.py:35].
- F18 `joint.GetAxisAttr()` — sig: `GetAxisAttr() -> Usd.Attribute`
  holding `token`, unitless axis enum [verified: a1_build.py:49].
- F19 `UsdPhysics.Tokens.z` — symbol (not a call): type `Tf.Token`
  [probable], value `"z"`, unitless axis enum; `.Set()`-valued into F18
  [verified: a1_build.py:49].
- F20 `UsdPhysics.DriveAPI.Apply(prim, name)` — sig:
  `Apply(prim: Usd.Prim, name: str | Tf.Token) -> UsdPhysics.DriveAPI`;
  name is the multi-apply instance name; `"angular"` observed, required
  (no default) [verified: a3_build.py:51].
- F21 `drive.CreateTypeAttr()` — sig:
  `CreateTypeAttr(defaultValue: str [probable] = <schema default> [unknown], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `token` (observed value `"force"`); observed no-arg call
  [verified: a3_build.py:52].
- F22 `drive.CreateStiffnessAttr()` — sig:
  `CreateStiffnessAttr(defaultValue: float [probable] = <schema default> [unknown], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `float`, P gain, N*m/rad [probable]; observed `.Set(1000.0)`
  [verified: a3_build.py:53].
- F23 `drive.CreateDampingAttr()` — sig:
  `CreateDampingAttr(defaultValue: float [probable] = <schema default> [unknown], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `float`, D gain, N*m*s/rad [probable]; observed `.Set(100.0)`
  [verified: a3_build.py:54].
- F24 `drive.CreateMaxForceAttr()` — sig:
  `CreateMaxForceAttr(defaultValue: float [probable] = <schema default> [unknown], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `float`, effort cap, N (linear) / N*m (angular) [probable];
  observed `.Set(1000000.0)` [verified: a3_build.py:55].
- F25 `drive.CreateTargetPositionAttr()` — sig:
  `CreateTargetPositionAttr(defaultValue: float [probable] = 0.0 [probable], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `float`, angular goal in DEGREES (readback arrives in RADIANS
  via T6); observed `.Set(90.0)` / `.Set(45.0)`
  [verified: a3_build.py:56, v4_build.py:33].
- F26 `attr.Set(value)` (generic Usd.Attribute writer) — sig:
  `Set(value: Gf.Vec3f | Gf.Vec3d | Gf.Quatf | float | str | Tf.Token) -> bool [probable]`
  (call sites ignore return); default: none (value required); units:
  per-attribute [verified: throughout builds].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 Gravity direction: `vector3f` (Gf.Vec3f) | unitless direction |
  authored `Gf.Vec3f(0,0,-1)` [verified: a1_build.py:15]; schema fallback
  default [unknown]. -Z = down; flipping changes fall axis.
- K2 Gravity magnitude: `float` | m/s^2 | authored `9.81`
  [verified: a1_build.py:16]; schema fallback [unknown]. Scales
  weight/settling speed; 0 would float links [0-effect probable].
- K3 Link mass: `float` | kg | authored 2.0 base / 1.0 arm (A1/A3),
  2.0/1.0/0.5 base/Link1/Link2 (A2/A4) [verified: a1_build.py:27,41,
  a2_build.py:47-58]; schema fallback [unknown]. Heavier = more inertia,
  slower drive response [effect probable].
- K4/K5 LocalPos0/LocalPos1: `point3f` (Gf.Vec3f) | METERS, per-body frame |
  authored per-link face offsets (0.5/0.3/0.2) [verified: a1_build.py:32,34,
  a2_build.py:40,42]; schema fallback (0,0,0) [probable]. Wrong offsets
  visibly displace/snap links on play [snap-effect probable].
- K6/K7 LocalRot0/LocalRot1: `quatf` (Gf.Quatf) | unitless quaternion |
  authored identity `Gf.Quatf(1.0)` [verified: a1_build.py:33,35]; schema
  fallback identity [probable]. Non-identity would twist the hinge axis
  [twist-effect probable].
- K8 Axis token: `token` | unitless enum | authored `z`
  [verified: a1_build.py:49]; schema fallback [unknown]. x/y would change
  the swing plane [plane-effect probable].
- K9 Drive type: `token` | unitless enum | authored `"force"`
  [verified: a3_build.py:52]; schema fallback [unknown]. Only drilled type
  (see U1).
- K10 Stiffness: `float` | N*m/rad [probable] | authored `1000.0`
  [verified: a3_build.py:53]; schema fallback [unknown]. Too low = never
  arrives, too high = oscillation [effect probable].
- K11 Damping: `float` | N*m*s/rad [probable] | authored `100.0`
  [verified: a3_build.py:54]; schema fallback [unknown]. Too low =
  overshoot/ring, too high = sluggish [effect probable].
- K12 MaxForce: `float` | N / N*m [probable] | authored `1000000.0`
  [verified: a3_build.py:55]; schema fallback [unknown]. Too low = stall
  short of target [effect probable].
- K13 TargetPosition: `float` | DEGREES (angular drive; readback RADIANS) |
  authored `90.0` (A3) / `45.0` (V4) [verified: a3_build.py:56,
  v4_build.py:33]; schema fallback 0.0 [probable]. Readback arrives at
  pi/2 / pi/4 rad exactly [verified: evidence/a3_run.json,
  evidence/v4_run.json].

### EKB rules (IF/THEN/BECAUSE)

- R1: IF hand-authoring a robot THEN put ArticulationRootAPI on the
  DYNAMIC base link + FixedJoint base->robot-root BECAUSE root-on-Xform
  with a static base yields ndof=0 [verified: failures.md R1].
- R2: IF commanding an angular drive THEN author TargetPosition in
  DEGREES and assert readback in RADIANS BECAUSE 90deg->1.5705 and
  45deg->0.7852 exactly [verified: README, evidence/a3_run.json,
  evidence/v4_run.json].
- R3: IF attaching bodies only THEN skip the articulation root; IF
  driving or reading DOFs THEN add the root first BECAUSE attach needs
  no root but DOF tensors parse from it [verified: failures.md W1].
- R4: IF authoring drives on imported joints THEN author DriveAPI overs
  directly on the referenced joint prim BECAUSE V4 overs arrived at
  target cleanly [verified: v4_build.py:27-33, evidence/v4_run.json].

### LIMITS (with cites)

- L1: Root must be the dynamic base link; root-on-Xform + static base =
  ndof=0 [verified: failures.md R1; a1_build.py:28-35].
- L2: Angular TargetPosition unit is DEGREES; DOF readback is RADIANS
  [verified: README; evidence/a3_run.json q1=1.5705;
  evidence/v4_run.json q1=0.7852].
- L3: Only "force" drive type drilled [verified: a3_build.py:52,
  v4_build.py:29].
- L4: Only revolute + fixed joints drilled [verified: all build scripts].

### UNKNOWN (all theoretical)

- U1: Non-force drive types (acceleration/velocity?) — never drilled.
- U2: Linear drives — never drilled.
- U3: Prismatic / spherical / D6 joints — never drilled.
- U4: Stiffness/damping/maxForce tuning envelope beyond 1000/100/1e6.
- U5: Multi-root assemblies (one root per arm under one stage).

---

## T2 — pxr.UsdGeom: geometry + xform authoring (9 functions, 4 knobs)

DOES: Authors link cubes, robot-root Xforms, ground planes, and translate
ops [verified].

### Functions (typed signatures; units; defaults)

- F1 `UsdGeom.Xform.Define(stage, path)` — sig:
  `Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdGeom.Xform`;
  defaults: none (both required); units: n/a [verified: a1_build.py:21].
- F2 `UsdGeom.Cube.Define(stage, path)` — sig:
  `Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdGeom.Cube`
  [verified: a1_build.py:22].
- F3 `cube.GetSizeAttr()` — sig: `GetSizeAttr() -> Usd.Attribute`
  holding `double`, edge length in METERS [verified: a1_build.py:23].
- F4 `UsdGeom.Plane.Define(stage, path)` — sig:
  `Define(stage: Usd.Stage, path: Sdf.Path | str) -> UsdGeom.Plane`
  [verified: a1_build.py:17].
- F5 `plane.CreateWidthAttr()` — sig:
  `CreateWidthAttr(defaultValue: float [probable] = <schema default> [unknown], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `double`, METERS; observed no-arg call; `.Set(20.0)`
  [verified: a1_build.py:18].
- F6 `plane.CreateLengthAttr()` — sig:
  `CreateLengthAttr(defaultValue: float [probable] = <schema default> [unknown], writeSparsely: bool [probable] = False [probable]) -> Usd.Attribute`
  holding `double`, METERS; observed no-arg call; `.Set(20.0)`
  [verified: a1_build.py:19].
- F7 `UsdGeom.Xformable(prim)` — sig:
  `Xformable(prim: Usd.Prim) -> UsdGeom.Xformable` view
  [verified: a1_build.py:24].
- F8 `xformable.AddTranslateOp()` — sig:
  `AddTranslateOp(precision: UsdGeom.XformOp.Precision [probable] = double [probable], opSuffix: str [probable] = "" [probable]) -> UsdGeom.XformOp`;
  observed no-arg call; op value in METERS [verified: a1_build.py:24].
- F9 `xformop.Set(value)` — sig: `Set(value: Gf.Vec3d) -> bool [probable]`
  (call sites ignore return); value in METERS; no default (required)
  [verified: a1_build.py:24].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 Cube size: `double` | METERS edge | authored 1.0 base/arm (A1/A3),
  1.0/0.6/0.4 base/Link1/Link2 (A2/A4) [verified: a1_build.py:23,
  a2_build.py:47-58]; schema fallback [unknown]. Joint LocalPos offsets
  are half-sizes so MUST match (0.5/0.3/0.2).
- K2/K3 Plane width/length: `double` | METERS | authored `20.0`
  [verified: a1_build.py:18-19]; schema fallback [unknown]. Smaller risks
  links falling off [edge-effect probable].
- K4 Translate: `double3` (Gf.Vec3d) | METERS | authored (0,0,z) stacking
  0.5/1.5 (A1), 0.5/1.3/1.8 (A2) [verified: a1_build.py:24,38,
  a2_build.py:47-58]; op default (0,0,0) [probable]. Mismatch with joint
  frames causes play-time snap [snap-effect probable].

### EKB rules

- R1: IF sizing a link THEN set joint LocalPos offsets to size/2 BECAUSE
  hinges sit at link faces (0.5 for 1.0 cubes, 0.3/0.2 for 0.6/0.4)
  [verified: a2_build.py:55-58].
- R2: IF stacking links THEN z = parent-top + size/2 BECAUSE A2 uses
  0.5/1.3/1.8 for 1.0/0.6/0.4 cubes [verified: a2_build.py:47-58].

### LIMITS

- L5: Only Cube link geometry drilled; only Plane grounds drilled
  [verified: all build scripts].

### UNKNOWN (all theoretical)

- U6: Mesh/capsule/sphere link geometry inside articulations.
- U7: Rotated/scaled XformOps on links (only translate drilled).

---

## T3 — pxr.Gf: math value types (3 functions, 2 knobs)

DOES: Provides vector/quaternion values for physics and xform attributes
[verified].

### Functions (typed signatures; units; defaults)

- F1 `Gf.Vec3f(x, y, z)` — sig:
  `Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` (float32 x3);
  defaults: none observed (all three passed); units: per-use — METERS
  (joint LocalPos) or unitless (gravity dir)
  [verified: a1_build.py:15,32].
- F2 `Gf.Vec3d(x, y, z)` — sig:
  `Vec3d(x: float, y: float, z: float) -> Gf.Vec3d` (float64 x3);
  defaults: none observed; units: METERS (translate ops)
  [verified: a1_build.py:24].
- F3 `Gf.Quatf(w)` / identity — sig:
  `Quatf(w: float, x: float [probable] = 0.0 [probable], y: float [probable] = 0.0 [probable], z: float [probable] = 0.0 [probable]) -> Gf.Quatf`;
  observed `Gf.Quatf(1.0)` identity; units: unitless quaternion (w,x,y,z)
  [verified: a1_build.py:33].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 Vector components: `float` x3 (Vec3f float32 / Vec3d float64) |
  METERS (positions) or unitless (directions) | authored per call site
  [verified: a1_build.py:15,24,32]. Wrong sign flips side or fall
  direction.
- K2 Quaternion components: `float` x4 (w,x,y,z) | unitless |
  authored identity (1,0,0,0) only [verified: a1_build.py:33]. Only
  identity drilled.

### EKB rules

- R1: IF setting a joint frame THEN use `Gf.Quatf(1.0)` identity on both
  sides BECAUSE every drilled hinge uses identity rots with zero
  twist faults [verified: a1_build.py:33-35, a2_build.py:41-43].

### LIMITS

- L6: Only identity quaternions drilled [verified: all build scripts].

### UNKNOWN

- (none — trivial value types) [verified].

---

## T4 — omni.usd: stage access + prim management (17 functions, 2 knobs)

DOES: Opens the live stage and creates/removes/looks-up prims plus
APIs/attributes/relationships/references [verified].

### Functions (typed signatures; units; defaults)

- F1 `omni.usd.get_context()` — sig: `get_context() -> UsdContext` (live
  USD context); units: n/a [verified: a1_build.py:9].
- F2 `context.get_stage()` — sig: `get_stage() -> Usd.Stage` (live stage)
  [verified: a1_build.py:9].
- F3 `stage.GetPrimAtPath(path)` — sig:
  `GetPrimAtPath(path: str | Sdf.Path) -> Usd.Prim` (possibly invalid;
  guard with F6); units: n/a [verified: a1_build.py:11].
- F4 `stage.DefinePrim(path)` — sig:
  `DefinePrim(path: str | Sdf.Path, typeName: Tf.Token [probable] = "" (typeless Xform-scope) [probable]) -> Usd.Prim`;
  observed single-arg call [verified: v4_build.py:16].
- F5 `stage.RemovePrim(path)` — sig:
  `RemovePrim(path: str | Sdf.Path) -> bool [probable]` (call sites
  ignore return); units: n/a [verified: a1_build.py:13].
- F6 `prim.IsValid()` — sig: `IsValid() -> bool`
  [verified: a1_build.py:12].
- F7 `stage.Traverse()` — sig: `Traverse() -> Usd.PrimRange` [probable]
  (iterator over all prims; list-comprehended at call site)
  [verified: a1_run.py:9].
- F8 `prim.HasAPI(schema_or_token)` — sig:
  `HasAPI(schema: type[Usd.APISchemaBase] [probable] | str | Tf.Token) -> bool`;
  observed `UsdPhysics.ArticulationRootAPI` class and
  `Classes.ROBOT_API.value` token string [verified: a1_run.py:10,
  v4_run.py:11].
- F9 `prim.ApplyAPI(token)` — sig:
  `ApplyAPI(apiName: str | Tf.Token, instanceName: str [probable] = "" [probable]) -> bool [probable]`
  (call sites ignore return; observed "None-ish"); observed single token
  arg e.g. "IsaacRobotAPI" via `Classes.ROBOT_API.value`
  [verified: a4_schema.py:58,61].
- F10 `prim.CreateAttribute(name, type)` — sig:
  `CreateAttribute(name: str | Tf.Token, type: Sdf.ValueTypeName, custom: bool [probable] = True [probable]) -> Usd.Attribute`;
  observed 2-arg call with `(tname, ttype)` from
  `Attributes.ROBOT_TYPE.value` [verified: a4_schema.py:59-60].
- F11 `prim.GetAttribute(name)` — sig:
  `GetAttribute(name: str | Tf.Token) -> Usd.Attribute`
  [verified: a4_schema.py:69, v4_run.py:12].
- F12 `attr.Get()` — sig:
  `Get(timeCode: Usd.TimeCode [probable] = Usd.TimeCode.Default() [probable]) -> Any`
  (type-matched stored value; `str` observed for robot type); observed
  no-arg call [verified: a4_schema.py:69].
- F13 `prim.GetRelationship(name)` — sig:
  `GetRelationship(name: str) -> Usd.Relationship`; observed
  `Relations.ROBOT_LINKS.value[0]` [verified: a4_schema.py:65-66].
- F14 `rel.GetTargets()` — sig: `GetTargets() -> list[Sdf.Path]`
  (str()-ified at call site) [verified: a4_schema.py:66].
- F15 `prim.GetReferences()` — sig: `GetReferences() -> Usd.References`
  [verified: v4_build.py:17].
- F16 `refs.AddReference(asset_path)` — sig:
  `AddReference(assetPath: str | Sdf.AssetPath, primPath: Sdf.Path [probable] = / [probable], layerOffset: Sdf.LayerOffset [probable] = None [probable]) -> bool [probable]`
  (call site ignores return; observed "None-ish"); observed single-arg
  call with M2 .usda package path (str); further reference kwargs
  unobserved [probable] [verified: v4_build.py:17-19].
- F17 `prim.GetPath()` — sig: `GetPath() -> Sdf.Path` (str()-ified for
  reports) [verified: a1_run.py:9].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 Prim paths: `str` (Sdf.Path-compatible) | unitless identity |
  authored "/World/A?Bot/..." per drill [verified: a1_run.py:9-10].
  Traverse + HasAPI scans find roots by API, not path.
- K2 Reference asset path: `str` (filesystem path to .usda) | unitless |
  authored M2 package path [verified: v4_build.py:17-19]. Composes
  imported robot under /World/V4Bot; wrong path = empty/broken prim
  [break-effect probable].

### EKB rules

- R1: IF rebuilding THEN RemovePrim each top path after an IsValid guard
  BECAUSE every build clears stale bots/grounds/scenes first [verified:
  a1_build.py:10-13].
- R2: IF finding articulation roots THEN Traverse + HasAPI(root API)
  BECAUSE path-independent scan reports exactly the rooted link
  [verified: a1_run.py:9-10, evidence/a1_run.json].
- R3: IF composing an imported robot THEN DefinePrim + AddReference
  BECAUSE V4 composed the M2 package this way and drove it [verified:
  v4_build.py:16-19, evidence/v4_run.json].

### LIMITS

- L7: Referenced joints accept authored DriveAPI overs and arrive at
  target [verified: v4_build.py:27-33, evidence/v4_run.json q1=0.7852].
- L8: `ApplyAPI` with string token observed only for Isaac robot/site
  APIs [verified: a4_schema.py:58,61].

### UNKNOWN (all theoretical)

- U8: Payload-based (vs reference-based) composition of robot packages.
- U9: `GetAttribute().Get()` at non-default timeCodes.
- U10: RemovePrim on prims with active articulation tensors mid-play.

---

## T5 — omni.timeline: sim clock + pause control (3 functions, 0 knobs)

DOES: Reads sim time and pauses the timeline after a run leg [verified].

### Functions (typed signatures; units; defaults)

- F1 `omni.timeline.get_timeline_interface()` — sig:
  `get_timeline_interface() -> ITimeline`; units: n/a
  [verified: a1_run.py:12].
- F2 `tl.get_current_time()` — sig: `get_current_time() -> float`
  (double SECONDS; float()-wrapped at call site); dt = t1-t0 proves time
  advanced [verified: a1_run.py:15,18; dt=1.000/2.000 in evidence].
- F3 `tl.pause()` — sig: `pause() -> None` [probable] (call sites ignore
  return; observed "None-ish"); ends the run leg [verified: a1_run.py:19].

### Knobs + effect-of-change (0 knobs — nothing to type)

- (none authored — clock is read-only; dt is derived) [verified].

### EKB rules

- R1: IF running a leg THEN snapshot t0 before stepping and t1 after,
  assert dt>0 BECAUSE every verifier requires time advance as the
  play-actually-ran proof [verified: verify_a1.py:42, all verifiers].
- R2: IF ending a run script THEN call `tl.pause()` BECAUSE all five run
  scripts pause, leaving a settled stage for the next leg [verified:
  a1_run.py:19, a2_run.py:20, a3_run.py:14, v4_run.py:23].

### LIMITS

- L9: `play()` via the timeline interface never drilled — play always
  via app_utils [verified: all run scripts].

### UNKNOWN (all theoretical)

- U11: `tl.play()` / `tl.stop()` behavior from in-sim scripts.
- U12: `get_current_time()` resolution under sub-stepped physics.

---

## T6 — isaacsim.core.experimental.prims.Articulation: live DOF state (4 functions, 1 knob)

DOES: Reads live articulation DOF positions after play [verified].

### Functions (typed signatures; units; defaults)

- F1 `Articulation(root_link_path)` — sig:
  `Articulation(root_link_path: str) -> Articulation` view (additional
  ctor kwargs possible but unobserved [probable]); path is the ROOT LINK
  prim (e.g. "/World/A1Bot/Base"), NOT the robot Xform; no default
  (required); units: n/a (prim path) [verified: a1_run.py:11].
- F2 `robot.get_dof_positions()` — sig:
  `get_dof_positions() -> Tensor` (tensor-like with `.numpy()`; exact
  tensor class — torch vs carb — [unknown]); values in RADIANS, shape
  (nArticulations, nDOF); scripts index `[0]` (first/only articulation
  instance) then `.tolist()` or `[0]` scalar [verified: a1_run.py:14,
  a3_run.py:9].
- F3 `robot.dof_names` — attr (not a call): type `Sequence[str]`
  [probable] (list-like of joint names, e.g. Hinge1,Hinge2); unitless
  names; `list(robot.dof_names)` for reports [verified: a2_run.py:14,
  evidence/a2_run.json names=Hinge1,Hinge2].
- F4 `tensor.numpy()` — sig: `numpy() -> numpy.ndarray` (float values in
  RADIANS), shaped (nArticulations, nDOF)
  [verified: indexing `[0]` in all run scripts].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 Constructor path: `str` (prim path) | unitless | no default
  (required); authored "/World/A?Bot/Base" [verified: a1_run.py:11]. Must
  be the rooted base LINK; pointing at the robot Xform or an unrooted
  prim yields no/zero DOFs [failure-mode probable per R1/failures.md].

### EKB rules

- R1: IF constructing Articulation THEN pass the root LINK path BECAUSE
  A1/A2/A3/V4 all construct on Base and read ndof>=1 [verified:
  a1_run.py:11, evidence/a1_run.json ndof=1].
- R2: IF asserting drive arrival THEN assert travel (q0<q1) + arrival
  (q1~=target rad +-0.25), NEVER q0~=0 BECAUSE q0 slips under active
  drives (0.4441 in A3, 0.0335 in V4) [verified: evidence/a3_run.json,
  evidence/v4_run.json, README, physics F5].
- R3: IF asserting rest state THEN allow |q|<=0.05 BECAUSE undriven
  vertical-axis chains read ~1e-8..1e-12 [verified:
  evidence/a1_run.json, evidence/a2_run.json, verify_a1.py:40].

### LIMITS

- L10: Tensors need play; USD parses need the root API [verified: README].
- L11: q0 slips under active drives — 0.4441 (A3) / 0.0335 (V4), not ~0
  [verified: evidence/a3_run.json, evidence/v4_run.json].
- L12: Rest q reads ~1e-8 on undriven vertical-axis chains [verified:
  evidence/a1_run.json, evidence/a2_run.json].
- L13: Only single-articulation `[0]` indexing drilled [verified: all
  run scripts].

### UNKNOWN (all theoretical)

- U13: `get_dof_velocities` — discovery goal 2 names it; zero evidence.
- U14: DOF writes / effort interfaces through this class.
- U15: `dof_names` ordering vs joint authoring order on wider chains.

---

## T7 — isaacsim.core.experimental.utils.app: play + stepping (2 functions, 1 knob)

DOES: Starts play and advances the app a fixed step count inside async
in-sim scripts [verified].

### Functions (typed signatures; units; defaults)

- F1 `app_utils.play()` — sig: `play() -> None` [probable] (call sites
  ignore return; observed "None-ish"); starts the timeline; observed
  no-arg call [verified: a1_run.py:13].
- F2 `await app_utils.update_app_async(steps=N)` — sig:
  `update_app_async(steps: int, additional kwargs unobserved [probable]) -> Coroutine[None]`
  (must be awaited, async); steps in SIM STEPS (frames; 60 steps ~=
  dt 1.000 s, 120 steps ~= dt 2.000 s at ~60 Hz [verified evidence]);
  observed `steps=60` rest legs, `steps=120` drive legs
  [verified: a1_run.py:16, a3_run.py:11].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 steps: `int` | SIM STEPS (frames @ ~60 Hz; 60 -> dt 1.000 s, 120 ->
  dt 2.000 s) | authored 60 (rest readback legs) / 120 (drive settle
  legs) [verified: evidence/a1_run.json dt=1.000,
  evidence/a3_run.json dt=2.000]; no default observed (always passed
  explicitly). Fewer steps risks unread arrival [risk probable].

### EKB rules

- R1: IF reading rest DOFs THEN 60 steps suffice BECAUSE A1/A2 rest legs
  settle at dt=1.000 [verified: a1_run.py:16, evidence].
- R2: IF driving to target THEN use 120 steps BECAUSE A3/V4 arrival legs
  settle at dt=2.000 [verified: a3_run.py:11, evidence].
- R3: IF stepping THEN await inside an async in-sim script BECAUSE every
  run script awaits update_app_async [verified: all run scripts].

### LIMITS

- L14: Only steps=60/120 drilled; stop behavior never drilled (pause via
  timeline instead) [verified: all run scripts].

### UNKNOWN (all theoretical)

- U16: Minimum steps for reliable arrival at other stiffness/damping.
- U17: `update_app_async` without prior `play()`.

---

## T8 — usd.schema.isaac.robot_schema: robot schema overlay + validation (7 functions, 2 knobs)

DOES: Applies the Isaac robot/link/joint/site schema overlay and validates
populated relations [verified].

### Functions (typed signatures; units; defaults)

- F1 `Classes.ROBOT_API.value` — symbol (not a call): type `str`,
  applied-API token `"IsaacRobotAPI"` (per README); unitless; passed to
  `prim.ApplyAPI` [verified: a4_schema.py:58, README].
- F2 `Classes.SITE_API.value` — symbol: type `str` (exact literal
  [unknown] — never echoed in reports); site-API token applied to tip
  Xform prim; unitless [verified use: a4_schema.py:61].
- F3 `Attributes.ROBOT_TYPE.value` — symbol: type
  `tuple[str, <middle element type> [unknown], Sdf.ValueTypeName]`
  (name, ?, type); unpacked as `tname, _, ttype`, then
  `robot.CreateAttribute(tname, ttype)` [verified: a4_schema.py:59-60].
- F4 `Relations.ROBOT_LINKS` — symbol: relation-name holder; `.value`:
  `tuple[str, ...] | list[str]` [probable]; `.value[0]`: `str`
  relationship name for `prim.GetRelationship`; unitless
  [verified: a4_schema.py:65-66].
- F5 `Relations.ROBOT_JOINTS` — symbol: same shape as F4
  (`.value`: `tuple[str, ...] | list[str]` [probable]); `.value[0]`:
  `str` [verified: a4_schema.py:67-68].
- F6 `PopulateRobotSchemaFromArticulation(stage, robot, base_link)` — sig:
  `PopulateRobotSchemaFromArticulation(stage: Usd.Stage, robot: Usd.Prim, base_link: Usd.Prim) -> tuple[Usd.Prim, Usd.Prim]`
  (root_link, root_joint); defaults: none (all required); units: n/a;
  `root_link.GetPath()` reported; applies Link/Joint APIs itself
  [verified: a4_schema.py:62-63,72].
- F7 `ValidateRobotSchemaRelationships(robot)` — sig:
  `ValidateRobotSchemaRelationships(robot: Usd.Prim) -> tuple[list[Sdf.Path] [probable], list[Sdf.Path] [probable], list[Sdf.Path] [probable], list[Sdf.Path] [probable]]`
  (valid_links, invalid_links, valid_joints, invalid_joints); bad =
  len(il)+len(ij) must be 0 [verified: a4_schema.py:64,70].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 Robot type string: `str` (token-ish classification attr) | unitless |
  authored `"Manipulator"` (A4) [verified: a4_schema.py:60,
  evidence/a4_run.json]; imported arm reads `"Default"`
  [verified: evidence/v4_run.json]. Verifier requires exact "Manipulator"
  on A4.
- K2 base_link prim arg to Populate: `Usd.Prim` | unitless | no default
  (required); authored `stage.GetPrimAtPath("/World/A4Bot/Base")`
  [verified: a4_schema.py:62-63, evidence/a4_run.json rootlink]. Graph-walk
  seed; must be the rooted base link.

### EKB rules

- R1: IF importing Populate/Validate THEN import from
  `usd.schema.isaac.robot_schema.utils` (submodule), NOT the package
  root BECAUSE both live in `.utils` [verified: a4_schema.py:10-11,
  README].
- R2: IF applying the overlay THEN ApplyAPI robot + set type + SiteAPI
  tip BEFORE Populate BECAUSE A4 orders it so and Populate fills
  relations from the articulation graph [verified: a4_schema.py:57-63].
- R3: IF validating THEN assert bad==0 AND expected links/joints subsets
  BECAUSE Populate includes RootFixed in joints (3 joints: RootFixed,
  Hinge1, Hinge2) and the verifier checks WANT sets [verified:
  evidence/a4_run.json, verify_a4.py:7-8,44-47].
- R4: IF unpacking ROBOT_TYPE THEN use 3-tuple `tname, _, ttype` BECAUSE
  `.value` carries (name, ?, type) [verified: a4_schema.py:59].

### LIMITS

- L15: Populate + Validate live in `.utils`, not the package root
  [verified: a4_schema.py:10-11, README].
- L16: Populate applies Link/Joint APIs itself (no manual per-link API
  application needed) [verified: README, a4_schema.py:62-63].
- L17: Populate includes the FixedJoint anchor (RootFixed) in ROBOT_JOINTS
  [verified: evidence/a4_run.json joints list].
- L18: Imported-arm robot type reads "Default", not "Manipulator"
  [verified: evidence/v4_run.json].
- L19: No play needed — pure USD authoring + validation [verified:
  a4_schema.py docstring, no app_utils import].

### UNKNOWN (all theoretical)

- U18: Robot types other than Manipulator/Default.
- U19: SiteAPI use beyond apply (tip semantics, multiple sites).
- U20: Schema behavior on multi-arm (multi-root-anchored) assemblies.

---

## T9 — isaacsim_send.py bridge: in-sim execution transport (1 function, 0 knobs)

DOES: Ships the aN_build/aN_run/a4_schema/v4 scripts into the live Isaac
Sim process and returns JSON evidence [verified: README].

### Functions (typed signatures; units; defaults)

- F1 Bridge round-trip (transport only) — sig (observed envelope):
  input: script file path `str` (.py executed in-sim); output: `dict`
  JSON envelope `{status: str, output: str, result: Any | evalue: str}`;
  `status == "ok"` + output carrying `*-REPORT`/`*-OK` lines is the pass
  signal; units: n/a [verified: README, every evidence/*.json, every
  verifier's `run.get("status")` gate].

### Knobs + effect-of-change (0 knobs — nothing to type)

- (none — owned by another pack, not documented here) [verified: TOOLS.md].

### EKB rules

- R1: IF a verifier gates on status THEN treat status!="ok" as immediate
  FAIL with evalue BECAUSE every verifier exits 1 before parsing output
  [verified: verify_a1.py:22-24, all verifiers].

### LIMITS

- L20: All authorship/execution scripts run in-sim via this bridge; only
  verify_* run locally [verified: README].

### UNKNOWN (all theoretical)

- U21: Bridge CLI flags / error envelope details — owned elsewhere.

---

## T10 — Local verify harness: stdlib json/re/sys/math evidence evaluators (7 functions, 2 knobs)

DOES: Parses evidence/*.json report lines locally and exits 0 on pass
[verified].

### Functions (typed signatures; units; defaults)

- F1 `_load(path)` (local helper, each verifier) — sig:
  `_load(path: str) -> dict`; tries encodings
  `tuple[str,str,str] = ("utf-8-sig", "utf-16", "utf-8")` on Unicode
  errors, falls back to plain utf-8 load; units: n/a [verified:
  verify_a1.py:9-16, identical in all five verifiers].
- F2 `json.load(fh)` — sig: `json.load(fh: TextIO) -> dict`
  [verified: verify_a1.py:13].
- F3 `open(path, encoding=enc)` — sig:
  `open(path: str, encoding: str = "utf-8" [probable stdlib default]) -> TextIO`;
  observed `open(path, encoding=enc)`; further open() kwargs unobserved
  [verified: verify_a1.py:12].
- F4 `re.search(pattern, output)` — sig:
  `re.search(pattern: str, string: str, flags: int [probable] = 0 [probable]) -> re.Match | None`;
  observed per-drill report-line regex (`A1-REPORT`/`A2-REPORT`/etc. with
  named groups) over the output string; None = FAIL "no report"
  [verified: verify_a1.py:25-29].
- F5 `run.get(key)` envelope reads — sig:
  `dict.get(key: str, default: Any [probable] = None [probable]) -> Any`;
  keys: `"status"` (str, must be `"ok"`), `"output"` (str report text),
  `"evalue"` (str error text on failure) [verified: verify_a1.py:22-24].
- F6 `float()/int()` group parsing + `math.pi` comparisons — sigs:
  `float(x: str) -> float`, `int(x: str) -> int`;
  `math.pi: float` constant; arrival tolerance +-0.25 RADIANS vs pi/2
  (A3) / pi/4 (V4); dt parsed as float SECONDS
  [verified: verify_a3.py:31-36, verify_v4.py:33-48].
- F7 `sys.exit(main())` — sigs: `main() -> int` (0 pass / 1 fail);
  `sys.exit(code: int) -> NoReturn` [probable]; prints `A?-PASS` or
  `A?-FAIL` + bulleted causes [verified: verify_a1.py:44-53].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 Tolerance thresholds: `float` | RADIANS (q) / SECONDS (dt) |
  authored rest |q|<=0.05, arrival +-0.25 rad, dt>0
  [verified: verify_a1.py:40, verify_a3.py:35-37]. Tightening risks flaky
  fails (q0 slip), loosening risks false passes [effect probable].
- K2 Encodings tuple: `tuple[str,str,str]` | unitless |
  authored `("utf-8-sig", "utf-16", "utf-8")` [verified: verify_a1.py:10].
  Handles BOM/UTF-16 bridge output; dropping one risks decode failure on
  some evidence [effect probable].

### EKB rules

- R1: IF writing a verifier THEN copy `_load` verbatim BECAUSE all five
  verifiers share the identical multi-encoding loader [verified: all
  verify_*.py:9-16].
- R2: IF parsing floats THEN use the `[-\d., eE+]+` char class for
  lists and `[-\d.]+` for scalars BECAUSE rest reads carry exponents
  (1.3e-08) while drive reports print %.4f [verified: verify_a1.py:25,
  verify_a3.py:26].
- R3: IF verifying chains THEN cross-check joint bodies from a sense
  snapshot (body0/body1 singleton lists) BECAUSE verify_a2 asserts
  Hinge bodies against a2_sense.json joints [verified:
  verify_a2.py:47-55].
- R4: IF status != "ok" THEN fail before regex BECAUSE output may be
  missing/traceback text [verified: all verifiers].

### LIMITS

- L21: Pure local parsing — no sim contact; trusts evidence files on disk
  [verified: all verify_*.py].
- L22: verify_a2 additionally depends on evidence/a2_sense.json snapshot
  shape `{joints: [{path, body0:[..], body1:[..]}]}` [verified:
  verify_a2.py:47-55].
- L23: Arrival tolerance +-0.25 rad is loose by design (q1 lands exact
  but PD variance allowed) [verified: verify_a3.py:35, q1=1.5705].

### UNKNOWN

- (none — fully visible in-script) [verified].

---

## T11 — Executor joint actions: attach-only wheels (2 functions, 3 knobs)

DOES: Attaches wheels to a dynamic cube via revolute joints without hand
USD [verified: failures.md W1].

### Functions (typed signatures; units; defaults)

- F1 `create.objects.sphere` — sig (executor action; NO in-pack script
  call site — param types [theoretical]):
  `create.objects.sphere(size: float [theoretical] (METERS, wheel size), pose args: types [theoretical], further kwargs: types [theoretical]) -> str (DynamicSphere prim path) [probable]`;
  exact CLI spelling owned by executor docs [probable]. Returns a dynamic
  rigid prim [verified behavior: failures.md W1].
- F2 `joint.create.joint` — sig (executor action; NO in-pack script call
  site — param types [theoretical]):
  `joint.create.joint(type: str [theoretical] (observed "revolute") [probable], axis: str [probable] (unitless enum X|Y|Z [theoretical]; observed "Y"), from: str (prim path) [probable], to: str (prim path) [probable], further kwargs: types [theoretical]) -> str (joint prim path) [probable]`;
  exact CLI spelling owned by executor docs [probable]. Auto-names
  `{from}_to_{to}` unique per wheel; sets wheel-center frames itself
  (LocalPos0 METERS = wheel offset in cube frame, LocalPos1 = origin,
  inverse-orient rots) [verified behavior: failures.md W1].

### Knobs + effect-of-change (attr type | unit | authored default)

- K1 axis: `str` (axis enum) | unitless | authored `"Y"` (as `axis=Y`
  CLI spelling [probable]) [verified value: failures.md W1]. Y-axis
  hinges give X-rolling wheels on +/-Y cube faces; other axes change roll
  direction [effect probable].
- K2 Lateral gap: `float` | METERS | authored `0.05` (inner edge 0.55 vs
  face 0.5) [verified value: failures.md W1]. Prevents initial
  interpenetration; zero gap risks spawn collision pop [effect probable].
- K3 Auto-name: `str` | unitless | pattern `{from}_to_{to}`
  [verified: failures.md W1]. Unique per wheel; renaming risks collisions
  only if duplicated.

### EKB rules

- R1: IF attaching executor wheels THEN pause the sim first BECAUSE the
  op requires `_need_paused` [verified: failures.md W1].
- R2: IF attaching THEN both sides must be dynamic rigid AND wheels need
  a small lateral gap BECAUSE DynamicSphere is dynamic and 0.05 gap was
  verified pop-free [verified: failures.md W1].
- R3: IF driving executor wheels later THEN add an articulation root on
  the dynamic cube first (per T1-R1) BECAUSE attach needs no root but
  drives do [verified: failures.md W1].

### LIMITS

- L24: Sim must be paused (`_need_paused`) [verified: failures.md W1].
- L25: Both sides must be dynamic rigid [verified: failures.md W1].
- L26: Wheels need a small lateral gap from the cube face (0.05 used)
  [verified: failures.md W1].
- L27: Executor sets wheel-center frames itself — no snap on play
  [verified: failures.md W1].
- L28: Auto-names `{from}_to_{to}` unique per wheel [verified:
  failures.md W1].
- L29: Attach-only verified; drive step open [verified: failures.md W1].
- L30: No articulation root needed for attach-only [verified:
  failures.md W1].

### UNKNOWN (all theoretical)

- U22: Driving executor-created wheel joints (root + drives on top).

---

## Cross-tool chains (verified assemblies)

- C1 Build->run->verify: aN_build authors USD in-sim via T9, aN_run steps
  (T7) and reads DOFs (T6) + clock (T5), verify_aN parses the envelope
  (T10) [verified: scripts + evidence].
- C2 Import->drive->schema: v4_build references M2 (T4-F16) + overs a
  drive (T1-F20..F25); v4_run checks schema (T8 reads via T4) + arrival
  (T6/T7) [verified: v4_build.py, v4_run.py, evidence/v4_run.json].
- C3 Root->tensor->schema: T1 root enables T6 tensors and T8 Populate
  graph-walk; all three agree on Base (roots report, ndof>=1, rootlink)
  [verified: evidence/a1_run.json, evidence/a4_run.json].

## Counts

- Tools: 11 | functions/symbols: 81 | knobs: 30 | EKB rules: 30
  (T1:4 T2:2 T3:1 T4:3 T5:2 T6:3 T7:3 T8:4 T9:1 T10:4 T11:3)
  | limits L1-L30: 30 | unknowns U1-U22: 22 (all theoretical).
- DATATYPE: signatures typed 81/81 | knobs typed 30/30 | still-unknown 21
  (markers: T1-F2/F3/F21-F24 schema defaults (6), T1-K1/K2/K3/
  K8-K12 fallbacks (8), T2-F5/F6 schema defaults (2), T2-K1/K2-K3
  fallbacks (2), T6-F2 exact tensor class (1), T8-F2 SITE_API literal (1),
  T8-F3 middle element type (1); function/knob pairs overlap, so 13
  distinct facts).
