# Cross-Val Tool Knowledge (2026-11-04)

> Exhaustive reference: [TOOLS_REF.md](TOOLS_REF.md) — 27 tools,
> 132 functions, 52 knobs, 50 limits, 28 unknowns (20 scripts FULL,
> 10 verifiers + 15 receipts skimmed).

Pack role: cross-skill co-validation drills X1–X14. Each drill = one
in-sim live/build script (`scripts/x*_live.py`, `x1_build.py`,
`x1_run.py`, `x4_build.py`, `x3_diag.py`, `x3_prec.py`) that prints a
single `XN-REPORT ...` stdout line, captured as `evidence/*.json`
receipts, asserted by a local verifier (`scripts/verify_xN.py`).
NOTE: this pack has NO SKILL.md / README.md / failures.md /
discovery.md (verified by directory listing on 2026-11-04), so there
are no documented failure entries to cite; LIMITS below cite live
script comments and evidence/ receipts instead.

## Tools

### omni.usd
DOES: one line — stage handle for every in-sim script.
FUNCTIONS USED:
- `omni.usd.get_context().get_stage()` — stage handle (all 8 read scripts).
- `stage.GetPrimAtPath(p)` + `prim.IsValid()` — validity gating before any read.
- `stage.DefinePrim(path)` — create prim for USD reference (x2_live).
LIMITS-live-verified:
- R11 rule (scripts/x5_live.py comment + x9/x10/x12/x14 docstrings):
  NEVER touch HasAPI/attrs on invalid prims (null-prim throw); gate
  every read on `IsValid()` and report cleanly instead.
UNKNOWN:
- Context switching / multi-stage behavior not drill-proven here.

### pxr.UsdGeom
DOES: one line — geometry authoring and read-only measurement lens.
FUNCTIONS USED:
- `Cube.Define / Plane.Define / Mesh.Define`, `Cube.Get(stage, p)`.
- `GetSizeAttr().Get()/Set()`, `CreateWidthAttr/CreateLengthAttr`,
  `CreatePointsAttr/CreateFaceVertexCountsAttr/CreateFaceVertexIndicesAttr`.
- `Xformable(prim).AddTranslateOp().Set(...)`,
  `GetOrderedXformOps()`, `XformOp.TypeTranslate/TypeScale`,
  `op.Get()`, `GetAttr().GetTimeSamples()`.
LIMITS-live-verified:
- Missing translate op returns sentinel (999.0 / (999,999,999)) in
  read scripts (x10/x9/x12/x14 helpers) — callers must handle absent ops.
- Anim lens reads time-sample counts off ordered ops by index
  (x10_live: `gops[0]` translate samples, `gops[1]` rotate samples).
UNKNOWN:
- Non-cube/plane/mesh schema coverage beyond the read scripts.

### pxr.UsdPhysics
DOES: one line — physics scene, bodies, joints, API-flag lens.
FUNCTIONS USED:
- `Scene.Define`, `CreateGravityDirectionAttr/MagnitudeAttr`.
- `RigidBodyAPI.Apply`, `CollisionAPI.Apply`, `MassAPI.Apply(...).GetMassAttr().Set()`,
  `MassAPI(prim).GetMassAttr().Get()`, `ArticulationRootAPI` (HasAPI check).
- `RevoluteJoint.Define`, `GetBody0Rel/GetBody1Rel().AddTarget()`,
  `GetLocalPos0/1Attr`, `GetLocalRot0/1Attr`, `GetAxisAttr`, `Tokens.z`.
- `prim.HasAPI(...)`, `prim.GetAttribute("drive:angular:physics:type|stiffness|damping").Get()`.
LIMITS-live-verified:
- Drive params are read as raw attributes (`drive:angular:physics:*`),
  not via a schema wrapper (x9/x10_live).
- evidence/x5_run.json: settled block reads `spd=0.0000 rigid=True coll=True`
  after 120 steps — the stability bar used by verifiers.
UNKNOWN:
- Joint authoring beyond single revolute (x4_build); drive writes not shown.

### pxr.UsdShade
DOES: one line — red PBR material authoring (x4_build only).
FUNCTIONS USED:
- `Material.Define`, `Shader.Define`, `SetShaderId("UsdPreviewSurface")`,
  `CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(...)`,
  `CreateSurfaceOutput().ConnectToSource(...)`, `MaterialBindingAPI(prim).Bind(mat)`.
LIMITS-live-verified:
- Only `UsdPreviewSurface` + `diffuseColor` proven in this pack.
UNKNOWN:
- Textures, other inputs, collection bindings — not drilled here.

### pxr.Gf
DOES: one line — math value types for authoring.
FUNCTIONS USED:
- `Gf.Vec3f`, `Gf.Vec3d`, `Gf.Quatf(1.0)` (identity joint frames).
LIMITS-live-verified:
- (none beyond successful x2/x4 receipts.)
UNKNOWN:
- Matrix/quat math beyond identity frames not drilled here.

### pxr.Sdf
DOES: one line — value type name for shader input (x4_build only).
FUNCTIONS USED:
- `Sdf.ValueTypeNames.Color3f`.
UNKNOWN:
- All other Sdf APIs not drilled here.

### pxr.UsdLux
DOES: one line — light rig lens (x12_live read; x6/x7/x8 import-only).
FUNCTIONS USED:
- `UsdLux.DomeLight.Get(stage, path).GetIntensityAttr().Get()`.
LIMITS-live-verified:
- V12 drill asserts dome intensity 3000 via this getter (x12_live docstring).
UNKNOWN:
- Writes, other light types, shadow/exposure attrs — x6/x7/x8 skim-level only.

### pxr.Usd (skim-level)
DOES: one line — imported by x3_diag.py and x3_prec.py (not fully read).
FUNCTIONS USED:
- (import-level only: `from pxr import Usd`; member use not read.)
UNKNOWN:
- Everything about its drill-proven use; read x3_diag.py/x3_prec.py to promote.

### pxr.PhysxSchema (skim-level)
DOES: one line — imported by x7_live.py only (not fully read).
FUNCTIONS USED:
- (import-level only; member use not read.)
UNKNOWN:
- Everything about its drill-proven use; read x7_live.py to promote.

### isaacsim.core.experimental.utils.app (app_utils)
DOES: one line — timeline transport for play/step live scripts.
FUNCTIONS USED:
- `app_utils.play()`, `await app_utils.update_app_async(steps=120)`.
LIMITS-live-verified:
- 120-step legs used by x2/x5; x9–x14 are explicitly READ-ONLY
  snapshots with NO timeline writes (their docstrings).
- evidence/x2_run.json: t0=0.000 -> t1=2.000 over 120 steps.
UNKNOWN:
- `update_app_async` beyond steps=120; stop/reset helpers not used here.

### omni.timeline
DOES: one line — wall-clock check and pause for live scripts.
FUNCTIONS USED:
- `get_timeline_interface()`, `get_current_time()`, `pause()`.
LIMITS-live-verified:
- verify_x2.py FAILS unless t1 > t0 ("no time advance").
UNKNOWN:
- play/stop via timeline interface (play goes through app_utils here).

### isaacsim.core.experimental.prims.Articulation
DOES: one line — articulation DOF read lens (x5/x10 read).
FUNCTIONS USED:
- `Articulation(path)`, `get_dof_positions()`, `get_dof_position_targets()`.
LIMITS-live-verified:
- Returns warp array OR ndarray — read scripts normalize with
  `e.numpy() if isinstance(e, wp.array) else np.asarray(e)` (x5/x10).
- evidence/x5_run.json: q=[1.735,1.092] rad, klim=True (+/-170deg bar).
UNKNOWN:
- DOF writes/target sets not drilled in read scripts.

### isaacsim.core.experimental.prims.RigidPrim
DOES: one line — rigid-body pose/velocity read lens (x2/x5 read).
FUNCTIONS USED:
- `RigidPrim(BLK)` and `RigidPrim(paths="...")`,
  `get_world_poses()[0].numpy()[0][2]`, `get_velocities()[0]`.
LIMITS-live-verified:
- `paths=` kw form addresses nested prims (x2_live:
  `/World/X2Bot/Geometry/base`).
- evidence/x2_run.json: z0=0.0000 z1=-0.0000 (stability bar |dz|<=0.2
  enforced by verify_x2.py).
UNKNOWN:
- Velocity/pose setters not drilled in read scripts.

### isaacsim.core.cloner.GridCloner
DOES: one line — grid cloning for the X4 capstone (x4_build only).
FUNCTIONS USED:
- `GridCloner(spacing=3.0)`, `define_base_env("/World/x4envs")`,
  `generate_paths("/World/x4envs/env", 2)`,
  `clone(source_prim_path=..., prim_paths=...)` (returns list; count reported).
LIMITS-live-verified:
- 2-clone X4 scene is the only proven scale in this pack.
UNKNOWN:
- Larger grids, non-cube sources, clone failure modes.

### isaacsim.core.experimental.utils.semantics.get_labels
DOES: one line — semantic-label lens (x12_live only).
FUNCTIONS USED:
- `get_labels(stage.GetPrimAtPath(p))` — returns dict, printed raw.
LIMITS-live-verified:
- V12 drill expects labels v12a / v12b (x12_live docstring).
UNKNOWN:
- Label writes, multi-label prims, missing-label return shape.

### isaacsim.core.simulation_manager.SimulationManager
DOES: one line — app/physics-engine lens (x14_live only).
FUNCTIONS USED:
- `SimulationManager.get_active_physics_engine()` (aliased `S`).
LIMITS-live-verified:
- evidence/x14_run.json: `engine=physx` is the asserted post-exam state.
UNKNOWN:
- Engine switching / manager lifecycle not drilled here.

### omni.graph.core (og)
DOES: one line — OmniGraph read lens (x9_live only).
FUNCTIONS USED:
- `og.get_node_by_path(...)`, `node.is_valid()`,
  `node.get_attribute("inputs:primPath").get()`,
  `og.get_graph_by_path(...)`, `graph.is_valid()`, `graph.is_disabled()`.
LIMITS-live-verified:
- Invalid Write node must print "MISSING", not throw (x9_live guard).
- Rival-writer scan: any other `Graph` prim under /World whose child
  `inputs:primPath` attr equals the V9 hinge path counts as rival (x9_live).
UNKNOWN:
- Graph authoring/enable writes, non-primPath attrs — not drilled here.

### numpy
DOES: one line — numeric checks and warp-array normalization.
FUNCTIONS USED:
- `np.asarray(..., dtype=float)`, `np.all`, `np.abs`, `np.degrees`,
  `np.linalg.norm`, `.flatten()`, `.numpy()` on warp results.
LIMITS-live-verified:
- Joint-limit bar: `np.all(np.abs(np.degrees(q)) <= 170.0)` (x5_live).
UNKNOWN:
- (stdlib-grade; no sim-specific unknowns.)

### warp
DOES: one line — tensor-array interop check for prim getters.
FUNCTIONS USED:
- `isinstance(a, wp.array)`, `wp.array.numpy()`.
LIMITS-live-verified:
- Getters may return `wp.array` or ndarray depending on context —
  always normalize before indexing (x5/x10 `_w` helper).
UNKNOWN:
- Kernel/device APIs — not used in this pack.

### json (local verifiers)
DOES: one line — evidence receipt + sense-snapshot parsing.
FUNCTIONS USED:
- `json.load(fh)`, `json.loads(...)` on nested `output` strings.
LIMITS-live-verified:
- Evidence files may be BOM/UTF-16-prefixed: verify_x2.py tries
  encodings ("utf-8-sig", "utf-16", "utf-8"); evidence/x2_run.json and
  evidence/x2_sense.json visibly start with a BOM char.
- Sense snapshot schema consumed: `{"prims": [...], "joints": [...]}`;
  joints carry type/body0/body1/axis/anchor sites (verify_x2.py,
  evidence/x2_sense.json: shoulder is `PhysicsRevoluteJoint`).
UNKNOWN:
- Full snapshot schema (only prims/joints slices asserted here).

### re (local verifiers)
DOES: one line — parse XN-REPORT stdout lines out of receipts.
FUNCTIONS USED:
- `re.search(r"X2-REPORT ...", run.get("output", ""))`, `m.group(i)`.
LIMITS-live-verified:
- Missing report line = FAIL with `no report: <first 300 chars>`
  (verify_x2.py); receipts must also have `status == "ok"`.
UNKNOWN:
- Other verifiers' exact patterns (skim-level; same family).

### sys (local verifiers)
DOES: one line — verifier exit-code contract.
FUNCTIONS USED:
- `sys.exit(main())`, `main()` returns 0 on `XN-PASS`, 1 on `XN-FAIL`.
LIMITS-live-verified:
- (contract visible in verify_x2.py; same shape across verify_x*.)
UNKNOWN:
- (none material.)

### os (skim-level, local verifiers)
DOES: one line — imported by verify_x1/x6/x8/x13 (not fully read).
FUNCTIONS USED:
- (import-level only; member use not read.)
UNKNOWN:
- Its drill-proven role; read one importing verifier to promote.

### glob (skim-level, local verifiers)
DOES: one line — imported by verify_x12.py only (not fully read).
FUNCTIONS USED:
- (import-level only; member use not read.)
UNKNOWN:
- Its drill-proven role; read verify_x12.py to promote.

### XN-REPORT / evidence-harness convention
DOES: one line — pack-level contract gluing live scripts to verifiers.
FUNCTIONS USED:
- Live scripts `print("XN-REPORT key=value ...")` single line.
- Receipts `evidence/*.json`: `{"status": "ok"|..., "output": "...", "result": null}`.
- Verifiers assert `status == "ok"`, regex the report line, exit 0/1.
LIMITS-live-verified:
- evidence/x2_run.json, x5_run.json, x14_run.json all `status: ok`
  with single-line reports — the proven-good shape.
- Cross-pack coupling: x2_live/x4_build `AddReference()` an ABSOLUTE
  Windows path into modeling-assets
  (`.../skills/modeling-assets/assets/m2_out/m2_bot/m2_bot.usda`) —
  breaks if the workspace moves.
UNKNOWN:
- How live scripts are launched into Sim (bridge vs editor) — no
  runner docs in this pack; 21 of 25 evidence files unread.

### Verifier exit-code contract (repo-wide, 2026-11-04)
Every `verify_*.py` in every pack MUST exit nonzero on failure:
`raise SystemExit(0 if ok else 1)`, `sys.exit(bool)`, or bare
`assert` gates (traceback exits 1). Printing `FAIL`/`*-FAIL` while
exiting 0 is a masked failure — harnesses count rc=0 as pass, so the
red never surfaces. Provenance: sdg/base `verify_s3.py` printed
`S3-FAIL` with rc=0 until this contract landed; audit
2026-11-04: 106/107 verifiers comply. Known exception:
ros-navigation/planning `verify_libfix.py` (in-sim only, prints
FPCHECK with no verdict) — give it asserted gates on the next live
run instead of inventing thresholds offline.

## Unverified
- PhysxSchema drill use (x7_live.py import-only; not read).
- pxr.Usd drill use (x3_diag.py, x3_prec.py import-only; not read).
- os / glob roles in verifiers (verify_x1/x6/x8/x13, verify_x12; not read).
- Live-script details for x1_build, x1_run, x3_diag, x3_prec, x6/x7/x8/x11/x13_live.
- Verifier thresholds for verify_x1/x3–x14 (only verify_x2 fully read).
- stages/x1.usd, stages/x3_over.usda, stages/x3_overB.usda (names only, never read).
- 21 unread evidence/*.json receipts (only x2_run, x5_run, x14_run, x2_sense sampled).
- Launch path of live scripts (no runner/bridge docs in pack).
- Any failure modes: no failures.md exists, so every LIMIT above rests
  on code comments + receipt samples, not a curated failure log.

## Sources-read
- action-reasoner/skills/cross-val/scripts/x5_live.py (FULL)
- action-reasoner/skills/cross-val/scripts/x4_build.py (FULL)
- action-reasoner/skills/cross-val/scripts/x10_live.py (FULL)
- action-reasoner/skills/cross-val/scripts/x9_live.py (FULL)
- action-reasoner/skills/cross-val/scripts/x12_live.py (FULL)
- action-reasoner/skills/cross-val/scripts/x14_live.py (FULL)
- action-reasoner/skills/cross-val/scripts/x2_live.py (FULL)
- action-reasoner/skills/cross-val/scripts/verify_x2.py (FULL)
- action-reasoner/skills/cross-val/evidence/x2_run.json (FULL)
- action-reasoner/skills/cross-val/evidence/x5_run.json (FULL)
- action-reasoner/skills/cross-val/evidence/x14_run.json (FULL)
- action-reasoner/skills/cross-val/evidence/x2_sense.json (partial: head + schema skim)
- Import grep across all 30 scripts (muse.search `^(import|from)\s+\S+`, mode regex)
- Directory listings of scripts/ (30 files), stages/ (3 files), evidence/ (25 files)
- ABSENT (verified missing): SKILL.md, README.md, failures.md, discovery.md
