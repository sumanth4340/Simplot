"""Tests for the Modal adapter grader (offline half). Run: python tests/test_grade.py

grade_adapter.build_messages / load_reasoner are pure over the local
checkout; the GPU worker runs the same functions over /grade.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"argr_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


grade = _load("grade_adapter", ROOT / "modal" / "grade_adapter.py")
eval_tasks = _load("eval_tasks", ROOT / "eval" / "eval_tasks.py")
passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def test_load_reasoner_matches_run_eval_wiring():
    mods = grade.load_reasoner(ROOT)
    (thinker, protocol, handlers, dispatcher, score, catalog,
     routing, signatures, roster) = mods
    assert len(catalog) > 100 and isinstance(routing, list) and routing
    assert signatures and all(isinstance(s, str) for s in signatures)
    assert roster and len(eval_tasks.TASKS) == 12


def test_build_messages_matches_endpoint_path():
    (thinker, _p, _h, _d, _s, _c,
     routing, signatures, roster) = grade.load_reasoner(ROOT)
    for task in eval_tasks.TASKS:
        msgs = grade.build_messages(task, thinker, signatures, roster,
                                    routing)
        assert [m["role"] for m in msgs] == ["system", "user"], task["id"]
        assert "OUTPUT RULES (strict):" in msgs[0]["content"], task["id"]
        assert task["task"] in msgs[1]["content"], task["id"]
        if task["kind"] == "dispatch":
            assert "DEPLOY agent=" in msgs[0]["content"], task["id"]
        else:
            assert "action lines" in msgs[0]["content"], task["id"]


def test_build_messages_uses_same_builders_as_thinker_plan():
    # run_eval's endpoint path calls these exact builders; grade must not
    # drift to a private prompt format.
    (thinker, _p, _h, _d, _s, _c,
     routing, signatures, roster) = grade.load_reasoner(ROOT)
    task = eval_tasks.TASKS[0]
    skills = thinker.select_skills(task["task"], routing)
    expect_sys = thinker.build_system_prompt(list(signatures), list(skills))
    expect_usr, _, _ = thinker.build_user_content(task["task"],
                                                 task["snapshot"], ())
    msgs = grade.build_messages(task, thinker, signatures, roster, routing)
    assert msgs[0]["content"] == expect_sys
    assert msgs[1]["content"] == expect_usr


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
