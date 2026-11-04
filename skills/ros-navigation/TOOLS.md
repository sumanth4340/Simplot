# ROS-Navigation Tool Knowledge (2026-11-04)

> Exhaustive reference: `TOOLS_REF.md` — 11 tools, ~105 functions, 56 knobs, 49 EKB rules, 45 limits, 46 unknowns (20 scripts fully read, 106 skimmed).

## Tools

### rclpy + system ROS 2 Lyrical (pixi env)
- DOES: Outside-sim ROS legs — subscribe to sim topics, publish joint commands.
- FUNCTIONS USED:
  - `rclpy.init()` / `rclpy.shutdown()` / `rclpy.spin_once(node, timeout_sec=0.5)`
  - `rclpy.node.Node`, `create_subscription(TYPE, topic, cb, 10)`, `create_publisher(JointState, topic, 10)`, `pub.publish(msg)`, `node.get_clock().now().to_msg()`, `node.destroy_node()`
  - Msgs: `rosgraph_msgs/Clock`, `sensor_msgs/JointState`, `sensor_msgs/LaserScan`, `tf2_msgs/TFMessage`, `nav_msgs/Odometry`; `rclpy.qos.QoSProfile` (topic_info.py)
  - Env: pixi python `C:\dev\lyrical\.pixi\envs\default\python.exe`, `setup.ps1` sourced, `Library/bin` (+`bin`) prepended to PATH
- LIMITS-live-verified:
  - System python 3.14 cannot import rclpy (`_rclpy_pybind11` missing) — bridge F1; must use pixi env python 3.12.
  - `rclpy.init()` fails ("no RMW implementations") unless `Library/bin` is on PATH — bridge F2.
  - DDS match lags seconds; publisher must pre-talk (~6 s throwaway) before the measured window; SUB latches so commands persist — bridge F10.
- UNKNOWN: Nav2 stack itself (no Nav2 in the 353-package Lyrical env — drills avoid it); QoS profiles beyond default/RELIABLE; multi-machine DDS.

### isaacsim_send.py bridge CLI (isaac-sim-remote)
- DOES: Local drivers send in-sim scripts / one-liners to the live Kit app and capture JSON output.
- FUNCTIONS USED:
  - `python isaacsim_send.py --raw --timeout <s> --file <script.py>` and `isaacsim_send.py --raw --timeout <s> "<one-liner>"`
  - Local harness: `subprocess.run(SEND + args, capture_output=True, text=True)`, `json.loads(p.stdout).get("output", "")`
- LIMITS-live-verified:
  - Between bridge calls the app idles: frames stop, physics/OG reads freeze, but timeline time advances (frozen values, fresh stamps) — discovery "Pumped ROS legs"; every physics-derived ROS leg must overlap forced frames.
  - `--file` calls run in isolated namespaces: python handles (e.g. LidarSensor auto products) die with the call; only USD-persisted state survives — bringup F2c.
  - python_server caches repo imports across sends beyond `sys.modules` — drills INLINE short library functions — planning R3.
- UNKNOWN: Exact server-side import-cache invalidation mechanism; concurrent-call safety.

### omni.graph.core (og.Controller) — graph authoring
- DOES: Atomically authors/executes OmniGraph ROS graphs (clock, joint states, subscribe, TF, odom, lidar helper).
- FUNCTIONS USED:
  - `og.Controller.Keys` with `CREATE_NODES` / `CONNECT` / `SET_VALUES` via `og.Controller.edit(...)` (both graph-path-string and `{"graph_path","evaluator_name"}` forms)
  - `og.ObjectLookup.attribute(...).get_upstream_connections()`, `og.Controller.attribute(...).set(...)`
- LIMITS-live-verified:
  - `Controller.attribute().set()` is runtime-only: play re-parses from USD and wipes it; persistent config needs USD-level writes — bringup F2 ruled-out list.
  - Deprecated `IsaacCreateRTXLidarScanBuffer` / `IsaacComputeRTXLidarFlatScan` CRASH the process at first play — bringup F2a; use `ROS2RtxLidarHelper` instead.
- UNKNOWN: Non-execution evaluators; graph profiling APIs.

### isaacsim.ros2.bridge OG nodes (play-gated publishers/subscribers)
- DOES: Publishes /clock, /joint_states, /tf, /odom, /scan; subscribes joint commands; drives articulations per tick.
- FUNCTIONS USED:
  - `ROS2PublishClock` (timeStamp <- IsaacReadSimulationTime), `ROS2PublishJointState` (targetPrim auto-read), `ROS2SubscribeJointState` (latches last msg), `ROS2PublishTransformTree` (parentPrim + targetPrims), `ROS2PublishOdometry`, `ROS2RtxLidarHelper(type=laser_scan)`
  - `isaacsim.core.nodes.IsaacArticulationController` (robotPath + jointNames + velocityCommand), `IsaacComputeOdometry` (chassisPrim), `IsaacReadSimulationTime`, `omni.graph.action.OnPlaybackTick`
  - `app_utils.enable_extension("isaacsim.ros2.bridge")` at the top of every graph script
- LIMITS-live-verified:
  - All topics publish only while playing; R1 clock passes unpumped, every physics-derived stream needs pumped frames — SKILL.md Limitations + bridge R-pattern.
  - `targetPrim` auto-read is LIVE per tick; `IsaacReadJointState` -> explicit-array wiring serves a match-time snapshot (frozen values, fresh stamps) — bridge F6; literal arrays publish nothing.
  - CTL silently no-ops without the `robotPath` STRING (targetPrim rel alone ignored) — bridge F7; needs `jointNames` + per-mode command arrays.
  - Authored DriveAPI alone never moves a joint (DOF defaults to effort mode); CTL per-tick commands switch it to velocity mode — bridge F4.
  - Wrapper velocity targets clear after call return (tensor-view GC invalidation) — bridge F5; ship CTL per-tick commands.
- UNKNOWN: Effort/position command modes over CTL (only velocity verified end to end); `ROS2RtxLidarHelper` types other than `laser_scan`; `fullScan` (deprecated-ignored).

### omni.usd + pxr USD authoring (stage builds)
- DOES: Builds bots, ground, graphs, lights, lidar mounts in the live stage; cleans prior-drill prims.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()`, `GetPrimAtPath`, `RemovePrim`, `GetChildren`, rels `SetTargets`, attrs `.Set/.Get`
  - `UsdGeom.Xform/Cube/Sphere/Cylinder.Define`, `AddTranslateOp/AddScaleOp`, `UsdLux.DomeLight.Define`, `UsdRender` (product queries)
  - `UsdPhysics.ArticulationRootAPI/RigidBodyAPI/MassAPI/CollisionAPI/RevoluteJoint/DriveAPI/FixedJoint`, `PhysxSchema.PhysxArticulationAPI/PhysxRigidBodyAPI` (solver iterations, sleep threshold), `Gf.Vec3d/Vec3f`
- LIMITS-live-verified:
  - Kinematic base inside an articulation -> backend builds 0 joints/0 links, silently — bridge F3; ship dynamic base + world FixedJoint + MassAPI + coincident J1 frames.
  - No CollisionAPI on spinning links: contact weld freezes joints (~104 deg) — bridge F8.
  - Never roll on raw USD Cylinder colliders: faceted-hull facet slap -> vault-launch cycle (+/-4 cm bounce, flaky odom) — bringup F1; ship analytic sphere collider + visual-only cylinder child.
  - Never `RemovePrim` a render product (scheduler-owned, crashes renderer) — bringup F2 ruled-out list.
  - Joint angles wrap (multi-turn modulo) — gate wrap-robust, never threshold raw positions — bridge F9.
  - One articulation per drill; unique articulation path per build (timestamp suffix); never define a second /PhysicsScene (splits/double-steps bodies).
- UNKNOWN: Capsule wheel colliders (named as alternative, sphere is what shipped); `UsdPhysics` joint types beyond revolute/fixed.

### isaacsim.core.experimental.prims Articulation wrapper (state probes)
- DOES: Reads live articulation state (num_dofs, dof_names, joint pos/vel) and issues debug velocity targets.
- FUNCTIONS USED:
  - `Articulation(...)` wrapper reads (`num_dofs`, `dof_names`, DOF pos/vel samples); `RigidPrim` (n1_truth.py); per discovery.md, wrapper DOF order [J1,J2] confirmed
- LIMITS-live-verified:
  - Wrapper-commanded motion freezes ~1 s after bridge-call return (tensor-view GC invalidation) — bridge F5; never rely on wrapper commands across calls.
  - Phantom ART reads (UNCONFIRMED): removed N1Base_* prims reappearing with zeroed transforms, suspected stale bridge USD view; harmless (mount picks newest-by-timestamp) — bringup F2 ruled-out list.
- UNKNOWN: Wrapper velocity commands within a single pumped call (bisected only as cross-call failure); torque/effort APIs.

### isaacsim.sensors.experimental.rtx Lidar + omni.replicator render products
- DOES: Creates the RTX lidar and its USD-persistent render product feeding /scan.
- FUNCTIONS USED:
  - `Lidar.create(path=..., config="Example_Rotary_2D", tick_rate=10.0, accumulate_outputs=True, positions=[[...]])` — NO `LidarSensor`
  - `rep.create.render_product(lidar_path, (128, 128))` -> `rp_obj.path` wired to Helper `renderProductPath`
- LIMITS-live-verified:
  - `LidarSensor` AUTO product (`rtx_sensor_*`) dies with the --file call's handles — bringup F2c; explicit rep product persists in USD (mirrors NVIDIA `test_rtx_sensor.py`).
  - Lidar parented under a rigid body emits EMPTY scans (19 empty ticks); same pose at the articulation root gives full frames — bringup F2d; always root-parent.
  - `positions=` are WORLD-frame, not parent-local: [[0,0,0.25]] lands inside the chassis (self-occluded empties) — bringup F2e; use world coords [[0,0,0.515]].
  - LaserScan invalid returns are -1.0, not inf: gate geometry on min-of-positive (`rmin_valid`) — bringup F2 ruled-out list.
  - `writer.attach([product])` never ticks for RTX sensors; `sensor.attach_writer` is the working in-sim diagnostic — bringup F2 ruled-out list.
- UNKNOWN: Lidar configs other than `Example_Rotary_2D`; resolutions other than (128,128); point-cloud (non-`laser_scan`) output; `tick_rate`/`accumulate_outputs` sensitivity.

### PowerShell pumped-leg harness (*.ps1)
- DOES: Forces sim frames (background pump job over the bridge) while a foreground ROS leg listens/talks.
- FUNCTIONS USED:
  - `Start-Job` pump loop (`python isaacsim_send.py --raw --timeout 300 --file *_pump40.py`), foreground `listen.ps1 <topic> <msgtype> <count> <timeout> <out>`, `Receive-Job -Wait`, `Remove-Job`
  - Scripts: `listen.ps1`, `r2/r4/n1/n2_pumped_listen.ps1`, `r3_pumped_talk.ps1`, `tmp_rmwprobe/rosenv/topics.ps1`, `r2_deep/pubcount.ps1`
  - Evidence via `Set-Content` (JSON data, txt one-liners)
- LIMITS-live-verified:
  - `Tee-Object` writes UTF-16 which garbles utf-8 verifier reads — planning R4; always `Set-Content`.
  - Every commanded drill opens with a match primer (pre-talk) — bridge F10.
- UNKNOWN: Optimal pump counts/durations beyond the shipped 6x40-step loops; `Start-Job` failure modes under sim hiccups.

### navigation-primitives library (occupancy/footprint/kinematics)
- DOES: Stage rasterization, robot footprint AABBs, exact FK/IK, pure-pursuit stepping (planning substrate).
- FUNCTIONS USED:
  - `occupancy_map_from_usd(stage, xr, yr, res, zcut, colliders)` (correct as-is)
  - `compute_robot_footprint` via `isaacsim.core.experimental.utils.bounds.compute_combined_aabb` (pass UsdPrim elements)
  - `kinematics.forward/inverse` (exact to 1e-9), `pure_pursuit_step(pos, yaw, path, cfg, prev)`, `PurePursuitConfig/DifferentialParams/HolonomicParams`
  - Local `nav_check.footprint_clips_np` (cv2-free oriented stamp)
- LIMITS-live-verified:
  - Library `compute_robot_footprint` passed `Sdf.Path` into `ComputeWorldBound` (wants UsdPrim) — crashed; fixed on disk (pass prims), drills inline the function — planning R2/R3.
  - `pure_pursuit_step` scans from index 0 with no progress tracking: full-path calls stall past 1 m (reverse oscillation) — planning R5; caller tracks monotonic nearest index k and passes path[k:].
  - Rasterizers see the WHOLE stage: clean prior drill colliders first or phantom cells appear (54 in V11) — planning R6.
  - Rasterizer slices are [x0:x1): count x1-x0, not inclusive — planning R7.
  - Rasterize with colliders_only; visual-only prims and un-collidered ground ignored; size prims off exact cell boundaries (float truncation).
- UNKNOWN: `kinematics` beyond the verified FK/IK + pursuit surface; cv2-based stamping (in-sim has cv2, drills use numpy-only).

### Local planning stack (numpy + scipy + heapq)
- DOES: Runs A*, erosion, footprint validation, and pursuit follow locally with no ROS/sim.
- FUNCTIONS USED:
  - `numpy` grids/stamps, `scipy.ndimage.binary_erosion` (4-connected structure), `heapq` open queue, octile heuristic, 8-connected moves with no-corner-cutting
- LIMITS-live-verified:
  - A* baselines must use king-move distance `max(|dx|,|dy|)`; Euclidean overestimates and valid paths "fail" — planning R1.
  - Planning A*/pursuit are kinematic (no dynamics) — SKILL.md Limitations.
  - Local python has numpy + scipy, NO cv2/pxr — planning stays numpy-only locally — discovery Environment facts.
- UNKNOWN: Larger-grid performance; erosion radii beyond the shipped 0.3/inscribed-radius; dynamic replanning.

### Minor / probe-only APIs (skimmed, not drill load-bearing)
- DOES: One-off diagnostics during bisection.
- FUNCTIONS USED:
  - `omni.isaac.dynamic_control` (dc) — r2_dcstate.py state probe
  - `omni.timeline`, `omni.kit.app`, `omni.kit.commands` — play/state/command probes
  - `omni.replicator.core.Writer`, `warp` — N2 sensor-attach diagnostics
  - `isaacsim.core.experimental.utils.prim` (prim_utils) — n2_canonical.py
  - Verifiers `verify_r*/verify_n*/x15.py` — stdlib-only (json/sys/re/math/subprocess) evidence gates
- LIMITS-live-verified:
  - Verifier vacuity: `all()` over zero msgs passes — conjoin every gate with HAVE (msgs>=5) — bringup F2 ruled-out list.
- UNKNOWN: Everything about these beyond their probe usage; none are approximable as drill-supported.

## Unverified

- Nav2 stack (absent from Lyrical env; Skill 11 covers substrate only).
- CTL effort/position command modes (velocity only, verified end to end).
- `ROS2RtxLidarHelper` types other than `laser_scan`; point-cloud output.
- Lidar configs other than `Example_Rotary_2D`; non-(128,128) resolutions.
- Capsule wheel colliders (named alternative; sphere shipped).
- Wrapper velocity commands within a single pumped call; torque/effort APIs.
- Phantom ART reads root cause (UNCONFIRMED stale bridge USD view).
- python_server import-cache invalidation mechanism; concurrent-call safety.
- Planner scaling (larger grids, other erosion radii, dynamic replanning).
- Probe-only APIs as supported surface (dc, timeline, kit.commands, warp, Writer, prim_utils).

## Sources-read

- action-reasoner/skills/ros-navigation/SKILL.md (full)
- action-reasoner/skills/ros-navigation/failures.md (full)
- action-reasoner/skills/ros-navigation/discovery.md (full)
- action-reasoner/skills/ros-navigation/bridge/scripts/listener_ros.py (full)
- action-reasoner/skills/ros-navigation/bridge/scripts/talker_ros.py (full)
- action-reasoner/skills/ros-navigation/bridge/scripts/r2_drive.py (full)
- action-reasoner/skills/ros-navigation/bridge/scripts/r1_build.py (full)
- action-reasoner/skills/ros-navigation/bringup/scripts/n1_build.py (full)
- action-reasoner/skills/ros-navigation/bringup/scripts/n2_mount.py (full)
- action-reasoner/skills/ros-navigation/planning/scripts/v11_pipeline.py (full)
- action-reasoner/skills/ros-navigation/bridge/scripts/r2_pumped_listen.ps1 (full)
- All remaining scripts skimmed by filename + import lines via repo-wide import grep (126 script files total: 64 bridge, 45 bringup, 17 planning).
