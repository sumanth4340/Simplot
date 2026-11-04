---
name: ros-navigation
description: >
  Full ROS 2 robot-navigation stack on Isaac Sim 6 — play-gated ROS 2 bridge
  bring-up (clock, joint_states, subscribe, TF), velocity-driven skid-steer
  odometry with RTX lidar /scan publishing, and local planning (occupancy
  grids, A*, footprints, pure pursuit). Use when bridging ROS topics, driving
  a wheeled base, debugging odometry or silent scans, or planning paths.
metadata:
  validated: 2026-11-04
  validated_by: R1-R4/V15/X15 + N1-N2 bring-up + N1-N4/V11/X11 all green on Isaac Sim 6.0.0/Kit 110
---

# ros-navigation

## Purpose

Three layers of one stack, validated live on Isaac Sim 6.0.0 / Kit 110
(RTX + PhysX, Windows, system ROS 2 Lyrical):

- `bridge/` — ROS 2 bridge bring-up (R1 clock, R2 joint_states,
  R3 subscribe round-trip, R4 TF) + V15 exam + X15 cross-val.
- `bringup/` — skid-steer odometry (N1) + RTX lidar `/scan` (N2).
- `planning/` — occupancy grid + A* + footprint + pure pursuit
  (N1-N4) + V11 exam + X11 cross-val. Runs locally (numpy-only);
  no ROS required.

Merged 2026-11-04 from the `ros`, `nav2`, and `navigation` packs;
drill tags are namespaced per part (bridge R1-R4, bringup N1-N2,
planning N1-N4/V11).

## Routing

| Signal | Part | Drills |
|---|---|---|
| /clock, /joint_states, subscribe, /tf, bridge nodes | `bridge/` | R1-R4, V15, X15 |
| Wheeled base, odometry, /scan, lidar mount | `bringup/` | N1, N2 |
| Occupancy grid, A*, footprint, pursuit | `planning/` | N1-N4, V11, X11 |

## Prerequisites

- Isaac Sim 6 / Kit 110; `isaacsim.ros2.bridge` loadable (bridge, bringup).
- Live bridge (`isaac-sim-remote`) for the in-sim build/drive scripts.
- System ROS 2 (Lyrical pixi env) for topic listeners — see bridge notes.
- Planning runs on local python (numpy + scipy, no cv2/pxr needed).

## Limitations

- Topics publish only while playing; physics-derived streams need
  pumped frames during every ROS leg (bridge R-pattern).
- Bringup odom is open-loop velocity drive, not localization;
  2D `laser_scan` only, not point clouds.
- Planning A*/pursuit are kinematic (no dynamics); rasterizers see
  the whole stage (clean prior colliders per build).

## Key procedures

### Pumped ROS legs (bridge)

Between bridge calls the app idles: frames stop, physics/OG reads
freeze, but timeline time advances. EVERY ROS listen/talk overlaps
forced frames: background `update_app_async` pump + foreground ROS
leg. R1 clock passes unpumped; everything physics-derived needs
pumps. System listeners must use the pixi env python with
`setup.ps1` sourced AND `Library/bin` prepended to PATH, or RMW
dlls fail to load. SUB latches the last command; DDS match lags
seconds — pre-talk before the measured window.

### Bridge node facts (bridge)

- `ROS2PublishJointState`: `targetPrim` auto-read is LIVE per tick;
  IsaacReadJointState -> explicit-array wiring serves a match-time
  snapshot (frozen values, fresh stamps). Avoid it.
- `IsaacArticulationController` needs `robotPath` (rel alone
  ignored) + `jointNames`; velocity commands verified end to end.
- Articulations: dynamic base + world FixedJoint (kinematic bases
  are excluded -> zero joints); no CollisionAPI on spinning links
  (contact weld freezes joints); unique articulation path per
  build; joint angles wrap (gate wrap-robust).

### Rolling-collider rule (bringup N1)

Never put raw USD Cylinder collision under a rolling wheel — it
cooks to a faceted hull and each facet slap pumps a hop the
velocity drives re-accelerate into (vault-launch cycle, +/-4 cm
bounce, flaky odom). Procedure: analytic sphere (or capsule)
collider carrying RigidBody+Collision+Mass, with the cylinder kept
as a visual-only child. Drive-geometry checklist: 0.36 m wheelbase,
+1.5 cm spawn clearance, damping 2 / maxForce 2, solver 64/16 +
32/8, CTL jointNames from geometry (never hardcoded).

### RTX lidar /scan recipe (bringup N2)

1. Enable `isaacsim.ros2.bridge` at the top of every graph script.
2. `Lidar.create(config=...)` with NO `LidarSensor`; make the
   product explicit and USD-persistent:
   `rep.create.render_product(lidar, (128, 128))`.
3. Parent the lidar to the articulation ROOT, never a rigid body
   (rigid-body parenting emits empty scans).
4. `positions=` are WORLD-frame: compute world coords.
5. Publish with `ROS2RtxLidarHelper(type=laser_scan)` straight
   from the product. Deprecated ScanBuffer/FlatScan nodes CRASH.
6. Gate geometry on min-of-positive ranges: invalid is -1.0.

NEVER `RemovePrim` a render product (scheduler-owned). NEVER trust
`Controller.attribute().set()` across play (runtime-only).
Verifier-vacuity rule: conjoin every gate with HAVE (msgs>=5).

### Local planning rules (planning N1-N4)

- Rasterize with colliders_only; visual-only prims and
  un-collidered ground are ignored. Predict exact counts with
  slice arithmetic ([x0:x1) half-open); size prims off exact cell
  boundaries to dodge float truncation.
- A* baselines use king-move distance max(|dx|,|dy|); erode by
  inscribed radius; 8-connected without corner cutting.
- Footprints derive from collider AABBs (pass UsdPrim, not
  Sdf.Path); cv2-free oriented stamp validates every waypoint.
- `pure_pursuit_step` scans from index 0: pass the REMAINING path
  (nearest-index window) or pursuit stalls past 1 m.
- python_server caches repo imports across sends: drills INLINE
  short library functions; evidence via Set-Content, never
  Tee-Object (UTF-16 garble).

## Drills

| Drill | Claim | Verifier |
|---|---|---|
| bridge R1 clock | /clock live, stamps increase, span>0 (8/8) | `bridge/scripts/verify_r1.py` |
| bridge R2 joint_states | 2 joints, full-rate motion (11/11) | `bridge/scripts/verify_r2.py` |
| bridge R3 subscribe | [0.8,-0.5] obeyed in-window (10/10) | `bridge/scripts/verify_r3.py` |
| bridge R4 TF | /tf 3 frames, finite xyz, a frame moved (10/10) | `bridge/scripts/verify_r4.py` |
| bridge V15 exam | R1-R4 replayed green (4/4) | `bridge/scripts/exam15.py` |
| bringup N1 odom | exact vx, monotonic x, z=0, w=0 (9 gates) | `bringup/scripts/verify_n1.py` |
| bringup N2 scan | 24 full frames, geometry-gated (11 gates) | `bringup/scripts/verify_n2.py` |
| planning N1 grid | 10/10, 40x40, occ=50, binary values | `planning/scripts/verify_n1.py` |
| planning N2 A* | 8/8, len=40 > king 32, all free | `planning/scripts/verify_n2.py` |
| planning N3 footprint | 10/10, stamps a=0/b=1/c=1, path 0/40 bad | `planning/scripts/verify_n3.py` |
| planning N4 pursuit | 7/7, done in 132 steps, arrival 0.494 | `planning/scripts/verify_n4.py` |
| planning V11 exam | 12/12 on a new yard, arrival 0.479 | `planning/scripts/verify_v11.py` |

Cross-val: `bridge/scripts/x15.py` (audit + error scan, 5/5);
planning X11 lives in the `cross-val` pack (10/10).

## Related skills

- RECEIVES from: `physics` (contacts/drives),
  `isaac-sim-ros2-bridge` (bridge nodes),
  `navigation-primitives` (planning library).
- PRODUCES for: `articulation-robots` (ROS-driven bases),
  `manipulation-motion` (joint control over ROS).

## Failure index

Details, bisection logs, and ruled-out causes: `failures.md`
(bridge F1-F10; bringup F1-F2 + ruled-out lists; planning R1-R7).

## References

- Bridge tools: `bridge/scripts/rN_build` (in-sim authorship),
  `rN_drive` (local driver), `verify_rN` (evaluators),
  `listener_ros.py` + `listen.ps1`, `talker_ros.py`,
  `rN_pumped_listen/talk.ps1`, `audit_stage.py`.
- Bringup tools: `bringup/scripts/n1_build.py`, `n1_drive.py`,
  `n2_mount.py`, `n2_drive.py`, `verify_n1.py`, `verify_n2.py`.
- Planning tools: `planning/scripts/n1_build/n1_run`,
  `n2_plan`, `n3_build/n3_run`, `n3_validate`, `n4_follow`,
  `v11_build/v11_run`, `v11_pipeline`, `nav_check.py`.
- Evidence: `bridge/evidence/`, `bringup/evidence/`,
  `planning/evidence/`.
- Upstream: `$ISAAC_SIM_DIR/standalone_examples/api/isaacsim.ros2.bridge/rtx_lidar.py`,
  NVIDIA `test_rtx_sensor.py`.

## Iteration Log

- v1.0 2026-11-04: merged `ros` + `nav2` + `navigation` packs
  into `ros-navigation` (bridge/bringup/planning); drill scripts
  and evidence unchanged apart from path updates.
- v0.1 2026-11-04: `nav2` distilled from N1/N2 drills (MSF Capture).
