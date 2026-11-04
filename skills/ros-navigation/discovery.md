# ros-navigation — Discovery Notes (live-verified)

---

# Part: bridge (merged from `ros`)

# ROS — Discovery Notes (live-verified, Isaac Sim 6.0.0 + Lyrical)

## System ROS (C:\dev\lyrical, pixi/conda-forge)
- `setup.ps1` alone is NOT enough for rclpy: prepend
  `.pixi/envs/default/Library/bin` (+ `.../bin`) to PATH or
  `rclpy.init()` fails ("failed to load any RMW implementations").
- Interpreter MUST be the pixi env python (3.12); system 3.14 lacks
  `_rclpy_pybind11` and cannot import rclpy at all.
- 353 packages, ROS_DISTRO=lyrical, no Nav2 -> drills avoid Nav2.
- DDS match lags seconds behind subscriber creation (PUBS=0 at
  first); publisher history (queueSize 10) replays backlog on match.

## Bridge nodes (isaacsim.ros2.bridge, all play-gated)
- ROS2PublishClock: timeStamp <- IsaacReadSimulationTime; /clock.
- ROS2PublishJointState: targetPrim auto-read LIVE per tick (ship
  this). Explicit joint arrays from IsaacReadJointState serve a
  match-time snapshot (frozen values + fresh stamps); literal
  arrays publish nothing. Node needs connected arrays or targetPrim.
- ROS2SubscribeJointState: outputs jointNames + position/
  velocity/effortCommand + timeStamp + execOut; LATCHES last msg.
- ROS2PublishTransformTree: parentPrim + targetPrims rels; /tf live.
- IsaacArticulationController: robotPath REQUIRED (targetPrim rel
  alone silently no-ops); jointNames + per-mode command arrays.

## Pumped ROS legs (the load-bearing pattern)
- Between bridge calls the app idles: frames stop, physics/OG
  reads freeze, but timeline time advances -> frozen values with
  fresh stamps. EVERY ROS listen/talk must overlap forced frames:
  background `update_app_async` pump job + foreground ROS leg.
- R1 clock passes unpumped (wall-timeline needs no frames); every
  physics-derived stream needs pumps. Verify motion in-window.

## Articulation authoring (minimal 2-revolute bot)
- Root: ArticulationRootAPI + PhysxArticulationAPI. Base dynamic +
  world FixedJoint (body0 unset). Kinematic base -> zero joints.
- Links: RigidBodyAPI + MassAPI(1kg) + sleepThreshold 0. NO
  CollisionAPI on driven links (contact weld at ~104deg freezes).
- Revolute joints need coincident frames (J1 localPos1=(0,-0.2,0)).
- Authored DriveAPI allocates the drive model (damping 50 /
  maxForce 100 for velocity mode); CTL switches mode per tick.
- Unique articulation path per build (timestamp suffix); joint
  positions wrap (multi-turn reports modulo); wrapper DOF order
  [J1,J2] confirmed via dof_names.

## Stage facts
- One articulation per drill at a time; builds clean own + prior
  drill prefixes (Section 4a rule). R1 graph is clock-only (no bot).
- Post-talk reads are scrap (unpowered drift); gate on in-window
  pump poses, never on post-talk REST poses (stop() resets anyway).

bringup (`nav2`) shipped no discovery.md; its notes live in SKILL.md.

---

# Part: planning (merged from `navigation`)

# Navigation — Discovery Notes (live-verified, 6.0.0)

## Library reuse map (navigation-primitives)
- occupancy_map_from_usd(stage, xr, yr, res, zcut, colliders):
  correct as-is; N1 used it via sys.path inject (fresh server).
  V11 inlined the 20-line loop (R3 import caching).
- compute_robot_footprint: BROKEN on this build (passed
  Sdf.Path into compute_combined_aabb, which takes str|Usd.Prim
  only). Fixed on disk (pass prims); N3 inlines the function.
  Flag for distill write-up + fresh-process verification.
- kinematics.py: forward/inverse exact to 1e-9 both drive
  types; pure_pursuit_step needs caller-side remaining-path
  windowing (R5) — full-path calls stall past 1m.

## Environment facts
- Local python: numpy + scipy present, cv2 + pxr absent ->
  planning/validation run locally with numpy-only stamping;
  stage reads (rasterize/footprint) run in-sim.
- In-sim python: numpy + scipy + cv2 present.
- No ROS 2 on this machine (no ros2 binary, ROS_DISTRO, or
  /opt/ros): ROS/Nav2 drills impossible; Skill 11 covers the
  navigation substrate only. Revisit when a ROS Humble env
  exists (likely needs Linux).

## Drill design rules
- Predict exact occupied counts with slice arithmetic before
  running (N1: 50, V11: 62) — exact match proves the
  rasterizer; probe centers independently prove placement.
- Keep drills colliders-clean: each yard build removes prior
  drill prims (R6); X-gates assert the cleanup (gone=True).
- Gate pursuit four ways: done flag, arrival < tolerance,
  max deviation, step budget (N4: 132/0.494/0.247).
- Evidence files: Set-Content only (R4); JSON for data, txt
  for one-line reports.

## Session notes
- Zero sim crashes this skill (first clean run since Skill 8).
- Windowed GUI + bridge healthy throughout.
