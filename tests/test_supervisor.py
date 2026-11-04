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
             config=None, guided_regex=None):
        if self.sleep:
            time.sleep(self.sleep)
        m = re.match(r"\[(\w+)/", task or "")
        agent = m.group(1) if m else "?"
        self.calls.append({"agent": agent, "task": task,
                           "snapshot": snapshot, "skills": skills,
                           "guided_regex": guided_regex,
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


def test_is_dispatch_text_detects_verbs_only():
    assert supervisor.is_dispatch_text(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n")
    assert supervisor.is_dispatch_text("  PARALLEL agents=sense+stage\n")
    assert supervisor.is_dispatch_text("# plan\nCOWORK agents=sense+stage\n")
    assert not supervisor.is_dispatch_text(
        "create.objects.plane size=20\nsim.play\n")
    assert not supervisor.is_dispatch_text("sim.step n=5\n")
    assert not supervisor.is_dispatch_text("# just a comment\nDONE\n")
    assert not supervisor.is_dispatch_text("")
    assert not supervisor.is_dispatch_text("deploy agent=sense\n")


def test_task_from_comments():
    assert supervisor.task_from_comments(
        "# survey the arena\nDEPLOY agent=sense\n") == "survey the arena"
    assert supervisor.task_from_comments(
        "#\n# second\nSTEP n=1 agent=sense do=x\n") == "second"
    assert supervisor.task_from_comments("STEP n=1 agent=sense do=x\n") == ""
    assert supervisor.task_from_comments("") == ""


def test_format_log_and_step_results():
    stub = _StubThinker({"stage": "create.objects.cuboid size=oops\n"})
    deps = _deps(stub)
    ok_res = supervisor.run_block(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n",
        "survey the stage", "sim: paused", deps)
    log = supervisor.format_log(ok_res)
    assert any("step 1 sense/read-stage" in ln for ln in log), log
    assert log[-1].startswith("verdict: ok"), log
    rows = supervisor.step_results(ok_res)
    assert rows == [{"key": "step1:sense", "line": 0, "ok": True,
                     "msg": "read-stage: valid 1/1"}], rows
    bad_res = supervisor.run_block(
        "DEPLOY agent=sense\nDEPLOY agent=stage\nDEPLOY agent=xval\n"
        "STEP n=1 agent=sense do=read-stage\n"
        "STEP n=2 agent=stage do=map-prims\n",
        "survey the stage", "sim: paused", deps)
    bad_log = supervisor.format_log(bad_res)
    assert bad_log[0].startswith("ERROR: step 2"), bad_log
    assert any(ln.startswith("verdict: FAIL") for ln in bad_log), bad_log
    bad_rows = supervisor.step_results(bad_res)
    assert [r["ok"] for r in bad_rows] == [True, False], bad_rows
    assert "cuboid" in bad_rows[1]["msg"] or "size" in bad_rows[1]["msg"], \
        bad_rows


def test_failure_and_combine_outcome_shapes():
    stub = _StubThinker({"stage": "create.objects.cuboid size=oops\n"})
    deps = _deps(stub)
    bad_text = ("DEPLOY agent=sense\nDEPLOY agent=stage\nDEPLOY agent=xval\n"
                "STEP n=1 agent=sense do=read-stage\n"
                "STEP n=2 agent=stage do=map-prims\n")
    bad_res = supervisor.run_block(bad_text, "survey", "sim: paused", deps)
    failed = supervisor.failure_outcome(bad_text, bad_res)
    assert failed["ok"] is False and failed["events"] == [], failed
    assert failed["lines"] == [ln for ln in bad_text.splitlines()
                               if ln.strip()], failed
    assert len(failed["results"]) == 2, failed
    ok_res = supervisor.run_block(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n",
        "survey", "sim: paused", deps)
    assert ok_res["ok"], ok_res
    fake_exec = {"ok": True, "lines": ["sim.play"],
                 "results": [{"key": "sim.play", "line": 1, "ok": True,
                              "msg": "playing"}],
                 "log": ["ok [sim.play] playing"], "events": []}
    combined = supervisor.combine_outcome(ok_res, fake_exec)
    assert combined["ok"] is True, combined
    assert combined["lines"] == ["sim.play"], combined
    assert [r["key"] for r in combined["results"]] == [
        "step1:sense", "sim.play"], combined
    assert combined["log"][0].startswith("step 1"), combined
    assert combined["log"][-1] == "ok [sim.play] playing", combined
    assert combined["events"] == [], combined


def test_guided_regex_forwarded_to_planner():
    stub = _StubThinker({})
    supervisor.run_block(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n",
        "survey the stage", "sim: paused", _deps(stub),
        guided_regex="X+")
    assert [c["guided_regex"] for c in stub.calls] == ["X+"], stub.calls
    stub2 = _StubThinker({})
    supervisor.run_block(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n",
        "survey the stage", "sim: paused", _deps(stub2))
    assert [c["guided_regex"] for c in stub2.calls] == [None], stub2.calls


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


def test_format_agent_lines_shows_emissions():
    stub = _StubThinker({"sense": "create.objects.cuboid size=1\nsim.play\n"})
    res = supervisor.run_block(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n",
        "survey the stage", "sim: paused", _deps(stub))
    assert res["ok"], res
    shown = supervisor.format_agent_lines(res)
    assert shown[0] == (
        "agent sense step 1 (read-stage) emitted 2 line(s):"), shown
    assert shown[1:] == [
        "  create.objects.cuboid size=1", "  sim.play"], shown


def test_format_agent_lines_caps_and_skips_blanks():
    res = {"steps": [{"n": 1, "agent": "rosnav", "do": "drive",
                      "lines": "\n".join(
                          [f"sim.set.drive_{i} v={i}" for i in range(12)]
                          + ["", "  "])}]}
    shown = supervisor.format_agent_lines(res, max_per_step=8)
    assert shown[0] == (
        "agent rosnav step 1 (drive) emitted 12 line(s):"), shown
    assert len(shown) == 10, shown  # header + 8 lines + overflow note
    assert shown[-1] == "  ... +4 more", shown


def test_format_agent_lines_empty_when_no_steps():
    assert supervisor.format_agent_lines({"steps": []}) == []
    assert supervisor.format_agent_lines({}) == []


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
