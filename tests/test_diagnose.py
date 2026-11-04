"""Tests for the failure black box. Run: python tests/test_diagnose.py

The black box packs NOVEL failures (ones no checklist names) into one
evidence bundle + one LLM task, so diagnosis takes a single model
call instead of a multi-leg flail. The model replies in action lines
only: a 1-3 line fix, or NO-FIX plus one probe line.
"""
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"ardg_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


diagnose = _load("diagnose", EXT_PY / "diagnose.py")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


BEFORE = "sim: paused\nprims: 3\ncube pos=0,0,1\n"
AFTER = "sim: paused\nprims: 4\ncube pos=0,0,1\nsphere pos=1,0,1\n"


def _failure(**kw):
    base = {"task": "add a sphere", "line": "create.objects.sphere r=9",
            "lineno": 2, "key": "create.objects.sphere",
            "msg": "boom: radius out of range", "stage": "exec",
            "shot_before": BEFORE, "shot_after": AFTER,
            "trace_tail": ("ok [sim.play] playing",)}
    base.update(kw)
    return diagnose.capture_failure(**base)


def test_capture_packs_evidence_and_delta():
    box = _failure()
    assert box["key"] == "create.objects.sphere", box
    assert box["stage"] == "exec", box
    assert box["stage_changed"] is True, box
    assert ("prims: 3", "prims: 4") in box["delta"]["changed"], box
    assert "sphere pos=1,0,1" in box["delta"]["added"], box
    assert box["trace_tail"] == ["ok [sim.play] playing"], box


def test_capture_marks_unchanged_stage():
    box = _failure(shot_after=BEFORE)
    assert box["stage_changed"] is False, box
    assert box["delta"] == {"added": [], "removed": [],
                            "changed": []}, box


def test_snapshot_delta_detects_all_kinds():
    delta = diagnose.snapshot_delta("a\nb\nc\nd\n", "a\nB\nd\ne\n")
    assert delta["removed"] == ["c"], delta
    assert delta["added"] == ["e"], delta
    assert delta["changed"] == [("b", "B")], delta


def test_snapshot_delta_caps_long_diffs():
    before = "".join(f"line {i}\n" for i in range(50))
    after = "".join(f"line X{i}\n" for i in range(50))
    delta = diagnose.snapshot_delta(before, after, cap=5)
    assert len(delta["changed"]) == 5, delta
    assert delta["changed_truncated"] == 45, delta


def test_diagnosis_task_carries_symptom_evidence_contract():
    task = diagnose.build_diagnosis_task(
        _failure(), signatures=["create.objects.sphere radius=.. pos=.."])
    assert "create.objects.sphere r=9" in task, task
    assert "boom: radius out of range" in task, task
    assert "stage_changed=yes" in task, task
    assert "create.objects.sphere radius=.. pos=.." in task, task
    assert "ONLY action lines" in task, task
    assert "NO-FIX" in task, task
    assert "never repeat the failed line unchanged" in task, task


def test_split_no_fix():
    no_fix, probe = diagnose.split_no_fix("NO-FIX\nsim.play\n")
    assert no_fix is True and probe.strip() == "sim.play", (no_fix, probe)
    no_fix, probe = diagnose.split_no_fix("no-fix\n")
    assert no_fix is True and probe == "", (no_fix, probe)
    no_fix, probe = diagnose.split_no_fix("create.objects.cuboid size=1\n")
    assert no_fix is False, (no_fix, probe)


def test_summarize_failure_one_liner():
    line = diagnose.summarize_failure(_failure())
    assert line.startswith("blackbox [exec]"), line
    assert "create.objects.sphere" in line, line
    assert "stage_changed=yes" in line, line


class _StubThinker:
    def __init__(self, text, backend="stub"):
        self.text = text
        self.backend = backend
        self.calls = []

    def plan(self, task, snapshot, sigs, skills, known_keys=None,
             config=None, images=None, loop=False, guided_regex=None):
        self.calls.append({"task": task, "snapshot": snapshot,
                           "skills": skills})
        return types.SimpleNamespace(actions_text=self.text, notes=[],
                                     skills=[], backend=self.backend)


def test_diagnose_returns_fix_in_one_call():
    deps = types.SimpleNamespace(
        thinker=_StubThinker("create.objects.sphere radius=0.4\n"),
        catalog={"create.objects.sphere": {}},
        signatures=["create.objects.sphere radius=.."])
    out = diagnose.diagnose(_failure(), deps)
    assert out["backend"] == "stub", out
    assert out["no_fix"] is False, out
    assert "radius=0.4" in out["fix_text"], out
    assert len(deps.thinker.calls) == 1, deps.thinker.calls
    assert "boom" in deps.thinker.calls[0]["task"], deps.thinker.calls
    assert AFTER in deps.thinker.calls[0]["snapshot"], deps.thinker.calls


def test_diagnose_returns_probe_on_no_fix():
    deps = types.SimpleNamespace(
        thinker=_StubThinker("NO-FIX\nsim.play\n"),
        catalog={"sim.play": {}},
        signatures=["sim.play"])
    out = diagnose.diagnose(_failure(), deps)
    assert out["no_fix"] is True, out
    assert out["probe_text"].strip() == "sim.play", out
    assert out["fix_text"] == "", out


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items()
                            if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
