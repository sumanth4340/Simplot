---
name: physics
description: >
  Rigid-body physics on Isaac Sim 6 — stepping, simulated-state reads,
  velocities, hinge drives, contacts, determinism, plus PhysX/Newton
  engine equivalence, runtime switching, and URDF conversion preflight.
  Use when stepping simulation, reading bodies, driving joints, switching
  physics engines, or preflighting asset conversion.
metadata:
  validated: 2026-11-04
  validated_by: P1-P5/V1 + P1-P4/V14/X14 all green on Isaac Sim 6.0.0/Kit 110
---

# physics

## Purpose

Two layers, verified live on Isaac Sim 6.0.0 / Kit 110 (RTX
3050, Windows):

- `core/` — stepping, simulated-state reads, velocities,
  hinge drives, stacks, determinism (P1-P5) + V1 exam.
- `engines/` — PhysX drop baseline (P1), Newton equivalence
  (P2), runtime switching (P3), conversion preflight (P4) +
  V14 exam + X14 cross-val.

Merged 2026-11-04 from the `physics-master` and `physics-x`
packs; drill tags are namespaced per part (core P1-P5/V1,
engines P1-P4/V14).

## Routing

| Signal | Part | Drills |
|---|---|---|
| Step, read bodies, velocity, hinge, stack, determinism | `core/` | P1-P5, V1 |
| Newton equivalence, engine switch, URDF preflight | `engines/` | P1-P4, V14, X14 |

## Prerequisites

- Isaac Sim 6 / Kit 110 with PhysX (default engine).
- Newton drills need `isaacsim.physics.newton` loadable.
- Live bridge (`isaac-sim-remote`) for in-sim scripts.

## Limitations

- Engine observed: `physx` (no Newton auto-switch in 6.0.0).
- Newton simulates plain UsdPhysics bodies identically but
  offers NO tensor readback (plugin lacks a Newton backend)
  and NO USD writeback (Fabric-only) — render observation
  is ground truth (engines R1).
- 6.0.0 lacks the physx_to_mjc profile (R5) and any URDF Sdf
  plugin for the manager (R6) — full conversion needs a
  newer build; P4 drills the shippable preflight piece.

## Key procedures

### Step + read (core)

Step via `play()` + `await update_app_async(steps=N)`;
confirm with `timeline.get_current_time()`.
`SimulationContext().step()` crashes inside Kit (core F1).
Read SIMULATED state only via `RigidPrim` / `Articulation`
tensors. USD reads are authored-state (accurate when
still/paused, stale mid-play).

### Velocities + drives (core)

`set_velocities(linear_velocities=...)` /
`get_velocities()` -> (linear, angular). No
`set_linear_velocities` (F3). Set velocities AFTER play();
pre-play values are ignored (F2). Angular drive
`target_velocity` is DEGREES/s: w=180 -> pi in 1.000 s.
`stop()` does NOT restore pre-play state; reset poses via
USD + clock before repeat trials (F4). Physics is
bit-deterministic: identical trajectories, maxdiff 0.0.

### Newton equivalence (engines P2)

Newton render motion matches PhysX to 0.0014 (end frames
0.11): run both engines, screenshot, diff the renders.
Exam drops stack: read the layout before gating rest
height (V14 rests 1.5001 on P1Cube, both engines) (R2).

### Runtime switching (engines P3)

Works both ways: enable `isaacsim.physics.newton`,
`switch_physics_engine(name)`,
confirm `get_active_physics_engine()`; available list
reports (name, active-flag) tuples; default physx.

### Conversion preflight (engines P4)

Standalone python.bat Kit hangs beside the live sim on 4GB
GPUs (R3); the convert script boots SimulationApp at import
so it is unimportable live (R4). Ship the preflight piece:
clean file silent, dirty file fires all 5 traits.

## Drills

| Drill | Claim | Verifier |
|---|---|---|
| core P1 gravity | 1 m cube z=2 -> rest 0.5, dt=2.000 s | `core/scripts/verify_p1.py` |
| core P2 velocity | vx=5 -> dx=5.0000, zero z drift | `core/scripts/verify_p2.py` |
| core P3 hinge | revolute + drive -> turn=pi exactly | `core/scripts/verify_p3.py` |
| core P4 stack | rest speeds <0.003 | `core/scripts/verify_p4.py` |
| core P5 determinism | two drops, maxdiff 0.000000 | `core/scripts/verify_p5.py` |
| core V1 exam | 5 kg cube z=5, theory-matched flight | `core/scripts/verify_v1.py` |
| engines P1 drop | z1=0.5000 exact, vz=0, engine physx | `engines/scripts/verify_p1.py` |
| engines P2 equiv | newton/physx motion match 0.0014 | `engines/scripts/verify_p2.py` |
| engines P3 switch | physx->newton->physx confirmed | `engines/scripts/verify_p3.py` |
| engines P4 preflight | clean silent, dirty fires 5 traits | `engines/scripts/verify_p4.py` |
| engines V14 exam | 9/9 both engines, stacked rest 1.5 | `engines/scripts/verify_v14.py` |

Cross-val: engines X14 (7/7 across stage/model/sense/physics/app).

## Related skills

- RECEIVES from: `stage-core` (prim authoring),
  `workspace-sense` (render observation for Newton).
- PRODUCES for: `ros-navigation` (contacts/drives),
  `articulation-robots` (joint dynamics), `deform`
  (rigid baselines for soft bodies).

## Failure index

Details, bisection logs, and ruled-out causes: `failures.md`
(core F1-F4; engines R1-R6).

## References

- Core tools: `core/scripts/pN_setup.py` / `pN_run.py`
  (in-sim), `verify_pN.py`, `v1_*` exam.
- Engines tools: `engines/scripts/p1_build/p1_run`,
  `p2_drive` (LOCAL shots+diffs), `p3_probe`, `p4_preflight`,
  `v14_build/v14_drive` (LOCAL),
  `probe_back/napi/fmt/nmotion/urdf`, `verify_pN/verify_v14`.
- Evidence: `core/evidence/`, `engines/evidence/`.

## Iteration Log

- v1.0 2026-11-04: merged `physics-master` + `physics-x`
  packs into `physics` (core/engines); drill scripts and
  evidence unchanged apart from path updates.
