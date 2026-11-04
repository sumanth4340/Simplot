"""Compile dispatcher SFT traces: composite task -> deploy plan.

Each task is a multi-agent job; the plan is a dispatch block validated
by dispatcher.validate_block (roster, ordering, xval rules) with the
primary skill retrieved by thinker.select_skills. Same gate discipline
as build_drill_traces.py: any invalid block or retrieval miss refuses
the task (exit 1).

Records use backend "drill" with drill tag "DSP" and carry the plan in
meta.dispatch (actions stays [] — dispatch lines are not catalog keys).

Outputs (default: action-reasoner/finetune/):
  traces_dispatch.jsonl - one {"messages": [...], "meta": {...}} per
    task x snapshot. Train on traces_mock + traces_drills +
    traces_dispatch + traces_live.

Usage:
  python action-reasoner/build_dispatch_traces.py [--out DIR]
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
    spec = importlib.util.spec_from_file_location(f"ardsp_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


thinker = _load("thinker")
dispatcher = _load("dispatcher")

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

# (task, dispatch lines, primary skill)
DISPATCH_TASKS = [
    ("drive a skid-steer rover with lidar odometry to the far cone", [
        "DEPLOY agent=sense",
        "DEPLOY agent=articulation needs=physics",
        "DEPLOY agent=physics",
        "DEPLOY agent=sensors",
        "DEPLOY agent=rosnav needs=articulation+sensors",
        "DEPLOY agent=xval",
        "PARALLEL agents=sense+physics",
        "COWORK agents=articulation+rosnav",
        "STEP n=1 agent=sense do=read-stage",
        "STEP n=2 agent=articulation do=attach-wheel-joints",
        "STEP n=3 agent=sensors do=mount-lidar",
        "STEP n=4 agent=rosnav do=drive-to-cone",
        "STEP n=5 agent=xval do=gauntlet-drive",
    ], "rosnav"),
    ("grasp the steel crate with the arm using IK and place it on the pallet", [
        "DEPLOY agent=sense",
        "DEPLOY agent=articulation needs=physics",
        "DEPLOY agent=physics",
        "DEPLOY agent=manipulation needs=articulation+physics",
        "DEPLOY agent=xval",
        "COWORK agents=articulation+manipulation",
        "STEP n=1 agent=sense do=read-stage",
        "STEP n=2 agent=manipulation do=solve-grasp-ik",
        "STEP n=3 agent=manipulation do=attach-and-place",
        "STEP n=4 agent=xval do=gauntlet-grasp",
    ], "manipulation"),
    ("run a KITTI dataset sweep with Replicator writers over the warehouse", [
        "DEPLOY agent=stage",
        "DEPLOY agent=modeling needs=stage",
        "DEPLOY agent=sensors",
        "DEPLOY agent=rendering",
        "DEPLOY agent=viewport needs=rendering",
        "DEPLOY agent=sdg needs=sensors+rendering",
        "DEPLOY agent=xval",
        "PARALLEL agents=rendering+viewport",
        "COWORK agents=sensors+sdg",
        "STEP n=1 agent=stage do=layout-props",
        "STEP n=2 agent=sensors do=pose-cameras",
        "STEP n=3 agent=sdg do=sweep-kitti",
        "STEP n=4 agent=xval do=gauntlet-labels",
    ], "sdg"),
    ("wire ROS bridge topics and publish lidar scans while the rover drives", [
        "DEPLOY agent=articulation needs=physics",
        "DEPLOY agent=physics",
        "DEPLOY agent=sensors",
        "DEPLOY agent=rosnav needs=articulation+sensors",
        "DEPLOY agent=omnigraph needs=rosnav+sensors",
        "DEPLOY agent=xval",
        "COWORK agents=rosnav+omnigraph",
        "STEP n=1 agent=rosnav do=bringup-bridge",
        "STEP n=2 agent=sensors do=mount-lidar",
        "STEP n=3 agent=omnigraph do=publish-scan-graph",
        "STEP n=4 agent=rosnav do=drive-while-scanning",
        "STEP n=5 agent=xval do=gauntlet-topics",
    ], "rosnav"),
    ("settle a soft deformable cone on the ground and read squash tensors", [
        "DEPLOY agent=sense",
        "DEPLOY agent=physics",
        "DEPLOY agent=deform needs=physics",
        "DEPLOY agent=xval",
        "COWORK agents=physics+deform",
        "STEP n=1 agent=physics do=author-physics-scene",
        "STEP n=2 agent=deform do=drop-and-settle",
        "STEP n=3 agent=deform do=read-squash",
        "STEP n=4 agent=xval do=gauntlet-deform",
    ], "deform"),
    ("capture frames with tuned dome exposure and rgb settle, then screenshot the viewport camera", [
        "DEPLOY agent=stage",
        "DEPLOY agent=rendering",
        "DEPLOY agent=viewport needs=rendering",
        "DEPLOY agent=xval",
        "COWORK agents=rendering+viewport",
        "STEP n=1 agent=rendering do=tune-dome-exposure",
        "STEP n=2 agent=viewport do=shoot-three-angles",
        "STEP n=3 agent=xval do=gauntlet-frames",
    ], "rendering"),
    ("keyframe the gate arm swing and sample the motion angle live", [
        "DEPLOY agent=articulation",
        "DEPLOY agent=manipulation needs=articulation",
        "DEPLOY agent=behavior needs=articulation",
        "DEPLOY agent=xval",
        "COWORK agents=manipulation+behavior",
        "STEP n=1 agent=articulation do=hinge-gate-arm",
        "STEP n=2 agent=behavior do=keyframe-swing",
        "STEP n=3 agent=behavior do=sample-angle",
        "STEP n=4 agent=xval do=gauntlet-motion",
    ], "behavior"),
    ("check single-GPU visibility then open the warehouse stage session", [
        "DEPLOY agent=gpunuc",
        "DEPLOY agent=appsession needs=gpunuc",
        "DEPLOY agent=stage",
        "DEPLOY agent=xval",
        "STEP n=1 agent=gpunuc do=enumerate-gpu",
        "STEP n=2 agent=appsession do=open-stage-session",
        "STEP n=3 agent=stage do=verify-warehouse",
        "STEP n=4 agent=xval do=gauntlet-session",
    ], "gpunuc"),
    ("advance the timeline ten steps, pause, and undo the mistaken prim", [
        "DEPLOY agent=pyapi",
        "DEPLOY agent=stage",
        "DEPLOY agent=xval",
        "STEP n=1 agent=pyapi do=play-ten-steps",
        "STEP n=2 agent=pyapi do=pause-and-undo",
        "STEP n=3 agent=stage do=verify-prim-gone",
        "STEP n=4 agent=xval do=gauntlet-timeline",
    ], "pyapi"),
    ("author an indexed mesh crate, clone a grid, and bind a steel material", [
        "DEPLOY agent=stage needs=physics",
        "DEPLOY agent=physics",
        "DEPLOY agent=modeling needs=stage+physics",
        "DEPLOY agent=xval",
        "COWORK agents=stage+modeling",
        "STEP n=1 agent=modeling do=author-mesh-crate",
        "STEP n=2 agent=modeling do=clone-grid",
        "STEP n=3 agent=modeling do=bind-steel",
        "STEP n=4 agent=xval do=gauntlet-assets",
    ], "modeling"),
    ("author an atomic omnigraph that rewrites cube height every tick", [
        "DEPLOY agent=stage",
        "DEPLOY agent=pyapi",
        "DEPLOY agent=omnigraph",
        "DEPLOY agent=xval",
        "STEP n=1 agent=stage do=place-cube",
        "STEP n=2 agent=omnigraph do=author-tick-graph",
        "STEP n=3 agent=pyapi do=run-and-verify-ticks",
        "STEP n=4 agent=xval do=gauntlet-graph",
    ], "omnigraph"),
    ("run the cross-skill gauntlet receipt check on the finished rover", [
        "DEPLOY agent=sense",
        "DEPLOY agent=xval",
        "STEP n=1 agent=sense do=read-rover-state",
        "STEP n=2 agent=xval do=gauntlet-receipts",
    ], "xval"),
]


def generate(out_dir: Path) -> dict:
    routing = json.loads((ROOT / "skills_routing.json").read_text(encoding="utf-8"))
    roster = dispatcher.describe_roster()
    stats = {"tasks": 0, "written": 0, "invalid": [], "misses": [],
             "agents": Counter(), "skills": Counter()}
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "traces_dispatch.jsonl", "w", encoding="utf-8") as f:
        for task, lines, skill in DISPATCH_TASKS:
            stats["tasks"] += 1
            plan_text = "\n".join(lines)
            try:
                ops = dispatcher.validate_block(plan_text)
            except dispatcher.DispatchError as e:
                stats["invalid"].append((task, "DSP", str(e)[:160]))
                continue
            for op in ops:
                if op["verb"] == "DEPLOY":
                    stats["agents"][op["args"]["agent"]] += 1
            skills = thinker.select_skills(task, routing)
            names = [s.get("skill") or s.get("name") for s in skills]
            if skill not in names:
                stats["misses"].append((task, "DSP", skill, names))
                continue
            for name in names:
                stats["skills"][name] += 1
            for snap_label, snapshot in SNAPSHOTS:
                record = {
                    "messages": [
                        {"role": "system",
                         "content": thinker.build_dispatch_prompt(roster, skills)},
                        {"role": "user",
                         "content": thinker.build_user_prompt(task, snapshot)},
                        {"role": "assistant", "content": plan_text},
                    ],
                    "meta": {
                        "task": task,
                        "drill": "DSP",
                        "backend": "drill",
                        "skills": names,
                        "validated": True,
                        "images": 0,
                        "snapshot": snap_label,
                        "actions": [],
                        "dispatch": lines,
                    },
                }
                schema_errs = trace_schema.validate_record(record)
                if schema_errs:
                    stats["invalid"].append(
                        (task, "DSP", f"schema: {schema_errs[0]}"[:160]))
                    break
                f.write(json.dumps(record) + "\n")
                stats["written"] += 1
    return stats


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build dispatcher SFT traces")
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
    print(f"agents deployed: {dict(stats['agents'])}")
    print(f"out: {args.out}")
    return 0 if not stats["invalid"] and not stats["misses"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
