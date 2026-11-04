"""Offline tests for the observer. Run: python tests/test_observer.py"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_PY = ROOT / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"arobs_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


observer = _load("observer")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def test_imports_outside_isaac():
    ok, reason = observer.backend_available()
    assert ok is False, "backend must be unavailable outside Isaac Sim"
    assert reason, "reason must explain why"


def test_describe_mentions_unavailable():
    assert "unavailable" in observer.describe(), observer.describe()


def test_capture_outside_isaac_fails_cleanly():
    called = []
    started, msg = observer.capture_viewport(
        on_done=lambda ok, m: called.append((ok, m)))
    assert started is False, msg
    assert "no capture backend" in msg, msg
    assert called == [], "on_done must not fire when capture never starts"


def test_next_capture_path_format():
    first = observer.next_capture_path()
    second = observer.next_capture_path(prefix="verify")
    assert first.suffix == ".png" and first.parent == observer.default_capture_dir()
    assert re.match(r"snapshot_\d{8}_\d{6}_\d{3}(\_\d+)?\.png$", first.name), first.name
    assert second.name.startswith("verify_"), second.name
    assert first != second, "paths must be unique"


def test_default_capture_dir_under_home():
    assert observer.default_capture_dir().parent == Path.home()
    assert observer.default_capture_dir().name == observer.CAPTURE_SUBDIR


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items() if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
