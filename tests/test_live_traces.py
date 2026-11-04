"""Tests for the live-trace converter. Run: python tests/test_live_traces.py"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arlt_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


build_live = _load("build_live_traces", ROOT / "build_live_traces.py")
trace_schema = _load("trace_schema", ROOT / "trace_schema.py")
passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _fixture(tmp):
    log = tmp / "traces.jsonl"
    snap = "sim: paused\n" + "prim\n" * 500  # forces truncation
    events = [
        {"event": "think", "ts": "t1", "task": "add a cone",
         "backend": "mock", "skills": [], "images": [],
         "snapshot": snap,
         "actions": "create.objects.cone radius=0.4 height=1 pos=0,0,2",
         "notes": ["mock planner (no LLM): matched cone"]},
        {"event": "run", "ts": "t2",
         "lines": ["create.objects.cone radius=0.4 height=1 pos=0,0,2"],
         "results": [{"key": "create.objects.cone", "ok": True, "msg": "ok"}]},
        {"event": "think", "ts": "t3", "task": "delete cubes",
         "backend": "mock", "skills": [], "images": [], "snapshot": snap,
         "actions": "create.objects.cuboid size=1 pos=0,0,2",
         "notes": ["mock planner (no LLM): matched cube"]},
        {"event": "run", "ts": "t4",
         "lines": ["create.objects.cuboid size=1 pos=0,0,2"],
         "results": [{"key": "create.objects.cuboid", "ok": True, "msg": "ok"}]},
        {"event": "run", "ts": "t5", "lines": ["sim.play"],
         "results": [{"key": "sim.play", "ok": True, "msg": "ok"}]},
        {"event": "run", "ts": "t6", "lines": ["sim.play"],
         "results": [{"key": "sim.play", "ok": False, "msg": "boom"}]},
        {"event": "bridge_run", "ts": "t7", "cmd": "cmd_test.txt",
         "lines": ["sim.play"],
         "results": [{"key": "sim.play", "ok": True, "msg": "ok"}]},
        {"event": "bridge_run", "ts": "t8", "cmd": "cmd_gone.txt",
         "lines": ["sim.play"],
         "results": [{"key": "sim.play", "ok": True, "msg": "ok"}]},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    bridge = tmp / "bridge"
    (bridge / "done").mkdir(parents=True)
    (bridge / "outbox").mkdir(parents=True)
    (bridge / "done" / "cmd_test.txt").write_text(
        "# park the rover\nsim.play\n", encoding="utf-8")
    (bridge / "outbox" / "cmd_test.result.json").write_text(
        json.dumps({"ok": True, "snapshot": "sim: paused"}), encoding="utf-8")
    return log, bridge


def test_converts_clean_runs_only():
    tmp = Path(tempfile.mkdtemp(prefix="ar_live_"))
    log, bridge = _fixture(tmp)
    stats = build_live.generate(tmp / "out", live_log=log, bridge_dir=bridge)
    assert stats["written"] == 2, stats
    assert stats["intent_mismatch"] == 1, stats
    assert stats["unpaired"] == 2, stats  # orphan run + missing cmd file
    assert stats["not_ok"] == 1, stats
    assert stats["schema_fail"] == 0, stats
    assert stats["truncated"] == 1, stats
    lines = (tmp / "out" / "traces_live.jsonl").read_text(
        encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        record = json.loads(line)
        assert trace_schema.validate_record(record) == []
        assert record["meta"]["backend"] == "live"
    tasks = sorted(json.loads(line)["meta"]["task"] for line in lines)
    assert tasks == ["add a cone", "park the rover"], tasks


def test_missing_log_writes_nothing():
    tmp = Path(tempfile.mkdtemp(prefix="ar_live_"))
    stats = build_live.generate(tmp / "out", live_log=tmp / "nope.jsonl",
                                bridge_dir=tmp / "bridge")
    assert stats["written"] == 0


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
