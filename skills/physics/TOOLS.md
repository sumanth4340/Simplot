# Physics Tool Knowledge (2026-11-04)

> Exhaustive reference: `TOOLS_REF.md` — 21 tools, 98 functions,
> 27 knobs, 19 limits, 17 unknowns (20/36 scripts fully read).

Pack: `action-reasoner/skills/physics/` (merged 2026-11-04 from
`physics-master` → `core/` and `physics-x` → `engines/`).
No per-part SKILL.md/failures.md/discovery.md exist — the three root
docs cover both parts. In-sim scripts run inside Kit via the live
bridge; LOCAL drivers shell out to the isaac-sim-remote skill.

## Tools

### 1. pxr.UsdPhysics — physics schema authoring

DOES: Authors scene, bodies, collisions, mass, joints, and drives on USD prims.

- FUNCTIONS USED:
  - `Scene.Define` + `CreateGravityDirectionAttr` / `CreateGravityMagnitudeAttr`
  - `RigidBodyAPI.Apply` / `CollisionAPI.Apply` / `MassAPI.Apply`
    (+ `GetMassAttr`/`Set`, `CreateMassAttr`, `CreateDensityAttr`,
    `GetDensityAttr`/`GetDiagonalInertiaAttr`/`HasAuthoredValue` in preflight)
  - `RevoluteJoint.Define`; `GetBody0Rel`/`GetBody1Rel`/`AddTarget`;
    `GetLocalPos0/1Attr`, `GetLocalRot0/1Attr`;
    `GetAxisAttr.Set(Tokens.z)` / `CreateAxisAttr("Y")`;
    `CreateBody0Rel`/`CreateBody1Rel` + `SetTargets`
  - `DriveAPI.Apply(joint_prim, "angular")`; `CreateTypeAttr("force")`,
    `CreateStiffnessAttr(0.0)`, `CreateDampingAttr(1000.0)`,
    `CreateMaxForceAttr`, `CreateTargetVelocityAttr(180.0)`
  - `ArticulationRootAPI.Apply` / `HasAPI`; `Joint` `IsA` check; `Tokens.z`
- LIMITS-live-verified:
  - Angular-drive `TargetVelocity` is DEGREES/s: w=180 turns exactly pi
    in 1.000 s (core/evidence/p3_run.json: q0=(1,0,0,0) → q1=(0,0,0,1),
    z pinned 1.5, t 55.167 → 56.167).
- UNKNOWN: `"linear"` DriveAPI use; stiffness/damping tuning beyond P3's (0.0/1000.0).

### 2. pxr.UsdGeom — geometry + xform ops + transform reads

DOES: Defines scene geometry and xform ops; reads local-to-world transforms and stage units.

- FUNCTIONS USED:
  - `Plane.Define` + `CreateWidthAttr`/`CreateLengthAttr`;
    `Cube.Define` + `GetSizeAttr`/`Set`, `CreateSizeAttr`;
    `Xform.Define` + `AddTranslateOp`/`AddScaleOp`
  - `Xformable(prim).AddTranslateOp().Set` /
    `GetOrderedXformOps()[0].Set` / `.Get` (pose reset + USD reads)
  - `XformCache().GetLocalToWorldTransform(prim).GetDeterminant()`
    (negative-determinant = mirrored collider)
  - `SetStageMetersPerUnit` / `GetStageMetersPerUnit` (units check)
- UNKNOWN: XformCache mid-play staleness is docstring/discovery-attested
  only (p1_run.py docstring); no evidence file isolates it.

### 3. pxr.Usd — stage lifecycle + prim introspection

DOES: Opens/creates/saves stages; looks up, removes, traverses, and introspects prims.

- FUNCTIONS USED:
  - `Stage.CreateNew` / `Open` / `Save`; `SetDefaultPrim`;
    `GetPrimAtPath`; `RemovePrim`; `Traverse`
  - `prim.GetAppliedSchemas` / `IsA` / `GetAttribute` / `GetTypeName` /
    `GetPath().GetPrefixes()`; `prim.CreateAttribute("mjc:ref", ...)`
- UNKNOWN: none — every listed call appears in a fully-read body.

### 4. pxr.Sdf — paths + value types

DOES: Supplies path and value-type primitives for joint targets and seeded attributes.

- FUNCTIONS USED: `Sdf.Path(...)` for joint body targets;
  `Sdf.ValueTypeNames.Float` for the seeded `mjc:ref` attr.
- UNKNOWN: none in the read set.

### 5. pxr.Gf — math value types

DOES: Supplies vector/quaternion values for translations, rotations, and scales.

- FUNCTIONS USED: `Vec3d` (translations), `Vec3f` (gravity dir,
  negative scale), `Quatf(1.0)` (joint-frame identity).
- UNKNOWN: none in the read set.

### 6. pxr.PhysxSchema — PhysX schema module (unobserved)

DOES: Imported by the conversion scripts but never called in any fully-read body.

- FUNCTIONS USED: none observed (import-only in p4_preflight.py and
  the p4_convert.py import block).
- UNKNOWN: entire usage surface — if used at all, only inside the
  skimmed p4_convert.py body.

### 7. omni.usd — live-stage access

DOES: Returns the running Kit session's stage handle for in-sim authoring/reads.

- FUNCTIONS USED: `get_context().get_stage()`; the handle feeds
  `GetPrimAtPath` / `RemovePrim` / `Traverse`.
- UNKNOWN: none in the read set.

### 8. omni.timeline — sim clock

DOES: Controls the Kit clock and verifies that stepping actually advanced time.

- FUNCTIONS USED: `get_timeline_interface()`; `get_current_time()`
  (advance confirm); `set_current_time(0.0)` (trial reset);
  `pause()` (freeze with sim state preserved for snapshots).
- UNKNOWN: none in the read set.

### 9. app_utils (isaacsim.core.experimental.utils.app) — play/stop/pump + ext mgmt

DOES: Runs the play/stop/step pump, enables extensions, and locates extension data paths.

- FUNCTIONS USED:
  - `play()`; `stop()`; `await update_app_async(steps=N)`
  - `enable_extension(...)` ("isaacsim.asset.importer.urdf" in
    probe_urdf.py; "isaacsim.physics.newton" per discovery.md)
  - `get_extension_path("isaacsim.asset.transformer.rules")`
- LIMITS-live-verified:
  - `play()` + `update_app_async(steps=N)` integrates N + 0–2 slipped
    real-time frames (failures.md F5); P5's first sample z=1.310497
    matches 22 steps, not 20 (core/evidence/p5_run.json). Assert
    windows and body-to-body deltas, or pause-first-then-step, and
    normalize by `get_current_time()` dt.
  - `stop()` does NOT restore pre-play state — stage + clock sit at end
    state (failures.md F4); P5 resets the cube pose via USD +
    `set_current_time(0.0)` before every trial.
- UNKNOWN: Newton-enable 30-pump-step procedure body
  (discovery-attested; the enabling script is not in the read set).

### 10. RigidPrim (isaacsim.core.experimental.prims) — simulated-state truth

DOES: Reads SIMULATED body state and commands velocities; the only trustworthy readback during play.

- FUNCTIONS USED:
  - `RigidPrim(paths=...)`; `get_world_poses()[0].numpy()` (positions/quats)
  - `set_velocities(linear_velocities=np.array(...))` strictly AFTER `play()`
  - `get_velocities()` → (linear, angular) (doc-attested: SKILL.md +
    failures.md F3; calling body not in the read set)
- LIMITS-live-verified:
  - `set_linear_velocities` / `get_linear_velocities` do NOT exist
    (AttributeError) — combined `set_velocities` / `get_velocities`
    only (failures.md F3).
  - Velocity set pre-play is ignored by PhysX; set AFTER `play()`
    (failures.md F2; P2: x 0 → 5.0000 exact, z drift 0 —
    core/evidence/p2_run.json).
  - Under Newton, tensor readback raises/is frozen (no Newton backend;
    log "Failed to find simulation backend 'newton'"): the drop read
    z1=2.0000 while renders proved the fall (failures.md R1;
    engines/evidence/p2_run.json P2-REPORT z1=2.0000).
- UNKNOWN: `get_velocities()` return-shape details; angular-velocity set
  path; joint-angle readback spelling (p3_run.py skimmed).

### 11. SimulationManager (isaacsim.core.simulation_manager) — engine switching

DOES: Reports, selects, and switches the active physics engine at runtime.

- FUNCTIONS USED:
  - `get_available_physics_engines()` → [(name, active)] tuples
  - `get_default_engine()` → "physx"; `get_active_physics_engine()`
  - `switch_physics_engine(name)` both directions + 10 pump steps;
    signature `(engine_name: Literal['physx','newton','remotesim'],
    verbose: bool=False) -> bool` (engines/evidence/p2_run.json P2-SIG)
  - `get_backend()`
- LIMITS-live-verified:
  - `get_backend()` returns `'torch'` under BOTH engines
    (engines/evidence/p3_run.json b1=b2=torch) — it names the tensor
    backend, not the physics engine; never gate engine identity on it.
- UNKNOWN: the `'remotesim'` switch target (in the signature, never drilled).

### 12. SimulationContext (isaacsim.core.api.simulation_context) — anti-pattern

DOES: Standalone stepping API that crashes inside Kit; kept only as the documented wrong path.

- FUNCTIONS USED: `instance()`; `SimulationContext()`; `step(render=True)`
  (raises; p1_run.py catches it and falls back).
- LIMITS-live-verified:
  - `step(render=True)` inside Kit raises `AttributeError: 'NoneType'
    object has no attribute 'get_physics_dt'` (failures.md F1;
    core/evidence/p1_run.json P1-STEP-FALLBACK). Recovery: `play()` +
    `update_app_async` + timeline confirm (exactly 2.000 s over
    120 steps, settle z=0.5 exact).
- UNKNOWN: none — failure and recovery are both evidenced.

### 13. isaacsim.physics.newton — Newton backend extension

DOES: Newton/MuJoCo/Warp backend that simulates plain UsdPhysics bodies with zero extra schema.

- FUNCTIONS USED:
  - Enable via `app_utils.enable_extension` + pump steps (discovery:
    30 steps, ~1 min first compile)
  - `import isaacsim.physics.newton as N` (probe_napi.py, skimmed)
  - Scene prims gain `newton:*` attrs (gravityEnabled,
    maxSolverIterations, timeStepsPerSecond); log note
    "Newton timestep from USD: 1000Hz"
- LIMITS-live-verified:
  - Simulates identically but offers NO tensor readback and NO USD
    writeback (Fabric-only render): Newton USDZ pinned 2.0000 vs
    PhysX 0.5000 while motion diffs matched 2.0117 vs 2.0131
    (Δ0.0014) and end frames 0.1068 (failures.md R1;
    engines/evidence/p2_report.txt). Render observation is ground truth.
  - First enable compiles ~33 Warp/MuJoCo kernels on cuda:0 (slowest
    12.2 s; engines/evidence/p2_run.json). The MuJoCo
    warp-3.12-vs-~=3.8 skew warning is benign for rigid drops (discovery.md).
  - No Newton auto-switch in 6.0.0; observed default/active engine is
    physx (SKILL.md; engines/evidence/p3_run.json default=physx).
- UNKNOWN: module API surface (probe_napi.py skimmed); native state via
  NewtonStage/mujoco qpos (explicit future work, R1); `newton:*` attr
  semantics beyond their names.

### 14. isaacsim.asset.transformer — rule-based conversion

DOES: Runs JSON-profile conversion passes (structure/merge/actuator) over USD assets.

- FUNCTIONS USED (skim-attested: import blocks + call-site grep; bodies
  not read): `AssetTransformerManager().run(input_stage=..., ...)`;
  `RuleProfile.from_json(...)`; per-rule report items (`r.rule.name`,
  `r.error`); variant package + MjcActuator audit (SKILL.md/discovery.md).
- LIMITS-live-verified:
  - The manager opens inputs via `Usd.Stage.Open`, and 6.0.0 registers
    no URDF/MJCF Sdf plugin: `run(input_stage=<.urdf>)` raises
    "Cannot determine file format" even with the importer ext enabled
    (failures.md R6) — URDF-profile runs fail before any rule.
- UNKNOWN: `run()` full signature and variant-package flow;
  builder/audit mirror bodies (p4_convert.py skimmed); gain-audit thresholds.

### 15. transformer.rules profile data — shipped conversion profiles

DOES: JSON RuleProfiles consumed via `RuleProfile.from_json`.

- FUNCTIONS USED: profiles `isaacsim_structure`, `merge_mesh`,
  `mjc_to_physx`, `urdf_to_mjc_physx` (discovery.md); located via
  `get_extension_path("isaacsim.asset.transformer.rules")` + `data/<profile>`.
- LIMITS-live-verified:
  - `physx_to_mjc_conversion.json` does NOT ship in 6.0.0 — the
    PhysX→MJC direction needs a newer build (failures.md R5); P4 drills
    the supported `urdf_to_mjc_physx` direction plus offline preflight instead.
- UNKNOWN: profile JSON schema details (no profile file ships in the pack).

### 16. isaacsim.asset.importer.urdf — URDF importer extension

DOES: URDF importer extension, probed for enablement only.

- FUNCTIONS USED: `app_utils.enable_extension("isaacsim.asset.importer.urdf")`.
- LIMITS-live-verified:
  - Enabling it still leaves zero urdf/mjcf entries in the registered
    Sdf formats (failures.md R6).
- UNKNOWN: whether the importer itself converts URDF→USD correctly
  (never drilled; only the manager-open path was probed).

### 17. isaac-sim-remote bridge (isaacsim_send.py + viewport_screenshot.py)

DOES: LOCAL drivers' channel into the live sim: executes inline/file scripts in-session and captures viewport screenshots; results return as JSON.

- FUNCTIONS USED:
  - `[sys.executable, isaacsim_send.py, --raw, --timeout 200]` +
    inline code or `--file viewport_screenshot.py --arg output_path=<abs>`
  - `subprocess.run(..., capture_output, timeout=240)`;
    `json.loads(stdout)["output"]`
  - Inline RESET (stop, pump 5, USD pose reset, clock reset, engine
    switch, pump 10, print `ACTIVE-*`), PLAY (play + 120 steps, print
    `PLAYED-120`), USDA (print `USDZ=%.4f`) snippets
- UNKNOWN: the 3x send-retry protocol (discovery.md mandates it for
  silent screenshot failures under GPU load; the p2_drive.py body has
  NO retry — v14_drive.py skimmed, conformance unconfirmed).

### 18. png_stats — screenshot differencing

DOES: Turns render pairs into motion numbers — the Newton ground-truth instrument.

- FUNCTIONS USED: `mean_abs_diff(a, b)` (P2: N_DIFF/P_DIFF/END_DIFF;
  V14 same); `png_stats` is imported in p2_drive.py but unused in its body.
- UNKNOWN: `png_stats()` purpose/signature (imported-unused); the module
  lives outside the pack (isaac-sim-remote skill) and was not read.

### 19. stdlib + numpy (+ inspect) — plumbing

DOES: Local JSON/subprocess/sys plumbing, file staging, and numerics.

- FUNCTIONS USED: `json.loads` + `["output"]`; `subprocess.run`;
  `sys.executable` / `sys.path.insert`; `os.makedirs` / `os.path.join`;
  `shutil.rmtree`; `numpy` arrays for velocities + tensor `.numpy()`;
  `re`/`sys`/`math` in verifiers and `inspect` in engines p2_run (skimmed).
- UNKNOWN: none material — generic plumbing.

### 20. verify_*.py — pack's own offline gates

DOES: Local pass/fail gates over evidence JSON/TXT (11 scripts: core
  verify_p1–p5/verify_v1, engines verify_p1–p4/verify_v14).

- FUNCTIONS USED (doc-attested; bodies skimmed): gates per the SKILL.md
  table — rest 0.5, dx=5.0000 with zero z drift, turn=pi, rest speeds
  <0.003, maxdiff 0.000000, z1=0.5/vz=0/engine=physx, motion match
  0.0014, switch confirmed both ways, clean-silent/dirty-5-traits,
  9/9 with stacked rest 1.5.
- LIMITS-live-verified:
  - Predict rest height from the FULL layout: V14Cube stacks onto the
    resting P1Cube, so the gate is 1.5001, not 0.5 — and both engines
    stack identically (failures.md R2;
    engines/evidence/v14_report.txt USDZ=1.5001, END_DIFF=0.4948).
- UNKNOWN: exact per-script gate logic and thresholds (bodies skimmed
  per the 8-script full-read cap).

### 21. Standalone Kit runner (python.bat + SimulationApp) — out-of-sim boot

DOES: Boots a second Kit/USD session outside the live sim (attempted self-test and convert paths).

- FUNCTIONS USED: `python.bat` launch (process-level);
  `SimulationApp(...)` at convert-script import time.
- LIMITS-live-verified:
  - A second Kit boot beside the live sim on a 4 GB GPU stalls (~21 s
    at newton ext start), the process vanishes, the pipe never closes
    (failures.md R3) — run conversion in-session; reserve standalone
    runners for headless boxes.
  - The convert script constructs `SimulationApp` at module top level,
    so importing it live would boot a second Kit: unimportable live
    (failures.md R4). P4 mirrors the builder/audit bodies in-session
    and calls shipped RuleProfiles through the manager instead.
- UNKNOWN: the standalone/headless success path (only the failure is drilled).

## Unverified

1. `Articulation` tensor reads — SKILL.md prescribes RigidPrim/Articulation
   tensors, but zero pack scripts import Articulation.
2. `get_velocities()` shape/semantics and the angular-velocity set path
   (doc-attested only; calling bodies not in the read set).
3. Joint-angle readback API spelling (core/scripts/p3_run.py body skimmed).
4. `pxr.PhysxSchema` usage (imported, never called in read bodies).
5. `isaacsim.physics.newton` module API (probe_napi.py skimmed);
   NewtonStage/mujoco-qpos native state (explicit R1 future work);
   the `'remotesim'` switch target.
6. Full two-pass conversion incl. variant package + gain audit (blocked by
   R5/R6; p4_convert.py and probe_urdf.py bodies skimmed).
7. Transformer profile JSON schema (no profile file ships in the pack).
8. URDF importer correctness outside the manager path (only manager-open probed).
9. 3x send-retry conformance (p2_drive.py lacks it; v14_drive.py skimmed).
10. `png_stats()` function (imported-unused; module outside the pack, unread).
11. Verifier gate-logic details (11 bodies skimmed) and v1_exam setup/run
    details (skimmed).
12. Discovery's "classic failures" missing-PhysicsScene and
    scaled-static-collider/translate-first have no failures.md entry in the
    merged pack.
13. X14 cross-val protocol (SKILL.md cites 7/7; no x14 scripts or evidence
    in the pack).
14. XformCache mid-play staleness (docstring/discovery only; no isolating evidence).
15. Newton 30-pump-step enable procedure body (discovery-attested; the
    enabling script is not in the read set).
16. Standalone/headless runner success path (only the failure is drilled).

## Sources-read

Root docs (3):

- action-reasoner/skills/physics/SKILL.md
- action-reasoner/skills/physics/failures.md
- action-reasoner/skills/physics/discovery.md

Scripts, fully read (8 of 36):

- action-reasoner/skills/physics/core/scripts/p1_setup.py
- action-reasoner/skills/physics/core/scripts/p1_run.py
- action-reasoner/skills/physics/core/scripts/p2_run.py
- action-reasoner/skills/physics/core/scripts/p3_setup.py
- action-reasoner/skills/physics/core/scripts/p5_run.py
- action-reasoner/skills/physics/engines/scripts/p2_drive.py
- action-reasoner/skills/physics/engines/scripts/p3_probe.py
- action-reasoner/skills/physics/engines/scripts/p4_preflight.py

Evidence, fully read (12):

- action-reasoner/skills/physics/core/evidence/p1_run.json
- action-reasoner/skills/physics/core/evidence/p2_run.json
- action-reasoner/skills/physics/core/evidence/p3_run.json
- action-reasoner/skills/physics/core/evidence/p4_run.json
- action-reasoner/skills/physics/core/evidence/p5_run.json
- action-reasoner/skills/physics/core/evidence/v1_exam.json
- action-reasoner/skills/physics/engines/evidence/p1_run.json
- action-reasoner/skills/physics/engines/evidence/p2_run.json
- action-reasoner/skills/physics/engines/evidence/p3_run.json
- action-reasoner/skills/physics/engines/evidence/p4_run.json
- action-reasoner/skills/physics/engines/evidence/p2_report.txt
- action-reasoner/skills/physics/engines/evidence/v14_report.txt

Skim method for the other 28 scripts: filename + full import grep across
all 36 scripts, plus import-block/call-site grep for p4_convert.py and
probe_urdf.py (transformer names). No other existing file was modified.
