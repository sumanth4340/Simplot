# Cross-Val TOOLS_REF — exhaustive tool reference (2026-11-04)

Pack role: cross-skill co-validation drills X1–X14. In-sim live/build
scripts print a single `XN-REPORT ...` stdout line; receipts land in
`evidence/*.json`; local verifiers assert them. This pack has NO
SKILL.md / README.md / failures.md / discovery.md (verified by
directory listing), so LIMITS cite live-script comments/docstrings and
evidence receipts instead.

Claim tags: every bullet ends with one of `[verified]` (read in pack
code or receipts), `[probable]` (strongly implied by pack code, one
inference step), `[theoretical]` (general knowledge, NOT drill-proven
here). UNKNOWN items are always `[theoretical]`.

Tools covered: 27 (17 in-sim incl. sense schema, 8 local-verifier,
harness convention, python builtins). Functions/methods documented:
132. Knobs: 52. Limits: 50. Unknowns: 28.
DATATYPE pass (2026-11-04): signatures typed 132/132 (every bullet
carries param types + return type + units/defaults or n/a, grounded
in script call sites or tagged [probable]/[theoretical]); knobs typed
52/52 (attr type + unit + default each); sense-schema fields typed 3/3
bullets; still-unknown type slots: 2 (GridCloner F2 return,
F4 element type).

## 1. omni.usd

DOES: stage handle + prim-handle API for every in-sim script. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `omni.usd.get_context() -> UsdContext [probable]` — no params.
  Returns USD context singleton (x1_build.py L5; same chain in all 16
  in-sim scripts). [verified]
- F2 `context.get_stage() -> Usd.Stage` — no params. Returns live
  stage handle (x1_build.py L5; all 16 in-sim scripts). [verified]
- F3 `stage.GetPrimAtPath(path: str) -> Usd.Prim` — Sdf-style prim
  path (x1_build.py L7, x2_live.py L35-36). Returns prim, possibly
  invalid/null. [verified]
- F4 `prim.IsValid() -> bool` — no params (x1_build.py L8). [verified]
- F5 `stage.DefinePrim(path: str, type_name: str = "" [theoretical]) -> Usd.Prim` — prim path (x2_live.py L14, x3_diag.py L7, x3_prec.py
  L24/L37, x4_build.py L45; 2nd arg never passed here). Returns
  defined prim, created if absent; hosts USD refs (x2/x3/x4).
  [verified]
- F6 `stage.RemovePrim(path: str) -> bool [probable]` — prim path
  (x1_build.py L9; return never consumed). x1_build clears 3 paths
  before rebuild. [verified]
- F7 `prim.GetReferences() -> Usd.References` — no params
  (x2_live.py L15, x3_diag.py L8, x3_prec.py L25, x4_build.py L46).
  Returns references proxy. [verified]
- F8 `refs.AddReference(asset_path: str) -> bool [theoretical]` —
  absolute file path only proven (x2_live.py L15-17, x3_diag.py L8-9,
  x3_prec.py L25, x4_build.py L46-48; return never consumed).
  Appends a reference arc. [verified]
- F9 `stage.GetRootLayer() -> Sdf.Layer` — no params (x3_diag.py
  L25, x3_prec.py L32). [verified]
- F10 `prim.GetAttribute(name: str) -> Usd.Attribute` — attribute
  name (x3_diag.py L14, x9_live.py L37-39). Returns attr, possibly
  invalid. [verified]
- F11 `attr.Get() -> Any` — no args passed in pack; resolved type
  per attr: size->float (x3_prec.py L27), drive type->str
  (x9_live.py L37), stiffness/damping->float (x9_live.py L38-39),
  nosleep->bool (x7_live.py L25-26), primPath->str (x9_live.py
  L51). (`time` kw unproven [theoretical].) [verified]
- F12 `attr.Set(value: float) -> bool [probable]` — value: float
  proven (x3_diag.py L23, x3_prec.py L28 `Set(2.0)`; other value
  types unproven [theoretical]; return never consumed). x3_diag/
  x3_prec write direct overs with it. [verified]
- F13 `attr.Clear() -> bool [probable]` — no params (x3_diag.py
  L30 `ok = ...Clear()`; value printed, exact type unproven).
  Clears authored value but LEAVES a root stack entry. [verified]
- F14 `attr.HasAuthoredValue() -> bool` — no params (x3_diag.py
  L18, printed by `dump()`). [verified]
- F15 `attr.GetPropertyStack(time: Usd.TimeCode) -> list[Sdf.PropertySpec [probable]]` — time code, always
  `Usd.TimeCode.Default()` here (x3_diag.py L16, x3_prec.py
  L30-31). Returns specs strongest-first; elements expose
  `.layer -> Sdf.Layer`. [verified]
- F16 `spec.layer.GetDisplayName() -> str` — no params (x3_diag.py
  L15, x3_prec.py L31/L42). Layer file basename (`World27.usd`,
  `x3_overB.usda`). [verified]
- F17 `prim.HasAPI(schema: type, instance_name: str = "" [theoretical]) -> bool` — applied-schema class:
  RigidBodyAPI (x2_live.py L38), ArticulationRootAPI (x5_live.py
  L31-32), CollisionAPI (x5_live.py L70-71, x11_live.py L39),
  PhysxContactReportAPI (x7_live.py L27-28). [verified]
- F18 `prim.GetChildren() -> Iterable[Usd.Prim]` — no params
  (x9_live.py L40/L47; concrete list [probable]). x9 counts graph
  nodes + rival scan. [verified]
- F19 `prim.GetName() -> str` — no params (x9_live.py L48; excludes
  `V9Graph` itself). [verified]
- F20 `prim.GetTypeName() -> str` — no params (x9_live.py L48;
  matches `== "Graph"`). [verified]
- F21 `attr.IsValid() -> bool` — no params (x9_live.py L51 guards
  `inputs:primPath` reads). [verified]

KNOBS (typed: attr type + unit + default):
- K1 `path: str` (Sdf path syntax), unit n/a, default n/a
  (caller-supplied; no default). Every lens keys off exact
  `/World/...` paths; x5 v1 failed purely on wrong `M4V2*` paths
  (x5_live docstring). Effect: wrong path → invalid prim →
  sentinel/false report → FAIL. [verified]
- K2 `asset_path: str` (absolute Windows file path), unit n/a,
  default n/a. Target into modeling-assets / stage-core. Effect:
  moved workspace → broken ref → invalid prims. [verified]
- K3 `Set value: float` (double proven), unit unitless here (custom
  `size` attr), default: none — falls back to weaker stack opinions
  when unauthored [probable]. Writes a DIRECT opinion on the
  session/root layer, strongest in the stack (x3_prec: 2.0 beats
  sublayer 5.0). [verified]

EKB RULES:
- IF a prim may not exist THEN gate every HasAPI/attr read on
  `IsValid()` first BECAUSE touching APIs on invalid prims throws
  (null-prim throw; R11 rule, x5_live comment + x9/x10/x12/x14
  docstrings). [verified]
- IF a read must never throw THEN report a sentinel/false on the
  invalid branch BECAUSE verifiers regex the report line and a throw
  yields no line at all (x5/x9/x10/x12/x14 all do this). [verified]
- IF you need the winning opinion THEN read `[0]` of
  `GetPropertyStack(Usd.TimeCode.Default())` BECAUSE the stack is
  strongest-first (x3_prec reads stack tops for stop0/stopB). [verified]
- IF you cleared an attr THEN do NOT assume the stack is clean BECAUSE
  `Clear()` leaves a root stack entry (x3_prec docstring cites
  failures.md L5 — which does not exist in THIS pack; the rule text
  itself is in the docstring). [verified]

LIMITS (with cites):
- L1: R11 null-prim rule — `HasAPI`/attrs on invalid prims throw;
  every read script gates on `IsValid()` (scripts/x5_live.py L29-31,
  x6–x14 docstrings). [verified]
- L2: Missing-translate-op sentinel convention — `_tx` helpers return
  999.0 / (999,999,999) tuples, `_tz` 999.0, `_sc` default
  (1.0,1.0,1.0) when no op matches (x6/x8/x9/x10/x11/x12/x13/x14).
  [verified]
- L3: Absolute-path references couple packs to this workspace
  (x2_live L15-17, x4_build L46-48, x3_diag L8-9, x3_prec L20-21).
  [verified]
- L4: `Clear()` is NOT a clean removal — root keeps a stack entry, so
  X3B uses a fresh prim instead of clear-then-reread (x3_prec
  docstring). [verified]

UNKNOWN:
- U1: Context switching / multi-stage behavior. [theoretical]
- U2: `RemovePrim` return contract and failure modes. [theoretical]
- U3: Relative/asset-path references (only absolute proven).
  [theoretical]

## 2. pxr.UsdGeom

DOES: geometry authoring (Cube/Plane/Mesh/Camera reads) + read-only
xform measurement lens. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `UsdGeom.Cube.Define(stage: Usd.Stage, path: str) -> UsdGeom.Cube`
  (x1_build.py L17, x4_build.py L20/L27/L31). Cube schema wrapping new
  prim. [verified]
- F2 `UsdGeom.Plane.Define(stage: Usd.Stage, path: str) -> UsdGeom.Plane`
  (x1_build.py L13, x2_live.py L21, x4_build.py L15). [verified]
- F3 `UsdGeom.Mesh.Define(stage: Usd.Stage, path: str) -> UsdGeom.Mesh`
  (x4_build.py L50). [verified]
- F4 `UsdGeom.Cube.Get(stage: Usd.Stage, path: str) -> UsdGeom.Cube` —
  EXISTING prim (read lens x5_live.py L33, x6_live.py L21, x7–x14
  `_size`). [verified]
- F5 `cube.GetSizeAttr() -> Usd.Attribute` + `Get() -> float` /
  `Set(v: float) -> bool [probable]` — cube edge length, units m
  [probable] (x1_build.py L18 `Set(1.0)`, x6_live.py L21
  `float(Get())`). [verified]
- F6 `plane.CreateWidthAttr() -> Usd.Attribute` /
  `CreateLengthAttr() -> Usd.Attribute`, `Set(v: float)` — plane dims
  in m [probable] (x1_build.py L14-15 `Set(20.0)`). [verified]
- F7 `mesh.CreatePointsAttr().Set(pts: list[Gf.Vec3f])` — 3 verts
  proven (x4_build.py L51), units m [probable]. [verified]
- F8 `mesh.CreateFaceVertexCountsAttr().Set(counts: list[int])` —
  `[3]`, one tri (x4_build.py L52), unitless. [verified]
- F9 `mesh.CreateFaceVertexIndicesAttr().Set(idx: list[int])` —
  `[0,1,2]` winding (x4_build.py L53), unitless. [verified]
- F10 `UsdGeom.Xformable(prim: Usd.Prim) -> UsdGeom.Xformable`
  (x1_build.py L19, x5_live.py L37). [verified]
- F11 `xform.AddTranslateOp() -> UsdGeom.XformOp` (no args passed in
  pack; suffix/precision kwargs unproven [theoretical]);
  `op.Set(v: Gf.Vec3d) -> bool [probable]`, units m [probable]
  (x1_build.py L19, x4_build.py L22/L29/L33/L54). [verified]
- F12 `xform.GetOrderedXformOps() -> list[UsdGeom.XformOp]`
  (x5_live.py L38, x6_live.py L25; basis of every
  `_tx/_tw/_tz/_sc`). [verified]
- F13 `op.GetOpType() -> UsdGeom.XformOp.Type` — op-type token;
  compared to `TypeTranslate` / `TypeScale` (x5_live.py L39/L41).
  [verified]
- F14 `op.Get() -> Gf.Vec3d | tuple[float, float, float]` — index
  [0]=x,[2]=z (x6_live.py L27, x11_live.py L26/L33); translate units
  m [probable], scale unitless. [verified]
- F15 `op.GetAttr() -> Usd.Attribute`;
  `GetTimeSamples() -> list[float] [theoretical]` — only `len()`
  consumed (x10_live.py L47-48: 2+2 samples); element type/time unit
  unproven. [verified]
- F16 `UsdGeom.Camera.Get(stage: Usd.Stage, path: str) -> UsdGeom.Camera`
  — existing prim (x6_live.py L39). [verified]
- F17 `cam.GetFocalLengthAttr().Get() -> float` — focal length, units
  mm [theoretical]; 24.0 asserted (x6_live.py L39-40). [verified]

KNOBS (typed: attr type + unit + default):
- K1 Cube `size: float`, unit m [probable], default 1.0
  [theoretical] (unauthored USD default; every drill authors its
  own). Asserted per drill: 0.15/0.2 (x9/x10), 0.4 (x10 gate),
  0.5/1.2 (x6), 0.5/1.0 (x8), 1.0 (x1/x4/x13A/x14), 1.2 (x7),
  0.8 (x12), 1.4/1.0 (x11). Effect: mismatch beyond tolerance →
  FAIL. [verified]
- K2 Plane `width/length: float`, unit m [probable], default 1.0
  [theoretical]. 20.0 grounds in x1/x2/x4. Effect: smaller plane
  risks bodies falling off the edge. [probable]
- K3 Translate values `tuple[float, float, float]` (from `op.Get()`),
  unit m [probable], default (0,0,0) [theoretical] (no-op =
  identity). Sense-lens assertions (e.g. x=3.0/4.0 bot, (-1,0,0.4)
  box A). Effect: drift → FAIL. [verified]
- K4 Scale op `tuple[float, float, float]`, unitless, default
  (1,1,1) [verified] (x11_live.py L34 `_sc` fallback). (1.6,0.8,1.0)
  on x11 F. Effect: any component off → FAIL (exact tuple match).
  [verified]
- K5 Focal length `float`, unit mm [theoretical], default 50.0
  [theoretical] (USD schema default; x6 scene authors 24.0). Effect:
  other value → FAIL. [verified]

EKB RULES:
- IF you read one axis off xform ops THEN loop `GetOrderedXformOps()`
  and match `GetOpType() == TypeTranslate` BECAUSE op order is not
  guaranteed and translate may not be first (every `_tx` does this).
  [verified]
- IF no translate op exists THEN return a 999 sentinel BECAUSE
  verifiers treat 999 as cleanly-missing, while an exception kills the
  whole report line (x6/x8/x9/x10/x14 `_tx`). [verified]
- IF you count animation THEN read time-sample counts off ordered ops
  by index BECAUSE the drill authors gate then translate (gops[0]) and
  rotate (gops[1]) samples (x10_live L44-48). [verified]
- IF a float round-trips through the report THEN format/parse with
  matching precision BECAUSE verifiers use exact (1e-6) or loose (0.02)
  tolerances per key (verify_x5–x14). [verified]

LIMITS (with cites):
- L1: `_tx` missing-op sentinel 999.0; `_tw` (999,999,999);
  `_sc` default (1,1,1); `_tz` 999.0 (x6/x8/x9/x10/x11/x12/x13/x14).
  [verified]
- L2: Anim lens reads `gops[0]`/`gops[1]` by INDEX — assumes translate
  then rotate order (scripts/x10_live.py L46-48). [verified]
- L3: Mesh proven only as single triangle, size reads back [1,1,0]
  (x4_build L50-53; verify_x4.py L42-44). [verified]

UNKNOWN:
- U1: Non-cube/plane/mesh/camera schema coverage. [theoretical]
- U2: Rotate/scale op authoring (only translate authored). [theoretical]
- U3: `Cube.Get` on a non-cube prim — behavior unproven. [theoretical]

## 3. pxr.UsdPhysics

DOES: physics scene, bodies, joints, mass, API-flag lens. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `UsdPhysics.Scene.Define(stage: Usd.Stage, path: str) -> UsdPhysics.Scene`
  (x1_build.py L10, x2_live.py L18, x4_build.py L12). [verified]
- F2 `scene.CreateGravityDirectionAttr().Set(v: Gf.Vec3f) -> bool [probable]`
  — unitless direction (x1_build.py L11 `Vec3f(0,0,-1)`; x2/x4
  same). [verified]
- F3 `scene.CreateGravityMagnitudeAttr().Set(g: float) -> bool [probable]`
  — units m/s^2 [probable]; Earth g 9.81 (x1_build.py L12; x2/x4
  same). [verified]
- F4 `UsdPhysics.RigidBodyAPI.Apply(prim: Usd.Prim) -> UsdPhysics.RigidBodyAPI`
  — makes body dynamic (x1_build.py L20, x4_build.py L23/L34).
  [verified]
- F5 `UsdPhysics.CollisionAPI.Apply(prim: Usd.Prim) -> UsdPhysics.CollisionAPI`
  — enables collisions (x1_build.py L16/L21, x4_build.py
  L18/L24/L30/L35). [verified]
- F6 `UsdPhysics.MassAPI.Apply(prim: Usd.Prim) -> UsdPhysics.MassAPI`;
  `GetMassAttr() -> Usd.Attribute`; `Set(m: float)` — m in kg
  [probable] (x1_build.py L22 `Set(1.0)`, x4_build.py L25). [verified]
- F7 `UsdPhysics.MassAPI.Get(stage: Usd.Stage, path: str) -> UsdPhysics.MassAPI`
  — existing prim (x7_live.py L21). [verified]
- F8 `UsdPhysics.MassAPI(prim: Usd.Prim) -> UsdPhysics.MassAPI`;
  `GetMassAttr().Get() -> float`, kg [probable] (x14_live.py L36).
  [verified]
- F9 `UsdPhysics.ArticulationRootAPI: type` — applied-API schema
  class, used only as `HasAPI()` arg (x5_live.py L31-32). Not
  called. [verified]
- F10 `UsdPhysics.RevoluteJoint.Define(stage: Usd.Stage, path: str) -> UsdPhysics.RevoluteJoint`
  (x4_build.py L36). [verified]
- F11 `joint.GetBody0Rel() -> Usd.Relationship` /
  `GetBody1Rel() -> Usd.Relationship`;
  `rel.AddTarget(path: str) -> None [theoretical]` — return never
  consumed (x4_build.py L37-38). Attaches bodies. [verified]
- F12 `joint.GetLocalPos0Attr().Set(p: Gf.Vec3f)` /
  `GetLocalPos1Attr().Set(p: Gf.Vec3f)` — joint frames (0,0,+/-0.5),
  units m [probable] (x4_build.py L39/L41). [verified]
- F13 `joint.GetLocalRot0Attr().Set(q: Gf.Quatf)` /
  `GetLocalRot1Attr().Set(q: Gf.Quatf)` — identity frames
  `Quatf(1.0)`, unitless (x4_build.py L40/L42). [verified]
- F14 `joint.GetAxisAttr().Set(axis: Tf.Token) -> bool [probable]` —
  `UsdPhysics.Tokens.z` proven (x4_build.py L43); x/y unproven
  [theoretical]. Hinge axis Z. [verified]
- F15 Raw drive attrs `prim.GetAttribute(name: str).Get()` — name one
  of `"drive:angular:physics:type|stiffness|damping"`; returns str
  (type, x9_live.py L37) / float (stiffness/damping, x9_live.py
  L38-39, x10_live.py L41-43). Units: stiffness N·m/rad, damping
  N·m·s/rad [theoretical]. No schema wrapper used. [verified]
- F16 Raw collider attr
  `prim.GetAttribute("physics:collisionEnabled").Get() -> bool | None [probable]`
  — None when attr missing (x11_live.py L41-42 `is not False`
  counts missing as enabled). [verified]

KNOBS (typed: attr type + unit + default):
- K1 Gravity `magnitude: float` (m/s^2 [probable], value 9.81) +
  `direction: Gf.Vec3f` (unitless, (0,0,-1)); defaults unproven
  [theoretical]. x1 drop cube settles z 2.0→0.5 over 120 steps.
  Effect: 0-g → no drop (z1 FAIL); flipped axis → flyaway.
  [probable]
- K2 Mass `m: float`, unit kg [probable], default: computed from
  density×volume when unauthored [theoretical]. Values 1.0 (x1/x4),
  2.0 (x7), 5.0 (x14). Effect: wrong mass → FAIL; dynamics change
  unmeasured here. [verified]
- K3 Drive triple `(type: str, stiffness: float, damping: float)` =
  ("position", 100, 10) (x9/x10); stiffness/damping units
  [theoretical] (see F15); defaults unproven [theoretical]. Effect:
  any mismatch → FAIL. [verified]
- K4 Joint frames `localPos: Gf.Vec3f` (m [probable], (0,0,+/-0.5))
  + `axis: Tf.Token` (z); defaults unproven [theoretical]. x4 hinge
  anchor sites must read midX+midY+maxZ/minZ (verify_x4). Effect:
  moved frame → site FAIL. [verified]
- K5 `physics:collisionEnabled: bool`, unitless, default True
  [probable] (missing attr counts as enabled, x11_live.py L41-42).
  x11 requires present-or-missing on D/E/F. Effect: explicit False
  → col FAIL. [verified]

EKB RULES:
- IF you read drive params THEN use raw attribute names
  `drive:angular:physics:*` BECAUSE no schema wrapper is exercised in
  this pack (x9_live L37-39, x10_live L41-43). [verified]
- IF you check collider enablement THEN treat missing attr as enabled
  (`en.Get() is not False`) BECAUSE the drill scene may not author the
  flag at all (x11_live L41-42). [verified]
- IF a joint must be sensed THEN author body0/body1 targets + local
  frames BECAUSE the sense snapshot reports bodies/sites and the
  verifier asserts them (verify_x2 shoulder, verify_x4 hinge sites).
  [verified]

LIMITS (with cites):
- L1: Drive reads are raw-attribute, not schema-wrapped (x9/x10_live).
  [verified]
- L2: Stability bar: settled block `spd=0.0000 rigid=True coll=True`
  after 120 steps (evidence/x5_run.json). [verified]
- L3: Only single-revolute joint authoring proven (x4_build L36-43).
  [verified]
- L4: X4 hinge sites must be exactly `midX+midY+maxZ` /
  `midX+midY+minZ` (scripts/verify_x4.py L35-37). [verified]

UNKNOWN:
- U1: Joint authoring beyond single revolute; drive WRITES. [theoretical]
- U2: Kinematic bodies, velocity limits, joint limits via API. [theoretical]

## 4. pxr.UsdShade

DOES: red PBR material authoring (x4_build only). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `UsdShade.Material.Define(stage: Usd.Stage, path: str) -> UsdShade.Material`
  (x4_build.py L56). [verified]
- F2 `UsdShade.Shader.Define(stage: Usd.Stage, path: str) -> UsdShade.Shader`
  (x4_build.py L57). [verified]
- F3 `shader.SetShaderId(id: str) -> None [theoretical]` — return
  never consumed; only `"UsdPreviewSurface"` proven (x4_build.py
  L58). [verified]
- F4 `shader.CreateInput(name: str, type: Sdf.ValueTypeName) -> UsdShade.Input`;
  `input.Set(c: Gf.Vec3f)` — `("diffuseColor", Color3f)`, unitless
  RGB 0–1; red `(1,0,0)` (x4_build.py L59). [verified]
- F5 `mat.CreateSurfaceOutput() -> UsdShade.Output` — no args (output
  name default "surface" [theoretical]; x4_build.py L60). [verified]
- F6 `output.ConnectToSource(source: UsdShade.ConnectableAPI, source_name: str) -> bool [theoretical]`
  — `(sh.ConnectableAPI(), "surface")`; return never consumed
  (x4_build.py L60). Wires shader→material. [verified]
- F7 `UsdShade.MaterialBindingAPI(prim: Usd.Prim) -> UsdShade.MaterialBindingAPI`;
  `Bind(mat: UsdShade.Material) -> None [theoretical]` — binds red
  onto X4Cube (x4_build.py L61; return never consumed). [verified]

KNOBS (typed: attr type + unit + default):
- K1 `diffuseColor: Color3f (Gf.Vec3f)`, unitless RGB, value
  (1,0,0); schema default unproven [theoretical]. The only authored
  look. Effect: other values unasserted (verifier only checks
  material prim EXISTS). [verified]
- K2 Bind target prim `path: str` (`/World/X4Cube`), unit n/a,
  default: unbound [probable]. Effect: binding elsewhere leaves the
  cube unbound; no verifier checks the BIND, only
  `/World/X4Looks/X4Red` presence (verify_x4 L45-46). [verified]

EKB RULES:
- IF a drill needs a material THEN author Material+Shader+Bind as one
  block BECAUSE the sense lens only sees prims the snapshot walker
  visits, and the trio keeps material + binding consistent (x4_build
  L56-61, verify_x4 L45-46). [probable]

LIMITS (with cites):
- L1: Only `UsdPreviewSurface` + `diffuseColor` proven in this pack
  (scripts/x4_build.py L56-61). [verified]
- L2: Verifier asserts material prim presence, NOT the bind or color
  (scripts/verify_x4.py L45-46). [verified]

UNKNOWN:
- U1: Textures, other inputs, collection bindings. [theoretical]

## 5. pxr.Gf

DOES: math value types for authoring. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` — 32-bit
  vector; units per use: unitless (gravity dir x1_build.py L11,
  color x4_build.py L59) or m [probable] (joint frames x4_build.py
  L39/L41, mesh points x4_build.py L51). [verified]
- F2 `Gf.Vec3d(x: float, y: float, z: float) -> Gf.Vec3d` — 64-bit
  vector; translate ops, units m [probable] (x1_build.py L19,
  x4_build.py L22/L29/L33/L54). [verified]
- F3 `Gf.Quatf(w: float) -> Gf.Quatf` — 1-arg identity form proven
  (`Quatf(1.0)`, x4_build.py L40/L42; imag default 0
  [theoretical]); full (w,x,y,z) ctor unproven [theoretical].
  Unitless joint rotation frames. [verified]

KNOBS: none beyond constructor values (covered under consuming tools).

EKB RULES:
- IF you set a translate op THEN use `Vec3d` BECAUSE every
  `AddTranslateOp().Set(v: Gf.Vec3d)` in this pack passes Vec3d
  (x1/x4_build).
  [verified]
- IF you set gravity/joint/color/points THEN use `Vec3f` BECAUSE every
  such call in this pack passes Vec3f (x1/x2/x4). [verified]

LIMITS (with cites):
- L1: No use beyond construction + pass-through (x1/x2/x4_build).
  [verified]

UNKNOWN:
- U1: Matrix/quat math beyond identity frames. [theoretical]

## 6. pxr.Sdf

DOES: value-type name for the shader input (x4_build only). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `Sdf.ValueTypeNames.Color3f: Sdf.ValueTypeName [probable]` —
  constant, not a call (x4_build.py L59
  `CreateInput(name: str, type: Sdf.ValueTypeName)`). [verified]

KNOBS / EKB: none (single constant use).

LIMITS (with cites):
- L1: Single use at scripts/x4_build.py L59. [verified]

UNKNOWN:
- U1: All other Sdf APIs. [theoretical]

## 7. pxr.UsdLux

DOES: light-rig read lens (dome + sun intensities). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `UsdLux.DomeLight.Get(stage: Usd.Stage, path: str) -> UsdLux.DomeLight`
  — existing prim (x6_live.py L35, x7_live.py L23, x8_live.py L33,
  x12_live.py L35, x13_live.py L34). [verified]
- F2 `dome.GetIntensityAttr() -> Usd.Attribute`; `Get() -> float` —
  unitless multiplier [theoretical] (x6_live.py L35-36). [verified]
- F3 `UsdLux.DistantLight.Get(stage: Usd.Stage, path: str) -> UsdLux.DistantLight`
  (x6_live.py L37, x8_live.py L35). [verified]
- F4 `sun.GetIntensityAttr().Get() -> float` — unitless
  [theoretical] (x6_live.py L37-38). [verified]

KNOBS (typed: attr type + unit + default):
- K1 Dome `intensity: float`, unitless [theoretical], default 1.0
  [theoretical]. Values 300 (x6/x7/x8), 3000 (x12/x13). Effect:
  mismatch → FAIL. [verified]
- K2 Sun `intensity: float`, unitless [theoretical], default 1.0
  [theoretical]. Value 1200 (x6/x8). Effect: mismatch → FAIL.
  [verified]

EKB RULES:
- IF you read a light THEN use `LightType.Get(stage, path)` +
  `GetIntensityAttr().Get()` BECAUSE that two-call chain is the only
  light access proven here (x6_live L35-38). [verified]

LIMITS (with cites):
- L1: Reads only; no light authoring in this pack (x6/x7/x8/x12/x13
  are READ-ONLY snapshots per docstrings). [verified]
- L2: Only DomeLight + DistantLight + intensity proven. [verified]

UNKNOWN:
- U1: Writes, other light types, shadow/exposure attrs. [theoretical]

## 8. pxr.Usd

DOES: composition engine — property stacks, root-layer sublayers,
time codes (x3_diag/x3_prec, FULLY read). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `Usd.TimeCode.Default() -> Usd.TimeCode` — no params (x3_diag.py
  L16, x3_prec.py L31/L42). Default time code for `GetPropertyStack`.
  [verified]
- F2 `root.subLayerPaths: list[str]` — Sdf.Layer property: readable
  sequence of str + writable `list[str]` assignment (x3_prec.py L33
  `list(root.subLayerPaths)`, L34-35 prepend+assign; x3_diag.py
  L26-27/L35;
  concrete proxy class unproven [theoretical]). No units. [verified]
- F3 `list(it: Iterable[str]) -> list[str]` — snapshot for restore
  (x3_diag.py L26, x3_prec.py L33). Python builtin. [verified]
- F4 `attr.GetPropertyStack(time: Usd.TimeCode)[0].layer.GetDisplayName() -> str`
  — winning layer basename (x3_prec.py L30-31/L41-42; see omni.usd
  F15/F16). [verified]

KNOBS (typed: attr type + unit + default):
- K1 `subLayerPaths: list[str]` order — strongest-first (x3_prec.py
  L34-35 prepends `[over, overB] + saved`); default = pre-drill
  stack, restored after (x3_prec.py L33/L43). Effect: appending
  instead → weaker than existing subs (order matters). [probable]
- K2 Over-file content: USDA text asserting `double size = 5` —
  `size: float` (double), unitless, value 5.0; generated by
  x3_prec.py L13-19 into stages/x3_over{,B}.usda. Effect: any value
  other than 5.0 breaks the sub==5.0 assertion. [verified]
- K3 Stack levels `ref/direct/sub: float`, unitless — reference 1.0,
  direct `Set(2.0)`, sublayer 5.0 (x3_prec.py L27-29/L36/L40). The
  three stack levels under test. Effect: change any → different
  winner. [verified]

EKB RULES:
- IF you test precedence THEN use Direct > Sublayer > Reference order
  BECAUSE x3 proves it: direct 2.0 beats sub 5.0 (withsub), sub 5.0
  beats ref 1.0 (X3B) (evidence/x3_run.json). [verified]
- IF you mutate `subLayerPaths` THEN save + restore BECAUSE the live
  stage is shared across drills and a leaked sublayer would corrupt
  later reads (x3_prec L33-35, L43; x3_diag L26-27, L35). [verified]
- IF you need a fresh no-direct-over read THEN define a NEW prim (X3B)
  instead of Clear() BECAUSE Clear leaves a root stack entry (x3_prec
  docstring). [verified]

LIMITS (with cites):
- L1: Proven winners: stop0=`World27.usd` (root), stopB=`x3_overB.usda`
  (evidence/x3_run.json). [verified]
- L2: Only `double size` attr + `over` composition proven; no
  class/variant/payload arcs (stages/x3_over.usda). [verified]

UNKNOWN:
- U1: Payloads, variants, inherits/specializes arcs. [theoretical]
- U2: Time-varying (non-Default) stack reads. [theoretical]

## 9. pxr.PhysxSchema

DOES: PhysX contact-report API presence check (x7_live, FULLY read).
[verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `PhysxSchema.PhysxContactReportAPI: type` — applied-API schema
  class, used only as `HasAPI()` arg on V7Cube (x7_live.py L27-28).
  Not called. [verified]
- F2 `prim.GetAttribute("physxScene:disableSleeping").Get() -> bool`
  — no-sleep flag on PhysicsScene, value True (x7_live.py L25-26;
  verifier `b(nosleep)` requires "True"). [verified]

KNOBS (typed: attr type + unit + default):
- K1 `physxScene:disableSleeping: bool`, unitless, default unproven
  [theoretical]. x7 requires True. Effect: False → nosleep FAIL.
  [verified]
- K2 Contact-report API applied `present: bool`, unitless, default
  False (not applied) [probable]. Effect: missing → report FAIL.
  [verified]

EKB RULES:
- IF you check PhysX extensions THEN mix HasAPI (report) and raw attrs
  (disableSleeping) BECAUSE that is exactly the proven split (x7_live
  L25-28). [verified]

LIMITS (with cites):
- L1: Single-drill, read-only use (scripts/x7_live.py). [verified]

UNKNOWN:
- U1: Report data reads, contact event APIs, all other PhysxSchema
  members. [theoretical]

## 10. isaacsim.core.experimental.utils.app (app_utils)

DOES: timeline transport for play/step live scripts + stopped check.
[verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `app_utils.play() -> None [theoretical]` — no params, sync
  (never awaited); return never consumed (x1_run.py L8, x2_live.py
  L28, x5_live.py L53). Starts timeline. [verified]
- F2 `await app_utils.update_app_async(steps: int) -> Awaitable[None [theoretical]]`
  — `steps` kw name proven, only 120 passed (x1_run.py L11,
  x2_live.py L31, x5_live.py L56); default value unproven
  [theoretical]. Units: steps/frames [probable]. MUST be awaited
  (live scripts are async contexts). [verified]
- F3 `app_utils.is_stopped() -> bool` — no params (x13_live.py L42;
  verifier `b(stopped)` requires "True"). x13 app lens asserts
  stopped=True post-reopen. [verified]

KNOBS (typed: attr type + unit + default):
- K1 `steps: int`, unit frames/steps [probable], default unproven
  [theoretical]. x1/x2/x5 legs use 120; t 0.000→2.000 (x1/x2
  receipts). Effect: fewer steps → less settle/drop (z1 FAIL risk);
  more → longer runtime. Exact seconds-per-step unproven. [probable]
- K2 play/pause pairing: convention (no attr type; unit/default n/a).
  x1/x2/x5 play, step, read, pause. Effect: no pause leaves sim
  running into the next drill (state leak). [probable]

EKB RULES:
- IF a drill measures motion THEN play → read z0/t0 → step 120 →
  read z1/t1 → pause BECAUSE verifiers require t1>t0 AND settled z
  (verify_x1 L34-39, verify_x2 L34-37). [verified]
- IF a drill is READ-ONLY (x6–x14 minus play legs) THEN make NO
  timeline calls except `is_stopped()` BECAUSE their docstrings forbid
  timeline writes and verifiers assert post states (x13 stopped=True).
  [verified]

LIMITS (with cites):
- L1: 120-step legs in x1/x2/x5; x6–x14 READ-ONLY snapshots with NO
  timeline writes (their docstrings; x13 only calls `is_stopped()`).
  [verified]
- L2: t0=0.000 → t1=2.000 over 120 steps (evidence/x1_run.json,
  x2_run.json). [verified]

UNKNOWN:
- U1: `update_app_async` beyond steps=120; stop/reset helpers.
  [theoretical]

## 11. omni.timeline

DOES: wall-clock check and pause for live scripts. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `omni.timeline.get_timeline_interface() -> Timeline [probable]` —
  no params; concrete class name unproven (x1_run.py L6, x2_live.py
  L26, x5_live.py L51). [verified]
- F2 `tl.get_current_time() -> float` — no params; units seconds
  [probable] (x1_run.py L10/L13; t0=0.000→t1=2.000 receipts).
  [verified]
- F3 `tl.pause() -> None [theoretical]` — no params; return never
  consumed (x1_run.py L14, x2_live.py L34, x5_live.py L60). [verified]

KNOBS: none (no parameters exercised).

EKB RULES:
- IF you assert time advanced THEN compare t1 > t0 as strict float
  inequality BECAUSE verifiers FAIL on `not t1 > t0` (verify_x1 L38-39,
  verify_x2 L34-35). [verified]
- IF you play via app_utils THEN still pause via timeline BECAUSE that
  is the proven pairing in all three play legs (x1_run L8/L14, x2_live
  L28/L34, x5_live L53/L60). [verified]

LIMITS (with cites):
- L1: verify_x1/x2 FAIL unless t1 > t0 ("no time advance"). [verified]

UNKNOWN:
- U1: play/stop via timeline interface (play goes through app_utils
  here). [theoretical]

## 12. isaacsim.core.experimental.prims.Articulation

DOES: articulation DOF read lens (x5/x10). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `Articulation(path: str) -> Articulation` — articulation root
  path, single positional str proven (`P+"/Root"` x5_live.py L54,
  `/World/V10Bot/Base` x10_live.py L49; other ctor params unproven
  [theoretical]). Returns articulation view. [verified]
- F2 `art.get_dof_positions() -> wp.array | np.ndarray` — no params;
  float vector shape (n_dof,) [probable], units rad [verified]
  (`np.degrees` applied, x5_live.py L68; q=[1.735,1.092] x5).
  [verified]
- F3 `art.get_dof_position_targets() -> wp.array | np.ndarray` — no
  params; float vector, units rad [probable] (x10_live.py L50-52;
  echo=+0.4). [verified]

KNOBS (typed: attr type + unit + default):
- K1 Root `path: str`, unit n/a, default n/a (caller-supplied). Must
  be the articulation root prim. Effect: wrong path → wrong/empty
  DOF vector. [probable]
- K2 klim bar `170.0: float`, unit deg, threshold (not a default).
  `np.all(abs(degrees(q)) <= 170)` (x5_live.py L68). Effect: any
  joint beyond → klim FAIL. [verified]
- K3 echo target `+0.4: float`, unit rad [probable] (x10_live.py
  L52). Effect: other target → FAIL. [verified]

EKB RULES:
- IF you consume a DOF getter THEN normalize with
  `e.numpy() if isinstance(e, wp.array) else np.asarray(e)` BECAUSE
  getters return warp array OR ndarray depending on context (x5_live
  `_w`, x10_live L51). [verified]
- IF you assert joint limits THEN convert rad→deg and allow ±170
  BECAUSE that is the proven bar (x5_live L68, evidence q values).
  [verified]

LIMITS (with cites):
- L1: Getter return-type duality warp/ndarray (x5_live L45-48,
  x10_live L50-52). [verified]
- L2: 2-DOF arms only (evidence/x5_run.json q pair). [verified]

UNKNOWN:
- U1: DOF writes / target sets. [theoretical]

## 13. isaacsim.core.experimental.prims.RigidPrim

DOES: rigid-body pose/velocity read lens (x1/x2/x5). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `RigidPrim(paths: str) -> RigidPrim` — kw form for nested prims
  (x1_run.py L7, x2_live.py L27 `/World/X2Bot/Geometry/base`).
  Returns rigid view. [verified]
- F2 `RigidPrim(paths: str)` positional — same ctor, first positional
  arg (x5_live.py L55 `RigidPrim(BLK)`). (`list[str]` + further
  kwargs unproven [theoretical].) Returns rigid view. [verified]
- F3 `rp.get_world_poses() -> tuple[pos_batch, quat_batch] [probable]`
  — no params; `[0]` is positions batch (`wp.array | np.ndarray`
  [verified], x5_live.py L58 `_w(batch)`); `.numpy()[0][2]` = z of
  first body in m [probable] (x1_run.py L9/L12, x2_live.py
  L29/L32). [verified]
- F4 `rp.get_velocities() -> tuple[vel_batch, angvel_batch] [probable]`
  — no params; `[0]` velocity batch (`wp.array | np.ndarray`
  [verified], x5_live.py L59); `v1[:3]` linear m/s [probable]; spd
  from `norm(v1[:3])` (x5_live.py L69). [verified]

KNOBS (typed: attr type + unit + default):
- K1 Pose index `[0][2]: int, int`, unitless (batch 0, z-axis 2). z
  of first body. Effect: wrong index → wrong-axis assertion.
  [verified]
- K2 z0/z1 bars `float`, unit m [probable] — x1: z0=2.0±0.05,
  z1=0.5±0.1 (drop); x2: |dz|≤0.2 (stability). Effect: out of bar →
  FAIL. [verified]
- K3 spd bar `0.2: float`, unit m/s [probable] (verify_x5.py L23
  `spd < 0.2`). Effect: moving block → FAIL. [verified]

EKB RULES:
- IF you address a nested prim THEN use the `paths=` kw form BECAUSE
  x2 reaches `/World/X2Bot/Geometry/base` that way (x2_live L27).
  [verified]
- IF you read z THEN index `get_world_poses()[0].numpy()[0][2]`
  BECAUSE that exact chain is proven in x1_run L9/L12 and x2_live
  L29/L32. [verified]

LIMITS (with cites):
- L1: `paths=` kw reaches nested prims (x2_live L27). [verified]
- L2: z0=1.9918 z1=0.5000 drop receipt (evidence/x1_run.json). [verified]

UNKNOWN:
- U1: Velocity/pose setters. [theoretical]

## 14. isaacsim.core.cloner.GridCloner

DOES: grid cloning for the X4 capstone (x4_build only). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `GridCloner(spacing: float) -> GridCloner` — kw `spacing=3.0`
  proven (x4_build.py L63); default value unproven [theoretical].
  Units m [probable]. [verified]
- F2 `cloner.define_base_env(env_path: str) -> ? [theoretical]` —
  return never consumed, type still unknown (x4_build.py L64
  `"/World/x4envs"`). Creates base env. [verified]
- F3 `cloner.generate_paths(prefix: str, count: int) -> list[str] [probable]`
  — (`"/World/x4envs/env"`, 2) (x4_build.py L65); len 2 implied by
  clones=2 receipt [probable]. Returns prim paths. [verified]
- F4 `cloner.clone(source_prim_path: str, prim_paths: list[str]) -> list[?] [theoretical]`
  — both kw (x4_build.py L66); `len()` == 2 proven, element type
  still unknown. Reported as clones=2. [verified]

KNOBS (typed: attr type + unit + default):
- K1 `spacing: float`, unit m [probable], default unproven
  [theoretical]. Value 3.0 (clone separation). Effect: unasserted
  (only count checked). [verified]
- K2 `count: int`, unitless, value 2 (the only proven scale).
  Verifier demands exactly 2 `/World/x4envs/env_*` prims. Effect:
  other counts unproven. [verified]
- K3 `source_prim_path: str`, unit n/a, default n/a. Must exist + be
  valid (`/World/X4Cube`). Effect: missing source → clone failure
  (mode unproven). [probable]

EKB RULES:
- IF you clone THEN report `len(clone(source_prim_path, prim_paths))`
  BECAUSE the verifier
  cross-checks the count against sensed `/World/x4envs/env_*` prims
  (x4_build L66, verify_x4 L47-49). [verified]

LIMITS (with cites):
- L1: 2-clone X4 scene is the only proven scale
  (evidence/x4_run.json `clones=2`). [verified]
- L2: Sensed clone paths use `env_` prefix (`/World/x4envs/env_*`;
  verify_x4 L47), NOT the bare `env` prefix passed to generate_paths.
  [verified]

UNKNOWN:
- U1: Larger grids, non-cube sources, clone failure modes. [theoretical]

## 15. isaacsim.core.experimental.utils.semantics.get_labels

DOES: semantic-label lens (x12_live only). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `get_labels(prim: Usd.Prim) -> dict[str, list[str]]` — prim from
  `stage.GetPrimAtPath` (x12_live.py L37-38). Returns e.g.
  `{'class': ['v12a']}`. Printed raw into report. [verified]

KNOBS (typed: attr type + unit + default):
- K1 Label values `list[str]` (`['v12a']`/`['v12b']`), unit n/a,
  default: missing-label shape unproven [theoretical]. Verifier does
  substring match `"v12a" in EV`. Effect: missing label → FAIL.
  [verified]

EKB RULES:
- IF you assert labels THEN substring-match the raw dict print BECAUSE
  the report embeds the full dict repr (`la={'class': ['v12a']}`,
  verify_x12 checks `"v12a" in EV`). [verified]

LIMITS (with cites):
- L1: Return shape is `{'class': [...]}` (evidence/x12_run.json).
  [verified]
- L2: Single-drill use, reads only (scripts/x12_live.py L37-38).
  [verified]

UNKNOWN:
- U1: Label writes, multi-label prims, missing-label return shape.
  [theoretical]

## 16. isaacsim.core.simulation_manager.SimulationManager

DOES: app/physics-engine lens (x14_live only). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `SimulationManager.get_active_physics_engine() -> str [probable]`
  — no params, called on class aliased `S`
  (staticmethod/classmethod kind unproven [theoretical]; x14_live.py
  L45). Returns engine string `physx`. [verified]

KNOBS: none (no parameters exercised).

EKB RULES:
- IF you assert the engine THEN substring-match `engine=physx` BECAUSE
  that is the proven-good post-exam state (evidence/x14_run.json,
  verify_x14). [verified]

LIMITS (with cites):
- L1: `engine=physx` is the asserted post-exam state
  (evidence/x14_run.json). [verified]

UNKNOWN:
- U1: Engine switching / manager lifecycle. [theoretical]

## 17. omni.graph.core (og)

DOES: OmniGraph read lens (x9_live only). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `og.get_node_by_path(path: str) -> og.Node [probable]` — node
  path (x9_live.py L41 `/World/V9Graph/Write`); concrete class name
  unproven. Returns node handle (check `.is_valid()`). [verified]
- F2 `node.is_valid() -> bool` — no params (x9_live.py L43). [verified]
- F3 `node.get_attribute(name: str) -> og.Attribute [probable]` — attr
  name (`"inputs:primPath"`, x9_live.py L42); `attr.get() -> str`
  for this attr (target path string [verified]; general return Any
  [probable]). [verified]
- F4 `og.get_graph_by_path(path: str) -> og.Graph [probable]` — graph
  path (x9_live.py L44); concrete class name unproven. Returns
  graph handle (check `.is_valid()`). [verified]
- F5 `graph.is_valid() -> bool` — no params (x9_live.py L45). [verified]
- F6 `graph.is_disabled() -> bool` — no params (x9_live.py L45); x9
  reports `en = not is_disabled()`. [verified]

KNOBS (typed: attr type + unit + default):
- K1 Write-node target `prim_path: str` (`/World/V9Bot/Hinge1`), unit
  n/a, default n/a. Verifier substring-matches
  `tgt=/World/V9Bot/Hinge1`. Effect: other target or MISSING →
  FAIL. [verified]
- K2 Node `count: int`, unitless, value 4 (children of
  /World/V9Graph). Effect: other count → FAIL. [verified]
- K3 Graph `enabled: bool`, unitless, value True. Effect: disabled →
  FAIL. [verified]
- K4 Rival `count: int`, unitless, value 0 — any other `Graph` prim
  under /World whose child `inputs:primPath` attr equals the V9
  hinge path counts as rival. Effect: rivals > 0 → FAIL. [verified]

EKB RULES:
- IF a graph node may be missing THEN print "MISSING", never throw,
  BECAUSE the report line must survive for the verifier to regex
  (x9_live L41-43). [verified]
- IF you scan rivals THEN iterate `/World` children filtering
  `GetTypeName() == "Graph"`, skip self by name, and guard each
  `inputs:primPath` attr with `IsValid()` BECAUSE non-Write children
  lack the attr (x9_live L46-52). [verified]

LIMITS (with cites):
- L1: Invalid Write node prints "MISSING", not throw (x9_live L41-43).
  [verified]
- L2: Rival definition = other Graph prim + child primPath attr equal
  to `/World/V9Bot/Hinge1` (x9_live L46-52). [verified]

UNKNOWN:
- U1: Graph authoring / enable writes, non-primPath attrs. [theoretical]

## 18. numpy

DOES: numeric checks and warp-array normalization. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `np.asarray(a: ArrayLike, dtype: DTypeLike | None = None [probable]) -> np.ndarray`
  — pack passes `dtype=float` (x5_live.py L48 `_w`, x10_live.py
  L51-52). Returns float ndarray. [verified]
- F2 `np.all(a: ndarray[bool]) -> bool [probable]` (numpy bool_
  [probable]) — klim bar (x5_live.py L68). [verified]
- F3 `np.abs(x: ndarray[float]) -> ndarray[float]` — element-wise abs
  (x5_live.py L68), unit-preserving (deg in→deg out here). [verified]
- F4 `np.degrees(x: ndarray[float]) -> ndarray[float]` — rad→deg
  (x5_live.py L68 klim). [verified]
- F5 `np.linalg.norm(x: ndarray[float]) -> float` — vector
  (x5_live.py L69 `v1[:3]`, m/s in → m/s scalar out). [verified]
- F6 `ndarray.flatten(order: str = "C" [theoretical]) -> ndarray` —
  no args passed (x5_live.py L57, x10_live.py L52). Flattens
  DOF/batch arrays. [verified]

KNOBS (typed: attr type + unit + default):
- K1 klim threshold `170.0: float`, unit deg, threshold (not a
  default). `np.all(abs(degrees(q)) <= 170.0)`. Effect: stricter
  value could FAIL settled arms (q=[1.735,1.092] rad ≈ [99°,63°]).
  [verified]

EKB RULES:
- IF you flatten a DOF/batch getter THEN call `.flatten()` before
  indexing BECAUSE batch dims vary (x5 L57-59, x10 L52). [verified]

LIMITS (with cites):
- L1: Joint-limit bar ±170° (scripts/x5_live.py L68). [verified]

UNKNOWN: none material (stdlib-grade). [probable]

## 19. warp

DOES: tensor-array interop check for prim getters. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `isinstance(obj: Any, cls: type) -> bool` — `obj` is
  wp.array|ndarray, `cls` is `wp.array` (x5_live.py L46, x10_live.py
  L51). The duality gate. (Python builtin; `wp.array: type`
  [verified] via import.) [verified]
- F2 `wp.array.numpy() -> np.ndarray` — no params, method on warp
  array (x5_live.py L47, x10_live.py L51). [verified]

KNOBS / EKB: normalization helper `_w` (see Articulation EKB). [verified]

LIMITS (with cites):
- L1: Getters may return `wp.array` or ndarray depending on context —
  always normalize before indexing (x5/x10 `_w` helper). [verified]

UNKNOWN:
- U1: Kernel/device APIs — not used in this pack. [theoretical]

## 20. json (local verifiers)

DOES: evidence receipt + sense-snapshot parsing. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `json.load(fp: TextIO) -> dict[str, Any]` — receipt dict
  (verify_x1.py L15 `_load`; verify_x5–x14 direct
  `EV=...["output"]`). [verified]
- F2 `json.load(open(path: str)) -> dict[str, Any]` — one-liner
  receipt load; `["output"]: str` extracted (verify_x5.py L4 et
  al.). [verified]
- F3 `json.loads(s: str) -> dict[str, Any]` — parses sense snapshot
  nested in `xN_sense.json["output"]` (verify_x1.py L42,
  verify_x2.py L42, verify_x4.py L24). [verified]
- F4 `open(path: str, encoding: str) -> TextIO` — mode default `"r"`
  [probable]; encoding tried in order ("utf-8-sig", "utf-16",
  "utf-8") to survive BOM/UTF-16 prefixes (verify_x1.py L11-18;
  verify_x2/3/4 `_load`). (Python builtin.) [verified]

KNOBS (typed: attr type + unit + default):
- K1 Encoding order `tuple[str, str, str]`, unit n/a, default n/a
  (loader tries all three). Catches BOM chars. Effect: plain utf-8
  open on a BOM file can misparse the first key. [probable]
- K2 Sense-snapshot schema (consumed fields): `prims[]: list[dict]`
  with `path: str`, `type: str`, `pos: list[float]` (m [probable]),
  `quat: list[float]` (unitless), `bbox_min/max: list[float]` (m
  [probable]), `size: list[float]` (m [probable]; mesh reads
  `[1.0,1.0,0.0]`, verify_x4.py L43), `rigid/collision/kinematic:
  bool`, `mass: float` (kg [probable]); `joints[]: list[dict]` with
  `path/type/body0/body1/axis/anchor0_site/anchor1_site: str`;
  top-level `physics_scene: str` (verify_x4.py L50). Defaults
  unproven [theoretical]. Effect: schema drift breaks verifiers.
  [verified]

EKB RULES:
- IF you load a receipt THEN try encodings utf-8-sig → utf-16 → utf-8
  BECAUSE evidence files may carry BOM/UTF-16 prefixes (verify_x2 `_load`
  L9-16; x2 receipts visibly BOM-led). [verified]
- IF you parse a sense snapshot THEN `json.loads(_load(path)["output"])`
  BECAUSE the snapshot is a JSON string nested inside the receipt's
  `output` field (verify_x1 L42, verify_x2 L42, verify_x4 L24). [verified]
- IF a receipt has `status != "ok"` THEN FAIL immediately with
  `status=`/`evalue=` BECAUSE a crashed live run has no report to regex
  (verify_x1 L24-26, verify_x2 L22-24, verify_x3/x4 same). [verified]

LIMITS (with cites):
- L1: BOM/UTF-16-tolerant loader (verify_x1.py L11-18 et al.). [verified]
- L2: Sense schema slices asserted: prim path/type/rigid/mass/size,
  joint type/bodies/sites, physics_scene (verify_x1/x2/x4). [verified]

UNKNOWN:
- U1: Full snapshot schema (only asserted slices read). [theoretical]

## 21. re (local verifiers)

DOES: parse XN-REPORT stdout lines out of receipts. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `re.search(pattern: str, string: str) -> re.Match | None` — two
  families: full-line patterns with 4–7 groups (verify_x1.py L27-28,
  verify_x2.py L25-26, verify_x3.py L25-27) and per-key `f(pat,
  i)`/`b(pat)` helpers (verify_x5–x14). [verified]
- F2 `m.group(i: int) -> str` — 1-based group index; callers
  `float()` it (verify_x1.py L32, verify_x3.py L31-32). [verified]
- F3 Helper `f(pat: str, i: int = 1) -> float` — default i=1
  [verified] (verify_x5.py L6-8 et al.). Returns float or NaN on
  no-match. [verified]
- F4 Helper `b(pat: str) -> bool | None [probable]` — truthy iff
  group(1) == "True" (`m and ...` yields None on no-match;
  verify_x5.py L10-12 et al.). [verified]
- F5 Helper `v3(pat: str) -> tuple[float, float, float]` — 3-group
  pattern; match → float triple, no-match → `(999, 999, 999)` ints
  [verified] (verify_x11.py L16-18, verify_x12.py L17-19,
  verify_x13.py L17-19). [verified]
- F6 Substring checks `needle in haystack` (`needle: str`, `haystack:
  str`) `-> bool` — `"dtype=position" in EV`, `"engine=physx" in EV`,
  `"v12a" in EV` (verify_x9.py L19/L23, verify_x14.py L21,
  verify_x12.py L27-28). Used where exact float parse is
  unnecessary. [verified]

KNOBS (typed: attr type + unit + default):
- K1 Key regexes `pattern: str`, unit n/a, default n/a — e.g.
  `z0=([-\d.]+)`, `q=\[([-\d.]+)`,
  `scF=([-\d.]+),([-\d.]+),([-\d.]+)`; must match the live script's
  printf format EXACTLY. Effect: format drift → no match →
  NaN/False → FAIL. [verified]
- K2 Tolerances `tol: float`, unit = key's unit (m/s/deg per key),
  defaults n/a (per-check literals) — 1e-6 exact (most x5–x14 keys),
  0.02 (x5 bx/bz), 0.05 (x1 z0, x14 zV), 0.1 (x1 z1), 0.2 (x2 |dz|,
  x5 spd), exact-tuple (x11 scF/tD/tF, x12/x13 tA). Effect: tighter
  → flake risk; looser → weak drill. [verified]

EKB RULES:
- IF the report line is missing THEN FAIL with `no report: <first 300
  chars>` BECAUSE the output prefix diagnoses whether the live script
  crashed or changed format (verify_x2 L27-29). [verified]
- IF many keys share one line THEN use `f(pat[, i])`/`b(pat)`/`v3(pat)` per-key
  helpers BECAUSE one bad key then fails its own check instead of
  voiding the whole regex (verify_x5–x14 pattern). [probable]
- IF a key is a fixed token THEN substring-match it BECAUSE float
  parsing adds nothing for `dtype=position` / `engine=physx`
  (verify_x9/x10/x14). [verified]

LIMITS (with cites):
- L1: Missing report = FAIL with output prefix (verify_x1 L29-31,
  verify_x2 L27-29, verify_x3 L28-30). [verified]
- L2: `b()` requires literal "True" (capital T, `%s` of Python bool);
  "true"/"1" would FAIL (verify_x5–x14 `b`). [verified]

UNKNOWN: none material (stdlib-grade). [probable]

## 22. sys (local verifiers)

DOES: verifier exit-code contract (verify_x1–x4 family only). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `sys.exit(code: int) -> NoReturn` — exits 0 on XN-PASS, 1 on
  XN-FAIL (verify_x1.py L55 `sys.exit(main())`; x2/x3/x4 same).
  [verified]
- F2 `main() -> int` — no params; returns 0/1; prints `XN-PASS` or
  `XN-FAIL` + `  - <reason>` lines (verify_x1.py L21/L46-52).
  [verified]

KNOBS: none.

EKB RULES:
- IF a verifier uses fails[] THEN return 1 with every reason printed
  BECAUSE multi-reason output diagnoses compound failures in one run
  (verify_x1 L46-52 pattern). [verified]

LIMITS (with cites):
- L1: Contract visible in verify_x1–x4; verify_x5–x14 instead print
  `PASS `/`FAIL ` per check + `XN-PASS/FAIL` with NO sys.exit call
  (exit code always 0 — a FAIL there does not fail a shell gate!).
  [verified]

UNKNOWN: none material. [probable]

## 23. os (local verifiers, FULLY read)

DOES: file-presence/size gates for stage + render artifacts. [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `os.path.exists(path: str) -> bool` — x1.usd gate (verify_x1.py
  L40) + v6 png gate (verify_x6.py L24). [verified]
- F2 `os.path.getsize(path: str) -> int` — units bytes. Bars: x1.usd
  > 0 (verify_x1.py L40), v6_frame.png > 20000 (verify_x6.py L24),
  v8_viewport/app.png > 20000 each (verify_x8.py L24),
  v13_stage.usd > 0 and v13_view.png > 20000 (verify_x13.py L28-29).
  [verified]

KNOBS (typed: attr type + unit + default):
- K1 Size bars `bytes: int`, unit bytes, values 0 (any non-empty USD)
  / 20000 (real render, not a blank placeholder). Effect: raising
  the png bar risks flakes on small frames; lowering admits blanks.
  [probable]
- K2 Cross-pack `paths: str`, unit n/a, default n/a —
  `rendering-lighting/evidence/v6_frame.png`,
  `viewport-ui/evidence/v8_*.png`, `app-session/evidence/v13_*`.
  Effect: other packs' evidence must exist or the gate FAILs (x6/x8/
  x13 couple to sibling packs). [verified]

EKB RULES:
- IF you gate a render artifact THEN require size > 20000 BECAUSE a
  tiny file means a blank/failed capture, and that bar is proven in
  three drills (verify_x6/x8/x13). [verified]
- IF you gate a saved stage THEN require exists + size > 0 BECAUSE
  save/open round-trips must leave a real file (verify_x1 L40,
  verify_x13). [verified]

LIMITS (with cites):
- L1: verify_x8 calls `os.path.getsize` WITHOUT `exists` — a missing
  png raises instead of FAILing cleanly (verify_x8 "shots exist").
  [verified]

UNKNOWN: none material (stdlib-grade). [probable]

## 24. glob (local verifiers, FULLY read)

DOES: SDG output-file counting (verify_x12 only). [verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `glob.glob(pattern: str) -> list[str]` — (`recursive: bool =
  False` kw never used [probable] stdlib default). Three calls:
  `OUT/rgb_*.npy`, `OUT/sem_*.npy`,
  `OUT/bounding_box_2d_tight_*.npy`, each required `len() == 3`
  (verify_x12.py L29-31). [verified]

KNOBS (typed: attr type + unit + default):
- K1 OUT dir `path: str` (`sdg/base/evidence/v12_out`), unit n/a,
  default n/a. Effect: moved dir → 0 files → FAIL. [verified]
- K2 Counts `3: int` + `3: int` + `3: int`, unitless (file counts).
  Effect: fewer → FAIL (partial SDG run). [verified]

EKB RULES:
- IF you gate an SDG batch THEN count all three writer streams
  separately BECAUSE rgb/sem/bbox come from different writers and any
  one can silently drop (verify_x12 "sdg: 3+3+3 files"). [verified]

LIMITS (with cites):
- L1: Single use in verify_x12 (skimmed listing confirmed import at
  top, `len(glob.glob(pattern)) == 3` x3). [verified]

UNKNOWN: none material (stdlib-grade). [probable]

## 25. python builtins (open/print)

DOES: report emission (print) + sublayer file generation (open).
[verified]

FUNCTIONS (typed; cites = grounding call sites):
- F1 `print(s: str) -> None` — single formatted string (x1_run.py L15
  `print("X1-REPORT ...")`; all live scripts). The ONLY stdout
  contract; one line per live script. [verified]
- F2 `print("X1-BUILD-OK") -> None` — literal str, no params
  (x1_build.py L23). Build-phase sentinel. [verified]
- F3 `open(path: str, mode: str) -> TextIO` — mode `"w"` proven
  (mode default `"r"` [probable]); x3_prec.py L16/L18 writes
  x3_over.usda + x3_overB.usda before composing. [verified]
- F4 `fh.write(s: str) -> int [probable]` — templated USDA string;
  return (char count) never consumed (x3_prec.py L17/L19). The `%s`
  hole selects X3A vs X3B over-target. [verified]

KNOBS (typed: attr type + unit + default):
- K1 printf formats `fmt: str` (`%.2f`, `%.4f`, `%s`, `%d`), unit
  n/a, default n/a — must match verifier regexes. Effect: adding a
  key is safe; changing a format breaks the regex (see re K1).
  [verified]
- K2 OVER template `OVER: str` (USDA text), unit n/a, default n/a —
  `over "World" { over "X3?" { over "Box" { double size = 5 }}}`
  (x3_prec.py L13-15). Effect: any structural change breaks the
  sub==5.0 assertion path. [verified]

EKB RULES:
- IF a live script reports THEN print EXACTLY one XN-REPORT line
  BECAUSE verifiers `re.search` the first match and multi-line output
  only adds noise (all xN receipts show single-line outputs). [verified]
- IF a drill needs fixture files THEN generate them in-script with
  open/write BECAUSE x3_prec self-generates its over-files, keeping
  the drill self-contained (x3_prec L13-19). [verified]

LIMITS (with cites):
- L1: Single-line report outputs in all 14 xN_run.json receipts.
  [verified]

UNKNOWN: none material. [probable]

## 26. XN-REPORT / evidence-harness convention

DOES: pack-level contract gluing live scripts to verifiers. [verified]

FUNCTIONS (convention steps, typed):
- F1 Live scripts `print("XN-REPORT " + kv: str) -> None` — one line,
  `%`-formatted (x1_run.py L15 et al.; see §25 F1). [verified]
- F2 Receipts `evidence/*.json: dict[str, Any]` — shape `{"status":
  str ("ok"|...), "output": str (captured stdout), "result": None}`.
  [verified]
- F3 Receipt variants — same `dict[str, Any]` shape [probable]:
  `x1_build.json` ("X1-BUILD-OK"), `xN_new.json`, `x1_open.json`,
  `x1_save.json`, `xN_sense.json` (nested snapshot: `output: str`
  containing JSON), `x_new0.json` (all status ok, skimmed names +
  x1_build content). [probable]
- F4 Verifiers: `status == "ok" -> bool` gate, then regex the report
  line, exit 0/1 via `sys.exit(code: int)` (x1–x4) or print
  per-check PASS/FAIL strings (x5–x14; exit code always 0).
  [verified]
- F5 Cross-pack evidence reads — `json.load(open(path: str)) ->
  dict` (verify_x6/x8/x13 png/usd via `os.path.getsize(path: str)
  -> int` bytes); verify_x11.py L5-6 reads ros-navigation
  `v11_grid.json` (`grid: list[list[int]] [probable]`, occ==62) +
  `v11_nav.json` (`done: bool`, `arrival: float` m [probable]
  <0.5, `bad: int`==0); verify_x12.py L29-31 counts sdg/base
  `v12_out` npy files (`len(list[str])==3` x3). [verified]

KNOBS (typed: attr type + unit + default):
- K1 `status: str`, unit n/a, required value exactly "ok". Effect:
  anything else → immediate FAIL (verify_x1–x4). [verified]
- K2 `evalue: str | None [probable]`, unit n/a, default None/absent
  [probable] — printed on status FAIL for diagnosis (verify_x1.py
  L25). Effect: informational only. [verified]
- K3 v11 nav bars — grid `occ: int`==62 (unitless count,
  verify_x11.py L20/L31), `done: bool` True, `arrival: float` <0.5
  (m [probable]), `bad: int`==0 (verify_x11.py L32-33). Effect: any
  miss → FAIL (verify_x11). [verified]

EKB RULES:
- IF you add a drill THEN follow print→receipt→verify with a NEW XN
  tag BECAUSE every verifier keys off its own `XN-REPORT` literal and
  tag collision would cross-match (all verify_xN). [probable]
- IF a verifier reads sibling-pack evidence THEN hard-code the
  relative path from repo root BECAUSE all cross-pack reads use
  `action-reasoner/skills/...` root-relative paths (verify_x6/x8/
  x11/x12/x13). [verified]

LIMITS (with cites):
- L1: All 14 xN_run.json receipts `status: ok` with single-line
  reports — the proven-good shape (evidence/*.json skim). [verified]
- L2: Cross-pack coupling: x2_live/x4_build `AddReference()` ABSOLUTE
  Windows paths into modeling-assets; x3 refs stage-core with absolute
  paths — breaks if the workspace moves. [verified]
- L3: verify_x5–x14 never call sys.exit — shell exit code stays 0 even
  on FAIL; only stdout says FAIL. [verified]

UNKNOWN:
- U1: How live scripts are launched into Sim (bridge vs editor) — no
  runner docs in this pack. [theoretical]
- U2: 21 unread evidence files' exact contents (names + shapes only).
  [theoretical]

## 27. Sense-snapshot schema (consumed, not authored here)

DOES: the `xN_sense.json` nested snapshot this pack's verifiers
consume (produced by another pack's sense tool). [verified]

FIELDS READ (typed):
- `prims[]: list[dict]` — `path: str`, `type: str`, `pos:
  list[float]` (m [probable]), `quat: list[float]` (unitless),
  `bbox_min/max: list[float]` (m [probable]), `size: list[float] |
  float` (m [probable]; mesh reads `[1.0,1.0,0.0]`, verify_x4.py
  L43), `rigid/collision/kinematic: bool`, `mass: float` (kg
  [probable]) (x1_sense head skim; verify_x1.py L42-44 / verify_x4.py
  L25/L28 consume path/type/rigid/mass/size). Defaults unproven
  [theoretical]. [verified]
- `joints[]: list[dict]` — `path/type/body0/body1/axis/anchor0_site/
  anchor1_site: str` (verify_x2.py L42-54, verify_x4.py L30-37).
  Defaults unproven [theoretical]. [verified]
- Top-level: `physics_scene: str` path (verify_x4.py L50);
  `prims: list[dict]` + `joints: list[dict]`. [verified]

EKB RULES:
- IF you assert a joint THEN filter by path suffix (`endswith(
  "/shoulder")` or `== "/World/X4Hinge"`) BECAUSE snapshots list every
  joint on stage (verify_x2 L43, verify_x4 L30). [verified]

LIMITS (with cites):
- L1: Only asserted slices read; full schema unproven (see json U1).
  [verified]

UNKNOWN:
- U1: Snapshot producer (which sense tool writes it). [theoretical]
- U2: Unasserted fields beyond the consumed slices. [theoretical]

## Unverified (carried + narrowed)

- Newton/advanced PhysX drill use: none in this pack (no such imports).
- Live-launch path (bridge vs editor): no runner docs in pack.
- Full sense-snapshot schema: only asserted slices read.
- 21 unread evidence files: names/shapes only (all `status: ok` where
  sampled: x1_run/x3_run/x4_run/x5–x14_run/x1_build all ok).
- Any failure modes: no failures.md exists; LIMITS rest on code
  comments + receipt samples, not a curated failure log.
- PROMOTED since TOOLS.md: pxr.Usd (x3_diag/x3_prec FULL), PhysxSchema
  (x7 FULL), os (verify_x1/x6/x8/x13 FULL), glob (verify_x12 FULL),
  UsdLux DistantLight + Camera focal (x6/x8 FULL), is_stopped (x13),
  subLayerPaths save/restore, Clear() root-entry rule, MISSING-guard,
  rival scan, env_ prefix, v11 nav bars, 3+3+3 SDG gate.

## Sources-read

FULL (20): scripts/x1_build.py, x1_run.py, x2_live.py, x3_diag.py,
x3_prec.py, x4_build.py, x5_live.py, x6_live.py, x7_live.py,
x8_live.py, x9_live.py, x10_live.py, x11_live.py, x12_live.py,
x13_live.py, x14_live.py, verify_x1.py, verify_x2.py, verify_x3.py,
verify_x4.py.
SKIMMED: scripts/verify_x5.py, verify_x6.py, verify_x7.py,
verify_x8.py, verify_x9.py, verify_x10.py, verify_x11.py,
verify_x12.py, verify_x13.py, verify_x14.py; evidence/x1_run.json,
x3_run.json, x4_run.json, x5_run.json, x6_run.json, x7_run.json,
x8_run.json, x9_run.json, x10_run.json, x11_run.json, x12_run.json,
x13_run.json, x14_run.json, x1_build.json (full contents),
x1_sense.json (head), x2_run/x2_sense/x5_run/x14_run (via TOOLS.md
prior read); stages/x3_over.usda (full); stages/ + evidence/ dir
listings.
ABSENT (verified missing): SKILL.md, README.md, failures.md,
discovery.md.
