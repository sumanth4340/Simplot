"""Tests for the thin multi-agent supervisor. Run: python tests/test_supervisor.py

Real protocol/dispatcher/catalog/routing throughout; thinker is the real
mock planner for the happy path and a scripted stub (sleep + thread
tracking) for concurrency, blackboard, and failure tests.
"""
import importlib.util
import re
import sys
import threading
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arsv_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


thinker = _load("thinker", EXT_PY / "thinker.py")
protocol = _load("protocol", EXT_PY / "protocol.py")
handlers = _load("handlers", EXT_PY / "handlers.py")
dispatcher = _load("dispatcher", EXT_PY / "dispatcher.py")
supervisor = _load("supervisor", EXT_PY / "supervisor.py")
catalog = protocol.load_catalog(ROOT / "actions_compact.json")
routing = __import__("json").loads(
    (ROOT / "skills_routing.json").read_text(encoding="utf-8"))
signatures = [protocol.help_line(k, catalog[k])
              for k in handlers.HANDLED_ACTIONS if k in catalog]
passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _deps(tk):
    return types.SimpleNamespace(thinker=tk, protocol=protocol,
                                 dispatcher=dispatcher, catalog=catalog,
                                 routing=routing, signatures=signatures)


class _StubThinker:
    """Scripted planner: script maps agent -> actions_text."""

    def __init__(self, script, sleep=0.0):
        self.script = script
        self.sleep = sleep
        self.calls = []

    def plan(self, task, snapshot, sigs, skills, known_keys=None,
             config=None):
        if self.sleep:
            time.sleep(self.sleep)
        m = re.match(r"\[(\w+)/", task or "")
        agent = m.group(1) if m else "?"
        self.calls.append({"agent": agent, "task": task,
                           "snapshot": snapshot, "skills": skills,
                           "ident": threading.get_ident()})
        return types.SimpleNamespace(
            actions_text=self.script.get(agent, "sim.play\n"),
            notes=[], skills=[], backend="stub")

    def select_skills(self, task, routing):
        return thinker.select_skills(task, routing)


def test_single_agent_mock_ok():
    res = supervisor.run_block("DEPLOY agent=sense\n"
                               "STEP n=1 agent=sense do=read-stage\n",
                               "create a green cube", "sim: paused",
                               _deps(thinker))
    assert res["ok"] and res["error"] == "", res
    assert len(res["steps"]) == 1, res
    step = res["steps"][0]
    assert step["valid"] == step["total"] > 0, step
    assert step["backend"] == "mock", step
    assert res["verdict"]["ok"], res["verdict"]
    assert res["final_lines"], res
    for key, raw, lineno in protocol.parse_batch(res["final_text"]):
        protocol.validate(key, raw, catalog, lineno=lineno)


def test_parallel_fans_out_on_threads():
    stub = _StubThinker({}, sleep=0.1)
    res = supervisor.run_block(
        "DEPLOY agent=sense\nDEPLOY agent=stage\nDEPLOY agent=xval\n"
        "PARALLEL agents=sense+stage\n"
        "STEP n=1 agent=sense do=read-stage\n"
        "STEP n=2 agent=stage do=map-prims\n",
        "survey the stage", "sim: paused", _deps(stub))
    assert res["ok"], res
    assert [s["n"] for s in res["steps"]] == [1, 2], res
    assert res["groups"][0]["mode"] == "threads", res["groups"]
    idents = {c["ident"] for c in stub.calls}
    assert len(idents) == 2, stub.calls  # two worker threads, provably parallel
    assert threading.get_ident() not in idents, stub.calls
    assert res["verdict"]["ok"], res["verdict"]


def test_cowork_blackboard_shares_prior_lines():
    stub = _StubThinker({"sense": "create.objects.plane size=20\n"})
    res = supervisor.run_block(
        "DEPLOY agent=sense\nDEPLOY agent=stage\nDEPLOY agent=xval\n"
        "COWORK agents=sense+stage\n"
        "STEP n=1 agent=sense do=read-stage\n"
        "STEP n=2 agent=stage do=map-prims\n",
        "survey the stage", "sim: paused", _deps(stub))
    assert res["ok"], res
    assert res["groups"][0]["mode"] == "blackboard", res["groups"]
    by_agent = {c["agent"]: c for c in stub.calls}
    assert "PRIOR COWORK LINES" not in by_agent["sense"]["snapshot"]
    assert "PRIOR COWORK LINES" in by_agent["stage"]["snapshot"]
    assert "create.objects.plane size=20" in by_agent["stage"]["snapshot"]


def test_step_failure_stops_and_skips_rest():
    stub = _StubThinker({"stage": "create.objects.cuboid size=oops\n"})
    res = supervisor.run_block(
        "DEPLOY agent=sense\nDEPLOY agent=stage\nDEPLOY agent=xval\n"
        "STEP n=1 agent=sense do=read-stage\n"
        "STEP n=2 agent=stage do=map-prims\n"
        "STEP n=3 agent=xval do=cross-check\n",
        "survey the stage", "sim: paused", _deps(stub))
    assert res["ok"] is False and "step 2" in res["error"], res
    assert [s["n"] for s in res["steps"]] == [1, 2], res
    assert res["steps"][1]["ok"] is False, res["steps"][1]
    assert res["skipped"] == [3], res
    assert all("cuboid" not in ln for ln in res["final_lines"]), res
    assert res["verdict"]["ok"] is False, res["verdict"]


def test_needs_blocks_until_dependency_completes():
    stub = _StubThinker({})
    deps = _deps(stub)
    early = supervisor.run_block(
        "DEPLOY agent=stage needs=sense\nDEPLOY agent=sense\n"
        "DEPLOY agent=xval\n"
        "STEP n=1 agent=stage do=map-prims\n",
        "survey the stage", "sim: paused", deps)
    assert early["ok"] is False and "needs" in early["error"], early
    assert "sense" in early["error"], early
    assert early["steps"] == [], early
    ordered = supervisor.run_block(
        "DEPLOY agent=stage needs=sense\nDEPLOY agent=sense\n"
        "DEPLOY agent=xval\n"
        "STEP n=1 agent=sense do=read-stage\n"
        "STEP n=2 agent=stage do=map-prims\n",
        "survey the stage", "sim: paused", deps)
    assert ordered["ok"], ordered
    assert [s["n"] for s in ordered["steps"]] == [1, 2], ordered


def test_invalid_blocks_rejected_with_zero_steps():
    deps = _deps(thinker)
    bad = supervisor.run_block("STEP n=1 agent=sense do=read-stage\n",
                               "x", "sim: paused", deps)
    assert bad["ok"] is False and "undeployed" in bad["error"], bad
    assert bad["steps"] == [], bad
    noxval = supervisor.run_block("DEPLOY agent=sense\nDEPLOY agent=stage\n"
                                  "STEP n=1 agent=sense do=read-stage\n",
                                  "x", "sim: paused", deps)
    assert noxval["ok"] is False and "xval" in noxval["error"], noxval


def test_empty_plan_ok_and_done_ends_plan():
    deps = _deps(thinker)
    empty = supervisor.run_block("# nothing to do\nDONE\n", "x",
                                 "sim: paused", deps)
    assert empty["ok"] and empty["steps"] == [], empty
    assert empty["verdict"]["ok"], empty["verdict"]
    cut = supervisor.run_block(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\nDONE\n"
        "STEP n=2 agent=sense do=read-stage\n",
        "create a green cube", "sim: paused", deps)
    assert cut["ok"], cut
    assert [s["n"] for s in cut["steps"]] == [1], cut
    assert cut["skipped"] == [2], cut


def test_xval_verdict_counts_emitted_lines():
    stub = _StubThinker({"sense": "sim.play\n",
                         "stage": "sim.play\nsim.pause\n"})
    res = supervisor.run_block(
        "DEPLOY agent=sense\nDEPLOY agent=stage\nDEPLOY agent=xval\n"
        "STEP n=1 agent=sense do=read-stage\n"
        "STEP n=2 agent=stage do=map-prims\n",
        "survey the stage", "sim: paused", _deps(stub))
    assert res["ok"], res
    assert res["verdict"] == {"ok": True, "checked": 3, "valid": 3,
                              "notes": ["xval re-validated 3/3 "
                                        "emitted lines"]}, res["verdict"]


def test_group_without_member_steps_skips_cleanly():
    stub = _StubThinker({})
    res = supervisor.run_block(
        "DEPLOY agent=sense\nDEPLOY agent=xval\n"
        "PARALLEL agents=sense\n"
        "STEP n=1 agent=xval do=cross-check\n",
        "survey the stage", "sim: paused", _deps(stub))
    assert res["ok"], res
    assert res["groups"][0]["steps"] == [], res["groups"]
    assert [s["n"] for s in res["steps"]] == [1], res


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
