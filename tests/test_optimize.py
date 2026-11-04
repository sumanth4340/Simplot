"""Tests for the optimizer gate. Run: python tests/test_optimize.py

The gate fuses the two experts into one execute/refuse call: the
agents' emission (supervisor result) plus the math verdict
(nav/preflight over the mission context). FAIL vetoes the batch and
attaches the fix; WARN annotates and executes. Fail-closed: any
doubt vetoes.
"""
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arop_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


optimize = _load("optimize", EXT_PY / "optimize.py")
preflight = _load("preflight", ROOT / "nav" / "preflight.py")
dwa = _load("dwa", ROOT / "nav" / "dwa.py")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _deps():
    return types.SimpleNamespace(preflight=preflight)


def _res(ok=True, error="", final="sim.play\n", verdict_ok=True):
    steps = [{"n": 1, "agent": "sense", "do": "read-stage",
              "lines": final, "valid": 1, "total": 1, "ok": ok,
              "backend": "stub", "notes": [], "errors": []}]
    return {"ok": ok, "error": error, "steps": steps if final else [],
            "skipped": [], "groups": [],
            "verdict": {"ok": verdict_ok, "checked": 1, "valid": 1,
                        "notes": []},
            "final_text": final, "final_lines": [final.strip()] if final else [],
            "backends": ["stub"]}


def _ctx(**kw):
    base = {"state": [0.0, 0.0, 0.0, 0.4, 0.0], "goal": (1.0, 1.0),
            "obstacles": [], "cfg": dwa.DWAConfig.live(), "scan": None,
            "max_range": 8.0}
    base.update(kw)
    return base


def test_clean_mission_executes():
    out = optimize.optimize(_res(), _ctx(), _deps())
    assert out["execute"] is True, out
    assert out["report"][0] == "OPTIMIZER verdict: EXECUTE", out
    assert out["annotations"] == [], out
    assert len(out["math"]) == 5, out  # footprint..seed, no scan


def test_math_fail_vetoes_with_fix_attached():
    out = optimize.optimize(_res(), _ctx(cfg=dwa.DWAConfig()), _deps())
    assert out["execute"] is False, out
    assert out["report"][0] == "OPTIMIZER verdict: VETO", out
    assert "1.15" in out["reason"], out  # the footprint fix, attached
    assert any(ln.startswith("FAIL [footprint]")
               for ln in out["report"]), out


def test_math_warn_annotates_and_executes():
    out = optimize.optimize(_res(), _ctx(goal=(3.0, 0.0)), _deps())
    assert out["execute"] is True, out
    assert len(out["annotations"]) == 1, out
    assert "bubble" in out["annotations"][0], out


def test_agent_failure_vetoes_without_math():
    out = optimize.optimize(
        _res(ok=False, error="step 1 failed; run stopped",
             final="", verdict_ok=False), _ctx(), _deps())
    assert out["execute"] is False, out
    assert out["math"] == [], out
    assert "step 1 failed" in out["reason"], out


def test_empty_emission_vetoes():
    out = optimize.optimize(_res(final=""), _ctx(), _deps())
    assert out["execute"] is False, out
    assert "no executable lines" in out["reason"], out


def test_no_context_executes_on_agents_alone():
    out = optimize.optimize(_res(), None, _deps())
    assert out["execute"] is True, out
    assert out["math"] == [], out
    assert any("math skipped" in ln for ln in out["report"]), out


def test_malformed_context_fails_closed():
    out = optimize.optimize(_res(), _ctx(state=[0.0]), _deps())
    assert out["execute"] is False, out
    assert out["report"][0] == "OPTIMIZER verdict: VETO", out


class _StubThinker:
    def __init__(self, script):
        self.script = script

    def plan(self, task, snapshot, sigs, skills, known_keys=None,
             config=None, guided_regex=None):
        import re
        m = re.match(r"\[(\w+)/", task or "")
        agent = m.group(1) if m else "?"
        return types.SimpleNamespace(
            actions_text=self.script.get(agent, "sim.play\n"),
            notes=[], skills=[], backend="stub")

    def select_skills(self, task, routing):
        return thinker.select_skills(task, routing)


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


def test_integration_real_emission_gated_by_math():
    deps = types.SimpleNamespace(thinker=_StubThinker({}), protocol=protocol,
                                 dispatcher=dispatcher, catalog=catalog,
                                 routing=routing, signatures=signatures)
    res = supervisor.run_block(
        "DEPLOY agent=sense\nSTEP n=1 agent=sense do=read-stage\n",
        "survey the stage", "sim: paused", deps)
    assert res["ok"], res
    go = optimize.optimize(res, _ctx(), _deps())
    assert go["execute"] is True, go
    stop = optimize.optimize(res, _ctx(cfg=dwa.DWAConfig()), _deps())
    assert stop["execute"] is False, stop
    assert "1.15" in stop["reason"], stop


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items()
                            if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
