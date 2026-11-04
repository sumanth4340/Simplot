# deform -- Failure Catalog (live-verified, Isaac Sim 6.0 / Kit 110)

## F1: DeformablePrim cooking FATALS on Newton-active sim (NULL-stage)
- FAILURE: `DeformablePrim("/World/D1Soft", deformable_type="volume")`
  hard-crashed Kit (connection reset, no traceback) on a sim where
  `get_active_physics_engine()` reported `newton`.
- CAUSE: volume/surface authoring calls
  `get_physx_cooking_interface().cook_auto_deformable_body(path)`
  (deformable_prim.py:164). With Newton active the PhysX cooking
  stage handle is NULL -> native
  `attempted member lookup on NULL TfWeakPtr<UsdStage>`. Proven by
  py-spy crash trace (MainThread inside `_check_or_apply_deformable_schema`
  <- `DeformablePrim.__init__`) and by the identical script passing
  on PhysX (`D1-BUILD-OK valid=True`).
- RECOVERY: author/cook deformables only with PhysX active. Never
  `switch_physics_engine` with a loaded stage either (same NULL-stage
  fatal). See d1_build.py (asserts ACTIVE: physx).
- PREVENTION: D1 is a PhysX drill. Newton deformable runs (pre-cooked
  USD loaded on a Newton-from-boot sim) are future work; reads there
  are Fabric-only/stale per `newton` skill, so verification would be
  render-observation based.

## F2: `default_engine=newton` boot flag alone does not activate Newton
- FAILURE: relaunch with
  `--/exts/isaacsim.core.simulation_manager/default_engine=newton`
  still reported `ACTIVE: physx`.
- CAUSE: `isaacsim.physics.newton` ships disabled; the flag only
  selects among LOADED engines.
- RECOVERY: also `--enable isaacsim.physics.newton` at boot, or
  `app_utils.enable_extension("isaacsim.physics.newton")` in-session
  on an empty stage (verified: `ACTIVE: newton`,
  `ENGINES: [('physx', False), ('newton', True)]`).
- PREVENTION: after any enable/switch, re-query
  `get_active_physics_engine()` before stepping; never assume.

## F3: deformable tensor reads fail without explicit PhysicsScene
- FAILURE: view/simview valid, timeline playing, yet
  `get_simulation_nodal_positions()` raised
  `Failed to get deformable body simulation mesh nodal positions
  from backend` for 120+ app-steps.
- CAUSE: scene had no `/World/PhysicsScene`. The official example
  gets one from the `sunlight` stage template; a bare stage has none
  and the deformable backend never binds. (Rigid bodies tolerate the
  missing scene; deformables do not.)
- RECOVERY: define `UsdPhysics.Scene` + `PhysxSceneAPI` (gravity,
  60Hz, TGS) and `SimulationManager.set_device("cuda")` BEFORE
  authoring the deformable; rebuild the deformable after. First read
  then succeeds after ~10 steps. See d1_build.py.
- PREVENTION: D1 build asserts `/World/PhysicsScene` valid; drive
  warms up with read retries (12x10 steps) instead of a fixed guess.

## F4: nodal getters return tuples; backend needs real steps
- FAILURE: `get_nodal_positions().numpy()` -> AttributeError (tuple);
  first read after 5 steps -> backend exception.
- CAUSE: `get_nodal_positions`/`get_element_indices` return
  3-tuples (sim, collision, rest), each `(N, NpB, 3)`; velocities and
  stresses return single arrays. Backend buffers populate only after
  real physics steps post-play.
- RECOVERY: unpack `[0]` (sim mesh) + `[0]` (first body); retry reads
  across warmup steps. See d1_drive.py `sim_pos()`/`sim_vel()`.
- PREVENTION: check return arity in deformable_prim.py before coding
  reads; never single-shot a first read right after play().

## F5: E=1e4 cone sinks 1/3 under the ground; E=1e6 never deforms
- FAILURE: youngs 1e4 -> settled zmin=-0.33 (jelly: self-weight
  stress ~ E). youngs 1e6 -> zero measurable squash (h 1.000->0.999).
- CAUSE: 1m-tall cone, self-weight ~10kPa. 1e4 Pa is the 100%-strain
  regime; 1e6 Pa is effectively rigid at this scale.
- RECOVERY: E=1e5 sweet spot: rest zmin=-0.040, height 1.000->0.986,
  spread +1.2% (bulge), stress max ~24.6k. See verify_d1.py gates.
- PREVENTION: scale E to body size; gate squash AND rest-on-ground
  together (either alone admits jelly-sink or rigid-fall). Do not
  gate x/y: landing tip-over varies run to run (0.02m vs 0.5m drift
  observed); z/shape/stress/velocity gates are stable.

## Ruled OUT during F1-F5 (do not chase)
- Newton-from-boot for D1: unnecessary; D1 is PhysX by design.
- FSD (Fabric Scene Delegate): affects sim-mesh VIZ only, not reads.
- `play()` vs `play(commit=True)`: both step physics; commit=True kept
  per skill guidance but was not the F3 fix (PhysicsScene was).
- Warp CUDA-graph compile message (`load on device 'cuda:0' ...
  compiled`): one-time JIT noise in drive output, not an error.
