"""Run the eval set against a backend and print a scored report.

Backends: mock (offline planner; dispatch unsupported) or endpoint
(live Glimmer via thinker.plan / plan_dispatch). --from scores saved
generations instead: a jsonl file of {"id": <task id>, "output": str}.

Usage:
  python action-reasoner/eval/run_eval.py --backend mock [--out report.json]
  python action-reasoner/eval/run_eval.py --backend endpoint [--out report.json]
  python action-reasoner/eval/run_eval.py --from gens.jsonl [--out report.json]
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"areval_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


EXT_PY = (ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim"
          / "action" / "reasoner" / "executor")
thinker = _load("thinker", EXT_PY / "thinker.py")
protocol = _load("protocol", EXT_PY / "protocol.py")
handlers = _load("handlers", EXT_PY / "handlers.py")
dispatcher = _load("dispatcher", EXT_PY / "dispatcher.py")
score = _load("score", EVAL / "score.py")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Score a backend on the eval set")
    parser.add_argument("--backend", choices=("mock", "endpoint"),
                        default="mock")
    parser.add_argument("--from", dest="from_file", default=None,
                        help="score saved generations (jsonl id/output)")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    catalog = protocol.load_catalog(ROOT / "actions_compact.json")
    routing = json.loads((ROOT / "skills_routing.json").read_text(encoding="utf-8"))
    signatures = [protocol.help_line(k, catalog[k])
                  for k in handlers.HANDLED_ACTIONS if k in catalog]
    roster = dispatcher.describe_roster()

    if args.from_file:
        saved = {}
        for line in Path(args.from_file).read_text(
                encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                saved[row["id"]] = row.get("output")
        backend_name = f"file:{args.from_file}"

        def generate(task):
            return saved.get(task["id"])
    elif args.backend == "mock":
        backend_name = "mock"

        def generate(task):
            if task["kind"] == "dispatch":
                return None
            return thinker.mock_plan(task["task"], task["snapshot"])[0]
    else:
        backend_name = "endpoint"
        cfg = thinker.load_config()
        if not cfg.configured:
            print("endpoint backend needs GLIMMER_ENDPOINT + GLIMMER_API_KEY")
            return 2

        def generate(task):
            skills = thinker.select_skills(task["task"], routing)
            if task["kind"] == "dispatch":
                plan = thinker.plan_dispatch(
                    task["task"], task["snapshot"], roster, skills,
                    config=cfg, guided_regex=thinker.load_guided_regex(),
                    validate=dispatcher.validate_block)
            else:
                plan = thinker.plan(
                    task["task"], task["snapshot"], signatures, skills,
                    known_keys=set(catalog), config=cfg,
                    guided_regex=thinker.load_guided_regex())
            return plan.actions_text

    report = score.run_suite(generate, catalog, routing)
    report["backend"] = backend_name
    summary = report["summary"]
    print(f"backend: {backend_name}")
    print(f"action valid-line rate: {summary['action_valid_rate']:.3f} "
          f"({summary['action_lines']} lines)")
    print(f"dispatch accept rate:   {summary['dispatch_accept_rate']:.3f} "
          f"({summary['dispatch_tasks']} tasks)")
    print(f"skill hit rate:         {summary['skill_hit_rate']:.3f}")
    print(f"unsupported:            {summary['unsupported']}")
    for entry in report["tasks"]:
        if entry.get("supported") is False:
            print(f"  {entry['id']}: unsupported")
        elif entry["kind"] == "action":
            print(f"  {entry['id']}: valid {entry['valid']}/{entry['total']} "
                  f"skill_hit={entry['skill_hit']} prose={entry['prose']}")
        else:
            print(f"  {entry['id']}: accepted={entry['accepted']}" +
                  (f" ({entry['error']})" if not entry["accepted"] else
                   f" deploys={entry['deploys']} steps={entry['steps']}"))
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=1), encoding="utf-8")
        print(f"report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
