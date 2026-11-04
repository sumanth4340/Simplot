"""Offline scoring for the eval set (no model, no network).

score_action_output / score_dispatch_output grade one model reply;
run_suite grades a generate(task)->str callable over eval_tasks.TASKS.
run_eval.py wires generate() to the mock planner or a live endpoint.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = (ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim"
          / "action" / "reasoner" / "executor")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arev_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


thinker = _load("thinker", EXT_PY / "thinker.py")
protocol = _load("protocol", EXT_PY / "protocol.py")
dispatcher = _load("dispatcher", EXT_PY / "dispatcher.py")
eval_tasks = _load("eval_tasks", ROOT / "eval" / "eval_tasks.py")


def score_action_output(content, catalog, expect_skill, retrieved):
    """Grade an action reply: line validity + skill retrieval hit."""
    kept, drop_notes = thinker.extract_actions(content, set(catalog))
    batch = protocol.parse_batch(kept)
    valid, errors = 0, []
    for key, raw, lineno in batch:
        try:
            protocol.validate(key, raw, catalog, lineno=lineno)
            valid += 1
        except (protocol.ValidationError, protocol.ProtocolError) as e:
            errors.append(f"line {lineno}: {e}"[:120])
    total = len(batch)
    return {
        "total": total,
        "valid": valid,
        "valid_rate": (valid / total) if total else 0.0,
        "skill_hit": expect_skill in (retrieved or []),
        "prose": bool(drop_notes),
        "errors": errors[:3],
    }


def score_dispatch_output(content):
    """Grade a dispatch reply: grammar acceptance + shape counts."""
    try:
        ops = dispatcher.validate_block(content)
    except dispatcher.DispatchError as e:
        return {"accepted": False, "error": str(e)[:160]}
    verbs = [o["verb"] for o in ops]
    return {
        "accepted": True,
        "deploys": verbs.count("DEPLOY"),
        "steps": verbs.count("STEP"),
        "agents": sorted({o["args"]["agent"] for o in ops
                          if o["verb"] == "DEPLOY"}),
    }


def run_suite(generate, catalog, routing):
    """Score generate() over all eval tasks. generate returns str/None."""
    per_task, action_ok, action_n = [], 0, 0
    dispatch_ok, dispatch_n, unsupported = 0, 0, 0
    hits, hit_n = 0, 0
    for task in eval_tasks.TASKS:
        retrieved = [s.get("skill") or s.get("name")
                     for s in thinker.select_skills(task["task"], routing)]
        hit_n += 1
        hits += task["expect_skill"] in retrieved
        try:
            content = generate(task)
        except Exception as exc:  # noqa: BLE001 - a backend blowup scores 0
            content = None
            err = f"backend error: {exc}"[:120]
        else:
            err = ""
        if content is None:
            unsupported += 1
            per_task.append({"id": task["id"], "kind": task["kind"],
                             "supported": False, "error": err})
            continue
        if task["kind"] == "action":
            scored = score_action_output(content, catalog,
                                         task["expect_skill"], retrieved)
            action_ok += scored["valid"]
            action_n += scored["total"]
        else:
            scored = score_dispatch_output(content)
            dispatch_n += 1
            dispatch_ok += scored["accepted"]
        scored.update({"id": task["id"], "kind": task["kind"],
                       "supported": True})
        per_task.append(scored)
    return {
        "tasks": per_task,
        "summary": {
            "action_valid_rate": (action_ok / action_n) if action_n else 0.0,
            "action_lines": action_n,
            "dispatch_accept_rate": (dispatch_ok / dispatch_n) if dispatch_n else 0.0,
            "dispatch_tasks": dispatch_n,
            "skill_hit_rate": (hits / hit_n) if hit_n else 0.0,
            "unsupported": unsupported,
        },
    }
