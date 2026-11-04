# Modeling-Assets Tool Knowledge (2026-11-04)

Full mastery ref: [TOOLS_REF.md](TOOLS_REF.md) — 10 tools + shape appendix, 54 functions, 63 knobs, 18 limits, 11 unknowns (19 files fully read, spatial-reasoning loaded).

Pack: `action-reasoner/skills/modeling-assets/` (Skill 3, GRADUATED).
Live baseline: Isaac Sim 6.0.0 / Kit 110, Windows.
Convention: M-drills run INSIDE Isaac Sim via the bridge; `verify_*` run LOCALLY.

## Tools

### 1. pxr.UsdGeom (in-sim mesh/shape authoring)
- DOES: Define and edit geometry prims (Mesh, Cube) and their transforms.
- FUNCTIONS USED:
  - `UsdGeom.Mesh.Define(stage, path)` + `CreatePointsAttr().Set(...)`,
    `CreateFaceVertexCountsAttr().Set(...)`, `CreateFaceVertexIndicesAttr().Set(...)` (m1_mesh.py)
  - `GetPointsAttr().Get()`, `GetDisplayColorAttr().Set()/Get()` (m1_mesh.py)
  - `UsdGeom.Cube.Define(stage, path)`, `GetSizeAttr().Set()/Get()` (m3_material.py, m4_clone.py, probes)
  - `UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(...))`,
    `UsdGeom.Xformable(pr).GetOrderedXformOps()` (m1/m3, probes)
  - `UsdGeom.XformCache()` world-pose readback (probes/audit_m4.py, audit_m4v2.py)
- LIMITS-live-verified:
  - Outward-CCW quad winding proven only for the drilled 8-point box face table
    (`[0,4,7,3]`, `[1,2,6,5]`, ...); cross-product argument in m1_mesh.py docstring,
    exact bounds in evidence/m1_sense.json.
  - Bottom-rests-at-z=0 done via translate op (+0.25 on a 0.5-tall box), not by
    authoring points at z>=0 (m1_mesh.py).
- UNKNOWN: any Mesh topology beyond the drilled box (tris, n-gons, normals/UVs);
  displayColor-vs-bound-material precedence; normals authoring.

### 2. pxr.UsdShade (in-sim PBR materials + binding)
- DOES: Create UsdPreviewSurface materials and bind them to prims.
- FUNCTIONS USED:
  - `UsdShade.Material.Define(stage, path)`, `UsdShade.Shader.Define(stage, path)`
  - `Shader.SetShaderId("UsdPreviewSurface")`,
    `Shader.CreateInput(name, Sdf.ValueTypeNames.*).Set(...)` (diffuseColor/roughness/metallic)
  - `Material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")`
  - `UsdShade.MaterialBindingAPI(prim).Bind(mat)`,
    `.GetDirectBinding().GetMaterialPath()` readback (m3_material.py, v3_build.py, v3_check.py)
- LIMITS-live-verified:
  - Bindings on referenced prims author as overs and survive save/reopen on both
    source (`/World/V3Bot/Geometry/base`) and clone (`/World/venvs/env_0/...`)
    (README; evidence/v3_check.json, v3_senseA/B.json).
  - Clones inherit source bindings (v3_check.py reads clone binding == `/World/V3Looks/V3Red`).
  - Only drilled values: diffuse red (1,0,0), roughness 0.4, metallic 0.0 (m3_material.py).
- UNKNOWN: unbind/re-bind; multi-material/geom-subset binding; texture inputs;
  MaterialBindingAPI collection bindings; any shader id besides UsdPreviewSurface.

### 3. omni.usd stage access (in-sim)
- DOES: Get the live stage and define/query/remove prims on it.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()` (every in-sim script)
  - `stage.GetPrimAtPath(path)`, `prim.IsValid()`, `stage.RemovePrim(path)` (idempotent cleanup)
  - `stage.DefinePrim(path)`, `prim.GetReferences().AddReference(pkg_path)` (m2_import.py, v3_build.py)
  - `stage.Traverse()` + `prim.GetTypeName()` joint hunt (m2_import.py)
- LIMITS-live-verified:
  - `import_urdf()` does NOT touch the live stage; the drill must
    DefinePrim + AddReference the emitted package itself (failures.md A1).
- UNKNOWN: save/open stage via API (V3 round-trip save/open went through bridge
  commands captured in evidence/v3_save.json + v3_open.json, not via a drilled API call);
  payload vs reference tradeoffs; variant sets.

### 4. isaacsim.asset.importer.urdf — URDFImporter (in-sim, OFFLINE converter)
- DOES: Convert a URDF file to a USD package on disk; returns package path.
- FUNCTIONS USED:
  - `URDFImporterConfig(urdf_path=..., usd_path=...)` (only these two kwargs drilled)
  - `URDFImporter(config).import_urdf()` -> `out` path string (m2_import.py)
  - Drilled input: assets/m2_bot.urdf (2 links: box base + cylinder arm, inertial+visual+collision;
    1 revolute joint `shoulder`, z-axis, limits +-1.57)
- LIMITS-live-verified:
  - Works offline in its own context; live stage keeps the previous scene while
    .usd files land on disk (failures.md A1; evidence: 6 .usd files, assets/m2_out/).
  - Reruns version the output dir (`m2_bot`, `m2_bot_1`, `m2_bot_2`) instead of
    overwriting (failures.md A1; assets/m2_out/ has all three).
  - Imported child links NEST under parents (`Geometry/base/arm`, not
    `Geometry/arm`) (failures.md A2).
  - Visuals+collisions double as `box`/`box_1`-style copies; joints land under
    `Physics/`; shoulder verified as `PhysicsRevoluteJoint` (README, verify_m2.py).
- UNKNOWN: MJCF/heightmap importer family (discovery.md: documented stretch, NOT drilled);
  any joint type besides revolute; mesh-geometry (STL/OBJ/COLLADA) URDF links;
  materials/textures in URDF; every URDFImporterConfig kwarg besides urdf_path/usd_path.

### 5. isaacsim.core.cloner — GridCloner (in-sim cloning)
- DOES: Clone a source prim N times onto a grid, returning positions.
- FUNCTIONS USED:
  - `GridCloner(spacing=2.0|3.0)`, `define_base_env("/World/envs")`,
    `generate_paths("/World/envs/env", N)`, `clone(source_prim_path=..., prim_paths=...)`
    (m4_clone.py: 3x3=9 cubes; v3_build.py: 2x2=4 referenced bots)
- LIMITS-live-verified:
  - 9/9 clones at distinct grid spots (evidence/m4_run.json + m4_sense.json).
  - Cloning a referenced bot preserves subtree + material bindings on clones
    (evidence/v3_senseB.json, v3_check.json).
  - Source prim (`/World/M4Src`) is separate from the env grid (`/World/envs`).
- UNKNOWN: `num_per_row` kwarg (named in README, never called in any drilled script);
  non-grid cloners; clone-then-modify independence (overs on clones not drilled);
  cloning physics-articulated sources under simulation.

### 6. pxr.UsdPhysics (READ-ONLY audit in probes)
- DOES: Inspect physics APIs on prims without authoring any.
- FUNCTIONS USED:
  - `prim.HasAPI(UsdPhysics.RigidBodyAPI|CollisionAPI|MassAPI|ArticulationRootAPI)`
  - `UsdPhysics.MassAPI(prim).GetMassAttr().Get()`,
    `UsdPhysics.Joint(pr)` / `UsdPhysics.RevoluteJoint(pr)` introspection
    (probes/audit_m4.py, probes/audit_m4v2.py)
- LIMITS-live-verified: none beyond "reads worked in probes" (probes have no
  paired evidence files, so no drill-grade claim).
- UNKNOWN: everything on the authoring side — no drill applies RigidBodyAPI,
  CollisionAPI, MassAPI, joints, or articulation roots; all physics authoring
  belongs to other packs (Skill 2 mechanics per discovery.md).

### 7. pxr.Gf + pxr.Sdf (value/type vocabulary)
- DOES: Supply 3-vector values and attribute type names for UsdGeom/UsdShade calls.
- FUNCTIONS USED:
  - `Gf.Vec3f(*p)` points/colors, `Gf.Vec3d(...)` translate ops
  - `Sdf.ValueTypeNames.Color3f`, `Sdf.ValueTypeNames.Float` for shader inputs
- LIMITS-live-verified: none (pure vocabulary, no failure modes observed).
- UNKNOWN: nothing relevant; open-ended value library, pack uses only the above.

### 8. Bridge transport — isaacsim_send.py wire protocol / probes/sync_send.py (local)
- DOES: Ship in-sim scripts to Isaac Sim over TCP and return a JSON result envelope.
- FUNCTIONS USED:
  - TCP to 127.0.0.1:8226; script wrapped as `async def _isolated_script(): ... await _isolated_script()`
    (probes/sync_send.py documents the same protocol as `isaacsim_send.py --file`)
  - Result envelope: `{"status": "ok"|..., "output": "<stdout>", "evalue?": ...}`
    (every evidence/*_run.json, *_new.json; consumed by all verify_* scripts)
- LIMITS-live-verified:
  - Envelope encodings vary (utf-8-sig / utf-16 / utf-8 all probed by verifiers'
    `_load()`), so readers must try multiple codecs.
- UNKNOWN: bridge server setup/flags (owned by workspace setup, not this pack);
  timeout/retry behavior under load; binary payload support.

### 9. Sense snapshots (Skill 0 reads, consumed as JSON)
- DOES: Provide the prim-listing evidence (`{"prims": [{path, type, ...}]}`) that
  verifiers check structure against.
- FUNCTIONS USED: none in-pack — verifiers only parse `evidence/mN_sense.json`
  / `v3_senseA/B.json` via `json.loads(env["output"])["prims"]`.
- LIMITS-live-verified:
  - V3 sense-before (32 KB) vs sense-after-reopen (34 KB) both contain the full
    want-set (ref tree + looks + 4 clone subtrees) (verify_v3.py).
- UNKNOWN: sense tool itself is Skill 0's (`workspace-sense`), not drilled here;
  position/size fields used loosely (verify_m1 prints pos/size).

### 10. Local verifier stack — Python stdlib json/re/sys (+ glob/os)
- DOES: Parse `*-REPORT ...` stdout lines and sense snapshots; exit 0/1 with FAIL list.
- FUNCTIONS USED:
  - `json.load` with multi-codec `_load()`; `re.search` on REPORT regexes;
    `glob.glob(OUTDIR + "/**/*.usd*", recursive=True)` (verify_m2);
    `os.path.exists/getsize` on stages/v3.usd (verify_v3)
- LIMITS-live-verified:
  - Report regexes are exact-match brittle by design (e.g.
    `M2-REPORT out=(\S+) root=(\w+) joints=(\S*) base=(\w+) arm=(\w+)`); missing
    report line = immediate FAIL.
- UNKNOWN: none in-pack; plain local scripting, no live API surface.

## Unverified

- MJCF + heightmap importers: same family per discovery.md, zero drills, zero evidence.
- Save/reopen MECHANISM: only the before/after evidence exists
  (evidence/v3_save.json, v3_open.json, v3_senseA/B.json); no drilled API call in scripts/.
- GridCloner `num_per_row`: README name-drops it; no script passes it.
- Physics authoring on modeled prims: UsdPhysics appears read-only in ungraduated
  probes (no evidence files); rigid/collision/mass/joint authoring unproven here.
- URDF coverage beyond the drilled sample: mesh links, mimic/fixed/prismatic joints,
  transmissions, Gazebo tags, package:// URIs, textures.
- Material edits after binding: rebind, unbind, value mutation post-bind, subset binding.
- stages/v3.usd (5.5 KB) round-trips only the V3 scene; large-asset save/load
  performance and USD layering strategy undrilled.

## Sources-read

Fully read (11):
- README.md (no SKILL.md in pack)
- failures.md (A1, A2)
- discovery.md
- scripts/m1_mesh.py
- scripts/m2_import.py
- scripts/m3_material.py
- scripts/m4_clone.py
- scripts/v3_build.py
- scripts/v3_check.py
- scripts/verify_m2.py
- scripts/verify_v3.py
- assets/m2_bot.urdf

Skimmed by name + imports + def/print map (6):
- scripts/verify_m1.py, scripts/verify_m3.py, scripts/verify_m4.py
  (same json/re/sys harness as verify_m2/v3; M1/M3/M4-specific REPORT regexes)
- scripts/probes/audit_m4.py (in-sim stage audit: presence walk, cube/joint detail,
  XformCache world poses, GraspSite check)
- scripts/probes/audit_m4v2.py (shorter v2 variant of the same audit)
- scripts/probes/sync_send.py (standalone TCP sender, isaacsim_send.py --file protocol)

Not read (data, not tools): evidence/*.json (20 files, referenced by shape only),
assets/m2_out/*/ (import outputs), stages/v3.usd.
