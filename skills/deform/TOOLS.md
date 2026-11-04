# Deform Tool Knowledge (2026-11-04)

> Exhaustive reference: `TOOLS_REF.md` — 15 tools · 61 functions/accessors · 33 knobs · 21 limits · 19 unknowns.

## Tools

### DeformablePrim (isaacsim.core.experimental.prims)
- DOES: authors a volume-deformable body on an Xform and exposes nodal tensor reads.
- FUNCTIONS USED:
  - `DeformablePrim(path, deformable_type="volume")` (d1_build, d1_drive, d1_probe, d1_diag)
  - `apply_physics_materials(material)` (d1_build, d1_probe)
  - `get_nodal_positions()` -> 3-tuple (sim, collision, rest); unpack `[0][0]` (d1_drive)
  - `get_nodal_velocities()` -> single array (d1_drive)
  - `get_nodal_stresses()` -> single array (d1_drive)
  - `get_element_indices()` -> 3-tuple; `[0]` is sim-mesh tets (d1_drive)
  - `is_physics_tensor_entity_valid()`, `.valid`, `._physics_deformable_body_view` (d1_diag)
- LIMITS-live-verified:
  - Cooking FATALS (native crash, no traceback) when PhysX is not the active engine (failures.md F1).
  - Tensor backend never binds without an explicit `/World/PhysicsScene`; reads raise "Failed to get ... from backend" even with valid views (failures.md F3).
  - Nodal position/element getters return tuples, not arrays; `.numpy()` on the tuple raises AttributeError (failures.md F4).
  - Backend buffers need real post-play physics steps; first read after 5 steps raises — retry across warmup (failures.md F4).
  - Must rebuild the deformable AFTER any scene change (SKILL.md authoring recipe; failures.md F3).
- UNKNOWN:
  - `deformable_type="surface"` behavior — drill uses volume only.
  - `get_world_poses()` on a deformable — probed in d1_probe.py but no result recorded in evidence/.

### VolumeDeformableMaterial (isaacsim.core.experimental.materials)
- DOES: defines stiffness/friction response of the volume body.
- FUNCTIONS USED:
  - `VolumeDeformableMaterial(path, youngs_moduli=[...], poissons_ratios=[...], dynamic_frictions=[...], static_frictions=[...])` (d1_build, d1_probe)
- LIMITS-live-verified:
  - Young's modulus must scale with body size: 1 m cone at E=1e4 Pa is jelly (sinks 1/3 under ground), at E=1e6 Pa effectively rigid (zero squash); sweet spot E=1e5 (failures.md F5).
- UNKNOWN:
  - Poisson-ratio / friction sensitivity — only 0.3/0.5 drill-proven.
  - Behavior for bodies much smaller or larger than 1 m.

### SimulationManager (isaacsim.core.simulation_manager)
- DOES: selects device/engine and reports backend state.
- FUNCTIONS USED:
  - `SimulationManager.set_device("cuda")` before authoring (d1_build)
  - `SimulationManager.get_active_physics_engine()` (d1_build, d1_drive, d1_probe, d1_diag)
  - `SimulationManager.get_available_physics_engines()` (d1_probe)
  - `SimulationManager.switch_physics_engine("newton")` (d1_probe)
  - `SimulationManager.get_backend()` (d1_probe)
  - `SimulationManager._physics_sim_view__warp` sim-view validity check (d1_diag)
- LIMITS-live-verified:
  - NEVER `switch_physics_engine` with a loaded stage — same NULL-stage native fatal as F1 (failures.md F1).
  - After any enable/switch, re-query `get_active_physics_engine()` before stepping; never assume (failures.md F2).
  - `set_device("cuda")` must precede stage setup/deformable authoring or the tensor backend never binds (failures.md F3).
- UNKNOWN:
  - `set_device("cpu")` for deformables — drill is CUDA-only.
  - `get_backend()` return values beyond the probe print — no recorded output.

### app_utils (isaacsim.core.experimental.utils.app)
- DOES: drives extensions, timeline, and stepped physics.
- FUNCTIONS USED:
  - `play(commit=True)` / `play()` / `stop()` (d1_drive, d1_probe, d1_diag)
  - `update_app_async(steps=N)` awaited stepping (d1_drive, d1_probe, d1_diag)
  - `enable_extension("isaacsim.physics.newton")` in-session on empty stage (d1_probe; failures.md F2)
- LIMITS-live-verified:
  - `play()` vs `play(commit=True)` both step physics; commit was NOT the F3 fix (failures.md ruled-out).
  - Fixed small step guesses are unreliable for first reads — warm up with read retries, 12x10 steps pattern (failures.md F3/F4).
- UNKNOWN:
  - Exact minimum warmup step count — drill uses retry-until-success, not a proven minimum.

### stage_utils (isaacsim.core.experimental.utils.stage)
- DOES: defines the Xform prim that hosts the deformable.
- FUNCTIONS USED:
  - `stage_utils.define_prim("/World/D1Soft", "Xform")` (d1_build, d1_probe)
- LIMITS-live-verified: none (no failures.md entry).
- UNKNOWN:
  - Whether other prim types can host a volume DeformablePrim.

### prim_utils (isaacsim.core.experimental.utils.prim)
- DOES: prim helpers (imported in d1_probe.py but never called there).
- FUNCTIONS USED: none observed.
- LIMITS-live-verified: none.
- UNKNOWN: entire module surface — not drill-exercised.

### GroundPlane + Mesh (isaacsim.core.experimental.objects)
- DOES: ground collider and cooking-mesh geometry for the deformable.
- FUNCTIONS USED:
  - `GroundPlane("/World/D1Ground")` (d1_build, d1_probe)
  - `Mesh("/World/D1Soft/mesh", primitives="Cone", positions=[0,0,1.5])` (d1_build, d1_probe)
- LIMITS-live-verified: none directly; cone geometry anchors the F5 stiffness scale (failures.md F5).
- UNKNOWN:
  - Non-cone primitives as deformable cooking meshes.
  - Drop heights other than 1.5 m.

### UsdPhysics.Scene + PhysxSceneAPI + Gf (pxr)
- DOES: explicit PhysicsScene with gravity, 60 Hz, TGS solver.
- FUNCTIONS USED:
  - `UsdPhysics.Scene.Define(st, "/World/PhysicsScene")`, `CreateGravityDirectionAttr`, `CreateGravityMagnitudeAttr` (d1_build)
  - `PhysxSchema.PhysxSceneAPI.Apply(...)`, `CreateTimeStepsPerSecondAttr(60)`, `CreateSolverTypeAttr("TGS")`, `CreateEnableStabilizationAttr(True)` (d1_build)
- LIMITS-live-verified:
  - Rigid bodies tolerate a missing scene; the deformable tensor backend NEVER binds without one (failures.md F3).
- UNKNOWN:
  - Non-TGS solvers or rates other than 60 Hz for deformables.

### omni.usd
- DOES: stage access for prim validity checks and cleanup.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()`, `GetPrimAtPath`, `RemovePrim` (d1_build, d1_probe, d1_diag)
- LIMITS-live-verified: none (no failures.md entry).
- UNKNOWN: none — thin usage, fully observed.

### omni.timeline
- DOES: confirms the timeline is actually playing during diagnosis.
- FUNCTIONS USED:
  - `omni.timeline.get_timeline_interface().is_playing()` (d1_diag)
- LIMITS-live-verified: none (no failures.md entry).
- UNKNOWN: none — single observed call.

### PhysX cooking interface (implicit via DeformablePrim)
- DOES: `cook_auto_deformable_body(path)` cooks sim/collision meshes at authoring time (deformable_prim.py:164, per failures.md F1).
- FUNCTIONS USED: none called directly; invoked inside `DeformablePrim.__init__`.
- LIMITS-live-verified:
  - Stage handle is NULL under Newton-active sims -> native fatal on member lookup (failures.md F1).
- UNKNOWN:
  - Direct calls to the cooking interface — never drill-exercised.

### Kit boot CLI flags
- DOES: selects/enables physics engines at launch.
- FUNCTIONS USED:
  - `--/exts/isaacsim.core.simulation_manager/default_engine=newton` (failures.md F2)
  - `--enable isaacsim.physics.newton` (failures.md F2)
- LIMITS-live-verified:
  - The `default_engine=newton` flag alone does NOT activate Newton (`isaacsim.physics.newton` ships disabled); must also `--enable` it (failures.md F2).
- UNKNOWN: none — flag interaction fully drill-proven.

### py-spy
- DOES: native crash-trace sampling; proved the F1 NULL-stage fatal location.
- FUNCTIONS USED:
  - Crash trace showing MainThread inside `_check_or_apply_deformable_schema` <- `DeformablePrim.__init__` (failures.md F1)
- LIMITS-live-verified: none (diagnostic tool, no failures.md entry against it).
- UNKNOWN:
  - Invocation/command-line used — not recorded in the pack.

### numpy
- DOES: array conversion and snapshot statistics for nodal reads.
- FUNCTIONS USED:
  - `_np.asarray(x.numpy(), dtype=float)`, `mean/min/max/std`, `abs` (d1_drive, d1_probe)
- LIMITS-live-verified: none (no failures.md entry).
- UNKNOWN: none — standard usage, fully observed.

### verify_d1.py local gate harness (json/sys)
- DOES: gates recorded evidence with 10 checks (engine, topology, drop, rest, squash, bulge, falling, at-rest, stress, tets).
- FUNCTIONS USED:
  - `json.load`, gate lambdas over `evidence/d1_nodes.json`, exit 0/1 (verify_d1.py)
- LIMITS-live-verified:
  - Never gate x/y: landing tip-over varies run to run (0.02 m vs 0.5 m drift); z/shape/stress/velocity gates are stable (failures.md F5).
  - Must gate squash AND rest-on-ground together — either alone admits jelly-sink or rigid-fall (failures.md F5).
- UNKNOWN: none — 10/10 gates drill-proven, 3/3 bit-identical (SKILL.md).

## Unverified

- Newton deformable runs (pre-cooked USD on a Newton-from-boot sim with render-observation verification) — designed as future work, unbuilt (SKILL.md Limitations; failures.md F1 prevention).
- Fabric Scene Delegate effect on reads — ruled OUT for sim-mesh reads (viz only), but never directly tested (failures.md ruled-out).
- Warp CUDA-graph compile message — classified as one-time JIT noise, not an error (failures.md ruled-out).
- Upstream example `$ISAAC_SIM_DIR/standalone_examples/api/isaacsim.core.experimental.api/deformable_stress_visualization.py` — cited in SKILL.md References but not present in the pack; not read.
- Minimum warmup step count for first successful tensor read — drill uses retry-until-success (12x10), no fixed minimum proven.
- Exact tet-count expectation generality — `[1, 2544, 4]` shape gate is cone-specific (verify_d1.py + evidence/d1_nodes.json).

## Sources-read

- action-reasoner/skills/deform/SKILL.md (full)
- action-reasoner/skills/deform/failures.md (full)
- action-reasoner/skills/deform/scripts/d1_build.py (full)
- action-reasoner/skills/deform/scripts/d1_drive.py (full)
- action-reasoner/skills/deform/scripts/d1_probe.py (full)
- action-reasoner/skills/deform/scripts/d1_diag.py (full)
- action-reasoner/skills/deform/scripts/verify_d1.py (full)
- action-reasoner/skills/deform/evidence/d1_nodes.json (full, context)
