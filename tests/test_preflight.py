"""Tests for the nav math preflight. Run: python tests/test_preflight.py

Every check pins a failure mode proven live on 2026-11-04 (see
nav/dwa.py comments): body-radius footprint hooking cones, phantom
walls from wrong bounds, crawl from v=0 replans, goal-in-bubble
crawl, and uniform/blind scans from mis-decoded lidar.
"""
import importlib.util
import math
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
preflight = _load("preflight", ROOT / "nav" / "preflight.py")

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def _by_name(checks, name):
    hits = [c for c in checks if c["check"] == name]
    assert len(hits) == 1, (name, checks)
    return hits[0]


def test_footprint_live_ok_body_radius_fails():
    live = preflight.check_footprint(dwa.DWAConfig.live())
    assert live["verdict"] == "ok", live
    body = preflight.check_footprint(dwa.DWAConfig())  # 0.7 unit default
    assert body["verdict"] == "fail", body
    assert "1.15" in body["msg"], body  # track/2 + wheel_r


def test_footprint_rejects_nonpositive_radius():
    cfg = dwa.DWAConfig.live()
    cfg.robot_radius = 0.0
    assert preflight.check_footprint(cfg)["verdict"] == "fail"


def test_bounds_outside_fails_inside_ok():
    cfg = dwa.DWAConfig.live()
    ok = preflight.check_bounds(cfg, (0.0, 0.0), (1.0, 1.0))
    assert ok["verdict"] == "ok", ok
    bad_goal = preflight.check_bounds(cfg, (0.0, 0.0), (10.0, 10.0))
    assert bad_goal["verdict"] == "fail", bad_goal
    assert "goal" in bad_goal["msg"], bad_goal
    bad_start = preflight.check_bounds(cfg, (10.0, 10.0), (1.0, 1.0))
    assert bad_start["verdict"] == "fail", bad_start
    assert "start" in bad_start["msg"], bad_start


def test_goal_in_wall_bubble_warns():
    cfg = dwa.DWAConfig.live()  # xmax wall face at 3.85
    near = preflight.check_bounds(cfg, (0.0, 0.0), (3.0, 0.0))
    assert near["verdict"] == "warn", near
    assert "bubble" in near["msg"], near


def test_goal_in_obstacle_bubble_warns():
    cfg = dwa.DWAConfig.live()
    hit = preflight.check_goal_clearance((1.0, 1.0), [(1.0, 1.0)], cfg)
    assert hit["verdict"] == "warn", hit
    clear = preflight.check_goal_clearance((1.0, 1.0), [(3.0, 3.0)], cfg)
    assert clear["verdict"] == "ok", clear
    assert preflight.check_goal_clearance((1.0, 1.0), [], cfg)["verdict"] == "ok"


def test_start_in_obstacle_bubble_warns():
    cfg = dwa.DWAConfig.live()
    state = [1.0, 1.0, 0.0, 0.0, 0.0]
    hit = preflight.check_start_clearance(state, [(1.0, 1.0)], cfg)
    assert hit["verdict"] == "warn", hit
    assert "escape" in hit["msg"], hit
    clear = preflight.check_start_clearance(state, [(3.0, 3.0)], cfg)
    assert clear["verdict"] == "ok", clear


def test_seed_warns_from_zero_far_from_goal():
    cfg = dwa.DWAConfig.live()
    state = [0.0, 0.0, 0.0, 0.0, 0.0]
    far = preflight.check_seed(state, (3.0, 0.0), cfg)
    assert far["verdict"] == "warn", far
    near = preflight.check_seed(state, (0.3, 0.0), cfg)
    assert near["verdict"] == "ok", near
    cruising = preflight.check_seed([0.0, 0.0, 0.0, 0.4, 0.0],
                                    (3.0, 0.0), cfg)
    assert cruising["verdict"] == "ok", cruising


def test_seed_warns_without_cruise_seed():
    cfg = dwa.DWAConfig.live()
    cfg.cruise_seed = 0.0
    got = preflight.check_seed([0.0, 0.0, 0.0, 0.0, 0.0],
                               (3.0, 0.0), cfg)
    assert got["verdict"] == "warn", got


def test_scan_phantom_ring_fails():
    scan = [(i * 0.1, 2.6) for i in range(72)]  # uniform: decode suspect
    got = preflight.check_scan(scan, 8.0)
    assert got["verdict"] == "fail", got
    assert "GMO" in got["msg"] or "phantom" in got["msg"], got


def test_scan_blind_warns_not_fails():
    scan = [(i * 0.1, 8.0) for i in range(72)]  # all max: blind room
    got = preflight.check_scan(scan, 8.0)
    assert got["verdict"] == "warn", got


def test_scan_rejects_empty_nan_and_sparse():
    assert preflight.check_scan([], 8.0)["verdict"] == "fail"
    nan_scan = [(0.0, 1.0), (0.1, float("nan"))]
    assert preflight.check_scan(nan_scan, 8.0)["verdict"] == "fail"
    inf_scan = [(0.0, 1.0), (0.1, float("inf"))]
    assert preflight.check_scan(inf_scan, 8.0)["verdict"] == "fail"
    sparse = [(0.0, 1.0), (0.5, 2.0)]
    assert preflight.check_scan(sparse, 8.0)["verdict"] == "warn"


def test_preflight_worst_verdict_wins():
    cfg = dwa.DWAConfig.live()
    state = [0.0, 0.0, 0.0, 0.4, 0.0]
    checks = preflight.preflight(state, (1.0, 1.0), [], cfg)
    assert preflight.verdict(checks) == "ok", checks
    assert {c["check"] for c in checks} == {
        "footprint", "bounds", "goal-clearance", "start-clearance",
        "seed"}, checks
    bad = preflight.preflight([0.0, 0.0, 0.0, 0.0, 0.0],
                              (10.0, 10.0), [], dwa.DWAConfig())
    assert preflight.verdict(bad) == "fail", bad
    assert _by_name(bad, "footprint")["verdict"] == "fail"
    assert _by_name(bad, "bounds")["verdict"] == "fail"


def test_preflight_includes_scan_when_given():
    cfg = dwa.DWAConfig.live()
    scan = [(i * 0.1, 2.6) for i in range(72)]
    checks = preflight.preflight([0.0, 0.0, 0.0, 0.4, 0.0],
                                 (1.0, 1.0), [], cfg, scan=scan)
    assert _by_name(checks, "scan")["verdict"] == "fail"
    assert preflight.verdict(checks) == "fail"


def test_format_report_leads_with_verdict():
    cfg = dwa.DWAConfig.live()
    checks = preflight.preflight([0.0, 0.0, 0.0, 0.4, 0.0],
                                 (1.0, 1.0), [], cfg)
    lines = preflight.format_report(checks)
    assert lines[0] == "PREFLIGHT verdict: OK", lines
    bad = preflight.preflight([0.0, 0.0, 0.0, 0.0, 0.0],
                              (10.0, 10.0), [], dwa.DWAConfig())
    lines = preflight.format_report(bad)
    assert lines[0] == "PREFLIGHT verdict: FAIL", lines
    assert any(ln.startswith("FAIL [footprint]") for ln in lines), lines
    assert any(ln.startswith("FAIL [bounds]") for ln in lines), lines


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items()
                            if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
