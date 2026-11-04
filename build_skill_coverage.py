"""Skill<->action coverage map: link drill packs to catalog actions.

Reads finetune trace meta (drill tag, skills, actions) and writes
skills_action_coverage.json: which skill packs exercise which compact
actions, and which runnable actions have zero drill coverage.

This is the skills/v3 merge layer as an *index*, not a second catalog:
catalog_v3.json stays read-only, actions_compact.json stays derived.
Run: python action-reasoner/build_skill_coverage.py
"""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXT_PY = (ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim"
          / "action" / "reasoner" / "executor")
TRACE_FILES = ("traces_drills.jsonl", "traces_mock.jsonl",
               "traces_dispatch.jsonl", "traces_live.jsonl")


def _load_handlers():
    spec = importlib.util.spec_from_file_location(
        "ar_cov_handlers", EXT_PY / "handlers.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _read_traces(finetune_dir):
    """Yield (source, meta) for every trace record."""
    for name in TRACE_FILES:
        path = finetune_dir / name
        if not path.is_file():
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield name, json.loads(line).get("meta", {})


def generate(out_path=None, finetune_dir=None):
    """Build the coverage map; write it unless out_path is None."""
    finetune_dir = Path(finetune_dir or ROOT / "finetune")
    compact = json.loads(
        (ROOT / "actions_compact.json").read_text(encoding="utf-8"))
    handled = set(_load_handlers().HANDLED_ACTIONS)

    by_drill_actions = {}
    by_drill_skills = {}
    drill_traces = Counter()
    drill_dispatch = Counter()
    by_action_drills = {key: set() for key in compact}
    by_action_skills = {key: set() for key in compact}
    action_traces = Counter()
    sources = Counter()
    unknown_keys = Counter()

    for source, meta in _read_traces(finetune_dir):
        sources[source] += 1
        drill = meta.get("drill") or meta.get("backend") or "unknown"
        skills = [s for s in (meta.get("skills") or []) if s]
        actions = [a for a in (meta.get("actions") or []) if a]
        drill_traces[drill] += 1
        if meta.get("dispatch"):
            drill_dispatch[drill] += 1
        by_drill_actions.setdefault(drill, set()).update(actions)
        by_drill_skills.setdefault(drill, set()).update(skills)
        for key in actions:
            if key not in compact:
                unknown_keys[key] += 1
                continue
            by_action_drills[key].add(drill)
            by_action_skills[key].update(skills)
            action_traces[key] += 1

    by_drill = {
        drill: {
            "traces": drill_traces[drill],
            "skills": sorted(by_drill_skills.get(drill, ())),
            "actions": sorted(by_drill_actions.get(drill, ())),
            "dispatch": drill_dispatch.get(drill, 0),
        }
        for drill in sorted(drill_traces)
    }
    by_action = {
        key: {
            "traces": action_traces.get(key, 0),
            "drills": sorted(by_action_drills[key]),
            "skills": sorted(by_action_skills[key]),
            "handled": key in handled,
            "available": bool(spec.get("available")),
        }
        for key, spec in compact.items()
    }
    handled_undrilled = sorted(
        k for k in handled if k in compact and not action_traces.get(k))
    available_undrilled = sorted(
        k for k, spec in compact.items()
        if spec.get("available") and not action_traces.get(k))
    coverage = {
        "meta": {
            "sources": dict(sources),
            "traces": sum(sources.values()),
            "compact_actions": len(compact),
            "handled_actions": len([k for k in handled if k in compact]),
            "unknown_keys": dict(unknown_keys),
        },
        "by_drill": by_drill,
        "by_action": by_action,
        "gaps": {
            "handled_undrilled": handled_undrilled,
            "available_undrilled": available_undrilled,
        },
    }
    stats = {
        "traces": sum(sources.values()),
        "drills": len(by_drill),
        "covered": sum(1 for k in compact if action_traces.get(k)),
        "handled_undrilled": handled_undrilled,
        "unknown_keys": dict(unknown_keys),
    }
    if out_path is not None:
        Path(out_path).write_text(json.dumps(coverage, indent=1),
                                  encoding="utf-8")
    return coverage, stats


def main():
    coverage, stats = generate(ROOT / "skills_action_coverage.json")
    print(f"traces: {stats['traces']} drills: {stats['drills']} "
          f"covered: {stats['covered']}/{coverage['meta']['compact_actions']}")
    print(f"handled without drills: {len(stats['handled_undrilled'])}")
    for key in stats["handled_undrilled"]:
        print(f"  - {key}")
    if stats["unknown_keys"]:
        print(f"trace keys outside compact: {stats['unknown_keys']}")


if __name__ == "__main__":
    main()
