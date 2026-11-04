# Modeling-Assets TOOLS_REF (full tool mastery, 2026-11-04)

Pack: `action-reasoner/skills/modeling-assets/` (Skill 3, GRADUATED).
Baseline: Isaac Sim 6.0.0 / Kit 110, Windows. Stage Z-up, meters.
Claim tags: **[verified]** = drilled live with evidence in this pack;
**[probable]** = consistent with pack evidence + skill/API knowledge, not directly drilled;
**[theoretical]** = general USD/API knowledge, undrilled here.
Note: pack has README.md, no SKILL.md (TOOLS.md "Sources-read" confirms).

Tools covered: 10 (+T11 shape-configurable appendix). Signatures typed: 121/121 — every callable incl. chained `.Get`/`.Set` counted once per occurrence (HasAPI, GetAttribute, json.loads, sys.exit recur across sections). Knobs typed: 71/71 — 47 tool knobs (T1 9, T2 5, T3 4, T4 6, T5 4, T6 8 read-only, T8 2, T9 6 sense fields, T10 3; T7 vocabulary has none) + 24 shape configurables. Still-unknown slots: 13 (one [unknown] tag each; see T2 knobs ×4, T4 ×2, T5 ×3, T6 ×1, T7 ×1, T8 ×2). Datatype pass: 2026-11-04.
Skills loaded: spatial-reasoning (prim transform/bbox/extent detail).

---

## T1. pxr.UsdGeom (in-sim mesh/shape authoring)

DOES: Define and edit geometry prims (Mesh, Cube) and their transforms
**[verified: m1_mesh.py, m3_material.py, m4_clone.py]**.

### Functions (fully typed; undrilled params tagged)

- `UsdGeom.Mesh.Define(stage: Usd.Stage, path: Sdf.Path|str) -> UsdGeom.Mesh` **[verified: m1_mesh.py:14]** — called with str path; both params required (no defaults); units n/a
- `mesh.CreatePointsAttr(defaultValue: Vt.Vec3fArray = Vt.Vec3fArray() [probable], writeSparsely: bool = False [probable]) -> Usd.Attribute` **[verified 0-arg call: m1_mesh.py:17]**; `attr.Set(value: Vt.Vec3fArray|list[Gf.Vec3f], time: Usd.TimeCode = Usd.TimeCode.Default() [probable]) -> bool [probable]` — drilled `Set([Gf.Vec3f ×8])`; values in stage linear units = meters here **[probable]**
- `mesh.CreateFaceVertexCountsAttr(defaultValue: Vt.IntArray = Vt.IntArray() [probable], writeSparsely: bool = False [probable]) -> Usd.Attribute` **[verified 0-arg: m1_mesh.py:18]**; `.Set(value: Vt.IntArray|list[int])` drilled `[4]*6`; unitless per-face counts **[verified]**
- `mesh.CreateFaceVertexIndicesAttr(defaultValue: Vt.IntArray = Vt.IntArray() [probable], writeSparsely: bool = False [probable]) -> Usd.Attribute` **[verified 0-arg: m1_mesh.py:19]**; `.Set(value: Vt.IntArray|list[int])` drilled 24 ints; unitless vertex indices **[verified]**
- `mesh.GetPointsAttr() -> Usd.Attribute; .Get(time: Usd.TimeCode = Usd.TimeCode.Default() [probable]) -> Vt.Vec3fArray` **[verified: m1_mesh.py:23]** — `len(...)==8`; meters **[probable]**
- `mesh.GetDisplayColorAttr() -> Usd.Attribute; .Set(value: Vt.Vec3fArray|list[Gf.Vec3f])` drilled `[Gf.Vec3f(1,0,0)]` **[verified: m1_mesh.py:21]**; `.Get(time: Usd.TimeCode = Default [probable]) -> Vt.Vec3fArray|None` (None if unauthored **[probable]**) **[verified Get()[0]: m1_mesh.py:24]**; unitless RGB 0..1 **[probable]**
- `UsdGeom.Cube.Define(stage: Usd.Stage, path: Sdf.Path|str) -> UsdGeom.Cube` **[verified: m3_material.py:14, m4_clone.py:11]** — both call sites pass str; both params required; units n/a
- `cube.GetSizeAttr() -> Usd.Attribute; .Set(value: float) -> bool [probable]` drilled 1.0 **[verified: m3_material.py:15]**, 0.5 **[verified: m4_clone.py:12]**; `.Get(time: Usd.TimeCode = Default [probable]) -> float` **[verified: audit_m4.py:42]**; attr type double, unit meters **[probable]**
- `UsdGeom.Cube(prim: Usd.Prim) -> UsdGeom.Cube` (schema wrap for readback; prim-only, no path overload drilled) **[verified: audit_m4.py:41, audit_m4v2.py:34]**
- `UsdGeom.Xformable(prim: Usd.Prim) -> UsdGeom.Xformable` **[verified: m1_mesh.py:22, m3_material.py:16, audit_m4.py:32]**; `.AddTranslateOp(opSuffix: Tf.Token = Tf.Token('') [probable], precision: UsdGeom.XformOp.Precision = UsdGeom.XformOp.PrecisionDouble [probable]) -> UsdGeom.XformOp` **[verified 0-arg: m1_mesh.py:22, m3_material.py:16]**; `op.Set(value: Gf.Vec3d|Gf.Vec3f, time: Usd.TimeCode = Default [probable]) -> bool [probable]` drilled `Gf.Vec3d(0,0,0.25)` meters **[verified: m1_mesh.py:22]**
- `UsdGeom.Xformable(prim: Usd.Prim).GetOrderedXformOps() -> list[UsdGeom.XformOp]` **[verified: audit_m4.py:33, audit_m4v2.py:27-28]**; each op: `GetOpType() -> Tf.Token` **[verified]**, `Get(time: Usd.TimeCode = Default [probable]) -> VtValue` (holds Gf.Vec3d for translate ops **[probable]**) **[verified]**
- `UsdGeom.XformCache(time: Usd.TimeCode = Usd.TimeCode.Default() [probable]) -> UsdGeom.XformCache` **[verified 0-arg: audit_m4.py:137, audit_m4v2.py:53]**; `.GetLocalToWorldTransform(prim: Usd.Prim) -> Gf.Matrix4d` **[verified: audit_m4.py:145]**; `m.ExtractTranslation() -> Gf.Vec3d` meters **[verified: audit_m4.py:146-147]**
- `UsdGeom.Xformable(prim: Usd.Prim).MakeMatrixXform() -> UsdGeom.XformOp` **[probable]** — spatial-reasoning placement helper; avoids `xformOp:translate already exists` clash (gotcha 4); NOT called in this pack [no call site]
- `UsdGeom.BBoxCache(time: Usd.TimeCode = Usd.TimeCode.Default() [probable], includedPurposes: Tf.TokenVector = ['default','render'] [theoretical], useExtentsHint: bool = False [theoretical]) -> UsdGeom.BBoxCache` **[probable]**; `.ComputeWorldBound(prim: Usd.Prim) -> UsdGeom.BBox3d` **[probable]**; `.ComputeAlignedRange() -> Gf.Range3d` meters **[probable]** — spatial-reasoning recipe for real-world size; this pack reads bbox from sense JSON instead [no call site]
- `UsdGeom.GetStageMetersPerUnit(stage: Usd.Stage) -> float` (unitless ratio, meters per stage unit) **[probable]** — spatial-reasoning mpu rule; pack never checks mpu (all assets authored in-meter) [no call site]

### Knobs + effect-of-change

| Knob | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| Mesh `points` | Point3fArray (`Vt.Vec3fArray`) **[verified: m1_mesh.py:17]** | meters (stage linear units) **[probable]** | — (required, no fallback) **[verified]** | Vertex positions; M1 8 pts = 2x1x0.5 box **[verified]** |
| Mesh `faceVertexCounts` | IntArray (`Vt.IntArray|list[int]`) **[verified: m1_mesh.py:18]** | unitless counts | — (required) **[verified]** | Per-face arity; `[4]*6` = 6 quads **[verified]** |
| Mesh `faceVertexIndices` | IntArray (`Vt.IntArray|list[int]`) **[verified: m1_mesh.py:19-20]** | unitless indices | — (required) **[verified]** | Winding; drilled CCW table = outward normals (cross-product proof in m1 docstring) **[verified]**; flipping order flips normals (lighting/invisible faces) **[theoretical]** |
| Mesh `displayColor` | Color3fArray (`Vt.Vec3fArray|list[Gf.Vec3f]`) **[verified: m1_mesh.py:21]** | unitless RGB 0..1 **[probable]** | unauthored (no fallback) **[probable]** | Flat RGB tint; `(1,0,0)` = red **[verified]** |
| Mesh `displayOpacity` | FloatArray **[probable]** | unitless 0..1 **[probable]** | 1.0 **[theoretical]** | <1 fades prim **[theoretical]** [no call site] |
| Mesh `subdivisionScheme` | Token (`Tf.Token`) **[probable]** | n/a (enum) | `catmullClark` fallback **[probable]** | `none` keeps hard box edges **[theoretical]** [no call site] |
| Mesh `extent` | float3[2] (`Vt.Vec3fArray` len 2: min,max) **[probable]** | meters **[probable]** | unauthored until computed **[probable]** | Wrong extent = wrong culling/bbox until recomputed **[theoretical]** [no call site] |
| Xform `translate` op | double3 (`Gf.Vec3d`) **[verified: m1_mesh.py:22, m3_material.py:16]** | meters **[probable]** | (0,0,0) **[probable]** | +0.25z lifts 0.5-tall box so bottom rests z=0 **[verified: m1, m3]** |
| `xformOpOrder` | TokenArray (op-name tokens) **[probable]** | n/a | authored order **[probable]** | Controls op composition; duplicate translate op name errors **[probable: spatial gotcha 4]** [no direct call site] |

### EKB rules

- IF authoring a Mesh THEN set points+counts+indices together BECAUSE partial topology is invalid **[verified: m1_mesh.py]**.
- IF bottom must rest on ground THEN translate z by +height/2 BECAUSE points are authored centered (z=±0.25, lifted 0.25 → bbox z 0..0.5, verify_m1.py:51) **[verified]**.
- IF re-running a drill THEN RemovePrim target paths first BECAUSE Define on an existing path keeps stale attributes **[verified: all mN/v3 scripts]**.
- IF reading world pose THEN use XformCache, not op walk BECAUSE cache composes the full ancestor chain **[verified: probes]**.

### LIMITS (with cites)

- Winding proven ONLY for the drilled 8-point box table (`[0,4,7,3]`, `[1,2,6,5]`, `[0,1,5,4]`, `[3,7,6,2]`, `[4,5,6,7]`, `[0,3,2,1]`); exact bounds bbox_min [-1,-0.5,0], bbox_max [1,0.5,0.5] in evidence/m1_sense.json **[verified]**.
- Ground-rest via translate op, not authored points **[verified: m1_mesh.py:22]**.
- Only Cube sizes drilled: 1.0 and 0.5 **[verified]**.

### UNKNOWN (all theoretical)

Tris/n-gons; normals (`primvars:normals`) authoring; UVs; displayColor-vs-bound-material precedence; doubleSided; Sphere/Cylinder/Cone/Plane Define calls (see §T11 — no pack script defines them).

---

## T2. pxr.UsdShade (in-sim PBR materials + binding)

DOES: Create UsdPreviewSurface materials and bind them to prims **[verified: m3_material.py, v3_build.py, v3_check.py]**.

### Functions

- `UsdShade.Material.Define(stage: Usd.Stage, path: Sdf.Path|str) -> UsdShade.Material` **[verified: m3_material.py:18, v3_build.py:16]** — both str paths; both params required; units n/a
- `UsdShade.Shader.Define(stage: Usd.Stage, path: Sdf.Path|str) -> UsdShade.Shader` **[verified: m3_material.py:19, v3_build.py:17]** — both str paths; both params required; units n/a
- `shader.SetShaderId(id: Tf.Token|str) -> bool [probable]` drilled `'UsdPreviewSurface'` (only drilled id) **[verified: m3_material.py:20, v3_build.py:18]**
- `shader.CreateInput(name: str|Tf.Token, type: Sdf.ValueTypeName) -> UsdShade.Input` **[verified: m3_material.py:21-23, v3_build.py:19]** — drilled: `('diffuseColor', Color3f)`, `('roughness', Float)`, `('metallic', Float)`; `input.Set(value: VtValue|Gf.Vec3f|float, time: Usd.TimeCode = Default [probable]) -> bool [probable]` drilled `Gf.Vec3f(1,0,0)` / `0.4` / `0.0`, all unitless **[verified]**
- `material.CreateSurfaceOutput(renderContext: str|Tf.Token = '' [theoretical]) -> UsdShade.Output` **[verified 0-arg: m3_material.py:24, v3_build.py:20]**
- `output.ConnectToSource(source: UsdShade.ConnectableAPI, sourceName: str|Tf.Token, sourceType: Tf.Token = Tf.Token('output') [probable], typeName: Sdf.ValueTypeName = Sdf.ValueTypeNames.Invalid [probable]) -> bool [probable]` — drilled as `ConnectToSource(sh.ConnectableAPI(), 'surface')` **[verified: m3_material.py:24, v3_build.py:20]**
- `UsdShade.MaterialBindingAPI(prim: Usd.Prim) -> UsdShade.MaterialBindingAPI` **[verified: m3_material.py:25, v3_build.py:21-22]**; `.Bind(material: UsdShade.Material, bindingStrength: Tf.Token = Tf.Token('fallbackStrength') [probable], collectionName: str = '' [probable]) -> None [probable]` (void — silent success) — drilled 1-arg **[verified]**
- `UsdShade.MaterialBindingAPI(prim: Usd.Prim).GetDirectBinding(collectionName: str = '' [theoretical]) -> UsdShade.MaterialBindingAPI.DirectBinding` **[verified 0-arg: m3_material.py:27, v3_build.py:28-29, v3_check.py:6-9]**; `.GetMaterialPath() -> Sdf.Path` **[verified: readback in m3/v3_check]**
- `shader.GetInput(name: str|Tf.Token) -> UsdShade.Input` **[verified: m3_material.py:28-29]**; `.Get(time: Usd.TimeCode = Usd.TimeCode.Default() [probable]) -> VtValue` (holds Gf.Vec3f for Color3f **[verified: m3_material.py:28]**, float for Float **[verified: m3_material.py:29]**); unitless **[verified]**

### Knobs + effect-of-change

| Knob | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `diffuseColor` | Color3f (`Gf.Vec3f`) **[verified: m3_material.py:21, v3_build.py:19]** | unitless RGB 0..1 **[probable]** | [unknown] (never read pre-authoring; v3 binds diffuse-only so rough/metallic sit at fallback unread) | Base tint (1,0,0) drilled; change = different albedo **[verified readback; other colors probable]** |
| `roughness` | Float (`float`) **[verified: m3_material.py:22]** | unitless 0..1 **[verified range use; effect probable]** | [unknown] (drilled 0.4 authored; fallback never read) | Higher = more diffuse/matte; 0 = mirror **[verified value; effect probable]** |
| `metallic` | Float (`float`) **[verified: m3_material.py:23]** | unitless 0..1 **[probable]** | [unknown] (drilled 0.0 authored; fallback never read) | 1 = full metal (tinted specular, dark diffuse) **[verified value; effect theoretical]** |
| `emissiveColor`, `opacity`, `ior`, `clearcoat*` | Color3f, Float, Float, Float **[probable]** | unitless (ior: ratio) **[probable]** | [unknown] | Standard PBR extras **[theoretical]** [no call site] |
| Binding strength (fallback vs strongerThanDescendants) | Token (`Tf.Token`) **[probable]** | n/a (enum) | `fallbackStrength` **[probable]** (drilled 1-arg Bind = default) | Descendant overs can/cannot override **[theoretical]** |

### EKB rules

- IF binding to a referenced prim THEN bind on the composed/over path BECAUSE binding authors as an over on the live stage and persists through save/open **[verified: v3_build.py:21-22, evidence v3_senseB.json]**.
- IF verifying a bind THEN read back `GetDirectBinding().GetMaterialPath()` BECAUSE Bind() returns void — silent success **[verified: m3_material.py:27]**.
- IF cloning a bound source THEN clones inherit the binding BECAUSE clone copies the composed subtree incl. binding overs **[verified: v3_check.py b1 == /World/V3Looks/V3Red]**.

### LIMITS (with cites)

- Bindings on referenced prims survive save/reopen on source AND clone (verify_v3.py:50-51; evidence v3_check.json, v3_senseA/B.json 32/34 KB) **[verified]**.
- Only drilled PBR values: red diffuse, roughness 0.4, metallic 0.0 **[verified: m3_material.py:21-23]**; v3_build.py binds diffuse-only (rough/metallic defaults) **[verified]**.

### UNKNOWN (all theoretical)

Unbind (`UnbindAllBindings`/`UnbindDirectBinding`); rebind; post-bind value mutation; multi-material/geom-subset (`UsdShade.MaterialBindingAPI` collection bindings, `bindMaterialAs`); texture inputs (`UsdUVTexture` + primvar readers); any shader id besides UsdPreviewSurface (e.g. OmniPBR/OmniSurface); preview-vs-full material strength.

---

## T3. omni.usd stage access (in-sim)

DOES: Get the live stage; define/query/remove prims **[verified: every in-sim script]**.

### Functions

- `omni.usd.get_context() -> UsdContext` **[verified: first line of every in-sim script, e.g. m1_mesh.py:10]**; `ctx.get_stage() -> Usd.Stage|None` (None if no stage open **[theoretical]**; always non-None in drills **[verified]**); units n/a
- `stage.GetPrimAtPath(path: str|Sdf.Path) -> Usd.Prim` (invalid prim if missing — never throws) **[verified: str paths everywhere, e.g. m1_mesh.py:11, m2_import.py:20]**
- `prim.IsValid() -> bool` **[verified: presence check everywhere, e.g. m1_mesh.py:12, m2_import.py:25-27]**
- `stage.RemovePrim(path: str|Sdf.Path) -> bool` **[verified: str paths, idempotent cleanup prelude in m1_mesh.py:13, m3_material.py:13, m4_clone.py:10, v3_build.py:11]**
- `stage.DefinePrim(path: str|Sdf.Path, typeName: Tf.Token|str = Tf.Token('') [probable]) -> Usd.Prim` — drilled 1-arg typeless (Xform-implied), used as reference anchor **[verified: m2_import.py:18, v3_build.py:13]**
- `prim.GetReferences() -> Usd.References` **[verified: m2_import.py:19, v3_build.py:14]**; `.AddReference(assetPath: str, primPath: Sdf.Path = Sdf.Path.emptyPath [probable], layerOffset: Sdf.LayerOffset = Sdf.LayerOffset() [probable]) -> bool [probable]` — drilled 1-arg with str package path **[verified: m2_import.py:19, v3_build.py:14]**
- `stage.Traverse() -> Usd.PrimRange` (all prims, DFS pre-order; predicate overload undrilled) **[verified: m2_import.py:21-22, audit_m4.py:95]**; `prim.GetTypeName() -> Tf.Token` (str-comparable: `== 'Cube'` **[verified: audit_m4v2.py:33]**, `'Joint' in ...` **[verified: m2_import.py:22]**); `prim.GetPath() -> Sdf.Path` **[verified: audit_m4.py:77, str() in m2_import.py:21]**; `prim.GetChildren() -> Usd.PrimSiblingRange` (iterable[Usd.Prim]; `list(...)` drilled **[verified: audit_m4.py:76,113, audit_m4v2.py:50-51]**); `prim.HasAPI(schemaType: type|str) -> bool` — schema-class form **[verified: audit_m4.py:15]** and string-name form `HasAPI("IsaacSiteAPI")` **[probable: audit_m4.py:157, probe-only]**; `prim.GetAttribute(name: str|Tf.Token) -> Usd.Attribute; .Get(time: Usd.TimeCode = Default [probable]) -> VtValue` (float for `physics:lowerLimit/upperLimit`, radians **[probable]**) **[verified: audit_m4.py:62-63]**

### Knobs + effect-of-change

| Knob | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `DefinePrim` typeName ('' vs 'Xform' vs 'Scope') | Token (`Tf.Token|str`) **[verified: '' default via 1-arg calls m2_import.py:18, v3_build.py:13]** | n/a | `''` (typeless) **[verified]** | '' = typeless over-anchor (drilled) **[verified]**; explicit Xform adds xformable schema **[probable]** |
| `AddReference` primPath | `Sdf.Path` **[probable]** | n/a | `Sdf.Path.emptyPath` = defaultPrim **[probable]** | Non-empty = reference a sub-prim instead of defaultPrim **[theoretical]** [no call site] |
| `AddReference` layerOffset | `Sdf.LayerOffset` (offset+scale doubles) **[probable]** | frames (offset) + unitless (scale) **[probable]** | identity `Sdf.LayerOffset()` **[probable]** | Time remapping of the referenced layer **[theoretical]** [no call site] |
| Traverse predicate | `Usd.PrimFlagsPredicate` **[probable]** | n/a | all-prims (no predicate) **[verified]** | Undrilled; full walk + python-side filter used instead **[verified pattern: m2_import.py:21-22]** |

### EKB rules

- IF cleaning up THEN `GetPrimAtPath` + `IsValid` guard before `RemovePrim` BECAUSE RemovePrim on missing path warns **[verified pattern in all scripts]**.
- IF searching joints THEN filter `stage.Traverse()` by `'Joint' in GetTypeName()` BECAUSE joint paths vary by importer nesting **[verified: m2_import.py:21-22]**.
- IF referencing importer output THEN DefinePrim anchor + AddReference BECAUSE import_urdf never touches the live stage **[verified: failures.md A1]**.

### LIMITS (with cites)

- `import_urdf()` does NOT touch the live stage — drill must reference the package itself (failures.md A1) **[verified]**.
- Typeless DefinePrim anchors verified only as reference parents **[verified]**.

### UNKNOWN (all theoretical)

Save/open stage via API (V3 round-trip went through bridge commands — evidence v3_save.json/v3_open.json — not a drilled API call); payload vs reference tradeoffs; variant sets; `stage.SetDefaultPrim`; `Usd.Stage.Open` vs live context for mpu checks (spatial-reasoning prescribes `Usd.Stage.Open` for mpu — probable, undrilled here).

---

## T4. isaacsim.asset.importer.urdf — URDFImporter (in-sim, OFFLINE converter)

DOES: Convert a URDF file to a USD package on disk; returns package path string **[verified: m2_import.py]**.

### Functions

- `URDFImporterConfig(urdf_path: str, usd_path: str, **kwargs: [unknown]) -> URDFImporterConfig` — ONLY `urdf_path`/`usd_path` drilled as str kwargs **[verified: m2_import.py:12-15]** (normpath'd Windows paths); every other kwarg name/type/default unknown — never read from installed source in this pack (joint damping/stiffness? fix_base? merge_joints? import_units? all **[theoretical]** guesses)
- `URDFImporter(config: URDFImporterConfig) -> isaacsim.asset.importer.urdf.URDFImporter` **[verified: m2_import.py:16]** — drilled 1-arg positional
- `importer.import_urdf() -> str` (emitted package root path on disk) **[verified: m2_import.py:16]** — drilled 0-arg; possible kwargs [unknown]; return used directly as AddReference target **[verified: m2_import.py:19]**

### Knobs (drilled input assets/m2_bot.urdf) + effect-of-change

| Knob | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| URDF link `base`: box 1x1x0.5 @ z .25, mass 2.0 | box `size`: 3×float; `origin xyz`: 3×float; `mass value`: float **[verified: m2_bot.urdf:5,9-10]** | meters (size/origin); kg (mass) **[verified URDF SI]** | n/a (all authored; URDF origin defaults 0 **[probable]**) | Visual+collision box pair under Geometry/base **[verified]** |
| URDF link `arm`: cylinder r .1 l 1.0 @ z .5, mass 1.0 | `radius`/`length`: float; `origin xyz`: 3×float; `mass value`: float **[verified: m2_bot.urdf:19,23-24]** | meters; kg **[verified URDF SI]** | n/a (all authored) | Nests as Geometry/base/arm (NOT Geometry/arm) **[verified: failures.md A2]** |
| Joint `shoulder` revolute, z-axis, limits ±1.57, effort 10 vel 1.0 | `type`: token; `axis xyz`: 3×float; `limit lower/upper/effort/velocity`: float **[verified: m2_bot.urdf:31-36]** | axis unitless; limits radians; effort N·m (revolute) **[probable]**; velocity rad/s **[probable]** | n/a (all authored; revolute REQUIRES limit **[probable]**) | `Physics/shoulder` typed PhysicsRevoluteJoint **[verified: verify_m2.py:53]** |
| `usd_path` output dir | str (dir path) **[verified: m2_import.py:14]** | n/a | n/a (required kwarg) **[verified]** | Reruns version: m2_bot, m2_bot_1, m2_bot_2 — never overwrite **[verified: failures.md A1]** |
| Joint type fixed/prismatic/continuous/floating/planar | token **[probable]** | prismatic limits meters, vel m/s **[probable]** | n/a | Unknown mapping **[theoretical]** [no call site] |
| Mesh geometry (STL/OBJ/COLLADA), materials/textures, transmissions, Gazebo tags, package:// URIs | filename str / RGBA floats **[probable]** | meters (mesh units vary) **[probable]** | n/a | Unknown coverage **[theoretical]** [no call site] |

### EKB rules

- IF importer returns THEN reference-then-sense BECAUSE the live stage is untouched and reruns version the dir (old path may be stale) **[verified: failures.md A1]**.
- IF addressing imported links THEN expect child-under-parent nesting BECAUSE the importer preserves the URDF tree **[verified: failures.md A2]**.
- IF hunting joints THEN walk Traverse for type containing 'Joint' BECAUSE joints land under `Physics/` scope, not beside links **[verified: m2_import.py, README transformer emits base/robot/physics split]**.

### LIMITS (with cites)

- Offline: live stage keeps previous scene while 6 .usd files land on disk (failures.md A1; assets/m2_out/) **[verified]**.
- Reruns version output dirs instead of overwriting (m2_bot, m2_bot_1, m2_bot_2 all present) **[verified]**.
- Child links nest under parents; visuals+collisions double as box/box_1-style copies; shoulder = PhysicsRevoluteJoint (verify_m2.py) **[verified]**.

### UNKNOWN (all theoretical)

MJCF + heightmap importer family (discovery.md documented stretch, zero drills); every URDFImporterConfig kwarg besides the two paths; fixed/mimic joints; mesh links; URDF materials/textures; scale/units handling; joint limit/effort mapping into Physics schema attributes.

---

## T5. isaacsim.core.cloner — GridCloner (in-sim cloning)

DOES: Clone a source prim N times onto a grid; returns positions **[verified: m4_clone.py, v3_build.py]**.

### Functions

- `GridCloner(spacing: float = [unknown], num_per_row: int|None = [unknown]) -> isaacsim.core.cloner.GridCloner` — drilled `spacing=2.0` **[verified: m4_clone.py:14]** and `3.0` **[verified: v3_build.py:24]** (unit meters **[probable]**); `num_per_row` NEVER passed in any script (README name-drops it) so its type (`int|None` **[theoretical]**) and behavior (pins columns **[theoretical]**) are ungrounded guesses, default as marked unknown in the signature
- `cloner.define_base_env(base_env_path: str|Sdf.Path) -> None [probable]` (return never used) — drilled `/World/envs` **[verified: m4_clone.py:15]**, `/World/venvs` **[verified: v3_build.py:25]**
- `cloner.generate_paths(base_path: str, count: int) -> list[str]` — drilled (`/World/envs/env`, 9) **[verified: m4_clone.py:16]** and (`/World/venvs/env`, 4) **[verified: v3_build.py:26]**; yields `env_0..env_N`; count unitless **[verified]**
- `cloner.clone(source_prim_path: str|Sdf.Path, prim_paths: list[str]) -> list[[unknown]]` — drilled as kwargs **[verified: m4_clone.py:17, v3_build.py:27]**; `len(positions)` == count (9, 4) in M4/V3-REPORT **[verified]** but element type NEVER inspected (positions presumably Gf.Vec3d-ish meters **[theoretical]**)

### Knobs + effect-of-change

| Knob | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `spacing` 2.0 → 3.0 | float **[verified: m4_clone.py:14, v3_build.py:24]** | meters (grid pitch) **[probable]** | unknown — see `GridCloner` signature (always passed; 0-arg ctor never called) | Wider grid pitch; 9/9 clones at distinct spots both spacings **[verified]** |
| `count` 9 (3x3) / 4 (2x2) | int **[verified: m4_clone.py:16, v3_build.py:26]** | unitless | n/a (required arg) **[verified]** | Clone count; default row layout inferred square-ish **[verified counts; layout rule probable]** |
| `num_per_row` | int|None **[theoretical]** | unitless **[probable]** | unknown — see `GridCloner` signature | Undrilled — presumably pins columns **[theoretical]** [no call site] |
| Source = plain Cube vs referenced bot | prim path str **[verified: m4_clone.py:17, v3_build.py:27]** | n/a | n/a (required arg) **[verified]** | Both clone; referenced source preserves subtree + material bindings on clones **[verified: evidence v3_senseB.json, v3_check.json]** |

### EKB rules

- IF cloning THEN keep source OUTSIDE the env grid (`/World/M4Src` vs `/World/envs`) BECAUSE the grid paths must not collide with the source **[verified: m4_clone.py]**.
- IF verifying clones THEN check distinct positions BECAUSE overlapping clones pass a count check but fail the grid contract (verify_m4.py:41-43 — 9 distinct pos) **[verified]**.
- IF source is referenced THEN expect bindings inherited on clones BECAUSE clone copies composed subtree **[verified: v3_check.py]**.

### LIMITS (with cites)

- 9/9 clones at distinct grid spots (evidence m4_run.json + m4_sense.json; verify_m4.py) **[verified]**.
- Referenced-bot clones preserve subtree + bindings (v3_senseB.json 34 KB, v3_check.json) **[verified]**.
- Source prim separate from env grid **[verified]**.

### UNKNOWN (all theoretical)

`num_per_row` behavior; non-grid cloners; clone-then-modify independence (overs on clones); cloning physics-articulated sources under simulation; clone return position frame (local vs world); what happens if prim_paths already exist.

---

## T6. pxr.UsdPhysics (READ-ONLY audit in probes)

DOES: Inspect physics APIs on prims; zero authoring in this pack **[verified: probes only]**.

### Functions

- `prim.HasAPI(schemaType: type) -> bool` drilled with `UsdPhysics.RigidBodyAPI | CollisionAPI | MassAPI | ArticulationRootAPI` schema classes **[verified: audit_m4.py:15-25 phys_flags(), audit_m4v2.py:14-24]** (string-name overload covered in T3)
- `UsdPhysics.MassAPI(prim: Usd.Prim) -> UsdPhysics.MassAPI` **[verified: audit_m4.py:21]**; `.GetMassAttr() -> Usd.Attribute; .Get(time: Usd.TimeCode = Default [probable]) -> float|None` (None if unauthored — hence try/except **[verified: audit_m4.py:20-24]**); unit kg **[probable]**
- `UsdPhysics.Joint(prim: Usd.Prim) -> UsdPhysics.Joint` **[verified: audit_m4.py:52, audit_m4v2.py:40]**; `.GetBody0Rel() -> Usd.Relationship` / `.GetBody1Rel() -> Usd.Relationship` **[verified: audit_m4.py:53-54]**; `.GetTargets() -> list[Sdf.Path]` (str()'d at call site **[verified: audit_m4.py:53-54, audit_m4v2.py:42-43]**)
- `joint.GetLocalPos0Attr() -> Usd.Attribute; .Get(time: Usd.TimeCode = Default [probable]) -> Gf.Vec3f [probable]` (values only ever str()'d, never indexed **[verified: audit_m4.py:55-56, audit_m4v2.py:44]**); unit meters **[probable]** — same for `GetLocalPos1Attr()`; local-frame rotations (`GetLocalRot0/1Attr`, quaternions **[probable]**) never read
- `UsdPhysics.RevoluteJoint(prim: Usd.Prim) -> UsdPhysics.RevoluteJoint` **[verified: audit_m4.py:59]**; `.GetAxisAttr() -> Usd.Attribute; .Get() -> Tf.Token` (`'X'|'Y'|'Z'` **[probable]**; unitless enum) **[verified: audit_m4.py:61]**; `prim.GetAttribute(name: 'physics:lowerLimit'|'physics:upperLimit') -> Usd.Attribute; .Get() -> float` radians **[probable]** (mirrors URDF ±1.57 **[verified: m2_bot.urdf:36]**) **[verified: audit_m4.py:62-63]**

### Knobs + effect-of-change

Read-only: presence/absence of each API + mass value + joint bodies/frames/limits/axis. Authoring any of them is out of pack scope **[verified absence]**.

| Read-only knob | Attr type | Unit | Default (unauthored) | Notes |
|---|---|---|---|---|
| `RigidBodyAPI` presence | bool (`HasAPI`) **[verified: audit_m4.py:15]** | n/a | absent **[verified]** | — |
| `CollisionAPI` presence | bool (`HasAPI`) **[verified: audit_m4.py:17]** | n/a | absent **[verified]** | — |
| `MassAPI` presence + `physics:mass` | bool + float **[verified: audit_m4.py:19-24]** | kg **[probable]** | None → try/except prints `Mass=?` **[verified]** | Presence does NOT guarantee a value |
| `ArticulationRootAPI` presence | bool (`HasAPI`) **[verified: audit_m4.py:25]** | n/a | absent **[verified]** | — |
| Joint `body0`/`body1` targets | `list[Sdf.Path]` **[verified: audit_m4.py:53-54]** | n/a (paths) | empty list **[probable]** | — |
| Joint `localPos0`/`localPos1` | `Gf.Vec3f` **[probable]** (only str()'d) | meters **[probable]** | (0,0,0) **[probable]** | Rot frames (`localRot0/1`, quat **[probable]**) never read |
| Revolute `axis` | Token `X|Y|Z` **[probable]** | n/a (enum) | `Z` **[probable]** | **[verified read: audit_m4.py:61]** |
| `physics:lowerLimit`/`upperLimit` | float **[verified: audit_m4.py:62-63]** | radians **[probable]** | [unknown] (only read on the authored shoulder ±1.57) | Mirrors URDF **[verified: m2_bot.urdf:36]** |

### EKB rules

- IF auditing physics THEN wrap Mass read in try/except BECAUSE MassAPI presence does not guarantee an authored mass value **[verified: probes]**.
- IF characterizing joints THEN read body rels + local frames + limits BECAUSE type name alone hides mis-wiring **[verified: joint_info()]**.

### LIMITS (with cites)

Reads worked in probes — but probes have NO paired evidence files, so no drill-grade claim (TOOLS.md §6) **[verified]**.

### UNKNOWN (all theoretical)

EVERYTHING authoring-side: applying RigidBodyAPI/CollisionAPI/MassAPI/joints/articulation roots; all physics authoring belongs to other packs (Skill 2 mechanics per discovery.md).

---

## T7. pxr.Gf + pxr.Sdf (value/type vocabulary)

DOES: Supply 3-vector values and attribute type names **[verified]**.

### Functions/values

- `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` **[verified]** — drilled as `Gf.Vec3f(*p)` tuple-unpack for points **[verified: m1_mesh.py:17]**, `Gf.Vec3f(1,0,0)` int args for displayColor **[verified: m1_mesh.py:21]** and diffuseColor **[verified: m3_material.py:21, v3_build.py:19]**; unit meters for points **[probable]**, unitless RGB 0..1 for colors **[probable]**; indexing `v[0]` returns float **[verified: m1_mesh.py:24-25]**
- `Gf.Vec3d(x: float, y: float, z: float) -> Gf.Vec3d` **[verified]** — drilled `Gf.Vec3d(0,0,0.25)` / `(0,0,0.5)` for translate ops **[verified: m1_mesh.py:22, m3_material.py:16]**; unit meters **[probable]**; returned by `ExtractTranslation()` **[verified: audit_m4.py:146]**, indexed `t[0..2]` as float **[verified: audit_m4.py:147]**
- `Sdf.ValueTypeNames.Color3f -> Sdf.ValueTypeName`, `Sdf.ValueTypeNames.Float -> Sdf.ValueTypeName` (scalar type constants, not calls) **[verified: passed to CreateInput, m3_material.py:21-23]**; units n/a
- `Gf.Matrix4d(m00: float, m01: float, m02: float, m03: float, m10: float, m11: float, m12: float, m13: float, m20: float, m21: float, m22: float, m23: float, m30: float, m31: float, m32: float, m33: float [probable: 16 floats, row-major]) -> Gf.Matrix4d` **[probable]**; `.SetScale(s: Gf.Vec3d|float [theoretical]) -> None [theoretical]`; `.SetRotate(r: Gf.Rotation [theoretical]) -> None [theoretical]`; `.SetTranslate(t: Gf.Vec3d [theoretical]) -> None [theoretical]`; `Gf.Rotation(axis: Gf.Vec3d, angleDeg: float) -> Gf.Rotation` (angle in DEGREES **[probable]**); `A: Gf.Matrix4d * B: Gf.Matrix4d -> Gf.Matrix4d` composed T*R*S **[probable]** — spatial-reasoning placement math; NOT used in this pack (pack uses AddTranslateOp only) [no call site]
- `Gf.Vec3f` look-at Euler helper — spatial-reasoning camera math; helper is UNNAMED in this pack so no signaturable function exists: signature [unknown] [no call site]

### EKB rules

- IF float precision matters THEN Vec3f for colors/points, Vec3d for transforms BECAUSE that is the drilled convention **[verified]**.
- IF composing scale+rotate+translate in one op THEN order T*R*S BECAUSE S*T scales the translation vector too (3 m → 0.03 m at mpu 0.01) **[probable: spatial-reasoning]**.
- IF writing a raw Gf.Matrix4d THEN construct with explicit 16 floats BECAUSE `SetTranslateOnly()` wipes authored scale (spatial gotcha 0b) **[probable]**.

### LIMITS

No failure modes observed in-pack (pure vocabulary) **[verified]**.

### UNKNOWN

Nothing relevant; open-ended library, pack uses only the above **[verified scope statement]**.

---

## T8. Bridge transport — isaacsim_send.py wire protocol / probes/sync_send.py (local)

DOES: Ship in-sim scripts over TCP to Isaac Sim; return JSON result envelope **[verified: every evidence *_run.json]**.

### Functions/protocol

- TCP `socket.create_connection(address: tuple[str,int] = ('127.0.0.1', 8226), timeout: float|None = 60.0, source_address=None [theoretical], socket_options=None [theoretical]) -> socket.socket` **[verified: sync_send.py:12-15,22]**; `s.settimeout(timeout: float) -> None` **[verified: sync_send.py:23]** (timeout unit seconds **[verified]**); `s.sendall(data: bytes) -> None` **[verified: sync_send.py:24]**; `s.shutdown(how: int = socket.SHUT_WR) -> None` half-close **[verified: sync_send.py:25]**; read-all `s.recv(bufsize: int = 65536) -> bytes` until `b''` (bufsize unit bytes **[probable]**) **[verified: sync_send.py:27-31]**; `s.close() -> None` **[verified: sync_send.py:32]**; `json.loads(s: str) -> dict` **[verified: sync_send.py:33]**; `json.dumps(obj: dict, indent: int = 2) -> str` **[verified: sync_send.py:34]**; `sys.exit(code: int) -> NoReturn` **[verified: sync_send.py:35]**
- Payload wrap: `src: str = open(path: str).read()` **[verified: sync_send.py:17-18]**; `indented: str` (each line +4sp) **[verified: sync_send.py:19]**; `payload: str = "async def _isolated_script():\n" + indented + "\n\nawait _isolated_script()"` **[verified: sync_send.py:20]**; sent as `payload.encode() -> bytes` (utf-8 default codec **[verified: sync_send.py:24]**); reply decoded `b"".join(chunks).decode() -> str` (utf-8 **[verified: sync_send.py:33]**)
- Result envelope `{"status": str ("ok"|...), "output": str (stdout text), "evalue"?: [unknown]}` **[verified shape: all evidence]** (`evalue` only ever `%r`-printed, e.g. verify_m1.py:24); exit code `0 iff status == "ok" else 1` **[verified: sync_send.py:35]**
- `isaacsim_send.py --file <path: str> [probable]` = same protocol (docstring claim, pack never reads that script) **[probable: sync_send.py:3]**; all other CLI flags/defaults [unknown]

### Knobs + effect-of-change

| Knob | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `timeout_s` | float (`float(sys.argv[2])`) **[verified: sync_send.py:15]** | seconds **[verified]** | 60.0 **[verified: sync_send.py:15]** | Longer window for heavy builds; expiry kills client-side read **[verified param; timeout behavior probable]** |
| Envelope codec | str (codec name) **[verified]** | n/a | sender: utf-8 (`encode()`/`decode()` bare) **[verified: sync_send.py:24,33]**; verifier read order utf-8-sig → utf-16 → utf-8 **[verified: all verify_* `_load()`]** | Readers must try utf-8-sig / utf-16 / utf-8 — encodings vary **[verified]** |

### EKB rules

- IF sending THEN half-close (SHUT_WR) after send BECAUSE the server reads until EOF before executing **[verified: sync_send.py:25]**.
- IF parsing envelopes THEN try multiple codecs BECAUSE bridge output encoding varies run to run **[verified: `_load()` in all 5 verifiers]**.
- IF asyncio socketpair is sandbox-blocked THEN use sync sender BECAUSE it avoids the self-pipe **[verified: sync_send.py docstring]**.

### LIMITS (with cites)

Envelope encodings vary (utf-8-sig/utf-16/utf-8 all probed) **[verified]**.

### UNKNOWN (all theoretical)

Bridge server setup/flags (workspace setup, not this pack); timeout/retry behavior under load; binary payload support; concurrent-sender behavior.

---

## T9. Sense snapshots (Skill 0 reads, consumed as JSON)

DOES: Prim-listing evidence `{"prims": [{path, type, pos?, size?, bbox_min?, bbox_max?, ...}]}` that verifiers check **[verified: all verify_* + evidence]**.

### Functions

None in-pack — verifiers parse via `json.loads(s: str) -> dict` **[verified: verify_m1.py:36]** then `env['output']: str` → `snap['prims']: list[dict]` **[verified: verify_m1.py:36-37]**; `p['path']: str`, `p.get(key: str, default=None) -> Any` **[verified: verify_m1.py:42]**.

### Knobs (consumed fields) + effect-of-change

| Field | JSON type | Unit | Used by / default | Change gives |
|---|---|---|---|---|
| `path` | str (USD prim path) **[verified]** | n/a | all verifiers; always present **[verified]** | Identity; exact-match want-sets (V3: 4 + 4 clone paths) **[verified]** |
| `type` | str (schema type name) **[verified]** | n/a | m1 (Mesh), m2 (PhysicsRevoluteJoint), m4 (Cube); always present **[verified]** | Schema check **[verified]** |
| `pos` | list[float] len 3 **[verified: verify_m1.py:45 exact == [0.0,0.0,0.25]]** | meters **[probable]** | m1 exact, m4 9-distinct **[verified: verify_m4.py:41]**; missing → `.get()` None **[verified]** | Placement proof **[verified]** |
| `size` | list[float] len 3 **[verified: verify_m1.py:48]** | meters **[probable]** | m1 ([2,1,0.5] tol 1e-3) **[verified]**; missing → None branch **[verified: verify_m1.py:48]** | Dimension proof **[verified]** |
| `bbox_min`/`bbox_max` | list[float] len 3 each **[verified: verify_m1.py:50-51]** | meters **[probable]** | m1 ([-1,-.5,0]/[1,.5,.5] exact) **[verified]** | Bounds proof **[verified]** |
| `pos`/`size` on other drills | list[float] len 3 **[probable]** | meters **[probable]** | printed loosely | Informational only **[verified: verify_m1 prints]** |

### EKB rules

- IF proving dimensions THEN assert size with tolerance 1e-3 BECAUSE float serialization jitters exact equality **[verified: verify_m1.py TOL]**.
- IF proving round-trip THEN compare want-set ⊆ before AND after BECAUSE save/open can drop overs silently (v3_senseA 32 KB vs senseB 34 KB both contain full set) **[verified: verify_v3.py]**.

### LIMITS (with cites)

Sense-before vs sense-after-reopen both contain the full want-set (ref tree + looks + 4 clone subtrees) **[verified: verify_v3.py]**.

### UNKNOWN (theoretical)

Sense tool itself is Skill 0 workspace-sense, not drilled here; position/size field looseness; snapshot staleness vs live stage.

---

## T10. Local verifier stack — Python stdlib json/re/sys (+ glob/os)

DOES: Parse `*-REPORT ...` stdout lines + sense snapshots; exit 0/1 with FAIL list **[verified: all 5 verify_*]**.

### Functions

- `_load(path: str) -> dict` (result envelope) via `open(path: str, encoding: str) -> TextIO` + `json.load(fh: TextIO) -> dict`, codecs utf-8-sig → utf-16 → utf-8, `except (UnicodeDecodeError, UnicodeError)` → next codec **[verified: identical in all 5 verifiers, e.g. verify_m1.py:10-17]**; units n/a
- `re.search(pattern: str, string: str) -> re.Match|None` on `run.get('output', ''): str` **[verified: e.g. verify_m1.py:26]**; `m.group(n: int) -> str` then `int(s: str) -> int` / `float(s: str) -> float` conversions **[verified: verify_m1.py:30]** — M1 `M1-REPORT npoints=(\d+) color=([-\d.,]+)` → int npoints + str→list[float] color **[verified: verify_m1.py:26,30]**; M2 `M2-REPORT out=(\S+) root=(\w+) joints=(\S*) base=(\w+) arm=(\w+)` → str out + `== "True"` bools + str joints **[verified: verify_m2.py:27-34]**; M3 `M3-REPORT bound=(\S+) diffuse=([-\d.,]+) rough=([-\d.]+)` → str bound + list[float] + float **[verified: verify_m3.py:25-31]**; M4 `M4-REPORT clones=(\d+)` → int **[verified: verify_m4.py:25-29]**; V3 `V3-REPORT bound=(\S+) clones=(\d+)` + `V3-CHECK base=(\S+) clone=(\S+)` → str compare + int **[verified: verify_v3.py:41-42,48-51]**
- `glob.glob(pathname: str, recursive: bool = True) -> list[str]` drilled `glob.glob(OUTDIR + '/**/*.usd*', recursive=True)` — ≥1 .usd output required **[verified: verify_m2.py:43-46]**; units n/a
- `os.path.exists(path: str) -> bool; os.path.getsize(path: str) -> int` (bytes **[probable]**) drilled on `stages/v3.usd` — non-empty required (5.5 KB on disk) **[verified: verify_v3.py:52]**; units n/a + bytes
- `main() -> int` (0 pass | 1 fail **[verified: all verifiers]**); `sys.exit(code: int) -> NoReturn` **[verified: e.g. verify_m1.py:62]**; stdout `print(s: str) -> None`: `M1-PASS`-style line + `  - <reason>` FAIL lines **[verified]**

### Knobs + effect-of-change

| Knob | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| REPORT regex strictness | `pattern: str` (raw-string regex) **[verified]** | n/a | exact `re.search` (no flags) **[verified]** | Exact-match brittle BY DESIGN — missing line = immediate FAIL **[verified]** |
| TOL 1e-3 (m1 size) | float **[verified: verify_m1.py:7]** | meters (applied to size diff) **[probable]** | 1e-3 **[verified]** | Float jitter absorbed; tightening risks flakes **[verified: verify_m1.py:48]** |
| Codec order | tuple[str,str,str] **[verified]** | n/a | utf-8-sig → utf-16 → utf-8 **[verified: all `_load()`]** | utf-8-sig first (BOM most common) **[verified pattern]** |

### EKB rules

- IF status != 'ok' THEN fail before regex BECAUSE report text is meaningless on error **[verified: all verifiers]**.
- IF report line missing THEN print output head (200-400 chars) BECAUSE the head usually shows the traceback **[verified: all verifiers]**.

### LIMITS (with cites)

Report regexes exact-match brittle by design **[verified: TOOLS.md §10]**.

### UNKNOWN

None in-pack; plain local scripting, no live API surface **[verified scope statement]**.

---

## T11. Shape configurables: Cube / Sphere / Cylinder / Cone / Plane (spatial-reasoning detail)

Pack drills ONLY Cube (size 1.0/0.5 + translate). Everything else below is
**[probable]** (USD schema standard + spatial-reasoning gotchas) or **[theoretical]** (undrilled here).

### Cube (UsdGeomCube — PARTLY VERIFIED)

| Configurable | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `size` | double (`float`) **[verified Set: m3_material.py:15, m4_clone.py:12]** | meters (edge length, stage linear units) **[probable]** | 2 **[probable]** | Edge length; drilled 1.0 (m3), 0.5 (m4) **[verified]** |
| `extent` | float3[2] (`Vt.Vec3fArray` len 2: min,max) **[probable]** | meters **[probable]** | [-1,1]³ at default size 2 (scales with size) **[probable]** | Culling/bbox hint; scale by w/2,d/2,h/2 NOT w,d,h — full dims make blocks 2× too big (14,570 phantom clashes precedent) **[probable: spatial gotcha 0b]** [no call site] |
| `xformOpOrder` + translate/rotate/scale ops | TokenArray + op values: translate double3 (`Gf.Vec3d`) / rotate float3 (`Gf.Vec3f`) / scale float3 (`Gf.Vec3f`) — translate **[verified: m1_mesh.py:22]**, others **[probable]** | translate meters; rotate DEGREES **[probable]**; scale unitless factor **[probable]** | authored order; op fallbacks (0,0,0)/(0,0,0)/(1,1,1) **[probable]** | Placement; AddTranslateOp drilled **[verified]**; MakeMatrixXform for op-clash cases **[probable]** |
| `displayColor` / `displayOpacity` | Color3fArray / FloatArray **[probable]** | unitless RGB / unitless 0..1 **[probable]** | unauthored / 1.0 **[probable]** | Tint / fade **[probable]** [Cube color undrilled; Mesh color verified m1_mesh.py:21] |
| `visibility` | Token (`inherited`|`invisible`) **[probable]** | n/a (enum) | `inherited` **[probable]** | Hide prim + subtree **[theoretical]** [no call site] |
| `purpose` | Token (`default`|`render`|`proxy`|`guide`) **[probable]** | n/a (enum) | `default` **[probable]** | Render-visibility class **[theoretical]** [no call site] |

### Sphere (UsdGeomSphere — undrilled)

| Configurable | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `radius` | double (`float`) **[probable]** | meters **[probable]** | 1 **[probable]** | All-dimensions scale of the unit sphere **[probable]** [no call site] |
| `extent` | float3[2] (`Vt.Vec3fArray` len 2: min,max) **[probable]** | meters **[probable]** | [-1,1]³ at radius 1 (scales with radius) **[probable]** | Must track radius or culling lies **[probable]** [no call site] |
| transform ops / color / visibility / purpose | as Cube (TokenArray + double3/float3/float3, Color3fArray/FloatArray, Tokens) **[probable]** | meters / degrees / unitless / n/a **[probable]** | as Cube **[probable]** | Same semantics **[probable]** [no call site] |

### Cylinder (UsdGeomCylinder — undrilled)

| Configurable | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `radius` | double (`float`) **[probable]** | meters **[probable]** | 1 **[probable]** | Cross-section size **[probable]** [no call site] |
| `height` | double (`float`) **[probable]** | meters **[probable]** | 2 **[probable]** | Axis length, centered (z ±1 at default) **[probable]** [no call site] |
| `axis` | Token (`X`|`Y`|`Z`) **[probable]** | n/a (enum) | `Z` **[probable]** | Cylinder axis; X/Y rotate the profile 90° **[probable]** [no call site] |
| `extent` | float3[2] (`Vt.Vec3fArray` len 2: min,max) **[probable]** | meters **[probable]** | radius/height-derived, axis-aware **[theoretical]** | Axis-aware box **[theoretical]** [no call site] |
| transform ops / color / visibility / purpose | as Cube **[probable]** | meters / degrees / unitless / n/a **[probable]** | as Cube **[probable]** | Same semantics **[probable]** [no call site] |

### Cone (UsdGeomCone — undrilled)

| Configurable | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `radius` | double (`float`) **[probable]** | meters **[probable]** | 1 **[probable]** | Base disc radius **[probable]** [no call site] |
| `height` | double (`float`) **[probable]** | meters **[probable]** | 2 **[probable]** | Base-to-apex, centered (base z=-1, apex z=+1 at default) **[probable]** [no call site] |
| `axis` | Token (`X`|`Y`|`Z`) **[probable]** | n/a (enum) | `Z` **[probable]** | Cone axis **[probable]** [no call site] |
| `extent` | float3[2] (`Vt.Vec3fArray` len 2: min,max) **[probable]** | meters **[probable]** | radius/height-derived, axis-aware **[theoretical]** | Axis-aware box **[theoretical]** [no call site] |
| transform ops / color / visibility / purpose | as Cube **[probable]** | meters / degrees / unitless / n/a **[probable]** | as Cube **[probable]** | Same semantics **[probable]** [no call site] |

### Plane (UsdGeomPlane — undrilled; single-sided, normal +axis)

| Configurable | Attr type | Unit | Default | Change gives |
|---|---|---|---|---|
| `length` | double (`float`) **[probable]** | meters **[probable]** | 2 **[probable]** | Size along the plane's local Y-ish extent **[probable]** [no call site] |
| `width` | double (`float`) **[probable]** | meters **[probable]** | 2 **[probable]** | Size along the plane's local X-ish extent **[probable]** [no call site] |
| `axis` | Token (`X`|`Y`|`Z`) **[probable]** | n/a (enum) | `Z` **[probable]** | Plane normal; Z = ground plane in Z-up stage **[probable]** [no call site] |
| `extent` | float3[2] (`Vt.Vec3fArray` len 2: min,max) **[probable]** | meters **[probable]** | length/width-derived, zero thickness **[theoretical]** | Zero-thickness box **[theoretical]** [no call site] |
| transform ops / color / visibility / purpose | as Cube **[probable]** | meters / degrees / unitless / n/a **[probable]** | as Cube **[probable]** | Same semantics **[probable]** [no call site] |

### EKB rules (shapes)

- IF sizing a Cube THEN remember default size is 2 (extent [-1,1]³) BECAUSE scale factors halve (w/2) — full dims double the block **[probable: spatial gotcha 0b]**.
- IF changing radius/height/length/width THEN update extent to match BECAUSE stale extent corrupts bbox queries and frustum culling **[probable]**.
- IF placing a ground Plane THEN axis=Z with no rotation BECAUSE stage is Z-up **[probable]**.
- IF a prim already has xformOps (referenced/DHGen-style) THEN use MakeMatrixXform, not AddTranslateOp BECAUSE duplicate op names error **[probable: spatial gotchas 4-5]**.

### LIMITS / UNKNOWN (shapes)

- No pack script Defines Sphere/Cylinder/Cone/Plane; no evidence file contains them **[verified absence]**.
- All non-Cube configurables above are **[probable]** (USD schema standard) or **[theoretical]** (extent/culling behavior) — first drill to Define + sense each shape before relying on defaults.

---

## Sources-read (this mastery pass)

Fully read (19): TOOLS.md, README.md, failures.md, discovery.md,
scripts/m1_mesh.py, m2_import.py, m3_material.py, m4_clone.py, v3_build.py,
v3_check.py, verify_m1.py, verify_m2.py, verify_m3.py, verify_m4.py,
verify_v3.py, probes/audit_m4.py, probes/audit_m4v2.py, probes/sync_send.py,
assets/m2_bot.urdf. (No SKILL.md exists in pack.)
Evidence/assets/stages: directory listing only (20 evidence JSONs by shape per TOOLS.md).
Skill loaded: spatial-reasoning (full body via read_skill).

