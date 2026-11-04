"""Compile SFT traces from the verified skill-pack drills.

Each drill (N1/N2/A-drills/D1/R1/R2/G1/G2/P1) becomes hand-authored
task -> action-line traces over CATALOG-ed runnable actions, with the
drill skill cited via the routing index. Same machine-validation
discipline as build_traces.py: any line that fails protocol.validate
refuses the whole task, and any task whose drill skill is NOT retrieved
by thinker.select_skills is reported as a miss (fix wording, rerun).

Snapshots multiply volume with real signal: identical task+plan under
three canned stage states teaches snapshot conditioning.

Outputs (default: action-reasoner/finetune/):
  traces_drills.jsonl - one {"messages": [...], "meta": {...}} per
    task x snapshot. Train on traces_mock.jsonl + traces_drills.jsonl.

Usage:
  python action-reasoner/build_drill_traces.py [--out DIR]
"""
import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXT_PY = (ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim"
          / "action" / "reasoner" / "executor")


def _load(name):
    spec = importlib.util.spec_from_file_location(f"ardt_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


thinker = _load("thinker")
protocol = _load("protocol")
handlers = _load("handlers")

_spec_ts = importlib.util.spec_from_file_location(
    "ar_trace_schema", ROOT / "trace_schema.py")
trace_schema = importlib.util.module_from_spec(_spec_ts)
sys.modules["ar_trace_schema"] = trace_schema
_spec_ts.loader.exec_module(trace_schema)

SNAPSHOTS = [
    ("canned-empty", "sim: paused\nstage has no /World"),
    ("canned-plane", "sim: paused\nstage: /World/ground (plane 20m)"),
    ("canned-rover", "sim: paused\nstage: /World/chassis + 4 wheels (no drives yet)"),
]

# (task, plan lines, drill tag, expected skill)
DRILL_TASKS = [
    # -- nav2 N1: skid-steer + sphere wheels + velocity drive --
    ("drive a skid-steer rover forward", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=chassis",
        "create.objects.sphere pos=0.2,0.15,0.1 radius=0.1 name=wheel_fl",
        "create.objects.sphere pos=0.2,-0.15,0.1 radius=0.1 name=wheel_fr",
        "create.objects.sphere pos=-0.2,0.15,0.1 radius=0.1 name=wheel_rl",
        "create.objects.sphere pos=-0.2,-0.15,0.1 radius=0.1 name=wheel_rr",
        "robot.set.joint_drive target=/World/wheel_fl stiffness=0 damping=2 max_force=2 target_velocity=1.0",
        "robot.set.joint_drive target=/World/wheel_fr stiffness=0 damping=2 max_force=2 target_velocity=1.0",
        "robot.set.joint_drive target=/World/wheel_rl stiffness=0 damping=2 max_force=2 target_velocity=1.0",
        "robot.set.joint_drive target=/World/wheel_rr stiffness=0 damping=2 max_force=2 target_velocity=1.0",
        "sim.play",
    ], "N1", "nav2"),
    ("make a four-wheeled rover drive ahead", [
        "# analytic sphere wheel colliders roll smooth; cylinders facet-slap (nav2 F1)",
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=chassis",
        "create.objects.sphere pos=0.2,0.15,0.1 radius=0.1 name=wheel_fl",
        "create.objects.sphere pos=0.2,-0.15,0.1 radius=0.1 name=wheel_fr",
        "create.objects.sphere pos=-0.2,0.15,0.1 radius=0.1 name=wheel_rl",
        "create.objects.sphere pos=-0.2,-0.15,0.1 radius=0.1 name=wheel_rr",
        "robot.set.joint_drive target=/World/wheel_fl stiffness=0 damping=2 max_force=2 target_velocity=1.0",
        "robot.set.joint_drive target=/World/wheel_fr stiffness=0 damping=2 max_force=2 target_velocity=1.0",
        "robot.set.joint_drive target=/World/wheel_rl stiffness=0 damping=2 max_force=2 target_velocity=1.0",
        "robot.set.joint_drive target=/World/wheel_rr stiffness=0 damping=2 max_force=2 target_velocity=1.0",
        "sim.play",
    ], "N1", "nav2"),
    ("fix a bouncy wheeled robot by refitting round wheels", [
        "# faceted cylinder colliders pump hops; refit analytic spheres (nav2 F1)",
        "scene.delete.prim target=/World/wheel_cyl_fl",
        "scene.delete.prim target=/World/wheel_cyl_fr",
        "create.objects.sphere pos=0.2,0.15,0.1 radius=0.1 name=wheel_fl",
        "create.objects.sphere pos=0.2,-0.15,0.1 radius=0.1 name=wheel_fr",
        "robot.set.joint_drive target=/World/wheel_fl damping=2 max_force=2 target_velocity=1.0",
        "sim.play",
    ], "N1", "nav2"),
    ("replace cylinder wheels with spheres so the base rolls smooth", [
        "scene.delete.prim target=/World/wheel_cyl_rl",
        "scene.delete.prim target=/World/wheel_cyl_rr",
        "create.objects.sphere pos=-0.2,0.15,0.1 radius=0.1 name=wheel_rl",
        "create.objects.sphere pos=-0.2,-0.15,0.1 radius=0.1 name=wheel_rr",
        "robot.set.joint_drive target=/World/wheel_rl damping=2 max_force=2 target_velocity=1.0",
        "sim.play",
    ], "N1", "nav2"),
    # -- nav2 N2: lidar /scan --
    ("publish lidar scans to scan", [
        "# parent lidar to articulation root; Helper graph publishes laser_scan (nav2 F2)",
        "sensor.create.rtx_lidar path=/World/lidar",
        "sim.play",
    ], "N2", "nav2"),
    ("mount a 2D lidar on a rover and scan", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=rover",
        "sensor.create.rtx_lidar path=/World/lidar",
        "sim.play",
    ], "N2", "nav2"),
    ("add a spinning lidar above the chassis", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=chassis",
        "sensor.create.rtx_lidar path=/World/lidar_top",
        "sim.step n=60",
    ], "N2", "nav2"),
    ("put a lidar on top and collect a scan", [
        "# lidar positions are world-frame; keep it clear of the chassis (nav2 F2)",
        "sensor.create.rtx_lidar path=/World/lidar_top",
        "sim.step n=60",
    ], "N2", "nav2"),
    # -- radac R1: radar --
    ("mount an RTX radar that actually detects", [
        "# generic WpmDmat model is silent; use the TI vendor config (radac F2)",
        "sensor.create.rtx_radar path=/World/radar config=IWRL6432AOP",
        "sim.play",
    ], "R1", "radac"),
    ("add a working radar sensor for crates", [
        "create.objects.fixed_cuboid pos=5,0,1.0 size=2.0 name=crate",
        "sensor.create.rtx_radar path=/World/radar config=IWRL6432AOP",
        "sim.play",
    ], "R1", "radac"),
    # -- radac R2: acoustic --
    ("capture ultrasonic echoes off nearby boxes", [
        "sensor.create.rtx_ultrasonic path=/World/sonic",
        "create.objects.fixed_cuboid pos=3,0,0.5 size=1.0 name=box0",
        "sim.play",
    ], "R2", "radac"),
    ("check what the acoustic array hears", [
        "# bare cubes echo fine; prove liveness by geometry removal (radac R2)",
        "sensor.create.rtx_ultrasonic path=/World/sonic",
        "create.objects.fixed_cuboid pos=4,-2,0.5 size=1.0 name=box1",
        "sim.step n=90",
    ], "R2", "radac"),
    # -- deform D1 --
    ("drop a soft cone on the ground and let it settle", [
        "# deformables need an explicit PhysicsScene or reads never bind (deform F3)",
        "physics.add.physics_scene path=/World/PhysicsScene",
        "create.objects.cone pos=0,0,1.5 name=soft",
        "sim.play",
        "sim.step n=300",
    ], "D1", "deform"),
    ("settle a soft jelly cone and read squash via tensors", [
        "physics.add.physics_scene path=/World/PhysicsScene",
        "create.objects.cone pos=0,0,1.5 name=soft",
        "sim.play",
        "sim.step n=300",
    ], "D1", "deform"),
    ("rest a soft body on a plane", [
        "create.objects.plane size=20 name=ground",
        "create.objects.cone pos=0,0,1.5 name=soft",
        "sim.play",
    ], "D1", "deform"),
    ("drop a deformable cone onto the floor", [
        "# gate squash AND rest-on-ground together; never gate x/y (deform F5)",
        "physics.add.physics_scene path=/World/PhysicsScene",
        "create.objects.cone pos=0,0,1.5 name=soft",
        "sim.play",
    ], "D1", "deform"),
    # -- sdg-adv A-drills --
    ("stage labeled boxes for a KITTI datasets volume sweep", [
        "# label everything before first capture; bbox set freezes (sdg-adv R7)",
        "create.objects.fixed_cuboid pos=2,0,0.5 size=1.0 name=kboxa",
        "create.objects.fixed_cuboid pos=-2,0,0.5 size=1.0 name=kboxb",
        "sim.play",
    ], "A1", "sdg-adv"),
    ("build a two-box labeled scene for a KITTI dataset sweep", [
        "create.objects.fixed_cuboid pos=2,0,0.5 size=1.0 name=kboxa",
        "create.objects.fixed_cuboid pos=-2,0,0.5 size=1.0 name=kboxb",
        "sim.play",
    ], "A1", "sdg-adv"),
    ("lay out a seeded randomization scene", [
        "# seeded default_rng poses give bit-identical layouts (sdg-adv A2)",
        "create.objects.fixed_cuboid pos=1,1,0.5 size=1.0 name=abox0",
        "create.objects.fixed_cuboid pos=-1,-1,0.5 size=1.0 name=abox1",
        "sim.play",
    ], "A2", "sdg-adv"),
    ("scatter boxes deterministically for a dataset sweep", [
        "create.objects.fixed_cuboid pos=1,1,0.5 size=1.0 name=abox0",
        "create.objects.fixed_cuboid pos=-1,-1,0.5 size=1.0 name=abox1",
        "sim.play",
    ], "A2", "sdg-adv"),
    # -- gpunuc G-drills --
    ("open a warehouse stage from the asset root", [
        "# resolve roots via get_assets_root_path, never hardcode (gpunuc G2)",
        "scene.open path=/Isaac/Environments/Simple_Warehouse/warehouse.usd",
    ], "G2", "gpunuc"),
    ("load the Simple_Warehouse environment and diagnose missing assets", [
        "scene.open path=/Isaac/Environments/Simple_Warehouse/warehouse.usd",
    ], "G2", "gpunuc"),
    ("set a 60hz physics step and check GPU device visibility", [
        "# confirm cuda:0 device first on single-GPU boxes (gpunuc G1)",
        "sim.set.dt physics=0.0166667 rendering=0.0166667",
        "sim.play",
    ], "G1", "gpunuc"),
    ("configure the timestep for single-GPU simulation", [
        "sim.set.dt physics=0.0166667 rendering=0.0166667",
        "sim.play",
    ], "G1", "gpunuc"),
    # -- pyapi P1 --
    ("play the timeline for ten steps then stop", [
        "sim.play",
        "sim.step n=10",
        "sim.stop",
    ], "P1", "pyapi"),
    ("advance physics ten steps and pause", [
        "sim.play",
        "sim.step n=10",
        "sim.pause",
    ], "P1", "pyapi"),
    ("undo a mistakenly executed create command", [
        "# undo lives in omni.kit.undo, not omni.kit.commands (pyapi P1)",
        "scene.delete.prim target=/World/oops",
    ], "P1", "pyapi"),
    ("delete the wrong box with a Kit command", [
        "scene.delete.prim target=/World/box_wrong",
    ], "P1", "pyapi"),
    # -- stage ST1: fixed/visual/rolling shapes + prim + save --
    ("create a fixed cylinder prim and set its radius attribute", [
        "create.objects.fixed_cylinder pos=2,0,0.5 radius=0.4 height=1.0 name=pillar",
        "create.objects.fixed_cone pos=-2,0,0.5 radius=0.4 height=1.0 name=spike",
        "create.objects.fixed_sphere pos=0,2,0.5 radius=0.5 name=ball",
        "create.objects.fixed_capsule pos=0,-2,0.5 radius=0.3 height=1.0 name=pod",
    ], "ST1", "stage"),
    ("create a visual cuboid prim marker", [
        "create.objects.visual_cuboid pos=1,1,0.5 size=1.0 color=0.5,0.8,1.0 name=ghost",
        "create.objects.visual_sphere pos=-1,1,0.5 radius=0.5 name=orb",
        "create.objects.visual_cylinder pos=1,-1,0.5 radius=0.4 height=1.0 name=tube",
        "create.objects.visual_cone pos=-1,-1,0.5 radius=0.4 height=1.0 name=tip",
        "create.objects.visual_capsule pos=0,0,0.5 radius=0.3 height=1.0 name=shell",
    ], "ST1", "stage"),
    ("create a rolling capsule and a cylinder obstacle", [
        "create.objects.capsule pos=0,0,0.5 radius=0.3 height=1.0 mass=1.0 name=roller",
        "create.objects.cylinder pos=3,0,0.5 radius=0.4 height=1.0 mass=2.0 name=barrel",
    ], "ST1", "stage"),
    ("create a prim group then save the stage", [
        "scene.create.prim path=/World/props type=Xform",
        "create.objects.fixed_sphere pos=0,0,0.5 radius=0.5 name=ball",
        "scene.save path=stages/props.usd",
    ], "ST1", "stage"),
    # -- modeling MO1: import/export/clone/material --
    ("import the robot URDF asset", [
        "import.robot.urdf path=r/urdf/bot.urdf fix_base=false",
    ], "MO1", "modeling"),
    ("import the MJCF robot asset", [
        "import.robot.mjcf path=r/mjcf/bot.xml",
    ], "MO1", "modeling"),
    ("import the warehouse USD asset", [
        "import.asset.usd path=/Isaac/Environments/Simple_Warehouse/warehouse.usd name=warehouse",
    ], "MO1", "modeling"),
    ("import the heightmap terrain asset", [
        "import.asset.heightmap path=r/terrain/hills.png scale=2.0",
    ], "MO1", "modeling"),
    ("export the robot back to a URDF asset", [
        "export.asset.urdf path=stages/bot_export.urdf",
    ], "MO1", "modeling"),
    ("clone the robot chassis into a grid", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=chassis",
        "robot.clone target=/World/chassis count=4",
    ], "MO1", "modeling"),
    ("bind a rigid body material to the crate", [
        "create.objects.cuboid pos=2,0,0.5 size=1.0 name=crate",
        "material.add.rigid_body_material stage=/World path=/World/Looks/steel density=7800 staticFriction=0.5 dynamicFriction=0.3 restitution=0.1",
        "material.bind.material prim_path=/World/crate material_path=/World/Looks/steel",
    ], "MO1", "modeling"),
    # -- physics PH1: add/remove/set + gravity + reset --
    ("add a rigid body to the static crate", [
        "create.objects.fixed_cuboid pos=2,0,0.5 size=1.0 name=crate",
        "physics.add.rigid_body target=/World/crate",
    ], "PH1", "physics"),
    ("strip and refit the rigid body collider", [
        "create.objects.cuboid pos=0,0,0.5 size=1.0 name=crate",
        "physics.remove.collider target=/World/crate",
        "physics.remove.rigid_body target=/World/crate",
        "physics.add.rigid_body target=/World/crate",
        "physics.add.collider target=/World/crate",
    ], "PH1", "physics"),
    ("set the rigid body pose then spin it with velocity", [
        "create.objects.cuboid pos=0,0,2.0 size=1.0 name=flyer",
        "physics.set.pose target=/World/flyer pos=1,2,0.5",
        "sim.play",
        "physics.set.velocity target=/World/flyer linear=0,0,-1 angular=0,0,0",
    ], "PH1", "physics"),
    ("set the rigid body kinematic for the physics trial", [
        "create.objects.cuboid pos=0,0,0.5 size=1.0 name=crate",
        "physics.set.rigid_body path=/World/crate kinematic=true",
    ], "PH1", "physics"),
    ("set the rigid static collider on the physics pad", [
        "create.objects.fixed_cuboid pos=-2,0,0.25 size=0.5 name=pad",
        "physics.set.static_collider path=/World/pad",
    ], "PH1", "physics"),
    ("set gravity for the physics sim", [
        "sim.set.gravity value=0,0,-1.62",
    ], "PH1", "physics"),
    ("reset the physics trial", [
        "sim.reset",
    ], "PH1", "physics"),
    # -- articulation AR1: torque + limits --
    ("set torque limits on the drive joints", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=ar_base",
        "create.objects.cuboid pos=0,0,0.9 size=0.5 name=ar_arm",
        "robot.add.articulation path=/World/ar_base",
        "joint.create.joint joint_type=revolute from_prim=/World/ar_base to_prim=/World/ar_arm axis=Z",
        "robot.set.torque_limit target=/World/Joints/ar_base_to_ar_arm value=20.0",
        "robot.set.torque target=/World/Joints/ar_base_to_ar_arm value=5.0",
        "robot.set.velocity_limit target=/World/ar_base value=3.0",
    ], "AR1", "articulation"),
    # -- sensors SE1: generic/lidar/light-beam --
    ("create a generic range sensor", [
        "sensor.do.range_sensor_create_generic path=/GenericSensor min_range=0.4 max_range=100.0",
    ], "SE1", "sensors"),
    ("create a spinning lidar range sensor", [
        "sensor.do.range_sensor_create_lidar path=/Lidar horizontal_fov=360.0 vertical_fov=30.0 rotation_rate=20.0",
    ], "SE1", "sensors"),
    ("mount a light beam curtain sensor", [
        "sensor.create.light_beam_sensor path=/LightBeam_Sensor num_rays=8",
    ], "SE1", "sensors"),
    # -- bulk ST1: layouts, stacks, fix-ups --
    ("create a row of five traffic cones", [
        "create.objects.fixed_cone pos=-4,0,0.5 radius=0.3 height=1.0 color=1.0,0.3,0.1 name=cone1",
        "create.objects.fixed_cone pos=-2,0,0.5 radius=0.3 height=1.0 color=1.0,0.3,0.1 name=cone2",
        "create.objects.fixed_cone pos=0,0,0.5 radius=0.3 height=1.0 color=1.0,0.3,0.1 name=cone3",
        "create.objects.fixed_cone pos=2,0,0.5 radius=0.3 height=1.0 color=1.0,0.3,0.1 name=cone4",
        "create.objects.fixed_cone pos=4,0,0.5 radius=0.3 height=1.0 color=1.0,0.3,0.1 name=cone5",
    ], "ST1", "stage"),
    ("create a stack of three crates", [
        "create.objects.cuboid pos=0,0,0.5 size=1.0 color=0.7,0.5,0.3 name=crate_low",
        "create.objects.cuboid pos=0,0,1.5 size=1.0 color=0.7,0.5,0.3 name=crate_mid",
        "create.objects.cuboid pos=0,0,2.5 size=1.0 color=0.7,0.5,0.3 name=crate_top",
    ], "ST1", "stage"),
    ("create a tinted glass marker cuboid", [
        "create.objects.visual_cuboid pos=1,1,0.5 size=1.0 color=0.4,0.8,1.0 name=marker",
    ], "ST1", "stage"),
    ("create a fenced pad with four posts", [
        "create.objects.fixed_cylinder pos=-1,-1,0.5 radius=0.1 height=1.0 name=post1",
        "create.objects.fixed_cylinder pos=1,-1,0.5 radius=0.1 height=1.0 name=post2",
        "create.objects.fixed_cylinder pos=-1,1,0.5 radius=0.1 height=1.0 name=post3",
        "create.objects.fixed_cylinder pos=1,1,0.5 radius=0.1 height=1.0 name=post4",
        "create.objects.visual_cuboid pos=0,0,0.05 size=2.4 color=0.3,0.3,0.3 name=padslab",
    ], "ST1", "stage"),
    ("delete the misplaced barrel prim and create it again", [
        "create.objects.cylinder pos=3,0,0.5 radius=0.4 height=1.0 mass=2.0 name=barrel2",
        "scene.delete.prim target=/World/barrel2",
        "create.objects.cylinder pos=4,0,0.5 radius=0.4 height=1.0 mass=2.0 name=barrel2",
    ], "ST1", "stage"),
    ("create nested prim groups for the arena", [
        "scene.create.prim path=/World/arena type=Xform",
        "scene.create.prim path=/World/arena/props type=Xform",
        "scene.create.prim path=/World/arena/robots type=Xform",
    ], "ST1", "stage"),
    ("save the finished arena stage to disk", [
        "scene.save path=stages/arena.usd",
    ], "ST1", "stage"),
    ("create heavy and light barrel prims", [
        "create.objects.cylinder pos=-1,0,0.5 radius=0.4 height=1.0 mass=20.0 name=heavy",
        "create.objects.cylinder pos=1,0,0.5 radius=0.4 height=1.0 mass=0.5 name=light",
    ], "ST1", "stage"),
    # -- bulk MO1: imports, clones, materials --
    ("import the forklift URDF asset", [
        "import.robot.urdf path=r/urdf/forklift.urdf fix_base=true",
    ], "MO1", "modeling"),
    ("import the MJCF hand asset with fixed fingers", [
        "import.robot.mjcf path=r/mjcf/hand.xml",
    ], "MO1", "modeling"),
    ("import the lab USD asset at the dock", [
        "import.asset.usd path=/Isaac/Environments/Simple_Lab/lab.usd name=lab pos=5,0,0",
    ], "MO1", "modeling"),
    ("import a dune heightmap terrain asset", [
        "import.asset.heightmap path=r/terrain/dunes.png scale=4.0",
    ], "MO1", "modeling"),
    ("export the rover to a URDF asset", [
        "export.asset.urdf path=stages/rover_export.urdf",
    ], "MO1", "modeling"),
    ("clone the pallet into a grid of six", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=pallet",
        "robot.clone target=/World/pallet count=6",
    ], "MO1", "modeling"),
    ("bind a rubber material to the gripper pads", [
        "create.objects.cuboid pos=0,0,0.5 size=0.4 name=pad_l",
        "material.add.rigid_body_material stage=/World path=/World/Looks/rubber density=1100 staticFriction=0.9 dynamicFriction=0.7 restitution=0.2",
        "material.bind.material prim_path=/World/pad_l material_path=/World/Looks/rubber",
    ], "MO1", "modeling"),
    ("bind a slick ice material to the slide", [
        "create.objects.fixed_cuboid pos=0,0,0.5 size=2.0 name=slide",
        "material.add.rigid_body_material stage=/World path=/World/Looks/ice density=917 staticFriction=0.05 dynamicFriction=0.03 restitution=0.4",
        "material.bind.material prim_path=/World/slide material_path=/World/Looks/ice",
    ], "MO1", "modeling"),
    # -- bulk PH1: bodies, mass, gravity, timeline --
    ("add a rigid body to the static rack", [
        "create.objects.fixed_cuboid pos=0,2,0.5 size=1.0 name=rack",
        "create.objects.fixed_cuboid pos=0,3,0.5 size=1.0 name=rack2",
        "physics.add.rigid_body target=/World/rack",
        "physics.add.rigid_body target=/World/rack2",
    ], "PH1", "physics"),
    ("set the rigid body mass for the physics drop test", [
        "create.objects.cuboid pos=0,0,2.0 size=1.0 name=dropper",
        "physics.set.mass target=/World/dropper value=5.0",
    ], "PH1", "physics"),
    ("set moon gravity for the physics drop test", [
        "sim.set.gravity value=0,0,-1.62",
        "create.objects.cuboid pos=0,0,3.0 size=0.5 name=hammer",
    ], "PH1", "physics"),
    ("set mars gravity for the physics rover", [
        "sim.set.gravity value=0,0,-3.71",
        "create.objects.sphere pos=1,0,0.5 radius=0.3 mass=1.0 name=rock",
    ], "PH1", "physics"),
    ("reset the physics trial between drops", [
        "create.objects.sphere pos=0,0,2.0 radius=0.3 mass=1.0 name=ball",
        "sim.reset",
    ], "PH1", "physics"),
    ("step the physics sim ten frames and pause", [
        "sim.play",
        "sim.step n=10",
        "sim.pause",
    ], "PH1", "physics"),
    ("stop the physics sim after the trial", [
        "create.objects.cuboid pos=0,0,0.5 size=1.0 name=prop",
        "sim.play",
        "sim.stop",
    ], "PH1", "physics"),
    ("make the rigid slide kinematic for the physics demo", [
        "create.objects.cuboid pos=0,0,0.5 size=1.0 name=slide2",
        "physics.set.rigid_body path=/World/slide2 kinematic=true",
    ], "PH1", "physics"),
    ("set the rigid body pose on the high shelf", [
        "create.objects.cuboid pos=0,0,0.5 size=0.5 name=parcel",
        "physics.set.pose target=/World/parcel pos=0,0,3.0",
    ], "PH1", "physics"),
    # -- bulk AR1: joints and drives --
    ("assemble the robot arm joints with angular drives", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=shoulder",
        "create.objects.cuboid pos=0,0,0.9 size=0.5 name=elbow",
        "robot.add.articulation path=/World/shoulder",
        "joint.create.joint joint_type=revolute from_prim=/World/shoulder to_prim=/World/elbow axis=Z",
        "robot.set.torque_limit target=/World/Joints/shoulder_to_elbow value=30.0",
    ], "AR1", "articulation"),
    ("set drive stiffness on the robot arm joints", [
        "create.objects.cuboid pos=2,0,0.25 size=0.5 name=wrist",
        "create.objects.cuboid pos=2,0,0.9 size=0.5 name=gripper",
        "robot.add.articulation path=/World/wrist",
        "joint.create.joint joint_type=revolute from_prim=/World/wrist to_prim=/World/gripper axis=Z",
        "robot.set.joint_drive target=/World/Joints/wrist_to_gripper stiffness=500.0 damping=50.0",
    ], "AR1", "articulation"),
    ("cap the drive torque on the arm joints", [
        "create.objects.cuboid pos=-2,0,0.25 size=0.5 name=hip",
        "create.objects.cuboid pos=-2,0,0.9 size=0.5 name=knee",
        "robot.add.articulation path=/World/hip",
        "joint.create.joint joint_type=revolute from_prim=/World/hip to_prim=/World/knee axis=Z",
        "robot.set.torque target=/World/Joints/hip_to_knee value=8.0",
        "robot.set.torque_limit target=/World/Joints/hip_to_knee value=15.0",
    ], "AR1", "articulation"),
    ("limit the articulation joint velocity with drive caps", [
        "create.objects.cuboid pos=4,0,0.25 size=0.5 name=turret",
        "create.objects.cuboid pos=4,0,0.9 size=0.5 name=barrel",
        "robot.add.articulation path=/World/turret",
        "joint.create.joint joint_type=revolute from_prim=/World/turret to_prim=/World/barrel axis=Z",
        "robot.set.velocity_limit target=/World/turret value=2.0",
    ], "AR1", "articulation"),
    # -- bulk SE1: sensor coverage --
    ("spin up the roof lidar range sensor", [
        "sensor.do.range_sensor_create_lidar path=/RoofLidar horizontal_fov=360.0 vertical_fov=30.0 rotation_rate=20.0 max_range=120.0",
    ], "SE1", "sensors"),
    ("mount a front bumper range sensor", [
        "sensor.do.range_sensor_create_generic path=/Bumper min_range=0.2 max_range=30.0",
    ], "SE1", "sensors"),
    ("mount a rear light beam curtain", [
        "sensor.create.light_beam_sensor path=/RearBeam num_rays=16 max_range=10.0",
    ], "SE1", "sensors"),
    ("create an ultrasonic parking range sensor", [
        "sensor.create.rtx_ultrasonic path=/ParkSonar",
    ], "SE1", "sensors"),
    ("create a radar blind-spot range sensor", [
        "sensor.create.rtx_radar path=/BlindRadar",
    ], "SE1", "sensors"),
    # -- bulk AP1: session and timeline --
    ("open the saved warehouse stage", [
        "scene.open path=stages/warehouse.usd",
    ], "AP1", "appsession"),
    ("play the timeline then pause it", [
        "sim.play",
        "sim.pause",
    ], "AP1", "appsession"),
    ("stop the timeline and reset the stage", [
        "sim.stop",
        "sim.reset",
    ], "AP1", "appsession"),
    ("step the playing timeline five frames", [
        "sim.play",
        "sim.step n=5",
        "sim.pause",
    ], "AP1", "appsession"),
    ("save the stage and open it back", [
        "scene.save path=stages/checkpoint.usd",
        "scene.open path=stages/checkpoint.usd",
    ], "AP1", "appsession"),
    ("set a finer physics sim dt for the contact test", [
        "sim.set.dt physics=0.008 rendering=0.016",
    ], "PH1", "physics"),
    # -- grade-gap ST1: color words always become r,g,b triples --
    ("create a red crate and a green crate side by side", [
        "# color words become r,g,b triples, never bare words (stage ST1)",
        "create.objects.cuboid pos=-1,0,0.5 size=1.0 color=1.0,0.0,0.0 name=crate_red",
        "create.objects.cuboid pos=1,0,0.5 size=1.0 color=0.2,0.8,0.2 name=crate_green",
    ], "ST1", "stage"),
    ("create a blue sphere and a yellow cone on the floor", [
        "create.objects.sphere pos=-1,0,0.3 radius=0.3 color=0.2,0.4,1.0 name=ball_blue",
        "create.objects.cone pos=1,0,0.5 color=1.0,0.85,0.2 name=cone_yellow",
    ], "ST1", "stage"),
    # -- grade-gap N2: lidar takes path + config + pos (no parent) --
    ("mount a vendor-configured lidar above the rover", [
        "# rtx lidar takes path + config + pos; it has no parent param (nav2 N2)",
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=rover",
        "sensor.create.rtx_lidar path=/World/lidar_nav config=OS1_128 pos=0,0,1.2",
        "sim.play",
    ], "N2", "nav2"),
    ("put a roof lidar at a world offset and step the scan", [
        "sensor.create.rtx_lidar path=/World/roof_lidar config=OS1_64 pos=2,0,2.5",
        "sim.step n=60",
    ], "N2", "nav2"),
]


def generate(out_dir: Path) -> dict:
    catalog = protocol.load_catalog(ROOT / "actions_compact.json")
    routing = json.loads((ROOT / "skills_routing.json").read_text(encoding="utf-8"))
    signatures = [protocol.help_line(k, catalog[k])
                  for k in handlers.HANDLED_ACTIONS if k in catalog]
    stats = {"tasks": 0, "written": 0, "invalid": [], "misses": [],
             "groups": Counter(), "skills": Counter()}
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "traces_drills.jsonl", "w", encoding="utf-8") as f:
        for task, lines, drill, skill in DRILL_TASKS:
            stats["tasks"] += 1
            actions_text = "\n".join(lines)
            batch = protocol.parse_batch(actions_text)
            valid = bool(batch)
            for key, raw, lineno in batch:
                try:
                    protocol.validate(key, raw, catalog, lineno=lineno)
                except (protocol.ValidationError, protocol.ProtocolError) as e:
                    valid = False
                    stats["invalid"].append((task, drill, f"{key}: {e}"[:160]))
                    break
                stats["groups"][catalog[key].get("group")] += 1
            if not valid:
                continue
            skills = thinker.select_skills(task, routing)
            names = [s.get("skill") or s.get("name") for s in skills]
            if skill not in names:
                stats["misses"].append((task, drill, skill, names))
                continue
            for name in names:
                stats["skills"][name] += 1
            for snap_label, snapshot in SNAPSHOTS:
                record = {
                    "messages": [
                        {"role": "system",
                         "content": thinker.build_system_prompt(signatures, skills)},
                        {"role": "user",
                         "content": thinker.build_user_prompt(task, snapshot)},
                        {"role": "assistant", "content": actions_text},
                    ],
                    "meta": {
                        "task": task,
                        "drill": drill,
                        "backend": "drill",
                        "skills": names,
                        "validated": True,
                        "images": 0,
                        "snapshot": snap_label,
                        "actions": [k for k, _, _ in batch],
                    },
                }
                schema_errs = trace_schema.validate_record(record)
                if schema_errs:
                    stats["invalid"].append(
                        (task, drill, f"schema: {schema_errs[0]}"[:160]))
                    break
                f.write(json.dumps(record) + "\n")
                stats["written"] += 1
    return stats


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build drill-derived SFT traces")
    parser.add_argument("--out", default=str(ROOT / "finetune"),
                        help="output directory")
    args = parser.parse_args(argv)
    stats = generate(Path(args.out))
    print(f"tasks: {stats['tasks']} traces written: {stats['written']}")
    print(f"invalid: {len(stats['invalid'])} misses: {len(stats['misses'])}")
    for task, drill, err in stats["invalid"]:
        print(f"  INVALID [{drill}] {task} :: {err}")
    for task, drill, skill, names in stats["misses"]:
        print(f"  MISS [{drill}] want={skill} task={task!r} got={names}")
    print(f"action groups in traces: {dict(stats['groups'])}")
    print(f"skill cites: {dict(stats['skills'])}")
    print(f"out: {args.out}")
    return 0 if not stats["invalid"] and not stats["misses"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
