# physics — Failure Catalog (live-verified)

Failure IDs are namespaced per part: core F1-F4, engines R1-R6. Script paths below are relative to each part dir.

---

# Part: core (merged from `physics-master`)

# Physics Master — Failure Catalog (live-verified)

## F1: SimulationContext.step inside Kit app
- FAILURE: `SimulationContext().step(render=True)` raises
  `AttributeError: 'NoneType' object has no attribute 'get_physics_dt'`.
- SYMPTOMS: P1 run fell back; same crash signature as the old executor bug.
- CAUSE: Standalone SimulationContext does not own the physics loop inside
  a Kit app; the Kit timeline/SimulationManager does.
- RECOVERY: `app_utils.play()` + `await update_app_async(steps=N)` + verify
  `timeline.get_current_time()` advanced. Proven: exactly 2.000 s over
  120 steps, correct gravity settle (P1 evidence).
- PREVENTION: Never step via SimulationContext inside Kit; always confirm
  time advance in the motion report.

## F2: velocity set pre-play is ignored
- P2 sets velocity strictly after play() per skill gotcha 5 (verified pattern).

## F3: RigidPrim velocity API spellings (Kit 110 experimental)
- FAILURE: `set_linear_velocities` / `get_linear_velocities` do not exist
  (`AttributeError`); guessed from legacy API names.
- CAUSE: Experimental `RigidPrim` uses combined `set_velocities(
  linear_velocities, angular_velocities)` and `get_velocities()` returning
  a (linear, angular) tuple. Verified against installed
  `isaacsim/core/experimental/prims/impl/rigid_prim.py`.
- PREVENTION: Read the installed ext source before calling; never trust
  remembered API spellings.

## F4: stop() does not restore pre-play state
- FAILURE: P5 trial 2 started at z=0.5 (trial 1's rest state) instead of
  z=2.0; programmatic `app_utils.stop()` leaves stage + clock at end state.
- SYMPTOMS: Second play() continues from previous end state, silently.
- CAUSE: Kit timeline stop via API does not perform the edit-state restore
  (or the restore path the Stop button uses is not triggered here).
- RECOVERY: Before each trial, reset body poses explicitly via USD
  translate ops and `timeline.set_current_time(0.0)`.
- PREVENTION: Never assume stop() resets; every repeat-trial drill owns
  its reset. P5 evidence shows the before/after.

## F5: play() + update_app_async(steps=N) runs N + slip frames
- FAILURE: Drill 03 expected exactly 20 steps of fall (z=1.4278) but got
  ~22 steps (z=1.3106, vz=-3.597 exactly matching 22 steps).
- SYMPTOMS: 0-2 extra real-time frames slip between play() and the
  blocking step loop; varies run to run (P5 saw both 20 and 22).
- CAUSE: play() starts the real-time clock; the blocking pump covers N
  steps but the wall-time gap around it also integrates.
- RECOVERY: Assert windows, not exact counts; compare body-to-body deltas
  (identical fall => association proof) and timeline dt, not step counts.
- PREVENTION: For exact-N experiments, pause first, then step; or read
  get_current_time() before/after and normalize by dt.

---

# Part: engines (merged from `physics-x`)

# Physics-X — Failure Catalog (live-verified)

## R6: no URDF Sdf plugin in 6.0.0 (manager can't open URDF)
- FAILURE: AssetTransformerManager.run(input_stage=<.urdf>)
  raises "Cannot determine file format" — even with the URDF
  importer extension enabled (registered formats have no
  urdf/mjcf entry).
- RECOVERY: P4 drills the shippable piece instead: conversion
  PREFLIGHT on offline USD (clean vs 5-trait dirty asset).

## R5: physx_to_mjc profile absent in 6.0.0 (pivot to URDF direction)
- FAILURE: physx_to_mjc_conversion.json missing; only
  mjc_to_physx + urdf_to_mjc_physx ship. The PhysX->MJC rule
  needs a newer build than this 6.0.0 install.
- RECOVERY: P4 converts a minimal URDF via the SHIPPED
  urdf_to_mjc_physx_conversion profile — same machinery
  (AssetTransformerManager, variant package, MjcActuator
  audit), supported direction.

## R4: convert script boots SimulationApp at import (unimportable live)
- FAILURE (design): convert_physx_to_newton.py runs
  SimulationApp(...) at module top level — importing it in the
  live Kit session would boot a second Kit.
- RECOVERY: P4 mirrors the documented builder/audit bodies
  in-session and calls the shipped RuleProfiles through
  AssetTransformerManager (conversion logic stays in the Rule).

## R3: standalone python.bat self-test hangs beside the live sim
- FAILURE: Second Kit boot stalled at ~21s (newton ext start),
  process vanished, pipe never closed; had to terminate.
- CAUSE (likely): 4GB GPU already driving the live windowed
  sim (+Warp kernels); second renderer init starves.
- RECOVERY: Run conversion in-session (R4 pattern); reserve
  standalone runners for headless machines.

## R2: exam drop stacks onto the resting P1 cube (read the layout)
- FAILURE: Gated V14 PhysX rest at 0.5; got 1.5001.
- CAUSE: V14Cube drops at (0,0) onto P1Cube resting at 0.5
  (top z=1.0) — correct contact stacking, wrong expectation.
- RECOVERY: Gate rest at 1.5. Bonus: Newton end-frame matches
  PhysX (0.49), so BOTH engines stack identically — stronger
  equivalence than a clean drop.

## R1: Newton simulates plain bodies but offers no tensor/USD readback
- FAILURE: Newton drop read z1=2.0000 via RigidPrim AND USD —
  looked frozen. Render A/B diff (2.05) matched PhysX (2.01)
  and end frames matched (0.20): the fall happened identically.
- CAUSE (log-verified): tensor plugin has no Newton backend
  ("Failed to find simulation backend 'newton'"); Newton
  renders from Fabric and never writes USD back (PhysX does).
- RECOVERY: Render observation (Skill 8 reuse) is ground truth
  for Newton motion. Native Newton state APIs (NewtonStage/
  mujoco qpos) left as future work.
