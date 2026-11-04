"""Tests for the proof-replay driver. Run: python tests/test_drive_mission.py

Covers the offline parts only (proof parse, line build, preflight
gate): firing legs needs a live bridge + sim, so run_leg/main stay
behind --dry-run when unverified.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"arnv_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


dwa = _load("dwa", ROOT / "nav" / "dwa.py")
driver = _load("drive_mission", ROOT / "nav" / "drive_mission.py")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def test_parse_proof_reads_all_steps():
    text = (ROOT / "nav" / "demo_proof.txt").read_text(encoding="utf-8")
    steps = driver.parse_proof_steps(text)
    # 41 drive commands; step 41 is the arrival record (no wheels)
    assert len(steps) == 41, len(steps)
    assert steps[0][:4] == (0.15, 0.0, 29, 29), steps[0]
    assert steps[-1][4:] == (2, 0.7), steps[-1]  # precision final leg


def test_parse_proof_rejects_garbage():
    for bad in ("", "GOAL REACHED someday\n", "step x: nonsense\n"):
        try:
            driver.parse_proof_steps(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"parsed garbage: {bad!r}")


def test_build_step_lines_exact():
    assert driver.build_step_lines(29, -12, "jl", "jr") == [
        "robot.set.joint_drive target=jl target_velocity=29",
        "robot.set.joint_drive target=jr target_velocity=-12",
    ]


def test_gate_mission_live_goes_body_stops():
    go, report = driver.gate_mission(driver.START_DEFAULT,
                                     driver.GOAL_DEFAULT,
                                     dwa.DWAConfig.live())
    assert go is True, report
    # the mission goal sits 0.65 m off the west wall: WARN, not FAIL
    assert report[0] == "PREFLIGHT verdict: WARN", report
    assert any("bubble" in ln for ln in report), report
    stop, report = driver.gate_mission(driver.START_DEFAULT,
                                       driver.GOAL_DEFAULT,
                                       dwa.DWAConfig())
    assert stop is False, report
    assert any(ln.startswith("FAIL [footprint]")
               for ln in report), report


def test_gate_mission_goal_outside_bounds_stops():
    go, report = driver.gate_mission(driver.START_DEFAULT, (99.0, 99.0),
                                     dwa.DWAConfig.live())
    assert go is False, report


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items()
                            if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
