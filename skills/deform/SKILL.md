---
name: deform
description: PhysX volume-deformable drill (D1) — explicit-PhysicsScene authoring, DeformablePrim tensor reads, stiffness scaling, and Newton no-go rules. Use when simulating soft bodies, reading deformable tensors, or checking Newton/deformable compatibility.
metadata:
  validated: 2026-11-04
  validated_by: D1 verifier 10/10 green 3/3 on Isaac Sim 6.0.0/Kit 110
---

# deform

## Purpose

Drop, settle, and numerically read a volume-deformable body under
PhysX: nodal positions/velocities/stresses plus tet connectivity,
gated on drop, rest, squash, and live stress. Validated live on
Isaac Sim 6.0.0 / Kit 110 (D1-PASS 10/10, 3/3 bit-identical).

## Prerequisites

- `physics-simulation` Part 7 (simulated-state reads) and the
  `physx` skill. PhysX must be the ACTIVE engine (see no-go rules).

## Limitations

- PhysX-only drill. Newton deformable runs need pre-cooked USD on a
  Newton-from-boot sim with render-observation verification; unbuilt.
- Landing tip-over varies run to run: never gate x/y, only z/shape.
- Stiffness must scale with body size (see below).

## Key procedures

### Deformable authoring recipe

1. `SimulationManager.set_device("cuda")` first.
2. Define an explicit `UsdPhysics.Scene` + `PhysxSceneAPI` (gravity,
   60 Hz, TGS). Rigid bodies tolerate a missing scene; the
   deformable tensor backend NEVER binds without one (reads fail
   with "Failed to get ... from backend" despite valid views).
3. Author GroundPlane + Xform + cooking Mesh, wrap
   `DeformablePrim(path, deformable_type="volume")`, apply a
   `VolumeDeformableMaterial`. Rebuild the deformable AFTER any
   scene change. See `scripts/d1_build.py`.

### Tensor-read pattern

`get_nodal_positions` / `get_element_indices` return 3-TUPLES
(sim, collision, rest), each `(N, NpB, 3)`; velocities and stresses
return single arrays. Unpack `[0]` (sim mesh) + `[0]` (first body).
Backend buffers need real post-play physics steps: warm up with
read retries (12x10 steps), never a fixed small guess.
See `scripts/d1_drive.py`; evidence `evidence/d1_nodes.json`.

### Stiffness-scaling rule

Scale Young's modulus to body size: a 1 m cone at E=1e4 Pa is jelly
(self-weight ~= E, sinks 1/3 under the ground); at E=1e6 Pa it is
effectively rigid (zero squash). Sweet spot here E=1e5: rest
zmin -0.040, height -1.4%, spread +1.2%, live stress. Always gate
squash AND rest-on-ground together (either alone admits jelly-sink
or rigid-fall). Gates: `scripts/verify_d1.py` (10 gates).

### Newton no-go rules (verified fatals)

- NEVER author/cook a `DeformablePrim` on a Newton-active sim:
  cooking goes through the PhysX cooking interface whose stage
  handle is NULL under Newton -> native fatal (py-spy proven).
- NEVER `switch_physics_engine` with a loaded stage (same fatal).
- The `default_engine=newton` boot flag alone does NOT activate
  Newton (extension ships disabled); also
  `--enable isaacsim.physics.newton`, then re-query the active
  engine before stepping.

## Related skills

- RECEIVES from: `physics-simulation`, `physx`.
- PRODUCES for: `manipulation-motion` (deformable grasp targets).

## Failure index

`failures.md` (F1 Newton cook fatal, F2 boot-flag gap, F3 missing
scene, F4 tuple/reads, F5 stiffness scale, ruled-out list).

## References

- Scripts: `scripts/d1_build.py`, `d1_drive.py`, `verify_d1.py`.
- Upstream: `$ISAAC_SIM_DIR/standalone_examples/api/isaacsim.core.experimental.api/deformable_stress_visualization.py`.

## Iteration Log

- v0.1 2026-11-04: distilled from D1 drill (MSF Capture).
