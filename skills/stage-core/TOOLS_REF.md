# Stage-Core TOOLS_REF — Exhaustive Tool Reference (2026-11-04)

Claim tags: [verified] = live-drilled green in this pack (S1–S5/V2 evidence) /
[probable] = API knowledge or code inference, not drill-proven here /
[theoretical] = hypothesis only, do not teach as fact.
Sources: SKILL.md absent (README.md is pack doc); README.md, failures.md,
discovery.md FULL; all 8 in-sim scripts + all 6 verifiers FULL (14/14);
skills spatial-reasoning + usd-pipeline loaded via read_skill.
DATATYPE pass (2026-11-04): 78/78 signatures fully typed, 38/38 knobs typed
(attr type + unit + default); 0 bare `(stage, path)` / `(...)` left.

## Tool 1 — omni.usd (UsdContext): live-stage access [verified]

DOES: Returns the running Kit app's live USD stage object to in-sim Python
so every other tool has a stage to author on [verified: s1/s2/s3/s4/s5/v2].

### Functions (2)

1. `omni.usd.get_context() -> UsdContext` [verified]
   - Params: none. Full form takes zero args — no drill passes any
     [verified: 8/8 in-sim scripts call it bare].
   - Returns: `UsdContext` singleton bound to the Kit app [verified].
   - Units/defaults: n/a (no params).
   - Used in: every in-sim script (`import omni.usd` + stage line).
2. `UsdContext.get_stage() -> Usd.Stage | None` [verified]
   - Params: none. Full form takes zero args [verified].
   - Returns: live `Usd.Stage`; `None` if no stage open [probable: None
     case never drilled — every drill runs after a bridge `new`].
   - Call form drilled: `stage = omni.usd.get_context().get_stage()`
     (s1_make_cube.py L5; s2_make_prims.py L5; s2_delete.py L4;
     s3_props.py L5; s4_layers.py L38; s5_comp.py L29; s5_diag.py L16;
     v2_build.py L19).

### Knobs (0)

No knobs: the call chain takes no arguments [verified].

### EKB rules

- IF writing any in-sim script THEN start with
  `stage = omni.usd.get_context().get_stage()` BECAUSE every authoring API
  needs the live stage handle [verified: 8/8 scripts].
- IF `get_stage()` returns None THEN the bridge has no open stage — issue
  `new` first BECAUSE context exists but stage does not without one
  [theoretical: never observed in drills].

### LIMITS (with cites)

- None filed against context access (TOOLS.md: "no failures filed") [verified].

### UNKNOWN (theoretical)

- Headless vs windowed `get_context()` behavior [theoretical].
- Other `omni.usd` helpers (authoring commands, selection API) [theoretical].

## Tool 2 — pxr UsdGeom: typed prims + properties [verified]

DOES: Defines typed geometry prims and authors/reads their shape, transform,
display, visibility, purpose, and custom attributes [verified: s1/s2/s3/v2].

### Functions (31)

Prim definition (6) — shared form
`UsdGeom.<T>.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.<T>`
[verified]: `stage: Usd.Stage` live stage from get_stage() (required, no
default) [verified]; `path: str | Sdf.Path` absolute prim path (required,
no default) — drills pass "/World/..." `str` [verified]; `Sdf.Path`
accepted [probable: no drill passes one]; returns the typed schema object;
`.GetPrim() -> Usd.Prim` recovers the prim [verified]. Units: n/a.

1. `UsdGeom.Cube.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Cube`
   [verified: s1_make_cube.py L6, s2_make_prims.py L11, s3_props.py L9,
   s5_comp.py L20/L24].
2. `UsdGeom.Sphere.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Sphere`
   [verified: s2_make_prims.py L15, v2_build.py L24].
3. `UsdGeom.Cylinder.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Cylinder`
   [verified: s2_make_prims.py L19].
4. `UsdGeom.Cone.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Cone`
   [verified: s2_make_prims.py L24].
5. `UsdGeom.Plane.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Plane`
   [verified: s2_make_prims.py L29].
6. `UsdGeom.Mesh.Define(stage: Usd.Stage, path: str | Sdf.Path) -> UsdGeom.Mesh`
   [verified: s2_make_prims.py L34 hand-authored triangle].

Shape getters (3) — no params; each `-> Usd.Attribute`, then
`.Set(value: float) -> bool [probable]` / `.Get() -> float` [verified]:
7. `Cube.GetSizeAttr() -> Usd.Attribute` — attr `double`, edge length in
   stage units (meters here) [verified: s1_make_cube.py L7 `.Set(1.0)`,
   s3_props.py L11 `.Set(2.0)` + L37 `.Get()`].
8. `Sphere.GetRadiusAttr() -> Usd.Attribute` /
   `Cylinder.GetRadiusAttr() -> Usd.Attribute` /
   `Cone.GetRadiusAttr() -> Usd.Attribute` — attr `double`, meters
   [verified: s2_make_prims.py L16/L20/L25; v2_build.py L25].
9. `Cylinder.GetHeightAttr() -> Usd.Attribute` /
   `Cone.GetHeightAttr() -> Usd.Attribute` — attr `double`, meters
   [verified: s2_make_prims.py L21/L26].

Plane/Mesh creators (5) — drilled no-arg form `Create<Name>Attr()
-> Usd.Attribute` [verified]; full USD form adds
`(defaultValue: Vt.Value [probable], writeSparsely: bool [probable] = False)`
[probable: undrilled]:
10. `Plane.CreateWidthAttr() -> Usd.Attribute` (attr `double`, meters) +
    `.Set(4.0: float)` [verified: s2_make_prims.py L30].
11. `Plane.CreateLengthAttr() -> Usd.Attribute` (attr `double`, meters) +
    `.Set(2.0: float)` [verified: s2_make_prims.py L31].
12. `Mesh.CreatePointsAttr() -> Usd.Attribute` (attr `point3f[]`, meters) +
    `.Set(list[Gf.Vec3f])` [verified: s2_make_prims.py L35 three Vec3f].
13. `Mesh.CreateFaceVertexCountsAttr() -> Usd.Attribute` (attr `int[]`,
    counts, unitless) + `.Set(list[int])` [verified: s2_make_prims.py L36].
14. `Mesh.CreateFaceVertexIndicesAttr() -> Usd.Attribute` (attr `int[]`,
    indices, unitless) + `.Set(list[int])` [verified: s2_make_prims.py L37].

Xform (5):
15. `UsdGeom.Xformable(prim: Usd.Prim) -> UsdGeom.Xformable` — wraps a prim
    [verified: s3_props.py L12 `Xformable(prim)`; s1_make_cube.py L8
    `Xformable(c.GetPrim())`]. No default; units n/a.
16. `Xformable.AddTranslateOp(opSuffix: str = "" [probable],
    precision: UsdGeom.XformOp.Precision [probable] = double [probable])
    -> UsdGeom.XformOp` — drilled bare `AddTranslateOp()` [verified:
    s1_make_cube.py L8, s2_make_prims.py L13/L17/L22/L27/L32/L38,
    s3_props.py L13, v2_build.py L26]; suffix/precision undrilled.
17. `Xformable.AddRotateXYZOp(opSuffix: str [probable] = "" [probable],
    precision: UsdGeom.XformOp.Precision [probable] = float [probable])
    -> UsdGeom.XformOp` — drilled bare `AddRotateXYZOp()` [verified:
    s3_props.py L14].
18. `Xformable.AddScaleOp(opSuffix: str [probable] = "" [probable],
    precision: UsdGeom.XformOp.Precision [probable] = float [probable])
    -> UsdGeom.XformOp` — drilled bare `AddScaleOp()` [verified:
    s3_props.py L15].
19. `XformOp.Set(value: Gf.Vec3d | Gf.Vec3f, time: Usd.TimeCode [probable]
    = Usd.TimeCode.Default() [probable]) -> bool [probable]` —
    translate takes `Gf.Vec3d` in meters [verified: s3_props.py L13
    (1,2,3)]; rotateXYZ takes `Gf.Vec3f` in DEGREES [verified:
    s3_props.py L14 (0,0,90) read back exact]; scale takes `Gf.Vec3f`
    unitless multiplier [verified: s3_props.py L15 (2,1,0.5)];
    time-sample form undrilled [probable]; return flag unchecked.

Display color/opacity (4):
20. `schema.GetDisplayColorAttr() -> Usd.Attribute` — attr `color3f[]`,
    RGB 0-1 unitless, no params [verified: s3_props.py L16/L32,
    v2_build.py L27].
21. `schema.GetDisplayOpacityAttr() -> Usd.Attribute` — attr `float[]`,
    0-1 unitless, no params [verified: s3_props.py L17/L39].
22. `Usd.Attribute.Set(value: list[Gf.Vec3f] | list[float] | float | str |
    list[int]) -> bool [probable]` — color `Set([Gf.Vec3f(1,0,0)])`
    [verified: s3_props.py L16]; opacity `Set([0.5])` [verified: s3 L17];
    scalar `.Set(float)` for size/radius/height/width/length [verified:
    s1 L7, s2 L12/L16/L20-21/L25-26/L30-31, s3 L11]; points
    `.Set(list[Gf.Vec3f])` [verified: s2 L35]; counts/indices
    `.Set(list[int])` [verified: s2 L36-37]; purpose `.Set(str)`
    [verified: s3 L23]; tag `.Set(str)` [verified: s3 L27]. Return flag
    unchecked in drills [probable].
23. `Usd.Attribute.Get(time: Usd.TimeCode [probable] =
    Usd.TimeCode.Default() [probable]) -> tuple | float | str` — arrays
    return tuple/list, drills index `[0]` [verified: s3_props.py L32/L39];
    scalars return `float` [verified: s3 L37, s4_layers.py L43]; tokens
    return `str` [verified: s3 L20/L24].

Imageable (5):
24. `UsdGeom.Imageable(prim: Usd.Prim) -> UsdGeom.Imageable` — wraps prim
    [verified: s3_props.py L18 `Imageable(prim)`]. No default; units n/a.
25. `Imageable.MakeInvisible(time: Usd.TimeCode [theoretical] =
    Default() [theoretical]) -> None [probable]` — drilled bare
    `MakeInvisible()`, sets visibility=invisible [verified: s3_props.py L19].
26. `Imageable.MakeVisible(time: Usd.TimeCode [theoretical] =
    Default() [theoretical]) -> None [probable]` — drilled bare
    `MakeVisible()`, sets visibility=inherited [verified: s3_props.py L21].
27. `Imageable.GetVisibilityAttr() -> Usd.Attribute` — attr `token`, no
    params; `.Get() -> str` verified as "invisible"/"inherited" [verified:
    s3_props.py L20/L22 report + verifier].
28. `Imageable.GetPurposeAttr() -> Usd.Attribute` — attr `token`
    (`uniform token` [probable]), no params on Get;
    `.Set(value: str)`, `.Get() -> str` with "guide"|"render" [verified:
    s3_props.py L23-26].

Prim-level attrs (3):
29. `Usd.Prim.CreateAttribute(name: str, typeName: Sdf.ValueTypeName,
    custom: bool = False [probable], variability: Sdf.Variability
    [probable] = Sdf.VariabilityVarying [probable]) -> Usd.Attribute` —
    drilled `CreateAttribute("master:tag", Sdf.ValueTypeNames.String,
    custom=True)` + `.Set("s3": str)` [verified: s3_props.py L27];
    further optional args beyond variability [probable].
30. `Usd.Prim.GetAttribute(name: str | Tf.Token [probable]) -> Usd.Attribute`
    [verified: s3_props.py L29-31 xformOp reads + L40 tag; s4_layers.py
    L43/L47 "size"; s5_comp.py L33 "size"]. No default; units n/a.
31. `schema.GetPrim() -> Usd.Prim` — no params [verified: s1_make_cube.py
    L8, s2_make_prims.py L13+, s3_props.py L10].

### Knobs (14) + effect-of-change

| # | Knob | Attr type | Unit | Default | Effect of change |
|---|---|---|---|---|---|
| K1 | Cube `size` | `double` [verified] | meters (stage units) [verified] | 2.0 [probable: USD schema default; unset never drilled] | 1.0->bbox [1,1,1]; 2.0->bbox 4 wide w/ scale (s3) [verified] |
| K2 | Sphere/Cyl/Cone `radius` | `double` [verified] | meters [verified] | 1.0 [probable: schema default; unset never drilled] | 0.5->bbox [1,1,1]; Cyl 0.25->bbox x/y 0.5 [verified] |
| K3 | Cylinder/Cone `height` | `double` [verified] | meters [verified] | 2.0 [probable: schema default; unset never drilled] | Cyl 2.0->bbox z 2.0; Cone 1.0->bbox z 1.0 [verified] |
| K4 | Plane width/length | `double` [verified] | meters [verified] | 2.0 / 2.0 [probable: schema defaults] | 4.0/2.0->bbox [4,2,0]; z always 0 [verified] |
| K5 | Mesh points/counts/indices | `point3f[]` / `int[]` / `int[]` [verified] | meters / count / index [verified] | empty x3 [probable: must author all] | Triangle (0,0,0)(1,0,0)(0,1,0)->bbox [1,1,0] [verified] |
| K6 | Translate | `double3` (`Gf.Vec3d`) [verified] | meters [verified] | (0,0,0) [probable: op absent = identity] | s3 (1,2,3) sensed exact [verified] |
| K7 | RotateXYZ | `float3` (`Gf.Vec3f`) [verified] | DEGREES [verified] | (0,0,0) [probable: op absent = identity] | (0,0,90) read back exact; rotates bbox [verified] |
| K8 | Scale | `float3` (`Gf.Vec3f`) [verified] | unitless multiplier [verified] | (1,1,1) [probable: op absent = identity] | (2,1,0.5) x size2 cube -> bbox x[-1..1]*2 [verified] |
| K9 | DisplayColor | `color3f[]` (`list[Gf.Vec3f]`) [verified] | RGB 0-1 unitless [verified] | unauthored = fallback white [probable] | (1,0,0) red; list-of-one form drilled [verified] |
| K10 | DisplayOpacity | `float[]` (`list[float]`) [verified] | 0-1 unitless [verified] | unauthored = fallback 1.0 opaque [probable] | [0.5] read back 0.5 [verified] |
| K11 | Visibility | `token` [verified] | enum string [verified] | "inherited" [probable: schema default] | invisible<->inherited via Make* [verified] |
| K12 | Purpose | `token` [verified] | enum string [verified] | "default" [probable: schema default] | guide/render set+readback exact [verified] |
| K13 | Custom attr | declared `Sdf.ValueTypeName` (`String` drilled) [verified] | per-type | none — must author [verified] | master:tag String "s3" round-trips [verified] |
| K14 | Prim path | `str` (`Sdf.Path` [probable]) [verified] | prim path | none — required [verified] | /World/<Name>; absolute, unique [verified] |

### EKB rules (Tool 2)

- IF sizing a Cube THEN set `size` = full edge length BECAUSE the attr IS
  edge length, not half-extent [verified: README + S2 bbox [1,1,1]].
- IF adding translate+rotate+scale THEN call Add*Op in that order BECAUSE
  drilled order reads back exact via xformOp:translate/rotateXYZ/scale
  [verified: s3]; other orders undrilled [theoretical].
- IF setting color/opacity THEN wrap in a one-element list BECAUSE drilled
  Set takes `[Vec3f]`/`[float]` and Get returns indexable [verified: s3].
- IF hiding a prim temporarily THEN use MakeInvisible/MakeVisible BECAUSE
  they round-trip invisible<->inherited exactly [verified: s3].
- IF tagging a prim THEN CreateAttribute(name, String, custom=True) BECAUSE
  the custom flag + String type round-trip reads back [verified: s3].
- IF authoring a Mesh THEN set points AND counts AND indices BECAUSE all
  three were required for the valid sensed triangle [verified: s2].
- IF rotating THEN always AddRotateXYZOp, never per-axis ops BECAUSE the
  spatial-reasoning skill mandates XYZ-only (per-axis op conflicts)
  [probable: skill rule, not drill-proven in this pack].
- IF a prim already has xformOps and AddTranslateOp errors THEN use
  MakeMatrixXform instead BECAUSE re-adding an existing op name fails
  [probable: spatial-reasoning gotcha 4, undrilled here].

### LIMITS (Tool 2, with cites)

- Cube size IS edge length (README verified fact) [verified].
- Purpose render/proxy needs explicit bbox query purposes on sense side
  (README verified fact; sense V1 probe fix) [verified].
- Torus named in discovery goals but Mesh drilled instead — Torus NOT proven
  (TOOLS.md UNKNOWN) [verified-absent].
- Only default-time opinions drilled; time-sampled authoring unproven
  (TOOLS.md UNKNOWN) [verified-absent].

### UNKNOWN (Tool 2, theoretical)

- Other gprim types (Torus, TorusKnot), extent/double-sided Imageable attrs
  [theoretical]. Time-sampled property authoring [theoretical]. All other
  UsdGeom schema APIs [theoretical].

## Tool 3 — pxr Usd/Sdf: stage, layers, composition, variants, payloads

DOES: Stage/layer management, prim lookup/deletion, sublayer stacking,
external asset authoring, references, variants, payloads, diagnostics, and
text USDA authoring [verified: s2/s3/s4/s5/v2].

### Functions (30)

Lookup/create/delete (3):
1. `stage.GetPrimAtPath(path: str | Sdf.Path) -> Usd.Prim` [verified:
   s2_make_prims.py L7 `str`; s3_props.py L6; s4_layers.py L42;
   s5_comp.py L14/L32/L39; s5_diag.py L11/L15/L17]. No default; units
   n/a. Returns possibly-INVALID prim (not None) — check `.IsValid()`
   before use [verified: s2_make_prims.py L8].
2. `stage.DefinePrim(path: str | Sdf.Path, typeName: str | Tf.Token
   [probable] = "" [probable]) -> Usd.Prim` — typeless
   `DefinePrim("/World/S5Ref")` / `DefinePrim("/World/S5Pay")` [verified:
   s5_comp.py L30/L37] and `DefinePrim("/World/V2Widget")` [verified:
   v2_build.py L29]; typed `DefinePrim("/Widget", "Xform")` on the asset
   stage [verified: s5_comp.py L13]. Default "" = no type [probable].
3. `stage.RemovePrim(path: str | Sdf.Path) -> bool [probable]` [verified:
   s2_make_prims.py L9, s2_delete.py L9, s3_props.py L8 — all pass `str`;
   return value never checked in drills]; deletes composed prim incl.
   opinions [probable].

Layers (3):
4. `stage.GetRootLayer() -> Sdf.Layer` — no params [verified:
   s4_layers.py L39, s5_comp.py L27 via ast, v2_build.py L20].
5. `Sdf.Layer.subLayerPaths: list[str]` (read/write property) — get
   returns `list[str]` of layer asset paths [verified: s4_layers.py L40
   `list(root.subLayerPaths)`]; set replaces the WHOLE list, no append
   [verified: s4_layers.py L41/L44-45/L49/L53, v2_build.py L21-22].
   Element: `str` file path (absolute C:/... drilled); units n/a.
6. `Sdf.Layer.Save(force: bool [probable] = False [probable]) -> bool
   [probable]` — drilled bare `Save()` persisting the .usda asset
   [verified: s5_comp.py L27 `ast.GetRootLayer().Save()`]; args and
   return unchecked in drills.

Asset stages (2):
7. `Usd.Stage.CreateNew(identifier: str) -> Usd.Stage` — drilled
   single-arg with absolute .usda path `str` [verified: s5_comp.py L12
   `CreateNew(ASSET)`]; further optional load-args undrilled
   [theoretical]. Units n/a.
8. `Usd.Stage.Open(identifier: str) -> Usd.Stage` — drilled single-arg
   `Open(P)` [verified: s5_diag.py L6 `Open(P)`]; further optional args
   undrilled [theoretical]. Units n/a.

Diagnostics (5):
9. `stage.GetDefaultPrim() -> Usd.Prim` (invalid-prim when unset, NOT None
   [probable]) — no params [verified: s5_diag.py L9-10
   `dp.GetPath() if dp else None` truthiness check];
   `stage.SetDefaultPrim(prim: Usd.Prim) -> None [probable]` [verified:
   s5_comp.py L13 `SetDefaultPrim(ast.DefinePrim("/Widget", "Xform"))`;
   return unused]; verifier greps `defaultPrim` in file
   [verified: verify_s5.py L47].
10. `prim.HasAuthoredReferences() -> bool` — no params [verified:
    s5_diag.py L20 True case].
11. `prim.GetChildren() -> list[Usd.Prim]` — no params [verified:
    s5_diag.py L22 iterated for refchildren].
12. `prim.GetPath() -> Sdf.Path` — no params [verified: s5_diag.py L10
    `dp.GetPath()`, L22 `str(c.GetPath())`].
13. `prim.IsValid() -> bool` — no params [verified: s2_make_prims.py L8,
    s3_props.py L7, s5_comp.py L39/L41/L43, s5_diag.py L12/L18].

Variants (7):
14. `prim.GetVariantSets() -> Usd.VariantSets` — no params [verified:
    s5_comp.py L15/L34, s5_diag.py L14/L23, v2_build.py L31].
15. `Usd.VariantSets.AddVariantSet(name: str) -> Usd.VariantSet`
    [verified: s5_comp.py L15 "config"]. No default; units n/a.
16. `Usd.VariantSet.AddVariant(name: str) -> None [probable]` [verified:
    s5_comp.py L16-17 "small"/"large"; return unused in drills].
17. `Usd.VariantSet.SetVariantSelection(name: str) -> bool [probable]`
    [verified: s5_comp.py L18/L22/L26 small->large->small cycle + L34
    on the referencing prim; return unchecked].
18. `Usd.VariantSets.GetVariantSet(name: str) -> Usd.VariantSet`
    [verified: s5_comp.py L34 referencing-prim side, v2_build.py L31].
19. `Usd.VariantSets.GetNames() -> list[str]` — no params [verified:
    s5_diag.py L14/L23 diagnose-before-reference].
20. `Usd.VariantSet.GetVariantEditContext() -> ContextManager[None]` —
    no params, takes NO name arg; edits the SELECTED variant [verified:
    README fact; s5_comp.py L19/L23 with-blocks].

References/payloads/load (4):
21. `prim.GetReferences() -> Usd.References` — no params [verified:
    s5_comp.py L31, v2_build.py L30];
    `Usd.References.AddReference(assetPath: str) -> bool [probable]` —
    drilled single-arg with absolute .usda path `str` [verified:
    s5_comp.py L31, v2_build.py L30]; no primPath arg drilled —
    defaultPrim routing [probable]; further optional args undrilled
    [theoretical]. Return unchecked.
22. `prim.GetPayloads() -> Usd.Payloads` — no params [verified:
    s5_comp.py L38];
    `Usd.Payloads.AddPayload(assetPath: str) -> bool [probable]` —
    drilled single-arg [verified: s5_comp.py L38]; further optional
    args undrilled [theoretical]. Return unchecked.
23. `stage.Unload(path: Sdf.Path) -> None [probable]` [verified:
    s5_comp.py L40 `Unload(Sdf.Path("/World/S5Pay"))`; Box invalid
    after]. Target = payload root; children follow. Return unused.
24. `stage.Load(path: Sdf.Path) -> None [probable]` [verified:
    s5_comp.py L42 `Load(Sdf.Path("/World/S5Pay"))`; Box valid again].

Property stack/time (2):
25. `attr.GetPropertyStack(time: Usd.TimeCode) -> list[Sdf.PropertySpec]`
    [verified: s4_layers.py L47-48/L51-52
    `GetPropertyStack(Usd.TimeCode.Default())`, indexed `[0: int]`,
    `[0].layer -> Sdf.Layer`, `.GetDisplayName() -> str` proves the
    winning layer]. `time` required positional, no default drilled
    [probable].
26. `Usd.TimeCode.Default() -> Usd.TimeCode` — no params [verified:
    s4_layers.py L48/L52 query time].

Tokens/paths/removal (2):
27. `Sdf.Path(pathString: str) -> Sdf.Path` [verified: s5_comp.py L40/L42
    `Sdf.Path("/World/S5Pay")`]; `Sdf.ValueTypeNames.String: Tf.Token
    [probable]` is a CONSTANT, not a call [verified: passed as the
    CreateAttribute typeName in s3_props.py L27]. Units n/a.
28. `Usd.Attribute.Clear() -> bool [probable]` — no params. Value falls
    through BUT root keeps a property-stack entry with authored=True
    [verified: failures.md L5; no in-pack script call site — signature
    [probable]].

Text USDA authoring (2):
29. `open(file: str, mode: str = "r" [probable], encoding: str | None
    [probable] = None [probable]) -> TextIO; TextIO.write(text: str)
    -> int` — drilled `open(STAGEDIR + "s4_base.usda", "w").write(
    BASE_USDA: str)` [verified: s4_layers.py L33-36; v2_build.py L10-17
    same "w" form]; readback drilled with explicit `encoding="utf-8"`
    [verified: verify_s4.py L48-49]. Base layers use `def Xform/Cube`
    blocks with size+translate+xformOpOrder; overrides use `over` blocks
    with size only [verified: s4_layers.py L12-31 literals; files on
    disk re-read].
30. Machine-emitted USDA trusted FORM (file grammar, not a callable):
    `prepend variantSets = "config"` (prim metadata, `str`) +
    `variantSet "config" = { "small" {...} "large" {...} }` [verified:
    stages/s5_widget.usda on disk; failures.md L3 cites URDF converter
    output]. Params/return n/a.

### Knobs (12) + effect-of-change

| # | Knob | Type | Unit | Default | Effect of change |
|---|---|---|---|---|---|
| K1 | Prim path in lookup/define/remove | `str \| Sdf.Path` [verified] | prim path | none — required [verified] | Wrong path -> invalid prim; remove needs exact path [verified] |
| K2 | subLayerPaths list order | `list[str]` [verified] | index 0 = strongest | session list — save first [verified] | Override must precede base [verified: s4] |
| K3 | subLayerPaths save/restore | `list[str]` copy [verified] | n/a (pattern) | n/a | Forgetting restore leaks stack into later drills [verified: s4 pattern] |
| K4 | Asset file path (CreateNew/Open/ref) | `str` absolute path [verified] | file path | none — required [verified] | Absolute C:/... drilled; relative undrilled [verified/probable] |
| K5 | DefaultPrim selection | `Usd.Prim` [verified] | prim ref | unset = invalid prim [probable] | Unset -> reference may route wrong; set to /Widget [verified] |
| K6 | Variant set/variant names | `str` [verified] | name token | none — required [verified] | Must match file ("config"/small/large) or selection fails [verified] |
| K7 | Selected variant | `str` [verified] | name token | authored selection ("small" here) [verified: s5_comp.py L26] | small->size 1.0, large->size 4.0 composed under ref [verified] |
| K8 | Reference vs payload arc | API choice (`GetReferences` \| `GetPayloads`) [verified] | n/a | n/a | Ref always loaded; payload unloadable (valid/invalid cycle) [verified] |
| K9 | Load/Unload target path | `Sdf.Path` [verified] | prim path | none — required [verified] | Must be payload root (/World/S5Pay); children follow [verified] |
| K10 | def vs over in USDA | keyword [verified] | n/a | n/a | def creates spec; over only overrides existing [verified: s4 files] |
| K11 | xformOpOrder in USDA | `uniform token[]` (`list[str]`) [verified] | op-name list | none — must author [verified] | Missing -> translate may not apply; always author it [verified: base] |
| K12 | TimeCode for stack query | `Usd.TimeCode` [verified] | time | `Default()` drilled [verified] | Default() drilled; other times undrilled [verified/theoretical] |

### EKB rules (Tool 3)

- IF testing an override THEN put the base in a weaker sublayer, never as
  root direct opinions BECAUSE a layer's own opinions always beat its
  sublayers [verified: failures.md L2, s4 v1 failure -> v2 recovery].
- IF stacking sublayers THEN save paths first, prepend, and restore after
  BECAUSE assignment replaces the whole list and leaks otherwise [verified].
- IF proving which layer wins THEN read `[0].layer.GetDisplayName()` of
  GetPropertyStack(Default()) BECAUSE display name identifies override vs
  base file [verified: s4].
- IF authoring variants THEN use the UsdVariantSets API, never hand-written
  `variantSet` USDA BECAUSE hand text fails two ways (silent drop / invalid
  Sdf) [verified: failures.md L3].
- IF referencing an asset THEN SetDefaultPrim on it + GetNames() diagnosis
  before referencing BECAUSE routing + set names must exist to compose
  [verified: s5_comp/s5_diag].
- IF switching a variant on a referencing prim THEN GetVariantSet(name) on
  THAT prim + SetVariantSelection BECAUSE selection is authored on the
  referring prim, not the asset [verified: s5_comp line 34].
- IF removing an opinion THEN prefer RemoveProperty or case-per-prim, NEVER
  Clear()-as-removal BECAUSE Clear leaves a root stack entry authored=True
  [verified: failures.md L5].
- IF opening any asset to inspect THEN use Usd.Stage.Open, never
  Sdf.Layer.FindOrOpen BECAUSE Sdf fails silently on binary .usd crates
  [probable: both loaded skills agree; undrilled in this pack].
- IF placing a referenced asset THEN read its metersPerUnit and correct
  scale/offset BECAUSE mixed-unit assets land 100x off or meters away
  [probable: spatial-reasoning + usd-pipeline; undrilled in this pack].
- IF pre-cleaning THEN GetPrimAtPath + IsValid + RemovePrim BECAUSE Define
  over an existing prim keeps stale opinions [verified: s2/s3 pattern].

### LIMITS (Tool 3, with cites)

- Root direct > sublayers; base must live weaker (failures.md L2) [verified].
- Chain Direct > Sublayer > Reference; root sublayer over BEATS reference
  value; doc line "Sublayers < Reference" corrected (failures.md L4) [verified].
- Hand `variantSet` USDA fails both ways; declare + `=` form or API; parse
  warnings don't fail sends so verify composed prims exist (L3) [verified].
- Clear() leaves root stack entry authored=True; cause OPEN (L5) [verified].
- GetVariantEditContext edits SELECTED variant, no name arg (README) [verified].

### UNKNOWN (Tool 3, theoretical)

- RemoveProperty as true removal [theoretical]. Sublayers inside referenced
  assets [theoretical]. over-vs-def beyond proven pattern [theoretical].
- Nested variant sets; CreateInMemory vs file-backed [theoretical].

## Tool 4 — isaacsim_send.py bridge: stage ops + exec + sense

DOES: Drives stage lifecycle from outside Sim (fresh stage, save .usd,
reopen, in-sim script exec) and reads stage state back via Skill 0 sense
[verified: evidence envelopes s1_newA/B, s2_new, s3_new, s4_new, s5_new,
v2_new/new2, s1/v2 save+open, sN_run, sN_sense JSONs]. NOTE: bridge script
file itself not found in workspace (searched depth-3) — op semantics below
are inferred from evidence envelopes + verifier parsing [probable].

### Functions (5)

Envelope type (all ops): `dict{status: str, output: str, evalue: str}`
[probable: bridge file not in workspace; keys proven by verifier parsing,
e.g. verify_s1.py L22/L33-34, verify_s3.py L23-29].

1. `new() -> envelope` — no params [probable: no evidence shows args].
   Result: 12-prim template (World, Render scope, 4 cameras, no lights)
   [verified: README + verifiers + evidence s1_newA/B, s2_new, s3_new,
   s4_new, s5_new, v2_new/new2].
2. `save(path: str) -> envelope` [probable] — `path: str`
   workspace-relative .usd path (e.g. "stages/s1.usd"); no default; units
   n/a. Writes .usd to disk (stages/s1.usd 4595B, v2.usd 4945B on disk)
   [verified: evidence s1_save.json/v2_save.json]; verifier asserts
   status ok + file exists + nonzero [verified: verify_s1.py L40-45,
   verify_v2.py L59-64].
3. `open(path: str) -> envelope` [probable] — `path: str` same form as
   save; reopens saved .usd; Kit auto-adds 4-prim viewport light rig
   [verified: failures.md L1; evidence s1_open.json; verify_s1.py
   L56-63 path-set check].
4. `exec(script: str) -> envelope` [probable] — `script: str`: in-sim
   python source text (or a script path `str` [theoretical: transport
   form undetermined, bridge file not in workspace]); no default.
   `output: str` free text; scripts print `*-REPORT`/`*-OK` markers
   parsed by regex [verified: verify_s3.py L26-29, verify_s4.py L26-27,
   verify_s5.py L26-27].
5. `sense() -> envelope` — no params [probable]; `output: str` is a JSON
   STRING `json.dumps({prims: list[dict{path: str, type: str,
   pos: list[float] meters, size: list[float] meters,
   bbox_min: list[float] meters, bbox_max: list[float] meters}]})`
   [verified: verifier parsing in verify_s1.py L24/L54, verify_s2.py
   L31/L49-58, verify_s3.py L58-70, verify_v2.py L30/L34-46].

### Knobs (4) + effect-of-change

| # | Knob | Type | Unit | Default | Effect of change |
|---|---|---|---|---|---|
| K1 | new vs open | op selector, both no-params [probable] | n/a | n/a | new=12 clean prims; open=+content+4 rig prims [verified] |
| K2 | save/open path | `str` workspace-relative .usd path [probable] | file path | none — required [probable] | .usd binary drilled; .usda round-trip undrilled [verified/theoretical] |
| K3 | exec script content | `str` python source (or path [theoretical]) [probable] | n/a | none — required [probable] | Must print parseable REPORT/OK markers [verified] |
| K4 | Post-open assertions | `set[str]` path-set compare [verified] | n/a | n/a (verifier-side) | Assert by path-set, never raw count [verified: L1] |

### EKB rules (Tool 4)

- IF asserting across save/open THEN compare path-sets (fresh set + new
  prim + LightRig extras) BECAUSE open injects 4 rig prims [verified: L1,
  verify_s1 lines 56-63].
- IF parsing exec output THEN regex the REPORT marker BECAUSE envelope
  output is free text + status/evalue keys [verified: verifiers].
- IF parsing sense THEN json.loads(env["output"]) then walk ["prims"]
  BECAUSE output is a JSON string inside the envelope [verified].
- IF reading bridge JSON THEN try encodings utf-8-sig/utf-16/utf-8 BECAUSE
  Windows bridge output has BOM variants [verified: _load in 6/6 verifiers].

### LIMITS (Tool 4, with cites)

- Open auto-adds /OmniKit_Viewport_LightRig (DomeLight + DistantLight);
  fresh new has no lights; open scenes never unlit (L1) [verified].
- Fresh new template = exactly 12 prims (README) [verified].

### UNKNOWN (Tool 4, theoretical)

- Save/open with unsaved sublayer edits; .usd vs .usda round-trip;
  bridge ops beyond new/save/open/exec/sense [theoretical].

## Tool 5 — verify_sN/verify_v2 local evaluators (stdlib-only)

DOES: Local pass/fail evaluation of each drill from bridge/sense JSON
evidence; exit 0 + `*-PASS` on pass, exit 1 + `*-FAIL` + reasons [verified:
all 6 read FULL this pass — prior TOOLS.md skim-only note superseded].

### Functions (10: 6 mains + 4 shared helper patterns)

1. `verify_s1.main() -> int` — no params [verified: verify_s1.py
   L27-70; `sys.exit(main())` L73; returns 0 + "S1-PASS" on pass, 1 +
   "S1-FAIL" + reasons]. Round-trip: save/open ok, s1.usd exists+nonzero,
   fresh A/B lack S1Cube, reopened has it pos [1,2,0.5] size [1,1,1],
   pathsB <= pathsC, extras all under LightRig [verified: 73 lines].
2. `verify_s2.main() -> int` — no params [verified: verify_s2.py L34-69;
   exit 0/1 same contract]. EXPECT 6 paths w/ type+size (TOL 1e-3),
   created = base+6, deleted = base, no leftovers [verified: 72 lines].
3. `verify_s3.main() -> int` — no params [verified: verify_s3.py L20-77].
   Regex S3-REPORT 12 fields exact (tr/rot/sc/size/color/vis1+2/pur1+2/
   op/tag), sense pos [1,2,3], bbox_min [0,0,2.5], bbox_max [2,4,3.5]
   TOL 1e-3 [verified: 80 lines].
4. `verify_s4.main() -> int` — no params [verified: verify_s4.py L20-61].
   Regex S4-REPORT base 1.0/over 3.0/stack0 has s4_override/reverted
   1.0/stack1 has s4_base + file content greps (override: S4Cube,3,over;
   base: S4Cube,def Cube) [verified: 64 lines].
5. `verify_s5.main() -> int` — no params [verified: verify_s5.py L20-55].
   Regex S5-REPORT small 1.0/large 4.0/loaded+gone+back True + asset
   greps variantSet+defaultPrim [verified: 57 lines].
6. `verify_v2.main() -> int` — no params [verified: verify_v2.py L49-73].
   EXPECT 3 paths (VBase Cube pos [0,0,0.5] size 2.5; V2Direct Sphere;
   V2Widget/Box Cube size 4.0, pos unchecked None), checked on BOTH built
   + reopened snaps + save/open ok + v2.usd nonzero [verified: 76 lines].
7. `_load(path: str) -> dict` — BOM-tolerant JSON load; tries
   `encodings: tuple[str, str, str] = ("utf-8-sig", "utf-16", "utf-8")`
   then a final plain utf-8 load [verified: identical in 6/6, e.g.
   verify_s1.py L10-17]. `path`: evidence-file path `str`, no default.
8. `_snap(name: str) -> dict` — `name`: evidence filename `str` (e.g.
   "s1_senseA.json"), loaded as EVDIR+name; raises `RuntimeError` unless
   `status == "ok"`; returns `json.loads(output: str) -> dict`
   [verified: verify_s1.py L20-24, verify_s2.py L27-31, verify_v2.py
   L26-30]. NOTE s3/s4/s5 inline this pattern instead of defining _snap
   [verified: verify_s3.py L22/L58, verify_s4.py L22, verify_s5.py L22].
9. `_check(snap: dict, tag: str, fails: list[str]) -> None` — `snap`:
   parsed sense dict; `tag`: "built"/"reopened" label `str`; `fails`:
   mutable error list appended in place, no return [verified:
   verify_v2.py L33-46 EXPECT-map helper: type exact, pos exact unless
   None, size TOL].
10. `sys.exit(main())` — stdlib `sys.exit(code: int) -> NoReturn`
    [verified: last line of 6/6 verifiers]; exit-code contract 0/1.

### Knobs (8 assertion knobs) + effect-of-change

| # | Knob | Type | Unit | Default | Effect of change |
|---|---|---|---|---|---|
| K1 | TOL | `float = 1e-3` [verified: verify_s2.py L6, verify_s3.py L7, verify_v2.py L8] | compare slop, same unit as values | 1e-3 | Float zip-compare slop; exact == for tokens/ints [verified] |
| K2 | EXPECT maps | `dict[str, tuple]` [verified] | n/a | per-file literal [verified] | Path->type/size/pos truth tables; edit when drill changes [verified] |
| K3 | REPORT regexes | `str` pattern [verified] | n/a | per-file literal [verified] | Must match script print format exactly or "no report" fail [verified] |
| K4 | status=="ok" gates | `str` compare [verified] | n/a | "ok" [verified] | Any non-ok envelope fails fast before assertions [verified] |
| K5 | Path-set inclusion (s1) | `set[str]` [verified: verify_s1.py L56-60] | n/a | n/a | pathsB<=pathsC; LightRig-only extras allowed [verified] |
| K6 | File greps (s4/s5) | `tuple[str, ...]` wanted tokens [verified] | n/a | per-file literal [verified] | USDA text must contain marker tokens [verified] |
| K7 | Dual-snapshot check (v2) | two `dict` snaps [verified: verify_v2.py L65-66] | n/a | n/a | Same EXPECT pre+post save/open proves persistence [verified] |
| K8 | Encoding fallback order | `tuple[str, str, str]` [verified] | n/a | ("utf-8-sig","utf-16","utf-8") [verified] | utf-8-sig first catches BOM; wrong order misreads [verified] |

### EKB rules (Tool 5)

- IF writing a verifier THEN copy _load BOM fallback verbatim BECAUSE
  bridge JSON encoding varies on Windows [verified: 6/6 identical].
- IF asserting floats THEN use TOL 1e-3 zip-compare BECAUSE exact float ==
  is brittle across sense serialization [verified: s2/s3/v2].
- IF asserting save/open persistence THEN check EXPECT on both snapshots
  BECAUSE single-snapshot checks miss reopen regressions [verified: v2].
- IF the script prints THEN regex-gate on its REPORT marker first BECAUSE
  missing marker means the in-sim run never completed [verified: s3/s4/s5].

### LIMITS (Tool 5, with cites)

- None filed — evaluators, not Sim APIs (TOOLS.md) [verified].
- Exact thresholds now FULLY read (this pass supersedes skim-only) [verified].

### UNKNOWN (Tool 5, theoretical)

- None outstanding; all 6 verifiers fully read line-by-line [verified].

## Unverified (not tools — never drilled, no scripts)

- Prim selection API (select_prim.py cited, no script) [verified-absent].
- Undo of a mutation (discovery goal 6, no script) [verified-absent].
- Torus prim type (goal names it; Mesh drilled instead) [verified-absent].
- RemoveProperty as true removal (L5 suggestion) [theoretical].
- Sublayers inside referenced assets (L4 re-verify call) [theoretical].
- Time-sampled/keyframed authoring (all default-time) [theoretical].
- isaac-sim-remote open_stage/prim_properties + usd-composition-architecture
  doc (background only; one line already disproven by L4) [theoretical].

## Sources-read (this pass)

- README.md (FULL — no SKILL.md exists), failures.md (FULL),
  discovery.md (FULL), TOOLS.md (FULL, pointer added).
- FULL: s1_make_cube, s2_make_prims, s2_delete, s3_props, s4_layers,
  s5_comp, s5_diag, v2_build (8/8), verify_s1..s5 + verify_v2 (6/6).
- FULL: stages/s5_widget.usda, s4_base.usda; listed s1.usd, v2.usd,
  s4_override.usda, v2_base/over.usda + 29 evidence JSONs by name.
- Skills loaded: spatial-reasoning (FULL), usd-pipeline (FULL).
