# physics TOOLS_REF — exhaustive tool reference (2026-11-04)

Pack: `action-reasoner/skills/physics/` (`core/` + `engines/`).
Root docs: `SKILL.md`, `failures.md`, `discovery.md`.
Scripts: 36 total — 20 fully read, 16 skimmed (see Sources at bottom).
Datatype pass (2026-11-04): signatures 104/105 typed
(still-unknown: Tool 18 `png_stats`); knobs 33/35 typed
(still-unknown: Tool 1 friction/restitution group, Tool 6 hidden
solver knobs). Rule: one `- ` bullet in a Functions subsection =
one signature entry; one `- ` bullet documenting an actual knob =
one knob entry (absence notes excluded).
Claim tags: **[V]** = live-verified (evidence/script cite),
**[P]** = probable (strong inference from verified data),
**[T]** = theoretical (untested, do not rely on).

Physics knobs live mostly in Tool 1 (UsdPhysics) and Tool 6
(PhysxSchema); engine knobs in Tool 13 (newton). Tools without
prim knobs say so explicitly.

---

## Tool 1. pxr.UsdPhysics — physics schema authoring

DOES: Authors the PhysicsScene, rigid bodies, collisions, mass,
joints, joint limits, and drives on USD prims. Every physics
scene in the pack is built with this module only (plus Tool 6
for PhysX extras). [V]

### Functions (full signatures as used in-pack; cites ground each type)

- `Scene.Define(stage: Usd.Stage, path: str | Sdf.Path)
  -> UsdPhysics.Scene` — creates the PhysicsScene prim. [V]
  Str paths in every setup script, e.g.
  `core/scripts/p1_setup.py:17`.
- `Scene.CreateGravityDirectionAttr() -> Usd.Attribute`, then
  `.Set(value: Gf.Vec3f) -> bool [probable]` — direction is a
  dimensionless unit vector; `(0,0,-1)` in all gravity drills.
  (`core/scripts/p1_setup.py:18`.) [V]
- `Scene.CreateGravityMagnitudeAttr() -> Usd.Attribute`, then
  `.Set(value: float) -> bool [probable]` — value in m/s^2:
  `9.81` normal, `0.0` zero-g.
  (`core/scripts/p2_setup.py:19`.) [V]
- `RigidBodyAPI.Apply(prim: Usd.Prim) -> UsdPhysics.RigidBodyAPI`
  — marks prim dynamic. (`core/scripts/p1_setup.py:29`.) [V]
- `CollisionAPI.Apply(prim: Usd.Prim) -> UsdPhysics.CollisionAPI`
  — marks prim a collider (static if no RigidBodyAPI).
  (`core/scripts/p1_setup.py:24`.) [V]
- `MassAPI.Apply(prim: Usd.Prim) -> UsdPhysics.MassAPI`;
  `.GetMassAttr() -> Usd.Attribute` + `.Set(value: float)` in
  kg (`core/scripts/p1_setup.py:31`);
  `.CreateMassAttr(defaultValue: float) -> Usd.Attribute` in kg
  (`engines/scripts/p4_convert.py:38`);
  `.CreateDensityAttr(defaultValue: float) -> Usd.Attribute` in
  kg/m^3 (`engines/scripts/p4_preflight.py:62`). All `.Set`
  returns `bool [probable]` (unchecked in-pack). Masses
  drilled: 1.0 (P1-P5), 2.0 (preflight dirty), 5.0 (V1, V14).
  [V]
- `MassAPI(prim: Usd.Prim) -> UsdPhysics.MassAPI` (ctor);
  `.GetMassAttr() / .GetDensityAttr() /
  .GetDiagonalInertiaAttr() -> Usd.Attribute` each;
  `.HasAuthoredValue() -> bool` — read path of the P4
  preflight inertia check.
  (`engines/scripts/p4_preflight.py:94-97`.) [V]
- `RevoluteJoint.Define(stage: Usd.Stage, path: str | Sdf.Path)
  -> UsdPhysics.RevoluteJoint`
  (`core/scripts/p3_setup.py:39`) [V];
  `FixedJoint.Define(stage: Usd.Stage, path: str | Sdf.Path)
  -> UsdPhysics.FixedJoint` (p4_convert root joint,
  `engines/scripts/p4_convert.py:42`). [V]
- `Joint.GetBody0Rel() / .GetBody1Rel() -> Usd.Relationship` +
  `.AddTarget(target: str | Sdf.Path [probable for Sdf.Path])
  -> bool [probable]` (P3 spelling, str targets:
  `core/scripts/p3_setup.py:40-41`) **or**
  `.CreateBody0Rel() / .CreateBody1Rel() -> Usd.Relationship`
  + `.SetTargets(targets: list[Sdf.Path]) -> bool [probable]`
  (P4 spelling: `engines/scripts/p4_convert.py:43,51-52`).
  Both verified. [V]
- `.GetLocalPos0Attr() / .GetLocalPos1Attr() -> Usd.Attribute`
  + `.Set(value: Gf.Vec3f)` in m (P3 ±0.5 z:
  `core/scripts/p3_setup.py:42,44`);
  `.GetLocalRot0Attr() / .GetLocalRot1Attr() -> Usd.Attribute`
  + `.Set(value: Gf.Quatf)` dimensionless (identity:
  `core/scripts/p3_setup.py:43,45`); **or**
  `.CreateLocalPos0Attr(defaultValue: Gf.Vec3f) /
  .CreateLocalPos1Attr(defaultValue: Gf.Vec3f) ->
  Usd.Attribute` in m (p4_convert ±0.1 z:
  `engines/scripts/p4_convert.py:53-54`). [V]
- `.GetAxisAttr() -> Usd.Attribute` + `.Set(value: Tf.Token |
  str [probable for str])` (P3: `UsdPhysics.Tokens.z`,
  `core/scripts/p3_setup.py:46`) **or**
  `.CreateAxisAttr(defaultValue: str | Tf.Token [probable for
  Tf.Token]) -> Usd.Attribute` (P4 arms: `"Y"`,
  `engines/scripts/p4_convert.py:50`). [V]
- `.CreateLowerLimitAttr(defaultValue: float) /
  .CreateUpperLimitAttr(defaultValue: float) -> Usd.Attribute`
  — joint limits in DEGREES: −90.0/+90.0 in p4_convert
  (`engines/scripts/p4_convert.py:55-56`). [V]
  (units [P]: same-degree convention as TargetVelocity; no
  in-sim limit-hit drill exists.)
- `DriveAPI.Apply(prim: Usd.Prim, name: str) ->
  UsdPhysics.DriveAPI` — `name="angular"` in-pack
  (`core/scripts/p3_setup.py:48`); `"linear"` never used. [V]
  `.CreateTypeAttr() -> Usd.Attribute` + `.Set(value: str)`
  (`"force"`, `core/scripts/p3_setup.py:49`); [V]
  `.CreateStiffnessAttr(defaultValue: float | None = None
  [probable]) -> Usd.Attribute` + `.Set(value: float)` —
  unit torque/rad (angular) [theoretical]; bare
  (`core/scripts/p3_setup.py:50`) or valued
  (`engines/scripts/p4_convert.py:65`); [V]
  `.CreateDampingAttr(defaultValue: float | None = None
  [probable]) -> Usd.Attribute` + `.Set(value: float)` —
  unit torque·s/rad (angular) [theoretical]
  (`core/scripts/p3_setup.py:51`,
  `engines/scripts/p4_convert.py:66`); [V]
  `.CreateMaxForceAttr() -> Usd.Attribute` + `.Set(value:
  float)` — unit N·m (angular) [theoretical]; 1e6 in P3
  (`core/scripts/p3_setup.py:52`); [V]
  `.CreateTargetVelocityAttr() -> Usd.Attribute` + `.Set(value:
  float)` — DEGREES/s [V] (`core/scripts/p3_setup.py:53`);
  `.CreateTargetPositionAttr(defaultValue: float) ->
  Usd.Attribute` — DEGREES (angular) [theoretical]; used only
  in the offline p4_convert builder (0.0,
  `engines/scripts/p4_convert.py:67`), never stepped in-sim.
  [V]
- `ArticulationRootAPI.Apply(prim: Usd.Prim) ->
  UsdPhysics.ArticulationRootAPI`
  (`engines/scripts/p4_convert.py:32`); [V]
  `prim.HasAPI(schema: type) -> bool` — bool probe in the
  preflight orphan check
  (`engines/scripts/p4_preflight.py:85-87`). [V]
- `prim.IsA(schema: type) -> bool` with `UsdPhysics.Joint` /
  `UsdPhysics.RevoluteJoint`
  (`engines/scripts/p4_preflight.py:85,90`). [V]
- `UsdPhysics.Tokens.z / .rotY: Tf.Token [probable]` — axis
  tokens (`core/scripts/p3_setup.py:46`,
  `engines/scripts/p4_convert.py:60`). [V-use/P-type]
- `UsdPhysics.SetStageKilogramsPerUnit(stage: Usd.Stage,
  kgPerUnit: float) -> None [probable]` — 1.0, p4_convert
  only (`engines/scripts/p4_convert.py:29`). [V]

### Knobs (attr type | unit | default/value)

- `physics:gravityMagnitude: Float [probable] | m/s^2 |
  schema default unknown [theoretical]; in-pack 9.81 / 0.0` —
  9.81 → 0.0: bodies stop falling; P2 zero-g cube holds z
  exactly, dx = vx·t to 5%. [V]
  (`core/scripts/p2_setup.py:19`, `core/evidence/p2_run.json`)
- `physics:gravityDirection: Vec3f [probable] | dimensionless
  unit vector | schema default unknown [theoretical]; in-pack
  (0,0,-1)` (`core/scripts/p1_setup.py:18`). [V]
- `physics:mass: Float [probable] | kg | schema default
  unknown [theoretical]; in-pack 1.0 / 2.0 / 5.0` — 1.0 → 5.0:
  free-fall/rest behavior UNCHANGED (rest 0.5, flight matches
  z(t)=5−4.9t²); mass does not affect drop kinematics. [V]
  (`core/scripts/v1_exam.py:29`, V1 gate)
- `physics:density: Float [probable] | kg/m^3 | schema default
  unknown [theoretical]; in-pack 500.0`
  (`engines/scripts/p4_preflight.py:62`, dirty fixture only).
  [V]
- `physics:diagonalInertia: Vec3f [probable] | kg·m^2 | never
  authored in-pack [theoretical]` — only read by the preflight
  inertia check (`engines/scripts/p4_preflight.py:97`).
  [V-read/T-value]
- RigidBodyAPI present vs absent (API schema, no value):
  present = dynamic (falls, drifts); absent + CollisionAPI =
  static collider (grounds, P3Base). [V]
- CollisionAPI on `Plane` vs `Cube` (API schema, no value):
  both work as ground (core uses Plane 20×20; engines P1 uses
  a 20 m cube sunk to z=−10 so its top is z=0; identical 0.5
  rest). [V]
- `drive:angular:targetVelocity: Float [probable] | DEGREES/s
  [V] | schema default unknown [theoretical]; in-pack 180.0`
  — arm turns exactly π in 1.000 s (q0=(1,0,0,0)→q1=
  (0,0,0,1)). [V] (`core/scripts/p3_setup.py:53`,
  `core/evidence/p3_run.json`)
- `drive:angular:stiffness: Float [probable] | torque/rad
  (angular) [theoretical] | in-pack 0.0 (P3) / 100.0,0.0
  (fixtures)`; `damping: Float [probable] | torque·s/rad
  (angular) [theoretical] | in-pack 1000.0 (P3) / 10.0,0.0
  (fixtures)`; `maxForce: Float [probable] | N·m (angular)
  [theoretical] | in-pack 1e6 (P3)` — P3's working
  velocity-drive tuning (0.0/1000.0/1e6); joint holds z=1.5
  while spinning. [V-values/T-units]
- `drive:type: Token | str [probable] | none | in-pack
  "force"` (`core/scripts/p3_setup.py:49`). [V]
- `limit:lower/upper: Float [probable] | DEGREES [P] |
  in-pack −90.0/+90.0` (`engines/scripts/p4_convert.py:55-56`):
  authored offline only; effect on a stepped joint is UNTESTED.
  [T-effect]
- `drive:angular:targetPosition: Float [probable] | DEGREES
  (angular) [theoretical] | in-pack 0.0` + stiffness=kp /
  damping=kd (100/10, 0/0): authored offline only as
  gain/no-gain fixtures for the MJC audit; in-sim
  position-drive behavior UNTESTED. [T-effect]
- `joint localPos0/1: Vec3f | m | in-pack ±0.5 z (P3), ±0.1 z
  (p4_convert)`; `localRot0/1: Quatf | dimensionless | in-pack
  identity`; `axis: Token | str | none | in-pack z (P3) /
  "Y" (P4 arms)`. [V]
- `stage kilogramsPerUnit: Float [probable] | kg | in-pack
  1.0` (`engines/scripts/p4_convert.py:29`). [V]
- Friction / restitution / contact offset / rest offset /
  solver iterations / stabilization toggles: STILL UNKNOWN —
  NEVER AUTHORED in this pack, so names, types, defaults, and
  effects are all unknown. [T] (P4 setup docstring says
  "Stabilization default (on)" but no attribute is set or
  read — docstring-only. [P])

### EKB rules

- IF a body must fall THEN apply RigidBodyAPI + CollisionAPI +
  MassAPI on the SAME prim BECAUSE every working drill does
  this (same-prim rule) and split-schema layouts are never
  drilled. [V]
- IF a trial repeats THEN reset poses via USD + clock 0.0
  BECAUSE stop() leaves end state (F4) and P5's explicit reset
  gives maxdiff 0.000000. [V]
- IF driving a hinge at w deg/s THEN expect turn = w·t/180·π
  BECAUSE TargetVelocity is degrees/s (P3: 180 → π in 1 s). [V]
- IF authoring joints THEN set body0+body1 targets AND local
  frames AND axis BECAUSE P3 sets all five and the joint holds
  (z pinned 1.5); missing-frame layouts are untested. [P]

### LIMITS (with cites)

- `"linear"` DriveAPI: never used; no in-pack evidence it
  works. (`TOOLS.md` tool 1 UNKNOWN; no script cites it.) [V]
- Stiffness/damping beyond P3's (0.0/1000.0) and p4_convert's
  offline (100/10, 0/0): no stepped evidence. [V]
- Limit/target-position drives: authored offline only
  (`engines/scripts/p4_convert.py:53-67`), never played. [V]

### UNKNOWN

- Friction/restitution/solver knob names, defaults, effects. [T]
- Whether joint limits are degrees (probable) and how hits
  behave (bounce/clamp). [T]
- Linear-drive target units. [T]

---

## Tool 2. pxr.UsdGeom — geometry + xform ops + transform reads

DOES: Defines scene geometry and xform ops; reads
local-to-world transforms and stage units. No physics knobs —
geometry only. [V]

### Functions

- `Plane.Define(stage: Usd.Stage, path: str | Sdf.Path) ->
  UsdGeom.Plane`; `.CreateWidthAttr() / .CreateLengthAttr() ->
  Usd.Attribute` + `.Set(value: float)` in m — core grounds
  20.0×20.0 (`core/scripts/p1_setup.py:21-23`). [V]
- `Cube.Define(stage: Usd.Stage, path: str | Sdf.Path) ->
  UsdGeom.Cube`; `.GetSizeAttr() -> Usd.Attribute` +
  `.Set(value: float)` in m (bodies 1.0:
  `core/scripts/p1_setup.py:26-27`; engines ground 20.0:
  `engines/scripts/p1_build.py:16-17`) **or**
  `.CreateSizeAttr(defaultValue: float) -> Usd.Attribute` in m
  (P4 fixtures 0.1: `engines/scripts/p4_convert.py:40`;
  zero-size trap 0.0: `engines/scripts/p4_preflight.py:49`).
  [V]
- `Xform.Define(stage: Usd.Stage, path: str | Sdf.Path) ->
  UsdGeom.Xform`; `.AddTranslateOp() -> UsdGeom.XformOp` +
  `.Set(value: Gf.Vec3d)` in m (link frames:
  `engines/scripts/p4_convert.py:35-36`) /
  `.AddScaleOp() -> UsdGeom.XformOp` + `.Set(value: Gf.Vec3f)`
  dimensionless (incl. the (−1,1,1) mirror trap:
  `engines/scripts/p4_preflight.py:52-53`). [V]
- `Xformable(prim: Usd.Prim) -> UsdGeom.Xformable`;
  `.AddTranslateOp() -> UsdGeom.XformOp` + `.Set(value:
  Gf.Vec3d)` with x,y,z: float in m — initial pose authoring
  (`core/scripts/p1_setup.py:28`). [V]
- `Xformable(prim: Usd.Prim).GetOrderedXformOps() ->
  list[UsdGeom.XformOp]`; `ops[0].Set(value: Gf.Vec3d)` in m
  (translate op) / `ops[0].Get() -> Gf.Vec3d [probable]` in m
  — pose reset + USD reads (P5 reset:
  `core/scripts/p5_run.py:18-20`; P2/V14 drivers:
  `engines/scripts/p2_drive.py:36-37`). [V]
- `op.GetOpType() -> UsdGeom.XformOp.Type [probable]` compared
  to `XformOp.TypeTranslate: UsdGeom.XformOp.Type [probable]`
  — translate-op filter (P5 `_reset_cube`,
  `core/scripts/p5_run.py:19`, robust to multi-op stacks). [V]
- `XformCache() -> UsdGeom.XformCache`;
  `.GetLocalToWorldTransform(prim: Usd.Prim) -> Gf.Matrix4d
  [probable]`; `.GetDeterminant() -> float [probable]`
  dimensionless — negative determinant = mirrored collider
  (preflight `negscale` trait:
  `engines/scripts/p4_preflight.py:82,101`). [V]
- `SetStageMetersPerUnit(stage: Usd.Stage, metersPerUnit:
  float) -> None [probable]` (`engines/scripts/p4_convert.py:
  28`) / `GetStageMetersPerUnit(stage: Usd.Stage) -> float`
  (`engines/scripts/p4_preflight.py:80`) — units check;
  mismatch adds the `units` hit (seeded in no fixture, gate
  untested). [V]
- `SetStageUpAxis(stage: Usd.Stage, axis: Tf.Token | str
  [probable for str]) -> None [probable]` — p4_convert only,
  `UsdGeom.Tokens.z` (`engines/scripts/p4_convert.py:27`). [V]

### Knobs (attr type | unit | value)

- Geometry (not physics) knobs: `plane width/length: Double
  [probable] | m | in-pack 20.0`; `cube size: Double
  [probable] | m | in-pack 1.0 / 0.1 / 0.0 / 20.0` — size 1.0
  at rest → center z=0.5; size 0.0 → preflight `zerosize` hit
  (offline only, never stepped). [V]
- `translate op: Vec3d | m`; `scale op: Vec3f |
  dimensionless` — negative determinant (mirror scale (−1,1,1)):
  preflight `negscale` hit offline; in-sim effect of stepping a
  mirrored collider is UNTESTED in this pack (translate-first
  rule is cited from the physics-simulation skill, not drilled
  here). [T-effect]
- `stage metersPerUnit: Float [probable] | m | in-pack 1.0`
  (`engines/scripts/p4_convert.py:28`); `stage upAxis: Token |
  str | none | in-pack z` (`engines/scripts/p4_convert.py:27`).
  [V]

### EKB rules

- IF resetting a body pose THEN write the translate xform op
  via USD BECAUSE P5/V14 do exactly this and re-drop cleanly. [V]
- IF checking mirror colliders THEN use XformCache determinant
  < 0 BECAUSE the preflight `negscale` trait fires only on the
  mirrored branch. [V]

### LIMITS

- USD xform reads are AUTHORED state: accurate still/paused,
  stale mid-play; under Newton they NEVER update (R1). [V]

### UNKNOWN

- XformCache mid-play staleness: docstring/discovery only, no
  isolating evidence. [P]

---

## Tool 3. pxr.Usd — stage lifecycle + prim introspection

DOES: Opens/creates/saves stages; looks up, removes,
traverses, and introspects prims. No physics knobs. [V]

### Functions

- `Stage.CreateNew(path: str) -> Usd.Stage` — offline P4/USDA
  builds (`engines/scripts/p4_convert.py:26`). [V]
- `Stage.Open(path: str) -> Usd.Stage` — preflight reads
  (`engines/scripts/p4_preflight.py:78`); ALSO the manager's
  input path (fails on .urdf — R6,
  `engines/scripts/probe_fmt.py:8`). [V]
- `stage.Save() -> None [probable]` — persists offline builds
  (`engines/scripts/p4_convert.py:68`). [V]
- `stage.SetDefaultPrim(prim: Usd.Prim) -> None [probable]`
  (`engines/scripts/p4_convert.py:31`) /
  `stage.GetDefaultPrim() -> Usd.Prim`
  (`engines/scripts/p4_convert.py:100`) — default-prim
  authoring + audit root lookup. [V]
- `stage.GetPrimAtPath(path: str | Sdf.Path) -> Usd.Prim`
  (str: `core/scripts/p1_setup.py:13`; Sdf.Path from
  `rel.GetTargets()`: `engines/scripts/p4_convert.py:116`) /
  `stage.RemovePrim(path: str | Sdf.Path [probable for
  Sdf.Path]) -> bool [probable]` (str:
  `core/scripts/p1_setup.py:15`) / `stage.Traverse() ->
  Usd.PrimRange [probable]` (iterable of Usd.Prim:
  `engines/scripts/p4_convert.py:105`) — live-stage CRUD +
  full scans. [V]
- `prim.GetAppliedSchemas() -> list[str]` — schema-name
  membership tests ("PhysicsMassAPI", "PhysicsCollisionAPI",
  "PhysxMimicJointAPI": `engines/scripts/p4_convert.py:87-88`,
  `engines/scripts/p4_preflight.py:84`). [V]
- `prim.IsA(schema: type) -> bool`
  (`engines/scripts/p4_preflight.py:85`) /
  `prim.GetTypeName() -> str`
  (`engines/scripts/p4_convert.py:106`) /
  `prim.GetAttribute(name: str) -> Usd.Attribute` (possibly
  invalid if missing: `engines/scripts/p4_convert.py:110`) /
  `prim.GetPath() -> Sdf.Path` + `.GetPrefixes() ->
  list[Sdf.Path]` (`engines/scripts/p4_preflight.py:87`) +
  `.name: str` (`engines/scripts/p4_convert.py:109`) /
  `prim.GetRelationship(name: str) -> Usd.Relationship`
  (`engines/scripts/p4_convert.py:114`) — audit
  introspection. [V]
- `prim.CreateAttribute(name: str, type: Sdf.ValueType) ->
  Usd.Attribute` + `.Set(value: float)` — seeds the `ref`
  trap (`"mjc:ref"`, `Sdf.ValueTypeNames.Float`, 1.0:
  `engines/scripts/p4_preflight.py:65`). [V]
- `stage.SetEditTarget(target: Usd.EditTarget | Sdf.Layer
  [probable]) -> None [probable]` with
  `stage.GetSessionLayer() -> Sdf.Layer [probable]` —
  variant-selection sandbox for the MJC audit
  (`engines/scripts/p4_convert.py:99`). [V]
- `root.GetVariantSets() -> Usd.VariantSets [probable]`;
  `.GetVariantSet(name: str) -> Usd.VariantSet [probable]`
  (`"Physics"`); `.GetVariantNames() -> list[str]` /
  `.SetVariantSelection(name: str) -> bool [probable]`
  (`"mujoco"`) — variant-package audit
  (`engines/scripts/p4_convert.py:101-103`). [V]

### Knobs + effect of change

- None (lifecycle/introspection only). [V]

### EKB rules

- IF scanning for physics traits THEN Traverse + schema-name
  membership BECAUSE preflight finds all 5 dirty traits this
  way with zero false hits on clean. [V]
- IF auditing a variant package THEN set session-layer edit
  target before selecting variants BECAUSE p4_convert does
  this (avoids dirtying the payload). [P]

### LIMITS

- `Stage.Open(.urdf)` raises "Cannot determine file format" —
  no URDF Sdf plugin in 6.0.0 (R6). [V]

### UNKNOWN

- None in the read set. [V]

---

## Tool 4. pxr.Sdf — paths + value types

DOES: Path and value-type primitives for joint targets and
seeded attributes. No physics knobs. [V]

### Functions

- `Sdf.Path(path: str) -> Sdf.Path` — joint body targets
  (`"/arm/base"`: `engines/scripts/p4_convert.py:43`). [V]
- `Sdf.ValueTypeNames.Float: Sdf.ValueType [probable]` — type
  of seeded `mjc:ref`
  (`engines/scripts/p4_preflight.py:65`). [V]
- `Sdf.FileFormat.FindAllFileFormatExtensions() -> list[str]`
  — registered format probe
  (`engines/scripts/probe_fmt.py:5`; urdf/mjcf absent — R6).
  [V]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs. IF probing converter support THEN list Sdf formats
  first BECAUSE R6 shows the manager fails before any rule
  when no plugin is registered. [V] No further unknowns. [V]

---

## Tool 5. pxr.Gf — math value types

DOES: Vector/quaternion values for translations, rotations,
scales. No physics knobs. [V]

### Functions

- `Gf.Vec3d(x: float, y: float, z: float) -> Gf.Vec3d` —
  double translations in m
  (`core/scripts/p1_setup.py:28`). [V]
- `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` —
  gravity dir (dimensionless: `core/scripts/p1_setup.py:18`),
  joint local-pos (m: `core/scripts/p3_setup.py:42`), mirror
  scale (dimensionless: `engines/scripts/p4_preflight.py:53`).
  [V]
- `Gf.Quatf(w: float, x: float = 0.0 [probable], y: float =
  0.0 [probable], z: float = 0.0 [probable]) -> Gf.Quatf` —
  dimensionless; identity `Quatf(1.0)` for joint frames
  (`core/scripts/p3_setup.py:43`). [V]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs, no limits, no unknowns. [V]

---

## Tool 6. pxr.PhysxSchema — PhysX extras (OBSERVED in p4_convert)

DOES: PhysX-only articulation/joint/mimic APIs on the offline
legacy-arm builder. (TOOLS.md said import-only; the full read
of `engines/scripts/p4_convert.py` corrects that.) [V]

### Functions

- `PhysxArticulationAPI.Apply(prim: Usd.Prim) ->
  PhysxSchema.PhysxArticulationAPI` — PhysX articulation
  marker on `/arm` alongside ArticulationRootAPI. [V]
  (`engines/scripts/p4_convert.py:33`)
- `PhysxJointAPI.Apply(prim: Usd.Prim) ->
  PhysxSchema.PhysxJointAPI` — PhysX joint extras on each
  revolute joint. [V] (`engines/scripts/p4_convert.py:57`)
- `PhysxMimicJointAPI.Apply(prim: Usd.Prim, axis: Tf.Token |
  str [probable for str]) -> PhysxSchema.PhysxMimicJointAPI`
  — mimic joint about rotY
  (`engines/scripts/p4_convert.py:59-60`). [V]
- `.CreateReferenceJointRel() -> Usd.Relationship` +
  `.SetTargets(targets: list[Sdf.Path]) -> bool [probable]`
  — mimic source joint (`[Sdf.Path("/arm/j1")]`:
  `engines/scripts/p4_convert.py:61`). [V]
- `.CreateGearingAttr(defaultValue: float) -> Usd.Attribute`
  — dimensionless ratio; 1.0 = 1:1 mimic
  (`engines/scripts/p4_convert.py:62`). [V]

### Knobs + effect of change

- `mimic gearing: Float [probable] | dimensionless ratio |
  in-pack 1.0` (`engines/scripts/p4_convert.py:62`): authored
  offline only; in-sim mimic behavior UNTESTED (no stepped
  mimic drill). [T-effect]
- PhysxArticulationAPI / PhysxJointAPI: presence markers only
  in-pack (API schemas, no values); solver/stabilization knobs
  these schemas MAY carry (e.g. solver iteration counts):
  STILL UNKNOWN — never touched, so names, types, defaults,
  effects all unknown. [T]

### EKB rules

- IF auditing MJC gains THEN skip actuators whose targets are
  ALL mimic joints BECAUSE p4_convert's audit exempts them
  (mimics inherit gains from the reference joint). [V]
- IF detecting mimics THEN match applied-schema names
  `NewtonMimicAPI` or prefix `PhysxMimicJointAPI` BECAUSE the
  audit helper does exactly this. [V]

### LIMITS

- All PhysX-schema authoring is offline-only; zero in-sim
  stepped evidence for any Tool 6 knob. [V]

### UNKNOWN

- Full PhysxSchema knob surface (solver settings, contact
  params, stabilization flags): names, defaults, effects. [T]
- Whether mimic joints step correctly under PhysX/Newton. [T]

---

## Tool 7. omni.usd — live-stage access

DOES: Returns the running Kit session's stage handle. [V]

### Functions

- `omni.usd.get_context() -> UsdContext [probable]`;
  `.get_stage() -> Usd.Stage` — feeds
  GetPrimAtPath/RemovePrim/Traverse
  (`core/scripts/p1_setup.py:9`). [V]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs. IF authoring live THEN fetch the stage this way
  BECAUSE every in-sim script does (no alternative is
  drilled). [V] No unknowns. [V]

---

## Tool 8. omni.timeline — sim clock

DOES: Clock reads/resets/pauses; proves stepping advanced
time. No physics knobs (clock only). [V]

### Functions

- `omni.timeline.get_timeline_interface() -> ITimeline
  [probable]` (`core/scripts/p1_run.py:11`). [V]
- `.get_current_time() -> float` — seconds; advance confirm
  (every run script gates t1 > t0:
  `core/scripts/p1_run.py:21`). [V]
- `.set_current_time(time: float) -> None [probable]` —
  seconds; trial reset (P5: `core/scripts/p5_run.py:27`;
  drivers: `engines/scripts/p2_drive.py:38`). [V]
- `.pause() -> None [probable]` — freeze WITH sim state
  preserved (all run scripts end pause, never stop:
  `core/scripts/p1_run.py:36`). [V]

### Knobs + effect of change

- Clock value: `Double [probable] | s | reset to 0.0 before
  a trial` — + USD pose reset reproduces trajectories to
  maxdiff 0.000000 (P5: `core/scripts/p5_run.py:27`). [V]

### EKB rules

- IF a run ends THEN pause() not stop() BECAUSE pause keeps
  sim state for snapshots while stop drops it (F4). [V]
- IF gating motion THEN require t1 > t0 BECAUSE every
  verifier does — time advance is the anti-no-op proof. [V]

### LIMITS / UNKNOWN

- No limits; no unknowns. [V]

---

## Tool 9. app_utils — play/stop/pump + ext mgmt

DOES: Play/stop/step pump, extension enablement, extension
path lookup. No prim knobs (transport + lifecycle). [V]

### Functions

- `app_utils.play() -> None [probable]` — starts the
  real-time clock + sim (`core/scripts/p1_run.py:19`). [V]
- `app_utils.stop() -> None [probable]` — halts; does NOT
  restore pre-play state (F4: `core/scripts/p5_run.py:37`). [V]
- `await app_utils.update_app_async(steps: int) -> None` —
  blocking pump of N steps/frames, no default evidenced
  (60/120/150/180 and 5/10/20/30 windows in-pack:
  `core/scripts/p1_run.py:33`). [V]
- `app_utils.enable_extension(name: str) -> None [probable]`
  — "isaacsim.asset.importer.urdf"
  (`engines/scripts/probe_fmt.py:2`), "isaacsim.physics.newton"
  (`engines/scripts/p2_run.py:23` + 30 pump steps). [V]
- `app_utils.get_extension_path(ext_id: str) -> str` — locates
  shipped RuleProfile JSON ("isaacsim.asset.transformer.rules":
  `engines/scripts/p4_convert.py:72-73`). [V]

### Knobs + effect of change

- Pump `steps: int | frames/steps | no default (always passed),
  N in {5,10,20,30,60,120,150,180}`: integrates N + 0–2 slipped
  real-time frames (F5); P5's first sample matches 22 steps not
  20. [V]
- Newton enable (`name: str` ext id) + 30 pump steps: compiles
  ~33 Warp/MuJoCo kernels on cuda:0 (~1 min first time), then
  Newton is switchable. [V] (`engines/evidence/p2_run.json`,
  `engines/scripts/p2_run.py:23-24`)

### EKB rules

- IF stepping exactly N frames THEN pause-first-then-step or
  normalize by get_current_time() dt BECAUSE play()+pump slips
  0–2 frames (F5). [V]
- IF repeating trials THEN own the reset (USD pose + clock)
  BECAUSE stop() does not restore (F4). [V]
- IF enabling Newton THEN pump 30 steps after enable BECAUSE
  p2_run does and the kernels need the compile window. [V]

### LIMITS

- Slip frames: assert windows/deltas, not exact counts. [V]
- stop() non-restore: proven (P5 trial 2 started at z=0.5). [V]

### UNKNOWN

- None material in the read set (Newton-enable body now read
  in p2_run — resolves TOOLS.md unknown #15). [V]

---

## Tool 10. RigidPrim — simulated-state truth

DOES: Reads SIMULATED body state, commands velocities; the
only trustworthy readback during play under PhysX. [V]

### Functions

- `RigidPrim(paths: str | list[str] [probable for list]) ->
  RigidPrim` — handle constructor; only `paths` is passed
  in-pack (single-path strings in all drills, e.g.
  `core/scripts/p1_run.py:18`; multi-path untested). [V]
- `get_world_poses() -> tuple[Tensor, Tensor]` — batched
  tensors: positions (N,3) float [probable] in m, quaternions
  (N,4) float [probable] dimensionless; `.numpy()[0]` = first
  body; `[2]` = z (`core/scripts/p1_run.py:20`). Quats as
  (x,y,z,w)? — P3 reads q0=(1,0,0,0)→q1=(0,0,0,1) for a π yaw,
  consistent with (w,x,y,z) OR (x,y,z,w) with rotation about
  z... treated as opaque 4-vectors by verifiers (yaw extracted
  by math, order unstated). Order convention [P] (verify
  against installed rigid_prim.py before relying). [P]
- `set_velocities(linear_velocities: np.ndarray shape (N,3),
  angular_velocities: np.ndarray [probable] = None [probable])
  -> None [probable]` — linear in m/s, angular in rad/s
  [probable]; called strictly AFTER play() with
  `np.array([[5.0,0.0,0.0]])` float64 [probable]
  (`core/scripts/p2_run.py:16`). Angular slot never passed
  in-pack. [V-shape/P-angular]
- `get_velocities() -> tuple[Tensor, Tensor]` — (linear (N,3)
  in m/s, angular (N,3) in rad/s [probable]); batched tensors;
  `core/scripts/p4_run.py:16-17` + engines
  `engines/scripts/p1_run.py:22` index `[0].numpy()[0]` for
  linear speed. [V] (TOOLS.md called this doc-attested;
  p4_run/p1_run bodies now fully read — calling bodies
  CONFIRMED.) [V]

### Knobs + effect of change

- Post-play `linear_velocities: np.ndarray (N,3) float64
  [probable] | m/s | in-pack [[5.0,0.0,0.0]]`: dx=5.0000 over
  dt=1.0, zero z drift. [V] (`core/scripts/p2_run.py:16`,
  `core/evidence/p2_run.json`)
- `angular_velocities: np.ndarray (N,3) [probable] | rad/s
  [probable] | never passed in-pack [theoretical]` — set path
  untested. [T]
- Pre-play set of the same `linear_velocities` knob: IGNORED
  by PhysX (F2). [V]

### EKB rules

- IF reading bodies mid-play THEN use RigidPrim tensors, never
  USD/XformCache BECAUSE USD is authored-state (stale mid-play,
  frozen under Newton). [V]
- IF setting velocity THEN play() first, set, then pump
  BECAUSE pre-play sets are ignored (F2/P2). [V]
- IF checking rest THEN gate linear speed < 0.1 (pack) /
  observed < 0.003 (P4: 0.0018/0.0027) BECAUSE contact
  micro-motion never reads exactly 0. [V]

### LIMITS

- `set_linear_velocities` / `get_linear_velocities` do NOT
  exist (AttributeError) — combined only (F3). [V]
- Under Newton, tensor readback raises/is frozen (no Newton
  backend; log "Failed to find simulation backend 'newton'"):
  drop read z1=2.0000 while renders proved the fall (R1;
  `engines/evidence/p2_run.json` z1=2.0000). [V]

### UNKNOWN

- Angular-velocity set path (never passed); multi-path batch
  semantics; joint-angle readback spelling (no joint readback
  anywhere in-pack). [T]
- `Articulation` tensor reads: SKILL.md prescribes them, zero
  scripts import Articulation. [T]

---

## Tool 11. SimulationManager — engine switching

DOES: Reports, selects, switches the active physics engine at
runtime. No prim knobs (engine routing). [V]

### Functions

- `SimulationManager.get_available_physics_engines() ->
  list[tuple[str, bool]] [probable]` — e.g. `[('newton',
  True), ('physx', False)]`
  (`engines/scripts/p2_run.py:25`). [V]
- `SimulationManager.get_default_engine() -> str` — "physx" on
  6.0.0 (`engines/scripts/p3_probe.py:11`). [V]
- `SimulationManager.get_active_physics_engine() -> str` —
  confirm after every switch
  (`engines/scripts/p3_probe.py:14`). [V]
- `SimulationManager.switch_physics_engine(engine_name:
  Literal['physx','newton','remotesim'], verbose: bool = False)
  -> bool` — exact signature via inspect (P2-SIG:
  `engines/scripts/p2_run.py:26-27`). Both directions drilled
  + 10 pump steps after. [V]
- `SimulationManager.get_backend() -> str` — returns 'torch'
  under BOTH engines (tensor backend, NOT engine id:
  `engines/scripts/p3_probe.py:15`). [V]

### Knobs + effect of change

- Engine `engine_name: Literal['physx','newton','remotesim'] |
  none (enum str) | default "physx"`: newton vs physx give
  identical rigid drops (P2 motion 2.0117 vs 2.0131, Δ0.0014;
  end frames 0.1068) and identical stacks (V14 rest 1.5 both
  engines). [V]
- Switch-back physx→newton→physx (`verbose: bool = False`):
  rebuilds fine, re-drop 0.5000 exact (discovery-attested;
  probe_back.py body read, no evidence file — treat numbers as
  [P]). [P]

### EKB rules

- IF switching engines THEN switch + pump 10 + confirm active
  BECAUSE every driver does this and gates on ACTIVE-*. [V]
- IF identifying the engine THEN use get_active_physics_
  engine(), never get_backend() BECAUSE backend is 'torch'
  under both (p3 evidence b1=b2=torch). [V]

### LIMITS

- No Newton auto-switch in 6.0.0; default/active is physx. [V]
- `'remotesim'` switch target: in signature, never drilled. [V]

### UNKNOWN

- remotesim behavior. [T]

---

## Tool 12. SimulationContext — anti-pattern (documented wrong path)

DOES: Standalone stepping API that crashes inside Kit; kept
only as the documented wrong path. [V]

### Functions

- `SimulationContext.instance() -> SimulationContext | None`
  (`core/scripts/p1_run.py:25`);
  `SimulationContext() -> SimulationContext`
  (`core/scripts/p1_run.py:27`);
  `.step(render: bool = True [probable]) -> None [probable]`
  (called `sim.step(render=True)`:
  `core/scripts/p1_run.py:29`) — raises `AttributeError:
  'NoneType' object has no attribute 'get_physics_dt'` inside
  Kit (F1; p1_run catches and falls back). [V]

### EKB rules

- IF inside Kit THEN never step via SimulationContext BECAUSE
  it crashes (F1); use play()+update_app_async+timeline. [V]

### Knobs / LIMITS / UNKNOWN

- No knobs. Failure + recovery both evidenced (2.000 s over
  120 steps, settle 0.5 exact). No unknowns. [V]

---

## Tool 13. isaacsim.physics.newton — Newton backend extension

DOES: Newton/MuJoCo/Warp backend simulating plain UsdPhysics
bodies with zero extra schema. [V]

### Functions

- Enable: `app_utils.enable_extension(name: str) -> None
  [probable]` with `"isaacsim.physics.newton"`
  (`engines/scripts/p2_run.py:23`) + 30 pump steps (~1 min
  first compile). [V]
- `import isaacsim.physics.newton as N: module` +
  `dir(obj: object) -> list[str]` module listing
  (`engines/scripts/probe_napi.py:2` — output content has NO
  evidence file; surface still unlisted). [P]
- Scene prim gains `newton:*` attrs once ext loads (name:
  str each): gravityEnabled, maxSolverIterations,
  timeStepsPerSecond (`engines/scripts/probe_napi.py:6-7`);
  log "Newton timestep from USD: 1000Hz". [V] (discovery.md)

### Knobs + effect of change

- `newton:timeStepsPerSecond: Int [theoretical] | Hz | 1000
  (log note)`: Newton substep rate [P]; changing it is
  UNTESTED. [T-effect]
- `newton:maxSolverIterations: Int [theoretical] | count |
  default unknown [theoretical]`: solver budget [P]; changing
  it is UNTESTED. [T-effect]
- `newton:gravityEnabled: Bool [theoretical] | flag |
  default unknown [theoretical]`: gravity toggle [P]; changing
  it is UNTESTED. [T-effect]
- NO other Newton knob is named anywhere in-pack. [V]

### EKB rules

- IF observing Newton motion THEN screenshot-diff renders
  BECAUSE tensors raise and USD never updates (R1); render is
  ground truth. [V]
- IF first-enabling Newton THEN budget ~1 min for ~33 kernel
  compiles (slowest 12.2 s, mujoco kernels) BECAUSE p2_run
  evidence shows exactly this. [V]
- IF a warp-version skew warning appears (3.12 vs ~=3.8) THEN
  ignore for rigid drops BECAUSE discovery marks it benign. [P]

### LIMITS

- NO tensor readback + NO USD writeback (Fabric-only render):
  Newton USDZ pinned 2.0000/3.0000 while motion diffs matched
  PhysX (R1; p2/v14 reports). [V]
- No auto-switch; default physx. [V]

### UNKNOWN

- Module API surface (probe_napi output never captured to
  evidence). [T]
- Native state via NewtonStage/mujoco qpos (explicit R1
  future work). [T]
- `newton:*` attr semantics beyond names; safe ranges. [T]

---

## Tool 14. isaacsim.asset.transformer — rule-based conversion

DOES: Runs JSON-profile conversion passes over USD assets.
Fully-read bodies now (p4_convert + probe_urdf) — corrects
TOOLS.md skim-attested status. [V]

### Functions

- `RuleProfile.from_json(json_text: str) -> RuleProfile` —
  loads shipped profile JSON from rules data dir
  (`engines/scripts/p4_convert.py:74-76`). [V]
- `profile.interface_asset_name: str = "p4arm.usda"` — names
  the variant-package interface file
  (`engines/scripts/p4_convert.py:77-78`). [V]
- `AssetTransformerManager() -> AssetTransformerManager`;
  `.run(input_stage: str, profile: RuleProfile, package_root:
  str) -> RunReport [probable]` — full signature as called
  with kwargs (`engines/scripts/p4_convert.py:80-81`,
  `engines/scripts/probe_urdf.py:47-48`). [V]
- `report.results: list[RuleResult] [probable]`;
  `r.success: bool`; `r.rule.name: str`; `r.error: str` —
  per-rule audit (`engines/scripts/p4_convert.py:82`,
  `engines/scripts/probe_urdf.py:53-58`). [V]
- Pass-1/pass-2 chaining: pass 2 input (`input_stage: str`) =
  `EVD/pass1/payloads/mujoco.usda` (path CONVENTION from the
  documented sequence; untested live because pass 1 needs the
  missing physx_to_mjc profile). [P]

### Knobs + effect of change

- Profile choice (`profile_name: str` filename in
  {isaacsim_structure, merge_mesh, mjc_to_physx,
  urdf_to_mjc_physx} + ".json"): selects the conversion
  direction; only urdf_to_mjc_physx is runnable in principle,
  and it is BLOCKED by R6. [V]
- `package_root: str | dir path | e.g. EVD + "/package"`;
  `interface_asset_name: str | filename | "p4arm.usda"`; no
  per-rule parameter knob is set anywhere in-pack. [V]

### EKB rules

- IF converting on 6.0.0 THEN run in-session through the
  manager BECAUSE standalone boots hang (R3) and the convert
  script is unimportable live (R4). [V]
- IF a rule fails THEN print r.rule.name + r.error BECAUSE
  probe_urdf's FAIL-RULE loop is the pack's only rule-level
  diagnostic. [V]

### LIMITS

- Manager opens inputs via Usd.Stage.Open; 6.0.0 has no
  URDF/MJCF Sdf plugin → URDF-profile runs fail before any
  rule (R6). [V]

### UNKNOWN

- Gain-audit thresholds beyond any(gains)-nonzero; full
  two-pass success path (blocked). [T]

---

## Tool 15. transformer.rules profile data — shipped profiles

DOES: JSON RuleProfiles consumed via RuleProfile.from_json. [V]

### Functions (data, not code)

- Profiles (`profile_name: str`): `isaacsim_structure`,
  `merge_mesh`, `mjc_to_physx`, `urdf_to_mjc_physx` (+ `.json`
  filenames: `isaacsim_structure.json`,
  `urdf_to_mjc_physx_conversion.json`,
  `physx_to_mjc_conversion.json` per call sites:
  `engines/scripts/p4_convert.py:92-96`,
  `engines/scripts/probe_urdf.py:41-44`). [V]
- Located via `app_utils.get_extension_path(ext_id: str) ->
  str` + `"/data/" + profile_name: str`
  (`engines/scripts/p4_convert.py:72-74`). [V]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs set in-pack. IF converting PhysX→MJC THEN get a
  newer build BECAUSE physx_to_mjc_conversion.json does NOT
  ship in 6.0.0 (R5). [V]
- Profile JSON schema details: no profile file ships in the
  pack. [T]

---

## Tool 16. isaacsim.asset.importer.urdf — URDF importer ext

DOES: URDF importer extension, probed for enablement only. [V]

### Functions

- `app_utils.enable_extension(name: str) -> None [probable]`
  with `"isaacsim.asset.importer.urdf"` + 30 pump steps
  (`engines/scripts/probe_fmt.py:2-3`; same signature as Tool
  9). [V]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs. Enabling still leaves zero urdf/mjcf Sdf formats
  (R6). Importer correctness outside the manager path: never
  drilled. [T]

---

## Tool 17. isaac-sim-remote bridge (isaacsim_send.py + viewport_screenshot.py)

DOES: LOCAL drivers' channel into the live sim: executes
inline/file scripts, captures screenshots; results return as
JSON. [V]

### Functions

- `SEND: list[str] = [sys.executable: str, LIB +
  "isaacsim_send.py": str, "--raw", "--timeout", "200"]` —
  `--timeout SECONDS: int-as-str` ("200"); screenshot sends
  add `"--file", path: str` + `"--arg", "output_path=" +
  abs_path: str`
  (`engines/scripts/p2_drive.py:17-18,52-53`). [V]
- `subprocess.run(args: list[str], capture_output: bool =
  True, text: bool = True, timeout: float = 240) ->
  CompletedProcess [probable]` — timeout in seconds
  (`engines/scripts/p2_drive.py:24-25`);
  `json.loads(s: str) -> dict` then `["output"]: str`
  (`engines/scripts/p2_drive.py:26-27`). [V]
- Inline snippets (`code: str`): RESET (stop, pump 5, USD pose
  reset, clock reset, engine switch, pump 10, ACTIVE-*) —
  `engines/scripts/p2_drive.py:30-41`; PLAY (play + N steps,
  PLAYED-N) — `p2_drive.py:42-44`; USDZ (USD z read) —
  `p2_drive.py:45-48`. [V]
- 3x send-retry (`attempt: int in (1,2,3)`): v14_drive HAS it
  (attempt loop, status=="ok" + non-empty output, else
  RuntimeError: `engines/scripts/v14_drive.py:23-34`); p2_drive
  LACKS it (single-shot `_send(args: list[str]) -> str`:
  `engines/scripts/p2_drive.py:23-27`). [V] (Resolves TOOLS.md
  unknown #9: v14 conforms, p2 does not.) [V]

### Knobs + effect of change

- `--timeout: int-as-str "200" | s` / subprocess
  `timeout: float = 240 | s`: wall budgets; screenshot sends
  under GPU load can fail silently without retry (discovery).
  [V]

### EKB rules

- IF driving the live sim locally THEN wrap sends in 3x retry
  on empty/error output BECAUSE GPU-loaded screenshot sends
  fail silently and v14's retry is the conformant pattern. [V]
- IF screenshotting THEN pass absolute output_path BECAUSE
  both drivers do (C:/Users/... prefix). [V]

### LIMITS / UNKNOWN

- Bridge-stall-equivalent observed once (orphaned pipe on hung
  standalone run, terminated cleanly). [V] No further unknowns. [V]

---

## Tool 18. png_stats — screenshot differencing

DOES: Turns render pairs into motion numbers — the Newton
ground-truth instrument. Lives OUTSIDE the pack
(isaac-sim-remote skill), never read. [V]

### Functions

- `mean_abs_diff(path_a: str, path_b: str) -> float` —
  dimensionless mean abs pixel intensity, scale 0–255
  [probable] (module never read; the gates below are the only
  scale evidence) — N_DIFF/P_DIFF/END_DIFF
  (`engines/scripts/p2_drive.py:66-68`). Gates: motion ∈
  (1.0, 4.0) [P2] / (0.8, 5.0) [V14]; cross-engine match <
  1.0; end-frame match < 0.5. [V]
- `png_stats`: STILL-UNKNOWN — no signature determinable:
  imported-unused in p2_drive
  (`engines/scripts/p2_drive.py:13`; never called); NOT
  imported in v14_drive
  (`engines/scripts/v14_drive.py:13`); module lives outside
  the pack, never read. [T]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs. IF comparing engines THEN gate motion-match +
  end-frame-match BECAUSE P2/V14 do (numbers above). [V]
- `png_stats`: purpose/signature STILL UNKNOWN (no call site;
  see Functions). [T]

---

## Tool 19. stdlib + numpy (+ inspect) — plumbing

DOES: JSON/subprocess/sys plumbing, file staging, numerics. [V]

### Functions

- `json.loads(s: str) -> dict [probable]` + `["output"]: str`
  / `["status"]: str` (`engines/scripts/p2_drive.py:26-27`,
  `engines/scripts/v14_drive.py:28-31`); `json.load(fp:
  TextIO) -> dict [probable]` (`core/scripts/verify_p1.py:13`,
  `engines/scripts/verify_p1.py:4`) — bridge result parse. [V]
- `subprocess.run(args: list[str], capture_output: bool,
  text: bool, timeout: float) -> CompletedProcess [probable]`
  — send transport, full types in Tool 17. [V]
- `sys.executable: str` / `sys.path.insert(index: int, path:
  str) -> None` (`0`, remote-scripts dir:
  `engines/scripts/p2_drive.py:11-12`) — LOCAL driver
  bootstrap. [V]
- `os.makedirs(path: str, exist_ok: bool = True) -> None`
  (`engines/scripts/p4_convert.py:21`) /
  `os.path.join(a: str, *parts: str) -> str`
  (`engines/scripts/p4_convert.py:74`) /
  `os.path.relpath(path: str, start: str) -> str`
  (`engines/scripts/probe_urdf.py:51`) / `os.walk(top: str)
  -> Iterator[tuple[str, list[str], list[str]]]`
  (`engines/scripts/probe_urdf.py:50`) /
  `shutil.rmtree(path: str, ignore_errors: bool = True) ->
  None` (`engines/scripts/p4_convert.py:20`) — evidence
  staging. [V]
- `numpy`: `np.array(obj: list[list[float]]) -> np.ndarray`
  float64 [probable] (`core/scripts/p2_run.py:16`); tensor
  `.numpy() -> np.ndarray` + `[0]` first body + `[2]` z
  (`core/scripts/p1_run.py:20`); speed norms
  `float((v**2).sum()**0.5) -> float` in m/s
  (`core/scripts/p4_run.py:23`). [V]
- `re.search(pattern: str, string: str) -> Match | None`
  (`core/scripts/verify_p1.py:24`) /
  `re.findall(pattern: str, string: str) -> list[str]`
  (`core/scripts/verify_p5.py:24`) + `math.atan2(y: float, x:
  float) -> float` in radians + `math.pi: float`
  (`core/scripts/verify_p3.py:22,39`) — yaw extraction in
  verifiers. [V]
- `inspect.signature(obj: Callable) -> Signature`
  (`S.switch_physics_engine`: `engines/scripts/p2_run.py:26`)
  — live signature capture (P2-SIG). [V]
- Multi-encoding `_load(path: str) -> dict`
  (tries utf-8-sig/utf-16/utf-8) in core verifiers
  (`core/scripts/verify_p1.py:9-16`) — bridge JSON encoding
  robustness. [V]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs, no limits, no material unknowns. [V]

---

## Tool 20. verify_*.py — pack's own offline gates

DOES: Local pass/fail gates over evidence JSON/TXT (11
scripts). Bodies now READ (via skim pass — exact thresholds
below). [V]

### Functions (gate logic per script — exact; helpers typed)

- core `verify_p1.py`: status ok; z0=2.0±0.05 m; z1=0.5±0.1 m;
  t1>t0 s; + paused-sense probe note (authored USD, advisory).
  Helpers: `_load(path: str) -> dict` (:9), `main() -> int`
  exit code (:19). [V]
- core `verify_p2.py`: dt>0 s; |dx − vx·dt| ≤ 5% m; |z1−z0| ≤
  0.05 m (gravity-off proof). Helpers: `_load(path: str) ->
  dict` (:9), `main() -> int` (:19). [V]
- core `verify_p3.py`: yaw(q1)−yaw(q0) mod 2π = π±0.35 rad;
  z1=1.5±0.2 m (joint held); t1>t0 s. Helpers: `_load(path:
  str) -> dict` (:9), `_yaw(q: Sequence[float]) -> float`
  radians (:20), `main() -> int` (:25). [V]
- core `verify_p4.py`: za1=0.5±0.05 m; zb1=1.5±0.1 m; va1,vb1 ≤
  0.1 m/s (observed 0.0018/0.0027); t1>t0 s. Helpers:
  `_load(path: str) -> dict` (:9), `main() -> int` (:19). [V]
- core `verify_p5.py`: 2 trajs; trial 0 falls; maxdiff ≤ 1e-4
  m (observed 0.000000). Helpers: `_load(path: str) -> dict`
  (:9), `main() -> int` (:19). [V]
- core `verify_v1.py`: 6 samples; z[1] ∈ (2.0, 3.5) m in
  flight (~2.82); z[2:] = 0.5±0.1 m. Helpers: `_load(path:
  str) -> dict` (:9), `main() -> int` (:19). [V]
- engines `verify_p1.py`: build valid; z0=2±0.05 m; z1=0.5±
  0.05 m; dt=2.0±0.2 s; vz=0±0.05 m/s; engine physx. Helper:
  `f(pat: str, s: str, i: int = 1) -> float` (:7, NaN on
  no-match). [V]
- engines `verify_p2.py`: ACTIVE-newton + ACTIVE-physx;
  N/P_DIFF ∈ (1.0, 4.0); |N−P| < 1.0; END < 0.5; Newton USDZ
  pinned 2.0 exact m; PhysX USDZ rest 0.5 exact m. Helper:
  `f(pat: str, i: int = 1) -> float` (:6). [V]
- engines `verify_p3.py`: both available; a1=newton;
  a2=physx; b1/b2 reported. No helpers (top-level checks). [V]
- engines `verify_p4.py`: clean=[] AND dirty fires all 5
  traits in sorted order. No helpers (top-level checks). [V]
- engines `verify_v14.py`: prim valid; both ACTIVE; N/P_DIFF
  ∈ (0.8, 5.0); |N−P| < 1.0; END < 0.5; Newton USDZ pinned
  3.0 exact m; PhysX stacked 1.5±0.05 m. Helper: `f(pat: str,
  i: int = 1) -> float` (:7). [V]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs. IF gating rest height THEN predict from the FULL
  layout BECAUSE V14 stacks to 1.5 not 0.5 (R2). [V]
- No unknowns (bodies read; corrects TOOLS.md unknown #11). [V]

---

## Tool 21. Standalone Kit runner (python.bat + SimulationApp)

DOES: Boots a second Kit/USD session outside the live sim
(attempted self-test and convert paths). [V]

### Functions

- `python.bat` launch (process-level; no Python signature —
  OS process, argv unlisted in-pack). [V]
- `SimulationApp(launch_config: dict[str, Any] [theoretical] =
  {} [theoretical]) -> SimulationApp [theoretical]` — NO
  in-pack call site (top-level construction in the convert
  script → unimportable live, R4); shape is theoretical, do
  not rely on it. [T]

### Knobs / EKB / LIMITS / UNKNOWN

- No knobs. IF on a 4 GB GPU beside the live sim THEN run
  conversion in-session BECAUSE a second Kit boot stalls ~21 s
  at newton ext start, vanishes, pipe never closes (R3). [V]
- Standalone/headless SUCCESS path: only the failure is
  drilled. [T]

---

## Sources

Root docs (3): SKILL.md, failures.md, discovery.md.

Fully read (20 of 36): core p1_setup, p1_run, p2_setup,
p2_run, p3_setup, p3_run, p4_setup, p4_run, p5_setup, p5_run,
v1_exam; engines p1_build, p1_run, p2_run, p2_drive, p3_probe,
v14_build, v14_drive, p4_convert, p4_preflight.

Skimmed (16): core verify_p1–p5, verify_v1; engines
verify_p1–p4, verify_v14, probe_back, probe_fmt, probe_napi,
probe_nmotion, probe_urdf (import blocks + full bodies via
single cat pass; gate thresholds + call sites extracted).

Evidence read (7): core p4/p5_run.json; engines p2/p3/p4_
run.json, p2_report.txt, v14_report.txt (plus TOOLS.md's 12
for the rest).

