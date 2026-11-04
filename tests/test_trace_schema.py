"""Tests for the trace record schema. Run: python tests/test_trace_schema.py"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arts_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


trace_schema = _load("trace_schema", ROOT / "trace_schema.py")
build_traces = _load("build_traces", ROOT / "build_traces.py")
build_drills = _load("build_drill_traces", ROOT / "build_drill_traces.py")
passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _good_record():
    return {
        "messages": [
            {"role": "system", "content": "rules"},
            {"role": "user", "content": "TASK: x"},
            {"role": "assistant", "content": "sim.play\n"},
        ],
        "meta": {"task": "x", "backend": "mock", "validated": True,
                 "images": 0, "actions": ["sim.play"], "skills": ["pyapi"]},
    }


def test_valid_record_passes():
    assert trace_schema.validate_record(_good_record()) == []


def test_rejects_bad_shapes():
    cases = []
    bad_roles = _good_record()
    bad_roles["messages"] = bad_roles["messages"][::-1]
    cases.append(bad_roles)
    empty_assistant = _good_record()
    empty_assistant["messages"][2]["content"] = "  "
    cases.append(empty_assistant)
    not_validated = _good_record()
    not_validated["meta"]["validated"] = False
    cases.append(not_validated)
    bad_backend = _good_record()
    bad_backend["meta"]["backend"] = "template"
    cases.append(bad_backend)
    bad_images = _good_record()
    bad_images["meta"]["images"] = -1
    cases.append(bad_images)
    bad_key = _good_record()
    bad_key["meta"]["actions"] = ["make me a cube"]
    cases.append(bad_key)
    no_actions = _good_record()
    no_actions["meta"]["actions"] = []
    cases.append(no_actions)
    drill_nosnap = _good_record()
    drill_nosnap["meta"]["backend"] = "drill"
    cases.append(drill_nosnap)
    cases.append({"messages": [], "meta": {}})
    cases.append("not a record")
    for i, rec in enumerate(cases):
        assert trace_schema.validate_record(rec), f"case {i} accepted"


def test_builders_emit_valid_records():
    tmp = Path(tempfile.mkdtemp(prefix="ar_schema_"))
    stats = build_traces.generate(tmp / "mock")
    assert stats["tasks"] > 0 and not stats["skipped"], stats["skipped"]
    stats = build_drills.generate(tmp / "drills")
    assert stats["written"] > 0 and not stats["invalid"], stats["invalid"]
    assert not stats["misses"], stats["misses"]
    n = 0
    for name in ("mock/traces_mock.jsonl", "drills/traces_drills.jsonl"):
        for line in (tmp / name).read_text(encoding="utf-8").splitlines():
            errs = trace_schema.validate_record(json.loads(line))
            assert not errs, errs
            n += 1
    assert n > 100, n


def test_dispatch_record_passes():
    rec = _good_record()
    rec["meta"]["backend"] = "drill"
    rec["meta"]["drill"] = "DSP"
    rec["meta"]["snapshot"] = "canned-empty"
    rec["meta"]["actions"] = []
    rec["meta"]["dispatch"] = ["DEPLOY agent=sense",
                               "STEP n=1 agent=sense do=read-stage"]
    assert trace_schema.validate_record(rec) == []
    bad = json.loads(json.dumps(rec))
    bad["meta"]["actions"] = ["sim.play"]
    assert trace_schema.validate_record(bad), "dispatch + actions accepted"


def test_schema_json_is_valid_json():
    schema = json.loads((ROOT / "traces_schema.json").read_text(encoding="utf-8"))
    assert schema["title"] == "Action Reasoner SFT trace record"
    assert schema["properties"]["meta"]["required"] == [
        "task", "backend", "validated", "images", "actions", "skills"]


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
