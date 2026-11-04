# Skill routing map

| Skill | When to use | Extras |
|---|---|---|
| `action-and-event-data-generation` | Entry point for Isaac Sim synthetic data generation (SDG) with actors, humans, robots, events, incidents, captions, or cameras. Use when planning an Action and  | - |
| `actor-sdg-generate-lighting-variations` | Generate deterministic USD lighting override sublayers for Actor SDG. Use when randomizing lights, creating lighting variations, or preparing IRA prop_asset_pat | scripts |
| `actor-sdg-sweep-config` | Generate validated Isaac Sim Replicator Agent YAML variations and optionally batch-run Actor SDG. Use when sweeping an IRA config or preparing batch Actor SDG r | scripts |
| `behavior-tree-generation` | LLM-driven Behavior Tree Generation for Isaac Sim: turn a natural-language scenario into behavior-tree files. Use when generating a tree, authoring context/sche | scripts+refs |
| `calibrate-metropolis-camera` | Extract camera intrinsics, extrinsics, and FOV polygons to calibration.json. Use after cameras are placed; to place them first use place-camera-max-coverage. | scripts+refs |
| `data-collection-sim` | Headless Replicator SDG for static scenes (writers, poses, Kitti). Use when collecting annotated training data. Do NOT use for mobile-robot SDG (use mobility-ge | scripts |
| `generate-incident-config` | Author and validate the IRI event config YAML defining topple, fire, and spill incidents. Use when writing or debugging an incident config; to drive events use  | scripts+refs |
| `isaac-camera` | USD camera setup, render products, intrinsics, and lens distortion. Use when configuring Isaac Sim cameras. | - |
| `isaac-sim-assets` | Configure and troubleshoot Isaac Sim asset access through Asset Region Profiles, custom or local asset roots, downloadable asset packs, availability manifests,  | - |
| `isaac-sim-headless-deployment` | Run a built Isaac Sim 6 headless with --no-window and the renderer disabled. Use for batch SDG jobs, physics-only CI, or unattended server runs. | scripts |
| `isaac-sim-installation` | Install Isaac Sim from a public standalone build, Docker image, or Python package behind preflight, compatibility, EULA, and --execute gates. Use when installin | scripts+refs |
| `isaac-sim-migration` | Audit and validate Isaac Sim release migrations; currently covers 5.1 to 6.0. Do NOT use for new-project setup or unrelated runtime bugs. | - |
| `isaac-sim-orchestrator` | Integrate approved multi-skill Isaac Sim demos and validate delivery. Route focused obstacle-aware arm demos to motion-generation, including video requests; sco | refs |
| `isaac-sim-remote` | Localhost IPC client for a trusted Isaac Sim python_server (127.0.0.1:8226). Use for live stage iteration; intentional full Kit/Python surface on loopback only. | scripts+refs |
| `isaac-sim-rendering` | Headless RT2/PathTracing production rendering with ACES tuning. Use when capturing frames or validating render quality. | scripts |
| `isaac-sim-robot-navigation` | Live robot navigation and RL policy deployment in Isaac Sim. Use for runtime control or deploying exported robot policies with RobotPolicyRunner, env.yaml, and  | refs |
| `isaac-sim-ros-workspaces` | Clone, configure, or build IsaacSim-ros_workspaces using native ROS, Docker, custom interfaces, or Pixi. Use only for Isaac Sim ROS workspace requests, not gene | scripts+refs |
| `isaac-sim-ros2-bridge` | ROS 2 OmniGraph bridge, Nav2, and multi-robot namespacing in Isaac Sim 6. Use for ROS 2 integration and fleet topics. | scripts |
| `isaac-sim-sensor` | RTX and physics sensor simulation (camera, LiDAR, IMU, contact). Use when adding, tuning, or validating sensors. | scripts |
| `isaac-sim-troubleshooting` | Diagnose standalone library import/load/link failures and Kit hangs, freezes, or performance stalls. | - |
| `isaac-sim-validator` | Pre-delivery QA gate for standalone Isaac Sim libraries and Kit scripts. Level 3 executes untrusted Python unsandboxed and needs --confirm-execute. | scripts+refs |
| `isaac-sim-web-viewer` | Use when you need Isaac Sim in Chromium over WebRTC at http://HOST:8210 via this Compose stack. Not for installs, image-only pulls, or headless. | scripts+refs |
| `isaac-sim-workflow` | Scope Isaac Sim demos, libraries, POCs, and captures when deliverables or criteria are undefined, or only a plan is requested. Route approved builds to isaac-si | - |
| `manipulation-ik` | Differential IK, grasp frames, and joint-space manipulation in Isaac Sim 6. Use for arm control, grasps, and contact validation. | scripts |
| `meta-skills` | Use when asked to structure, create, compose, or improve agent skills, including new-skill proposals and Meta-Skilling Framework (MSF) authoring plans. | refs |
| `mobility-gen` | MobilityGen SDG: record trajectories then replay-render sensors. Use for mobile-robot synthetic datasets. | scripts |
| `motion-generation` | Build obstacle-aware arm and mobile-base controllers. Primary for UR10 pick-and-place around obstacles with physics/video; use manipulation-ik for obstacle-free | scripts+refs |
| `navigation-primitives` | Shared mobile-robot substrate: footprints, A*, kinematics, cameras. Use before navigation/MobilityGen; not for map.yaml export (use occupancy-map). | scripts |
| `object-bin-packing` | Pack boxes/parcels into a bin, pallet, or container and render SDG with IRO's bin_pack harmonizer. Use for warehouse/logistics packing synthetic data. | scripts |
| `occupancy-map` | Export ROS occupancy grids (map.yaml/png) from USD for Nav2. Not for footprints, A*, or kinematics (use navigation-primitives). | scripts |
| `physics-simulation` | PhysX/Newton scene and prim setup (bodies, joints, materials, sensors). Use when configuring simulation physics. | scripts |
| `physx-to-newton-conversion` | Convert a legacy PhysX-only USD asset (for example an Isaac Sim 5.x robot) to a Newton-capable package with the PhysX to MJC Conversion preset. Use when a PhysX | scripts |
| `place-camera-aim-at` | Occlusion-aware CircularCameraPlacement around one target prim or world point. Use for multi-angle product or robot inspection shots that must keep the subject  | scripts+refs |
| `place-camera-max-coverage` | Greedy CameraPlacementManager that fills a navmesh or XY scope until a patch-coverage ratio is met. Use for facility surveillance layouts that minimize camera c | scripts+refs |
| `profile-isaac-sim` | Profile standalone Isaac Sim libraries or Kit workloads. Use when measuring runtime performance with benchmarks or Tracy captures. | scripts |
| `run-incident-events` | Tag prims and drive IRI topple, fire, and spill incidents on a live stage, then record a report. Use when running incidents; to author the config YAML use gener | scripts+refs |
| `skill-distillation` | Propose skill-library updates from session learnings (loop step 5); writes only after explicit user confirmation. Use after novel fixes, workflows, or user corr | - |
| `spatial-reasoning` | USD spatial math: transforms, bbox, layouts, and planning helpers. Use when placing, scaling, or arranging scene assets. | scripts |
| `urdf-mjcf-to-usd-conversion` | Convert URDF/MJCF to USD for Isaac Sim and Isaac Lab. Use when importing a new robot description. | scripts |
| `usd-articulation` | Validate and build multi-arm articulations in USD. Use when assembling or fixing robot joint hierarchies. | scripts |
| `usd-composition-architecture` | Layered USD composition with physics and appearance payloads. Use when structuring sim-ready robot or environment assets. | - |
| `usd-pipeline` | USD asset discovery, measurement, placement, and shader compatibility. Use for scene assembly and headless render prep. | scripts |
| `validation-diff-gifs` | Pixel-diff GIFs comparing validation captures to golden images. Use to triage benchmark or regression image failures. | scripts |
| `vlm-scene-captioning` | Generate image + caption pairs and structured scene graphs (IRC, isaacsim.replicator.caption.core) for VLM training. Use when captioning scenes or wiring IRC in | scripts+refs |
| `nav2` | Skid-steer odometry and RTX lidar ROS2 scan bring-up drills (N1/N2) - wheel-collider rules, drive geometry, and the root-parented lidar + Helper-graph /scan rec | scripts+refs |
| `sdg-adv` | Advanced synthetic data at scale - KittiWriter contract, seeded deterministic layouts, 50-frame volume sweeps, and re-sweep exams (A1/A2/A3/VA). Use when writin | scripts+refs |
| `deform` | PhysX volume-deformable drill (D1) - explicit-PhysicsScene authoring, DeformablePrim tensor reads, stiffness scaling, and Newton no-go rules. Use when simulatin | scripts+refs |
| `radac` | RTX radar (R1) and acoustic (R2) GMO drills - vendor-config radar with ghost fingerprinting, bare-constructor acoustic arrays, and writer-based capture. Use whe | scripts+refs |
| `gpunuc` | Device honesty (G1) and asset-root resolution (G2) drills - single-GPU enumeration/selection with phantom-id negative test, and public-API asset resolution with | scripts+refs |
| `pyapi` | Kit Python API gap drills (P1) - command execute/undo map, omni.client sync-tuple contract, and the timeline play/advance/stop roundtrip over physics steps. Use | scripts+refs |
| `sense` | Live stage telemetry: sense.py JSON snapshot via the bridge, local verify/co_verify evidence checks. Use when reading prims, poses, velocities, or joints. | scripts |
| `stage` | Stage and USD core: save/open round-trip, prim authoring (Cube size is edge length, hand Mesh), properties, variants, payloads. Use when creating prims, create  | scripts |
| `modeling` | Indexed mesh authoring (points/counts/indices, CCW winding), OFFLINE URDF/USD asset import then reference into live stage, GridCloner to clone prims in a grid,  | scripts |
| `articulation` | Articulation roots (root-on-dynamic-link + FixedJoint), DOF tensor reads after play, angular drive targets in DEGREES. Use when assembling robots or reading joi | scripts |
| `manipulation` | USD drive-target commanding + stop/play re-parse, IsaacSiteAPI grasp frames, DLS IK, FixedJoint grasp attach. Use for arm control, IK, or grasping. | scripts |
| `rendering` | RtxCamera + CameraSensor capture (resolution [H,W], settle, rgb unwrap), dome/DistantLight exposure response. Use when capturing frames or tuning lights. | scripts |
| `viewport` | Viewport/app screenshots, camera_control look_at, select_prim round-trip. Use when screenshotting or driving the viewport camera. | scripts |
| `omnigraph` | Atomic Controller.edit graphs (CREATE_NODES+CONNECT+SET_VALUES), typed 3-tuple template inputs, tick-vs-authoring gating. Use when authoring OmniGraph graphs. | scripts |
| `behavior` | 60 timecodes/sec sampling, live-time reads via XformCache(tc), xformOp-degrees vs DOF-radians layers. Use when keyframing animation or sampling motion. | scripts |
| `appsession` | External session driving via isaacsim_send (simulation_control, open_stage, stage_info), timeline STOPPED/PLAYING/PAUSED cycle. Use when controlling play or ope | scripts |
| `physics` | Rigid-body physics: stepping, simulated-state reads, velocity (linear/angular) reads, hinge drives, colliders, contacts, gravity, trial reset, determinism, Phys | scripts |
| `xval` | Cross-skill co-validation drills X1-X14 with XN-REPORT receipts. Use when gauntlet-checking a new capability against all graduated skills. | scripts |
| `sensors` | RTX camera/lidar + physics IMU/contact drills (S1-S4, V7): depth frames, range sensing, contact validation. Use when adding or validating a camera, lidar, IMU,  | scripts |
| `rosnav` | ROS bridge bringup and rover navigation: bridge topics, odometry, skid-steer drive, Nav2 planning. Use when wiring ROS topics, driving a rover, or planning path | scripts |
| `sdg` | Synthetic data generation: Replicator writers, poses, KITTI labels, dataset sweeps. Use when collecting annotated training data or running SDG captures. | scripts |