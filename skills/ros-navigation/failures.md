# ros-navigation — Failure Catalog (live-verified)

Failure IDs are namespaced per part: bridge F1-F10, bringup F1-F2, planning R1-R7. Script paths below are relative to each part dir (bridge/bringup/planning).

---

# Part: bridge (merged from `ros`)

# ROS — Failure Catalog (live-verified)

## F1: system python cannot import rclpy
- FAILURE: `listener` crashed: `rclpy._rclpy_pybind11` missing
  (`_rclpy_pybind11.cp314-win_amd64.pyd` absent) on system 3.14.
- CAUSE: rclpy lives in the pixi env (3.12), not system python.
- RECOVERY: Pin `C:\dev\lyrical\.pixi\envs\default\python.exe`.
- PREVENTION: Never use system python for ROS legs; verify the
  interpreter path with Test-Path (bin/ vs env layouts confuse).

## F2: rclpy.init fails (no RMW implementations)
- FAILURE: Import OK, init fails: "failed to load any RMW
  implementations" despite `setup.ps1` sourced and bin/ on PATH.
- CAUSE: Dependency dlls (OpenSSL etc.) live in the pixi env's
  `Library/bin`, which colcon setup does not add (pixi activation
  normally does).
- RECOVERY: Prepend `.pixi/envs/default/Library/bin` (+`/bin`).
- PREVENTION: Bake the PATH prepend into every ROS-entry ps1.

## F3: kinematic base yields zero joints (silent)
- FAILURE: `/joint_states` never appears; no Kit log errors; USD
  structure (root API, joint rels) all valid.
- CAUSE: PhysX excludes kinematic bodies from articulations; J1
  rooted at the kinematic base -> backend built 0 joints/0 links.
- RECOVERY (physics-agent recipe): dynamic base + world-anchored
  FixedJoint (0 DOFs) + MassAPI + PhysxArticulationAPI + coincident
  J1 frames. Verified: num_dofs=2, names [J1,J2].
- PREVENTION: Never kinematic a link inside an articulation; probe
  num_dofs live, not just USD structure.

## F4: authored DriveAPI alone never moves the joint
- FAILURE: Velocity pinned at exactly 0.0 across 60 steps with a
  fully-authored velocity drive (damping 50, target 1.0).
- CAUSE: Authored drive allocates the model but the DOF defaults
  to effort mode; runtime targets (wrapper or CTL per-tick) switch
  it into velocity mode. Either alone -> zero motion (bisected).
- RECOVERY: CTL node commanding per tick (graph-native, no GC risk).
- PREVENTION: Always pair authored drives with a live commander.

## F5: wrapper velocity targets clear after call return
- FAILURE: Wrapper-driven joints moved during pumped calls then
  froze ~1s after bridge-call return (mid-gap freeze at 1.82).
- CAUSE: Tensor-view invalidation on handle GC.
- RECOVERY: CTL per-tick commands (graph-local, persists).
- PREVENTION: Never rely on wrapper-commanded motion across calls.

## F6: RD-array wiring serves a match-time snapshot
- FAILURE: 8-12 samples at exactly 60Hz, advancing stamps,
  bit-identical values, on fresh AND rebuilt graphs.
- CAUSE: IsaacReadJointState -> explicit-array edges don't refresh
  per tick from the subscriber's view; targetPrim auto-read does.
- RECOVERY: targetPrim auto-read wiring (verified live).
- PREVENTION: Ship auto-read for joint states; distrust array-edge
  freshness claims without a motion gate.

## F7: CTL silently no-ops without robotPath
- FAILURE: CTL + targetPrim rel + velocityCommand set, zero motion,
  zero errors (runs C/GAP-A/r2_body).
- CAUSE: CTL resolves its robot from the robotPath STRING; the
  targetPrim relationship alone is ignored.
- RECOVERY: Set robotPath + jointNames (verified: pumps move).
- PREVENTION: Always set robotPath on CTL; probe motion, not config.

## F8: contact weld freezes spinning links
- FAILURE: Pumps 2+ frozen at J1=1.82 (104deg) after moving;
  user confirmed link1 inside the base cube in the viewport.
- CAUSE: Spinning link1 swung into the base collider and welded.
- RECOVERY: Remove CollisionAPI from driven links (free spin).
- PREVENTION: No colliders on continuously-spinning drill links.

## F9: angle wrap breaks naive motion gates
- FAILURE: J1 drove +6.47 rad but read -6.086 (wrapped) -> gate
  `pos>0.3` failed on a working drill.
- CAUSE: Multi-turn joint reports wrap (modulo artifacts).
- RECOVERY: Wrap-robust gate (any in-window moment, both signs).
- PREVENTION: Never threshold raw multi-turn positions.

## F10: talker matches after the pumped window (race)
- FAILURE: All pumps static (zeros), motion only post-pumps;
  signs/magnitudes then unreliable.
- CAUSE: DDS match lags (setup.ps1 + discovery ~20s) past pumps.
- RECOVERY: Pre-talk (6s throwaway) to build the match, then the
  measured pumped talk; SUB latches so commands persist.
- PREVENTION: Every commanded drill opens with a match primer.

---

# Part: bringup (merged from `nav2`)

# nav2 — Failure Catalog (live-verified)

## F1: USD cylinder wheel colliders shake the base (facet rolling)
- FAILURE: N1 skid-steer bounced +/-4cm, yawed, velocity spikes
  +/-8 rad/s on DOFs, front wheels over-spun 3-4x vs rears;
  odom verifier flaky (x integrates / forward speed random PASS/FAIL).
- CAUSE: USD Cylinder collision cooks to a faceted convex hull.
  Facet slap at each ground contact pumps a hop; the velocity
  drives re-accelerate into every slap (vault -> launch cycle),
  so the base never settles. Verified by bisection: identical
  robot with sphere colliders rolls glass-smooth (x 0->0.502m in
  300 steps, z pinned, dofv=[1,1,1,1] every sample, dofp equal).
- RECOVERY: Collision approximation — analytic sphere collider
  (r=0.1, carries RigidBody+Collision+Mass) + visual-only
  cylinder child (r=0.1, h=0.03, no physics APIs). See n1_build.py.
- PREVENTION: Never roll a robot on raw USD cylinder colliders
  at this scale; use sphere (or capsule) colliders for wheels and
  keep the cylinder as visual only.

## Ruled OUT during F1 (do not chase)
- Drive sign: +1 cmd -> net +X in every run (correct).
- CTL wipe on stop: real but harmless (authored drive holds 1.0).
- Drive gains: 20/50 violent, 2/2 mostly smooth, 1/0.5 violent
  again — gains modulate, do not cause. Ship damping 2/maxF 2.
- Engine/scenes/gravity: PhysX, single /PhysicsScene (TGS),
  g=9.81 fit, Z-up. Chassis collider: removal changed nothing.
- Split-prim RigidBody/Collision on wheels: same-prim rebuild
  changed nothing. Solver iterations 64/16+32/8: kept as
  articulation best practice, but did not fix F1 alone.

## Geometry shipped with the fix (n1_build.py)
- Wheelbase 0.24 -> 0.36 (tip margin 25.6 -> 35.8 deg).
- Spawn clearance +1.5cm (no zero-gap ground penetration pop).
- CTL jointNames follow geometry via wnames (no hardcoded list).

## F2: N2 scan pipeline silent (five stacked causes, all fixed)
- F2a: `IsaacCreateRTXLidarScanBuffer`/`IsaacComputeRTXLidarFlatScan`
  are deprecated and CRASH the process at first play (carb
  crashreporter right after the deprecation warnings). RECOVERY:
  `ROS2RtxLidarHelper(type=laser_scan)` straight from the product.
- F2b: `isaacsim.ros2.bridge` not loaded on fresh sims (OG node
  creation throws "extension not loaded"). RECOVERY:
  `app_utils.enable_extension("isaacsim.ros2.bridge")` at the top
  of every graph-authoring script (n1_build + n2_mount).
- F2c: `LidarSensor` AUTO product (rtx_sensor_*) dies with the
  --file call's handles (verified: string calls persist, file
  calls are isolated namespaces). RECOVERY: mirror NVIDIA's own
  `test_rtx_sensor.py`: `Lidar.create` (no LidarSensor) +
  `rep.create.render_product(lidar, (128,128))` which persists in
  USD. No keepalive needed.
- F2d: lidar parented under the chassis RIGID BODY emits empty
  scans (19 empty ticks, even boxed in on 4 sides); same pose at
  the articulation root gives 24 full frames. RECOVERY: parent to
  the articulation root, never a rigid body.
- F2e: `Lidar.create positions=` are WORLD-frame, not
  parent-local: [[0,0,0.25]] put the lidar at world z=0.25,
  INSIDE the chassis (0.19..0.34) -> self-occluded empties.
  RECOVERY: world coords [[0,0,0.515]].
- PREVENTION: root-parented lidar + explicit rep product (128,128)
  + Helper graph is the shipped N2 recipe (3/3 N2-PASS).

## Ruled OUT during F2 (do not chase)
- Drive/CTL/gains/engine: N1 green 3/3 throughout; odom flowed
  while scan was silent (same DDS, same pumps).
- QoS mismatch: /scan publisher RELIABLE/VOLATILE, compatible.
- HELP config: defaults all sane (enabled, frameSkip 0,
  type=laser_scan); fullScan deprecated-ignored. Publisher
  existed from the first run; data never arrived.
- Named-vs-auto product binding: identical (camera rel +
  GenericModelOutput orderedVar) except resolution.
- Raw `writer.attach([product])` never ticks for RTX sensors;
  `sensor.attach_writer` is the working in-sim diagnostic.
- `Controller.attribute().set()` is runtime-only; play re-parses
  from USD and wipes it. Use USD-level writes for persistent
  graph config (verified: OG-GET new, USD-GET old).
- LaserScan invalid returns are -1.0, not inf: gate geometry on
  min of positive ranges (`rmin_valid`), not raw min.
- Verifier vacuity: `all()` over zero msgs passes; conjoin every
  gate with HAVE (msgs>=5).
- NEVER RemovePrim render products: scheduler-owned, removal
  crashes the renderer (rtx.hydra backtrace, verified).
- Phantom ART reads (UNCONFIRMED): removed N1Base_* prims
  reappearing in later bridge reads with zeroed transforms;
  suspected stale bridge USD view. Harmless: mount picks
  newest-by-timestamp; N1/N2 green despite it.

---

# Part: planning (merged from `navigation`)

# Navigation — Failure Catalog (live-verified)

## R7: rasterizer slices are [x0:x1) — count x1-x0, not inclusive
- FAILURE: Predicted V11 occ=84 (inclusive ranges); got 62.
- CAUSE: grid[y0:y1, x0:x1] holds (x1-x0)*(y1-y0) cells; D is
  5x5=25 (not 6x6), F is 7x3=21 (not 8x4). 25+16+21=62 exact.
- RECOVERY: Derive expected counts with slice arithmetic; probe
  centers (d/e/f=255) independently confirm placement.

## R6: rasterizers see the WHOLE stage — clean prior colliders
- CAUSE (caught pre-run): v11 rasterizer walks all of /World;
  N1/N3 collider prims left in stage would add 54 phantom cells.
- RECOVERY: Every yard build removes prior drill prims first
  (clean-slate pattern, like the O-builds).

## R5: pure_pursuit_step scans from index 0 — pass the REMAINING path
- FAILURE: Full-path pursuit stalled near start (400 steps,
  arrival 10.4m): once >1m along, the first waypoint beyond
  lookahead was BEHIND the robot -> reverse oscillation.
- CAUSE: Stateless step scans path[0:]; no progress tracking.
- RECOVERY: Caller tracks nearest index k (monotonic) and
  passes path[k:] each step -> done in 132, arrival 0.494.
  Distill candidate: clarify the contract in the docstring.

## R4: Tee-Object evidence files garble verifiers (use Set-Content)
- FAILURE: n3_validate.txt via Tee-Object: console showed
  "a=0 b=1 c=1 bad=0/40" but file gates all FAILED.
- CAUSE: Tee-Object writes UTF-16; the utf-8 file read garbles.
- RECOVERY: Pipe evidence through Set-Content (like the JSON
  evidence), never Tee-Object.

## R3: python_server caches repo imports across sends
- FAILURE: Fixed robot_footprint.py on disk (Path->Prim), but
  re-sent scripts kept crashing with the OLD code — even after
  `del sys.modules[...]` + fresh import.
- CAUSE: Server-side import caching beyond sys.modules (stale
  code object served for the same path).
- RECOVERY: Drills INLINE short library functions instead of
  importing repo modules. Keep the disk fix (correct for fresh
  processes); verify library patches in a NEW process, not a
  re-sent script. Also clear the script dir's __pycache__.

## R2: library robot_footprint passed Sdf.Path, needs UsdPrim (FIXED)
- FAILURE: compute_robot_footprint crashed: BBoxCache.
  ComputeWorldBound got Path, C++ wants UsdPrim.
- CAUSE: Library collected prim.GetPath() into a list fed to
  bounds_utils.compute_combined_aabb, which forwards elements
  to ComputeWorldBound(prim).
- FIX: Pass prims (2-line library patch, single usage site).
- VERIFIED 2026-11-03: fresh-import live check exact
  (0.4^3/0.4/0.2/0.2828); fix comment added to library file.

## R1: path-length baselines must use king-move distance
- FAILURE: Gated A* waypoint count against int(Euclidean cells)
  (45); valid 8-connected path (40 waypoints) "failed".
- CAUSE: King moves cover diagonals in 1 step; Euclidean
  overestimates the lower bound.
- RECOVERY: Baseline = max(|dx|,|dy|) moves (32 here); a valid
  avoidance path exceeds it (40 > 32).
