"""Build fine-tuning data for the Action Reasoner.

Curates the compact catalog (drops the 26 import-failed actions the
validator rejects anyway) and generates validated task -> action traces
in the same chat format the Thinker uses at inference, so fine-tuning
aligns with deployment.

Outputs (default: action-reasoner/finetune/):
  actions_finetune.json - the 169 trainable compact actions
  traces_mock.jsonl     - one {"messages": [...], "meta": {...}} per task

Mock traces teach output FORMAT (action-only lines over runnable actions),
not reasoning; reasoning traces come from live Glimmer runs, which the GUI
appends to ~/action-reasoner-traces/traces.jsonl (see FINETUNE_README.md).

Usage:
  python action-reasoner/build_traces.py [--out DIR]
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
    spec = importlib.util.spec_from_file_location(f"arft_{name}", EXT_PY / f"{name}.py")
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

# Realistic empty stage (matches Executor.snapshot with no /World).
SNAPSHOT_EMPTY = "sim: paused\nstage has no /World"

# Battery uses only mock-vocabulary keywords so every trace is a correct
# task -> plan mapping (no default-scene fallbacks in the data).
TASKS = [
    "create a red cube",
    "make a ground plane and a blue sphere",
    "build a small scene with a box and a ball",
    "create a cube and a sphere side by side",
    "set up an empty warehouse floor",
    "drop a heavy box on the ground",
    "make the cube heavy",
    "make a moon rover with two wheels",
    "build a moon robot",
    "build a chassis with wheels",
    "build a robot car and drive it",
    "make the ground and roll a ball",
    "create a ball and roll the sim",
    "run the simulation",
    "play",
    "add a lidar sensor on top",
    "scan the room with lidar",
    "create a sensor rover",
    "make a rover with lidar and drive",
]


def curate(catalog: dict) -> tuple:
    """Split catalog into (trainable, excluded) compact actions."""
    trainable = {k: v for k, v in catalog.items() if v.get("available", True)}
    excluded = {k: v for k, v in catalog.items() if not v.get("available", True)}
    return trainable, excluded


def generate(out_dir: Path) -> dict:
    catalog = protocol.load_catalog(ROOT / "actions_compact.json")
    routing = json.loads((ROOT / "skills_routing.json").read_text(encoding="utf-8"))
    trainable, excluded = curate(catalog)
    signatures = [protocol.help_line(k, catalog[k])
                  for k in handlers.HANDLED_ACTIONS if k in catalog]

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "actions_finetune.json").write_text(
        json.dumps(trainable, indent=1), encoding="utf-8")

    stats = {"tasks": 0, "skipped": [], "groups": Counter(),
             "excluded_groups": Counter(v.get("group") for v in excluded.values())}
    with open(out_dir / "traces_mock.jsonl", "w", encoding="utf-8") as f:
        for task in TASKS:
            actions_text, _ = thinker.mock_plan(task, SNAPSHOT_EMPTY)
            batch = protocol.parse_batch(actions_text)
            valid = True
            for key, raw, lineno in batch:
                try:
                    protocol.validate(key, raw, catalog, lineno=lineno)
                except (protocol.ValidationError, protocol.ProtocolError):
                    valid = False
                    break
                stats["groups"][catalog[key].get("group")] += 1
            if not valid or not batch:
                stats["skipped"].append(task)
                continue
            skills = thinker.select_skills(task, routing)
            record = {
                "messages": [
                    {"role": "system",
                     "content": thinker.build_system_prompt(signatures, skills)},
                    {"role": "user",
                     "content": thinker.build_user_prompt(task, SNAPSHOT_EMPTY)},
                    {"role": "assistant", "content": actions_text},
                ],
                "meta": {
                    "task": task,
                    "backend": "mock",
                    "skills": [s.get("skill") or s.get("name") for s in skills],
                    "validated": True,
                    "images": 0,
                    "snapshot": "canned-empty",
                    "actions": [k for k, _, _ in batch],
                },
            }
            schema_errs = trace_schema.validate_record(record)
            if schema_errs:
                stats["skipped"].append(f"{task} [schema: {schema_errs[0]}]")
                continue
            f.write(json.dumps(record) + "\n")
            stats["tasks"] += 1
    stats["trainable"] = len(trainable)
    stats["excluded"] = sorted(excluded)
    return stats


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build Action Reasoner fine-tune data")
    parser.add_argument("--out", default=str(ROOT / "finetune"),
                        help="output directory")
    args = parser.parse_args(argv)
    stats = generate(Path(args.out))
    print(f"trainable actions: {stats['trainable']} "
          f"(excluded {len(stats['excluded'])}: {dict(stats['excluded_groups'])}")
    for key in stats["excluded"]:
        print(f"  excluded: {key}")
    print(f"traces: {stats['tasks']} written, {len(stats['skipped'])} skipped")
    for task in stats["skipped"]:
        print(f"  skipped: {task}")
    print(f"action groups in traces: {dict(stats['groups'])}")
    print(f"out: {args.out}")
    return 0 if not stats["skipped"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
