# Stage-Core Tool Knowledge (2026-11-04)

> Exhaustive reference: [TOOLS_REF.md](TOOLS_REF.md) — 5 tools, 78 functions, 38 knobs, 28 EKB rules, 14 limits, 13 unknowns + 7 unverified items (all 14 scripts read FULL; spatial-reasoning + usd-pipeline loaded).

## Tools

### omni.usd (UsdContext)
- DOES: Access the live Kit stage from in-sim Python.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()` — get live stage (every in-sim script).
- LIMITS-live-verified: none (no failures filed against context access).
- UNKNOWN: Whether `get_context()` behaves the same headless vs windowed; other `omni.usd` helpers (authoring commands, selection API) — not drill-proven here.

### pxr UsdGeom (prim authoring + properties)
- DOES: Define typed prims and set transform/shape/display properties.
- FUNCTIONS USED:
  - `UsdGeom.Cube/Sphere/Cylinder/Cone/Plane/Mesh.Define(stage, path)` — typed prim creation (s2_make_prims, s1, s3, s5, v2).
  - `GetSizeAttr/GetRadiusAttr/GetHeightAttr().Set()` — shape params (s1, s2, s3, s5, v2).
  - `CreateWidthAttr/CreateLengthAttr` (Plane), `CreatePointsAttr/CreateFaceVertexCountsAttr/CreateFaceVertexIndicesAttr` (hand-authored Mesh) (s2).
  - `UsdGeom.Xformable(prim).AddTranslateOp/AddRotateXYZOp/AddScaleOp` + `Set(Gf.Vec3d/Vec3f)` (s1, s2, s3, v2).
  - `GetDisplayColorAttr/GetDisplayOpacityAttr().Set/Get` (s3, v2).
  - `UsdGeom.Imageable(prim).MakeInvisible/MakeVisible/GetVisibilityAttr/GetPurposeAttr` — visibility + purpose (s3).
  - `prim.CreateAttribute("master:tag", Sdf.ValueTypeNames.String, custom=True)` — custom attrs (s3).
  - `prim.GetAttribute("xformOp:...").Get()` — property readback (s3).
- LIMITS-live-verified:
  - Cube `size` attr IS edge length (README verified fact; do not treat as half-extent).
  - Purpose `render`/`proxy` needs explicit bbox query purposes on the sense side (README verified fact).
- UNKNOWN: Other gprim types (Torus named in discovery goals but no Torus in scripts — S2 covers 6 prims with Mesh instead); extent/double-sided/other Imageable schema attrs; time-sampled (animated) property authoring.

### pxr Usd / Sdf (stage, layers, composition, variants, payloads)
- DOES: Stage/layer management, prim lookup/deletion, sublayer stacking, references, variants, payloads, diagnostics.
- FUNCTIONS USED:
  - `stage.GetPrimAtPath/DefinePrim/RemovePrim` — lookup/create/delete (s2, s3, s5, v2).
  - `stage.GetRootLayer()`, `root.subLayerPaths` get/set (list prepend/restore) — sublayer stack control (s4, v2).
  - `Usd.Stage.CreateNew(path)` + `GetRootLayer().Save()` — author external .usda asset (s5_comp).
  - `Usd.Stage.Open(path)`, `GetDefaultPrim`, `HasAuthoredReferences`, `GetChildren`, `GetPath` — diagnostics (s5_diag).
  - `prim.GetVariantSets().AddVariantSet/AddVariant/SetVariantSelection/GetVariantSet/GetNames` + `GetVariantEditContext()` — variant authoring/selection/switching (s5_comp, s5_diag, v2).
  - `prim.GetReferences().AddReference(asset)` — reference external asset (s5_comp, v2).
  - `prim.GetPayloads().AddPayload(asset)`, `stage.Unload/Load(Sdf.Path)` — payload load/unload/load cycle (s5_comp).
  - `attr.GetPropertyStack(Usd.TimeCode.Default())[0].layer.GetDisplayName()` — prove which layer wins (s4).
  - `Usd.TimeCode.Default()` — property-stack query time (s4).
  - `Sdf.Path`, `Sdf.ValueTypeNames.String` — path + type tokens (s3, s5).
  - `Usd.Attribute.Clear()` — attempted opinion removal (failures.md L5 context).
  - Text-authored USDA (`def`/`over` blocks written via plain `open().write()`) for base/override sublayers (s4, v2).
- LIMITS-live-verified:
  - A layer's own direct opinions always beat its sublayers; overrides only win against weaker layers — base must live in a weaker sublayer file, never as root direct opinions (failures.md L2; s4 v1 failure → v2 recovery).
  - Precedence chain is Direct > Sublayer > Reference — a root sublayer over BEATS a reference value (failures.md L4; doc line "Sublayers < Reference" corrected).
  - Hand-written `variantSet` USDA fails two ways (`=` without declaration silently drops the set; no-`=` is invalid Sdf text, layer unopenable) — always declare the set AND use `=` form, or author via UsdVariantSets API; parse warnings don't fail sends so verify composed prims exist (failures.md L3; trust machine-emitted USDA, e.g. URDF converter output).
  - `Attribute.Clear()` leaves a root property-stack entry (authored=True) even though value falls through — do NOT teach Clear()-as-removal; prefer RemoveProperty or case-per-prim (failures.md L5, OPEN/unresolved cause).
  - `GetVariantEditContext()` edits the SELECTED variant and takes no name arg (README verified fact).
- UNKNOWN: `RemoveProperty` as true removal (suggested in L5, not drill-proven); sublayers inside the referenced asset (L4 says re-verify if configuration changes); `over` vs `def` semantics beyond the proven pattern; nested variant sets; `Usd.Stage.CreateInMemory` vs file-backed for assets.

### isaacsim_send.py bridge — stage ops (new / save / open) + sense reads
- DOES: Drive stage lifecycle from outside Sim (fresh stage, save .usd to disk, reopen) and read back stage state via Skill 0 sense.
- FUNCTIONS USED:
  - `new` stage op (evidence s1_newA/s1_newB/s2_new/s3_new/s4_new/s5_new/v2_new/v2_new2.json).
  - `save` .usd to disk + `open` it back (evidence s1_save/s1_open/v2_save/v2_open.json; stages/ s1.usd, v2.usd).
  - In-sim script execution via bridge (all sN/v2 scripts "run INSIDE Isaac Sim via isaacsim_send.py" per README).
  - Sense reads for verification (evidence s1_senseA/B/C, s2_senseA/B/C, s3_sense, v2_senseA/B.json).
- LIMITS-live-verified:
  - Opening a saved .usd auto-adds the 4-prim viewport light rig (`/OmniKit_Viewport_LightRig/Lights/` DomeLight + DistantLight) — fresh `new` has 12 prims, reopened has 16+content; assert by path-set, not raw count; fresh `new` template has no lights at all (failures.md L1).
  - Fresh `new` template carries exactly 12 prims (World, Render scope, 4 cameras, no lights) (README verified fact).
- UNKNOWN: Save/open of stages with unsaved sublayer edits; binary .usd vs .usda round-trip differences; bridge ops beyond new/save/open/exec/sense.

### verify_sN / verify_v2 local evaluators (stdlib-only: json, os, sys, re)
- DOES: Local pass/fail evaluation of each drill from bridge/sense JSON evidence; exit 0 on pass.
- FUNCTIONS USED:
  - `verify_s1.py` (json/os/sys), `verify_s2.py` (json/sys), `verify_s3.py` (json/re/sys), `verify_s4.py` (json/re/sys), `verify_s5.py` (json/re/sys), `verify_v2.py` (json/os/sys) — skimmed by name+imports only, not read fully.
- LIMITS-live-verified: none filed (evaluators, not Sim APIs).
- UNKNOWN: Exact assertion thresholds inside each verifier (not read — skim-only per pass rules).

## Unverified

- Prim selection API (`select_prim.py` cited in discovery.md Sources, never drilled — no select script in scripts/).
- Undo of a mutation (discovery competence goal 6, never drilled — no undo script in scripts/).
- Torus prim type (discovery goal names Cube/Sphere/Cylinder/Cone/Torus/Plane; drills prove Mesh instead of Torus).
- `RemoveProperty` as true opinion removal (failures.md L5 suggestion only).
- Sublayers nested inside a referenced asset (failures.md L4 calls for re-verification).
- Time-sampled/keyframed property authoring (all drills use default-time opinions only).
- isaac-sim-remote `open_stage.py` / `prim_properties.py` and usd-composition-architecture doc (discovery.md Sources — cited as unverified background, one line already proven wrong by L4).

## Sources-read

- action-reasoner/skills/stage-core/README.md (FULL — no SKILL.md exists in this pack)
- action-reasoner/skills/stage-core/failures.md (FULL)
- action-reasoner/skills/stage-core/discovery.md (FULL)
- action-reasoner/skills/stage-core/scripts/s1_make_cube.py (FULL)
- action-reasoner/skills/stage-core/scripts/s2_make_prims.py (FULL)
- action-reasoner/skills/stage-core/scripts/s2_delete.py (FULL)
- action-reasoner/skills/stage-core/scripts/s3_props.py (FULL)
- action-reasoner/skills/stage-core/scripts/s4_layers.py (FULL)
- action-reasoner/skills/stage-core/scripts/s5_comp.py (FULL)
- action-reasoner/skills/stage-core/scripts/s5_diag.py (FULL)
- action-reasoner/skills/stage-core/scripts/v2_build.py (FULL)
- Skimmed by name + imports only (NOT fully read): scripts/verify_s1.py, verify_s2.py, verify_s3.py, verify_s4.py, verify_s5.py, verify_v2.py
- Listed by name only: stages/s1.usd, stages/s4_base.usda, stages/s4_override.usda, stages/s5_widget.usda, stages/v2.usd, stages/v2_base.usda, stages/v2_over.usda; evidence/*.json (29 files)
