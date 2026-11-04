# Workspace-Sense Tool Knowledge (2026-11-04)

> Exhaustive reference: [TOOLS_REF.md](TOOLS_REF.md) — 8 tools, ~80 functions, ~30 knobs, EKB rules per tool, limits + unknowns, all claims tagged verified/probable/theoretical. (This file stays the compact summary.)

Pack contract: `sense.py` runs INSIDE Isaac Sim via the bridge and prints one
JSON telemetry snapshot; `verify_*.py` / `co_verify.py` run LOCALLY on
`evidence/*.json` envelopes (`{status: "ok", output: "<stdout>"}`).
No SKILL.md / README.md / discovery.md exists in this pack (only
`failures.md`); drill intent below is reconstructed from script docstrings.

## Tools

### 1. pxr USD core — `Usd`, `UsdGeom`, `UsdPhysics`, `Gf` (in-sim)
DOES: Authors drill scenes and reads authored-state pose, bounds, physics
flags, and joint anchors off the live stage.
FUNCTIONS USED:
- Stage walk: `stage.Traverse()`, `stage.GetPrimAtPath(path)`,
  `stage.RemovePrim(path)`, `prim.GetPath()/GetTypeName()/GetChildren()/
  GetName()/GetAttribute()/IsValid()/HasAPI()/GetAppliedSchemas()`,
  `stage.GetRootLayer().GetIdentifier()`
- Authored pose: `Usd.TimeCode.Default()`, `UsdGeom.XformCache(tcode)`,
  `GetLocalToWorldTransform(prim)`, `ExtractTranslation()/
  ExtractRotation().GetQuaternion()/GetImaginary()/GetReal()`
- Bounds: `UsdGeom.BBoxCache(tcode, [Tokens.default_, "render", "proxy"])`,
  `ComputeWorldBound(prim).ComputeAlignedRange()`, `GetMin()/GetMax()`
- Scene authoring: `UsdGeom.Cube/Cylinder/Plane.Define`,
  `GetSizeAttr()/GetRadiusAttr()/GetHeightAttr()/GetAxisAttr()`,
  `CreateWidthAttr()/CreateLengthAttr()`,
  `UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(...))`,
  `Gf.Vec3f/Gf.Quatf`, `UsdGeom.Tokens.x`
- Physics authoring/flags: `UsdPhysics.Scene.Define`,
  `CreateGravityDirectionAttr()/CreateGravityMagnitudeAttr()`,
  `RigidBodyAPI.Apply/HasAPI/GetKinematicEnabledAttr()`,
  `CollisionAPI.Apply/HasAPI`, `MassAPI.Apply/GetMassAttr()`,
  `RevoluteJoint.Define`, `Joint(prim)`, `GetBody0Rel()/GetBody1Rel()`,
  `GetLocalPos0Attr()/GetLocalPos1Attr()/GetLocalRot0Attr()/
  GetLocalRot1Attr()/GetAxisAttr()`, `UsdPhysics.Tokens.x`
- Probe-only flags: `HasAPI(ArticulationRootAPI/DriveAPI/RevoluteJoint/
  FixedJoint)` (`probes/dup_inventory.py`, fully read)
LIMITS-live-verified:
- `BBoxCache(time, ["default"])` excludes explicit `"render"`/`"proxy"`
  purpose prims: S3 cube sensed bbox ±FLT_MAX (empty) — failures.md V1;
  fix live in `sense.py:87` (query `["default", "render", "proxy"]`),
  covered by `evidence/co_sense_p3.json` (S3/V1 drill).
- USD `XformCache`/`BBoxCache` reads are AUTHORED-state only while playing;
  simulated pose/velocities must come from RigidPrim tensors — `sense.py`
  docstring v0.2; proven by `evidence/d3_hot.json` (`live.*.source=
  "tensor"`) vs `evidence/d3_sense0.json` (`live=null` at clock=0).
- `ComputeLocalBound` returns WORLD-frame bounds on this Kit build, so
  `_site_of` derives local range as world bbox minus body translation —
  `sense.py:21-27` live note; anchor-site assertions in
  `evidence/co_sense_p3.json` checks (`co_verify.py:109-112`) pass on it.
- Rotated bodies get inflated world bboxes; site label is approximate and
  prefixed `rotated:` — `sense.py:36-57` live note.
- `"guide"` purpose stays excluded by design (guides are not physical) —
  `sense.py:85-87`; no drill covers guides, so exclusion effect is
  asserted but unmeasured (see Unverified).
UNKNOWN:
- Whether other Kit builds need more purpose tokens or fix ComputeLocalBound.
- Site-label accuracy for scaled, skewed, or articulated bodies; the
  `rotated:` path has no calibrated tolerance and no drill assertion.
- Kinematic-enabled bodies and `mass=None` records are emitted but never
  asserted by any verifier.

### 2. `omni.usd` (in-sim)
DOES: Single entry point to the live stage for every in-sim script.
FUNCTIONS USED:
- `omni.usd.get_context().get_stage()`; `None`/falsy stage →
  `{"errors": ["no stage open"]}` (`sense.py:70-74`)
LIMITS-live-verified: (none beyond the no-stage guard; omit further)
UNKNOWN:
- Behavior with multiple open stages / non-`/World` roots — no drill covers it.

### 3. `omni.timeline` (in-sim)
DOES: Reads or resets the play clock that gates live-vs-edit sensing.
FUNCTIONS USED:
- `omni.timeline.get_timeline_interface()`,
  `get_current_time()/set_current_time(0.0)`,
  `is_playing()/is_stopped()/is_paused()` (guarded by `hasattr` in
  `probes/dup_inventory.py`, fully read)
LIMITS-live-verified:
- `live=null` at clock=0 (edit state); `source="rest"` when stopped with
  clock>0; `source="tensor"` while playing — `sense.py:190-193`,
  proven by `evidence/d3_sense0.json` (null), `d3_senseB/C.json`
  (`rest`), `d3_hot.json` (`tensor`); asserted in
  `verify_drill03b.py` Phases 1-2.
UNKNOWN:
- Paused-mid-play (`is_paused`) vs stopped-with-clock>0 tensor semantics —
  `rested` treats any non-playing clock>0 as rest; paused-state tensor
  freshness unproven.

### 4. `isaacsim.core.experimental.utils.app` as `app_utils` (in-sim)
DOES: Play-state queries, sim stop, and fallback physics stepping.
FUNCTIONS USED:
- `app_utils.is_playing()` (timeline `playing` flag, `sense.py:78`)
- `app_utils.stop()` (reset to edit before Drill 03, `drill03_setup.py:41`)
- `await app_utils.update_app_async(steps=N)` (step fallback,
  `drill03_step.py:20`)
LIMITS-live-verified:
- `SimulationContext.step` path can be unavailable in-sim; scripts fall back
  to `await update_app_async(steps)` and print a `STEP-FALLBACK` marker —
  `drill03_step.py:10-20` live-defensive path.
UNKNOWN:
- Numerical equivalence of `sim.step(render=True)` vs `update_app_async`
  stepping — verifiers accept either via the `via=` tag without comparing.

### 5. `isaacsim.core.experimental.prims.RigidPrim` (in-sim)
DOES: Tensor source of SIMULATED world poses and velocities for all rigid bodies.
FUNCTIONS USED:
- `RigidPrim(paths=[...])` multi-body (`sense.py:196`) and
  `RigidPrim(paths="/World/LiveCube")` single-path (`drill03_step.py:8`)
- `rp.get_world_poses()[0].numpy()`, `rp.get_velocities()[0].numpy()`
  (`.numpy()` tensor→array conversion on both)
LIMITS-live-verified:
- `get_velocities()` can raise live; `sense.py:200-204` catches it and emits
  `linvel/angvel=null` (pose still reported).
- Two-body same-fall agreement proven to 1e-6 (`evidence/d3_senseB.json`
  gap exactly 2.0) and rested z=0.5±0.05 (`evidence/d3_senseC.json`);
  in-flight `VEL-REPORT z/vz/instdiff` proven by `evidence/d3_vel.json` —
  all asserted in `verify_drill03b.py` Phases 2-3.
UNKNOWN:
- Conditions under which `get_velocities()` raises (pose-only fallback
  trigger) are uncharacterized.
- Tensor reads while paused (not stopped, not playing) are unproven.

### 6. `isaacsim.core.api.simulation_context.SimulationContext` (in-sim)
DOES: Preferred Drill 03 stepper (`sim.step(render=True)` × N, stays playing).
FUNCTIONS USED:
- `SimulationContext.instance()`, `SimulationContext()`,
  `sim.step(render=True)` (`drill03_step.py:11-17`)
UNKNOWN:
- When `instance()` returns None vs an existing context, and when the
  constructor path itself fails (only the fallback marker is observed).
- Effect of `render=True/False` on sensed state — only `True` is drilled.

### 7. Bridge transport — `isaacsim_send.py` + evidence envelope (CLI/JSON)
DOES: Ships in-sim scripts to Isaac Sim and captures printed markers/JSON
into `evidence/*.json` as `{status, output}`.
FUNCTIONS USED:
- `isaacsim_send.py --arg STEPS=N` injects globals (`STEPS` in
  `drill03_step.py:1-4`)
- Stdout markers parsed downstream: `CLEAN-SLATE-OK removed=N`,
  `DRILL02-SETUP-OK`, `DRILL03-SETUP-OK`, `LIVE-TRUTH z=.. vz=.. via=..`,
  `VEL-REPORT z=.. vz=.. instdiff=..`, `PROBE_JSON:{...}`
- Envelope parse: `env["status"]=="ok"` then `json.loads(env["output"])`
  (`co_verify.py:23-28`, `verify_drill03b.py:24-28`)
LIMITS-live-verified:
- Bridge output encoding varies: the loader tries `utf-8-sig`, `utf-16`,
  then `utf-8` — `co_verify.py:13-20`, `verify_drill03b.py:14-21`;
  needed by real `evidence/*.json` files.
UNKNOWN:
- Full bridge CLI surface (timeouts, retries, arg types beyond `STEPS`,
  failure `status` values) — nothing in-pack documents it; verifiers only
  handle `status != "ok"` as fatal.

### 8. Local verifier harness — stdlib `json`/`sys`/`re` (local)
DOES: Offline assertions over evidence envelopes; exit 0 + `*-PASS` or
exit 1 + `*-FAIL` with diff lines.
FUNCTIONS USED:
- `json.load/json.loads`, `sys.exit(main())`, `re.search` for VEL-REPORT
- `_close(a, b)` with `TOL=1e-3` (`co_verify.py:10,30-31`); multi-encoding
  `_load` (see Tool 7)
- Exact-match assertions: body pos/mass/rigid/collision flags, static
  ground flags, `physics_scene=="/World/PhysicsScene"`, hinge
  type/bodies/anchors/axis/sites (`co_verify.py:34-112`); hot/rest/velocity
  three-phase gate (`verify_drill03b.py:31-99`)
LIMITS-live-verified:
- Verifiers require zero probe `errors[]` (`co_verify.py:82-83`,
  `verify_drill03b.py:49`); any `live:` capture failure fails the drill.
UNKNOWN:
- `verify_drill01.py`, `verify_drill02.py`, `verify_drill03.py` (v1 suite)
  were skimmed by name+imports only — their exact assertions vs the v2
  `verify_drill03b.py` gate are unconfirmed; presumed superseded, not proven.

## Unverified

- Pack has no SKILL.md/README/discovery.md: the drill contract (D1/D2/D3,
  co-drills P1-P4, S3/V1 purpose drill) and cross-validation expectations
  are reconstructed from code, not stated anywhere.
- `probes/dup_detail.py`, `probes/dup_inventory.py` target `M4Bot/M4Block/
  GraspJoint/Hinge1/2` scenes no drill in this pack builds — cross-pack
  scene coverage is unknown (dup_detail skimmed only; dup_inventory fully
  read but its target scene is absent from `evidence/`).
- `drill_cube.py` (Drill 01 setup), `drill03_vel.py` (VEL-REPORT author)
  skimmed by name+imports only — exact authored prims/flags unconfirmed.
- `UsdPhysics.Scene` gravity beyond direction/magnitude, solver settings,
  and multi-scene stages are unused and unproven.
- Anchor `quat` records (`anchor0/1_quat`) are emitted by `sense.py` but
  never asserted by any fully-read verifier.
- `clean_slate.py` path list is the pack's only teardown; stray prims
  outside its 22 paths (e.g. `/World/LiveCube2`, P5/V1 leftovers) survive
  a clean — `/World/LiveCube2` IS in drill03_setup's own clear list but
  NOT in `clean_slate.py:5-11`.

## Sources-read

Fully read (9):
- `action-reasoner/skills/workspace-sense/failures.md` (V1 entry)
- `action-reasoner/skills/workspace-sense/scripts/sense.py` (210 lines)
- `action-reasoner/skills/workspace-sense/scripts/co_verify.py` (106 lines)
- `action-reasoner/skills/workspace-sense/scripts/verify_drill03b.py` (92 lines)
- `action-reasoner/skills/workspace-sense/scripts/probes/dup_inventory.py` (122 lines)
- `action-reasoner/skills/workspace-sense/scripts/drill_joint.py` (37 lines)
- `action-reasoner/skills/workspace-sense/scripts/drill03_setup.py` (38 lines)
- `action-reasoner/skills/workspace-sense/scripts/drill03_step.py` (24 lines)
- `action-reasoner/skills/workspace-sense/scripts/clean_slate.py` (17 lines)

Skimmed by name + imports only (6):
- `action-reasoner/skills/workspace-sense/scripts/drill_cube.py`
- `action-reasoner/skills/workspace-sense/scripts/drill03_vel.py`
- `action-reasoner/skills/workspace-sense/scripts/verify_drill01.py`
- `action-reasoner/skills/workspace-sense/scripts/verify_drill02.py`
- `action-reasoner/skills/workspace-sense/scripts/verify_drill03.py`
- `action-reasoner/skills/workspace-sense/scripts/probes/dup_detail.py`

Absent (skipped per instructions):
- `SKILL.md` / `README.md` / `discovery.md` — none exist in pack root.
