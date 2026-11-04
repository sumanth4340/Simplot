"""Compile vision-grounded SFT traces from live-captured screenshots.

Each VIS task was executed live in Kit (fresh stage per task) and
screenshotted mid-plan; the PNGs live in finetune/images/. This builder
re-validates every plan line via protocol.validate and every skill via
thinker.select_skills (same discipline as build_drill_traces.py), then
writes traces_vision.jsonl with meta.backend="live", images=1, and
image_files=[...]. Records validate through trace_schema.py.

Usage:
  python action-reasoner/build_vision_traces.py [--out DIR]
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


def _load(name, path):
    spec = importlib.util.spec_from_file_location("arvt_%s" % name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


thinker = _load("thinker", EXT_PY / "thinker.py")
protocol = _load("protocol", EXT_PY / "protocol.py")
handlers = _load("handlers", EXT_PY / "handlers.py")
trace_schema = _load("trace_schema", ROOT / "trace_schema.py")

# (id, task, skill, lines) — PNG must exist at finetune/images/<id>.png.
# Every plan was executed live during capture (0 failures); the builder
# re-checks validity + skill retrieval offline.
VIS_TASKS = [
    ("vis01", "create two cube prims and delete the red one", "stage", [
        "create.objects.cuboid pos=-1,0,0.5 size=1.0 color=0.6,0.6,0.6 name=gray",
        "create.objects.cuboid pos=1,0,0.5 size=1.0 color=1.0,0.2,0.2 name=red",
        "scene.delete.prim target=/World/red",
    ]),
    ("vis02", "clone the tallest cone prim into a grid", "modeling", [
        "create.objects.fixed_cone pos=-2,0,0.3 radius=0.3 height=0.6 name=short",
        "create.objects.fixed_cone pos=0,0,0.5 radius=0.3 height=1.0 name=mid",
        "create.objects.fixed_cone pos=2,0,0.8 radius=0.3 height=1.6 name=tall",
        "robot.clone target=/World/tall count=3",
    ]),
    ("vis03", "set the rigid body sphere pose onto the pad", "physics", [
        "create.objects.sphere pos=-2,0,0.5 radius=0.4 color=0.2,0.4,1.0 mass=1.0 name=blue",
        "create.objects.fixed_cuboid pos=1,0,0.25 size=1.0 name=pad",
        "physics.set.pose target=/World/blue pos=1,0,0.9",
    ]),
    ("vis04", "bind a rubber material to the dark gripper pads", "modeling", [
        "create.objects.cuboid pos=0,0,0.5 size=0.4 color=0.15,0.15,0.15 name=pads",
        "material.add.rigid_body_material stage=/World path=/World/Looks/rubber density=1100 staticFriction=0.9 dynamicFriction=0.7 restitution=0.2",
        "material.bind.material prim_path=/World/pads material_path=/World/Looks/rubber",
    ]),
    ("vis05", "cap the elbow drive torque on the arm joints", "articulation", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 name=ve_base",
        "create.objects.cuboid pos=0,0,0.9 size=0.5 name=ve_arm",
        "robot.add.articulation path=/World/ve_base",
        "joint.create.joint joint_type=revolute from_prim=/World/ve_base to_prim=/World/ve_arm axis=Z",
        "robot.set.torque_limit target=/World/Joints/ve_base_to_ve_arm value=25.0",
    ]),
    ("vis06", "mount a bumper range sensor beside the blue rover", "sensors", [
        "create.objects.cuboid pos=0,0,0.5 size=1.0 color=0.2,0.3,0.8 name=rover",
        "sensor.do.range_sensor_create_generic path=/VBumper min_range=0.2 max_range=30.0",
    ]),
    ("vis07", "stack the small rigid crate on the big crate for the physics test", "physics", [
        "create.objects.cuboid pos=0,0,0.5 size=1.0 name=big",
        "create.objects.cuboid pos=2,0,0.25 size=0.5 name=small",
        "physics.set.pose target=/World/small pos=0,0,1.25",
    ]),
    ("vis08", "save the arena stage after staging three cones", "stage", [
        "create.objects.fixed_cone pos=-1,0,0.5 radius=0.3 height=1.0 name=ac1",
        "create.objects.fixed_cone pos=0,0,0.5 radius=0.3 height=1.0 name=ac2",
        "create.objects.fixed_cone pos=1,0,0.5 radius=0.3 height=1.0 name=ac3",
        "scene.save path=stages/vis_arena.usd",
    ]),
    ("vis09", "make the heavy rigid barrel kinematic for the physics photo", "physics", [
        "create.objects.cylinder pos=0,0,0.5 radius=0.4 height=1.0 mass=20.0 name=barrel",
        "physics.set.rigid_body path=/World/barrel kinematic=true",
    ]),
    ("vis10", "clone the goal marker into a row of three", "modeling", [
        "create.objects.visual_sphere pos=0,0,0.5 radius=0.4 color=0.2,1.0,0.3 name=goalm",
        "robot.clone target=/World/goalm count=3",
    ]),
    ("vis11", "add a rigid body to the leaning tower top", "physics", [
        "create.objects.fixed_cuboid pos=0,0,0.5 size=1.0 name=twr",
        "create.objects.fixed_cuboid pos=0.1,0,1.5 size=1.0 name=twrtop",
        "physics.add.rigid_body target=/World/twrtop",
    ]),
    ("vis12", "create a prop group with a red crate inside", "stage", [
        "scene.create.prim path=/World/vprops type=Xform",
        "create.objects.cuboid pos=0,0,0.5 size=0.8 color=1.0,0.2,0.2 name=vcrate",
    ]),
    ("vis13", "set mars gravity and drop the rock", "physics", [
        "sim.set.gravity value=0,0,-3.71",
        "create.objects.sphere pos=0,0,1.5 radius=0.3 mass=1.0 name=vrock",
    ]),
    ("vis14", "mount a light curtain across the doorway posts", "sensors", [
        "create.objects.fixed_cylinder pos=-1,0,0.5 radius=0.1 height=1.0 name=door1",
        "create.objects.fixed_cylinder pos=1,0,0.5 radius=0.1 height=1.0 name=door2",
        "sensor.create.light_beam_sensor path=/VDoor num_rays=16",
    ]),
    ("vis15", "reset the physics trial and restage the drop ball", "physics", [
        "create.objects.sphere pos=0,0,2.0 radius=0.3 mass=1.0 name=vball",
        "sim.reset",
    ]),
    ("vis16", "drop a soft purple deformable cone and let it settle on the ground", "deform", [
        "physics.add.physics_scene path=/World/PhysicsScene",
        "create.objects.cone pos=0,0,1.5 color=0.6,0.2,0.8 name=vsoft",
        "sim.play",
    ]),
    ("vis17", "assembling a robot arm articulation with angular drive targets", "articulation", [
        "create.objects.cuboid pos=0,0,0.25 size=0.5 color=0.5,0.5,0.5 name=vbase",
        "create.objects.cuboid pos=0,0,0.9 size=0.5 color=1.0,0.8,0.2 name=varm",
        "joint.create.joint joint_type=revolute from_prim=/World/vbase to_prim=/World/varm axis=Z",
    ]),
    ("vis18", "bind a bumpy rubber rigid-body material to the crate", "modeling", [
        "create.objects.cuboid pos=0,0,0.5 size=0.8 color=0.6,0.4,0.2 name=vcrate",
        "material.add.rigid_body_material stage=/World path=/World/Looks/vrubber density=1100 staticFriction=0.9 dynamicFriction=0.7 restitution=0.2",
        "material.bind.material prim_path=/World/vcrate material_path=/World/Looks/vrubber",
    ]),
    ("vis19", "drop the red ball in moon gravity for the trial", "physics", [
        "create.objects.sphere pos=0,0,2.0 radius=0.3 color=1.0,0.2,0.2 mass=1.0 name=vmoon",
        "sim.set.gravity value=0,0,-1.62",
        "sim.play",
    ]),
    ("vis20", "measure range on the crate stack with a spinning rtx lidar", "sensors", [
        "create.objects.fixed_cuboid pos=0,0,0.5 size=1.0 name=vstack0",
        "create.objects.fixed_cuboid pos=0,0,1.5 size=1.0 name=vstack1",
        "sensor.create.rtx_lidar path=/World/vlidar",
        "sim.play",
    ]),
]


def generate(out_dir: Path) -> dict:
    catalog = protocol.load_catalog(ROOT / "actions_compact.json")
    routing = json.loads((ROOT / "skills_routing.json").read_text(encoding="utf-8"))
    signatures = [protocol.help_line(k, catalog[k])
                  for k in handlers.HANDLED_ACTIONS if k in catalog]
    stats = {"tasks": 0, "written": 0, "invalid": [], "misses": [],
             "groups": Counter(), "skills": Counter()}
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir = ROOT / "finetune" / "images"
    with open(out_dir / "traces_vision.jsonl", "w", encoding="utf-8") as f:
        for vid, task, skill, lines in VIS_TASKS:
            stats["tasks"] += 1
            img_rel = "images/%s.png" % vid
            if not (img_dir / ("%s.png" % vid)).exists():
                stats["invalid"].append((task, vid, "missing " + img_rel))
                continue
            actions_text = "\n".join(lines)
            batch = protocol.parse_batch(actions_text)
            valid = bool(batch)
            for key, raw, lineno in batch:
                try:
                    protocol.validate(key, raw, catalog, lineno=lineno)
                except (protocol.ValidationError, protocol.ProtocolError) as e:
                    valid = False
                    stats["invalid"].append((task, vid, f"{key}: {e}"[:160]))
                    break
                stats["groups"][catalog[key].get("group")] += 1
            if not valid:
                continue
            skills = thinker.select_skills(task, routing)
            names = [s.get("skill") or s.get("name") for s in skills]
            if skill not in names:
                stats["misses"].append((task, vid, skill, names))
                continue
            for name in names:
                stats["skills"][name] += 1
            record = {
                "messages": [
                    {"role": "system",
                     "content": thinker.build_system_prompt(signatures, skills)},
                    {"role": "user",
                     "content": "STAGE IMAGE: %s\nTASK: %s" % (img_rel, task)},
                    {"role": "assistant", "content": actions_text},
                ],
                "meta": {
                    "task": task,
                    "backend": "live",
                    "validated": True,
                    "images": 1,
                    "image_files": [img_rel],
                    "actions": [k for k, _, _ in batch],
                    "skills": names,
                },
            }
            schema_errs = trace_schema.validate_record(record)
            if schema_errs:
                stats["invalid"].append((task, vid, "; ".join(schema_errs)[:160]))
                continue
            f.write(json.dumps(record) + "\n")
            stats["written"] += 1
    return stats


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build vision SFT traces")
    parser.add_argument("--out", default=str(ROOT / "finetune"),
                        help="output directory")
    args = parser.parse_args(argv)
    stats = generate(Path(args.out))
    print(f"tasks: {stats['tasks']} traces written: {stats['written']}")
    print(f"invalid: {len(stats['invalid'])} misses: {len(stats['misses'])}")
    for task, vid, err in stats["invalid"]:
        print(f"  INVALID [{vid}] {task} :: {err}")
    for task, vid, skill, names in stats["misses"]:
        print(f"  MISS [{vid}] want={skill} task={task!r} got={names}")
    print(f"action groups in traces: {dict(stats['groups'])}")
    print(f"skill cites: {dict(stats['skills'])}")
    print(f"out: {args.out}")
    return 0 if not stats["invalid"] and not stats["misses"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
