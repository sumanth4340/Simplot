"""Offline tests: file bridge queue. Run: python tests/test_bridge.py"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"arexec_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


bridge = _load("bridge")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _ok_batch(text):
    lines = [ln.strip() for ln in text.splitlines()
             if ln.strip() and not ln.strip().startswith("#")]
    return {
        "ok": True,
        "lines": lines,
        "results": [{"key": ln.split()[0], "line": i + 1, "ok": True, "msg": "ran"}
                    for i, ln in enumerate(lines)],
        "log": [f"ok [{ln.split()[0]}] ran" for ln in lines],
    }


def test_layout():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "bridge"
        dirs = bridge.ensure_layout(base)
        assert dirs["base"] == base
        assert dirs["inbox"].is_dir() and dirs["outbox"].is_dir()
        assert dirs["done"].is_dir()


def test_empty_inbox():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        out = bridge.process_inbox(base, _ok_batch, snapshot_fn=lambda: "sim: paused")
        assert out == [], out
        status = bridge.read_status(base)
        assert status["bridge"] == "on" and status["pending"] == 0, status
        assert status["last_cmd"] is None


def test_happy_path():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        dirs = bridge.ensure_layout(base)
        (dirs["inbox"] / "cmd_001_rover.txt").write_text("sim.play\n", encoding="utf-8")
        seen = {}

        def run(text):
            seen["text"] = text
            return _ok_batch(text)

        out = bridge.process_inbox(base, run, snapshot_fn=lambda: "sim: paused")
        assert len(out) == 1, out
        res = out[0]
        assert res["cmd"] == "cmd_001_rover.txt" and res["ok"] is True
        assert res["snapshot"] == "sim: paused" and res["shot"] is None
        assert res["lines"] == ["sim.play"] and seen["text"] == "sim.play\n"
        result_file = Path(res["result_file"])
        assert result_file.name == "cmd_001_rover.result.json"
        disk = json.loads(result_file.read_text(encoding="utf-8"))
        assert disk["cmd"] == "cmd_001_rover.txt" and disk["ok"] is True
        assert disk["log"] == ["ok [sim.play] ran"], disk
        assert not (dirs["inbox"] / "cmd_001_rover.txt").exists()
        assert (dirs["done"] / "cmd_001_rover.txt").is_file()
        assert list(dirs["outbox"].glob(".tmp_*")) == []
        status = bridge.read_status(base)
        assert status["last_cmd"] == "cmd_001_rover.txt" and status["last_ok"] is True


def test_failed_batch_still_moves():
    def fail_batch(text):
        return {"ok": False, "lines": ["bogus.action"],
                "results": [{"key": "bogus.action", "line": 1, "ok": False,
                             "msg": "unknown action"}],
                "log": ["ERROR: unknown action 'bogus.action'"]}

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        dirs = bridge.ensure_layout(base)
        (dirs["inbox"] / "cmd_bad.txt").write_text("bogus.action\n", encoding="utf-8")
        out = bridge.process_inbox(base, fail_batch)
        assert len(out) == 1 and out[0]["ok"] is False
        assert out[0]["snapshot"] == ""  # no snapshot_fn -> empty string
        assert (dirs["done"] / "cmd_bad.txt").is_file()
        assert bridge.read_status(base)["last_ok"] is False


def test_run_batch_exception_is_a_result():
    def boom(text):
        raise RuntimeError("kablam")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        dirs = bridge.ensure_layout(base)
        (dirs["inbox"] / "cmd_boom.txt").write_text("sim.play\n", encoding="utf-8")
        out = bridge.process_inbox(base, boom)
        assert len(out) == 1 and out[0]["ok"] is False
        assert "kablam" in out[0]["results"][0]["msg"]
        assert (dirs["done"] / "cmd_boom.txt").is_file()


def test_sorted_and_filtered():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        dirs = bridge.ensure_layout(base)
        (dirs["inbox"] / "b_second.txt").write_text("sim.play\n", encoding="utf-8")
        (dirs["inbox"] / "a_first.txt").write_text("sim.pause\n", encoding="utf-8")
        (dirs["inbox"] / "notes.md").write_text("not a batch\n", encoding="utf-8")
        (dirs["inbox"] / ".hidden.txt").write_text("sim.play\n", encoding="utf-8")
        out = bridge.process_inbox(base, _ok_batch)
        assert [r["cmd"] for r in out] == ["a_first.txt", "b_second.txt"]
        assert (dirs["inbox"] / "notes.md").is_file()
        assert (dirs["inbox"] / ".hidden.txt").is_file()
        assert bridge.read_status(base)["pending"] == 0


def test_done_collision_suffix():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        dirs = bridge.ensure_layout(base)
        (dirs["done"] / "cmd.txt").write_text("old\n", encoding="utf-8")
        (dirs["inbox"] / "cmd.txt").write_text("sim.play\n", encoding="utf-8")
        bridge.process_inbox(base, _ok_batch)
        assert (dirs["done"] / "cmd.txt").read_text(encoding="utf-8") == "old\n"
        assert (dirs["done"] / "cmd_2.txt").read_text(encoding="utf-8") == "sim.play\n"


def test_update_result_shot():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        dirs = bridge.ensure_layout(base)
        (dirs["inbox"] / "cmd.txt").write_text("sim.play\n", encoding="utf-8")
        out = bridge.process_inbox(base, _ok_batch)
        result_file = out[0]["result_file"]
        assert bridge.update_result_shot(result_file, "C:/shots/cmd.png", True) is True
        disk = json.loads(Path(result_file).read_text(encoding="utf-8"))
        assert disk["shot"] == "C:/shots/cmd.png" and disk["shot_ok"] is True
        assert bridge.update_result_shot(result_file, "C:/shots/cmd.png", False) is True
        disk = json.loads(Path(result_file).read_text(encoding="utf-8"))
        assert disk["shot"] is None and disk["shot_ok"] is False
        assert bridge.update_result_shot(str(Path(tmp) / "missing.json"), "x", True) is False


def test_status_survives_corrupt_file():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        bridge.ensure_layout(base)
        (base / "status.json").write_text("{nope", encoding="utf-8")
        assert bridge.read_status(base) == {}
        out = bridge.process_inbox(base, _ok_batch)
        assert out == []  # must not crash; status rewritten clean
        assert bridge.read_status(base)["pending"] == 0


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
