# physics — Discovery Notes (live-verified)

---

# Part: core (merged from `physics-master`)

# Skill 1 PHYSICS Master — Discovery

## Scope
Owns everything about bodies in motion: gravity, contacts, stacking,
joint drives, velocities, determinism. A trained agent loading this pack
must set up any rigid-body scene and predict its outcome without guessing.
Reads the world through Skill 0 WORKSPACE-SENSE; writes through live USD +
physics APIs (catalog actions sidelined per user direction).

## Competence goals (must pass unaided after training)
1. Build a gravity scene from nothing: PhysicsScene, static ground,
   dynamic bodies with correct same-prim RigidBody+Collision+Mass.
2. Step physics deterministically and read SIMULATED state (RigidPrim /
   Articulation tensors), never authored USD transforms.
3. Predict and verify: drop/settle heights, rest contact, joint motion
   under drives, velocity set post-play.
4. Diagnose the classic failures: missing PhysicsScene, scaled static
   collider (translate-first), velocity set pre-play, XformCache readback.

## Drill plan (each: setup + run + local verify + evidence)
- P1 gravity drop: 1 m cube from z=2 onto plane -> rest z=0.5. Proves
  scene, stepping path, live readback, timeline advance.
- P2 velocity: post-play linear velocity -> displacement matches v*t.
- P3 joint drive: revolute hinge + target velocity -> angle advances.
- P4 stack: two cubes settle without jitter/explosion (stabilization on).
- P5 determinism: same drill twice -> identical trajectories.

## Verified sources (live, this machine)
- physics-simulation skill: Scene config, same-prim rule, translate-first
  static colliders, SimulationContext.step(render=True), Part 7 readback.
- Active engine recorded per drill (Newton auto-switch expected on full.kit).

---

# Part: engines (merged from `physics-x`)

# Physics-X — Discovery Notes (live-verified, 6.0.0)

## Newton on this build (facts, not docs)
- Enable: app_utils.enable_extension("isaacsim.physics.
  newton") + 30 pump steps (Warp/MuJoCo kernels compile on
  cuda:0, ~1 min first time). API: get_available_physics_
  engines() -> [(name, active)], get_active_physics_engine()
  -> "newton"/"physx", get_default_engine(), switch_physics_
  engine(name: physx|newton|remotesim). Switch-back to PhysX
  rebuilds fine (re-drop 0.5000 exact).
- Plain rigid bodies simulate under Newton with ZERO extra
  schema — but NOTHING reads back: RigidPrim tensors raise
  (no Newton tensor backend, log-verified) and USD keeps
  authored values. Render is the only easy observable;
  native state (NewtonStage/mujoco qpos) is future work.
- Scene prims already carry newton:* attrs (gravityEnabled,
  maxSolverIterations, timeStepsPerSecond) once the ext
  loads. Log note: "Newton timestep from USD: 1000Hz".
- MuJoCo dependency skew warning (warp 3.12 vs ~=3.8) is
  benign for rigid drops.

## Equivalence drill design
- Render-equivalence protocol (P2/V14 drivers): per engine
  reset -> switch -> shot A -> play N -> shot B -> USD read;
  gate cross-engine motion match (< 1.0), end-frame match
  (< 0.5), plus engine-specific USD facts (Newton pinned,
  PhysX rest). P2 numbers: 2.0117 vs 2.0131, end 0.1068.
- Local drivers need send retry (3x on empty/error output):
  screenshot sends under GPU load can fail silently.
- Predict rest from the FULL layout (R2 stacking); cubes
  dropped at the same XZ stack.

## Conversion on 6.0.0 (blocked paths, shippable piece)
- Shipped transformer profiles: isaacsim_structure,
  merge_mesh, mjc_to_physx, urdf_to_mjc_physx. MISSING:
  physx_to_mjc_conversion (needs newer build, R5).
- Manager opens inputs via Usd.Stage.Open; no URDF/MJCF Sdf
  plugin is registered even with importer exts on (R6) —
  URDF-profile runs fail before any rule.
- P4 drills preflight (offline USD, in-session pxr): clean
  asset silent, dirty asset fires inertia/negscale/orphan/
  ref/zerosize. Full passes await a newer build or a
  headless runner box (R3 4GB contention).

## Session notes
- Zero crashes; 1 bridge-stall-equivalent (orphaned pipe on
  the hung standalone run, terminated cleanly).
- v14 shots double as Newton motion evidence (artifact set:
  *_A.png/*_B.png per engine per drill).
