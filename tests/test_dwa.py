"""Tests for the DWA planner. Run: python tests/test_dwa.py"""
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

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"PASS {name}")


def test_open_space_drives_straight_to_goal():
    cfg = dwa.DWAConfig()
    v, w, traj = dwa.dwa_control([0.0, 0.0, 0.0, 0.0, 0.0],
                                 (3.0, 0.0), [], cfg)
    assert v > 0, (v, w)
    assert abs(w) < 0.11, (v, w)
    assert traj[-1][0] > 0, traj[-1]


def test_obstacle_ahead_turns_away():
    cfg = dwa.DWAConfig()
    v, w, traj = dwa.dwa_control([0.0, 0.0, 0.0, 0.4, 0.0],
                                 (3.0, 0.0), [(1.0, 0.6)], cfg)
    assert v > 0.2, (v, w)  # keeps moving, doesn't just stop
    assert abs(w) > 0.05 or v < 0.39, (v, w)  # steers or slows down
    for x, y, *_ in traj:
        assert math.hypot(x - 1.0, y - 0.6) >= cfg.robot_radius - 1e-6, (x, y)


def test_trajectory_never_hits_obstacles():
    cfg = dwa.DWAConfig()
    obs = [(1.0, 0.2), (1.0, -0.2), (2.0, 0.5)]
    v, w, traj = dwa.dwa_control([0.0, 0.0, 0.0, 0.0, 0.0],
                                 (3.0, 0.0), obs, cfg)
    assert v > 0, (v, w)
    for x, y, *_ in traj:
        for ox, oy in obs:
            assert math.hypot(x - ox, y - oy) >= cfg.robot_radius - 1e-6


def test_goal_reached_stops():
    cfg = dwa.DWAConfig()
    v, w, traj = dwa.dwa_control([2.9, 0.1, 0.0, 0.3, 0.0],
                                 (3.0, 0.0), [], cfg)
    assert (v, w) == (0.0, 0.0), (v, w)
    assert len(traj) == 1


def test_wheel_targets_match_live_calibration():
    cfg = dwa.DWAConfig()
    left, right = dwa.wheel_targets(0.31, 0.0, cfg)
    assert abs(left - 59.2) < 0.5, (left, right)  # +60 drives nose-fwd
    assert abs(right - 59.2) < 0.5, (left, right)
    left, right = dwa.wheel_targets(0.0, 0.5, cfg)  # CCW pivot
    assert left < 0 and right > 0, (left, right)  # (-81,+81) yaws +8.2 live


def test_escape_reverses_out_of_bubble():
    cfg = dwa.DWAConfig.live()  # radius 1.2
    state = [-0.79, -0.89, math.radians(179), 0.0, 0.0]
    ring = [(-2.0 + 0.4 * math.cos(a), 0.0 + 0.4 * math.sin(a))
            for a in [i * math.pi / 6 for i in range(12)]]
    v, w, traj = dwa.dwa_control(state, (-2.2, 2.4), ring, cfg)
    assert v < -0.01, (v, w)  # backs out, never (0,0) deadlock
    start_clear = min(math.hypot(ox - state[0], oy - state[1])
                      for ox, oy in ring)
    ex, ey = traj[-1][0], traj[-1][1]
    end_clear = min(math.hypot(ox - ex, oy - ey) for ox, oy in ring)
    assert end_clear > start_clear, (start_clear, end_clear)


def test_pivot_beats_reverse_when_turn_is_safe():
    cfg = dwa.DWAConfig.live()  # radius 1.2
    cfg.bounds = (-1.3, 1.3, -1.3, 1.3)  # tight room: movers die, pivot fits
    state = [0.0, 0.0, 0.0, 0.0, 0.0]
    scan = dwa.synth_scan((0.0, 0.0, 0.0), [], cfg.bounds)
    obs = dwa.scan_to_points(scan, (0.0, 0.0, 0.0))
    v, w, traj = dwa.dwa_control(state, (-1.2, 0.0), obs, cfg)
    assert v == 0.0 and abs(w) > 0.05, (v, w)  # pivots, never reverses
    for x, y, *_ in traj[1:]:
        for ox, oy in obs:
            assert math.hypot(x - ox, y - oy) >= cfg.robot_radius - 1e-6


def test_saved_start_never_reverses():
    cfg = dwa.DWAConfig.live()  # radius 1.2, true wall bounds
    state = [1.807, 0.0, math.radians(-3.4), 0.0, 0.0]
    circles = [(-2.0, 0.0, 0.4), (1.0, 2.2, 0.4), (1.0, -2.2, 0.4)]
    scan = dwa.synth_scan((state[0], state[1], state[2]),
                          circles, cfg.bounds)
    obs = dwa.scan_to_points(scan, (state[0], state[1], state[2]))
    v, w, traj = dwa.dwa_control(state, (-2.2, 2.4), obs, cfg)
    assert v >= 0.0, (v, w)  # forward or pivot, never reverse
    for x, y, *_ in traj[1:]:
        for ox, oy in obs:
            assert math.hypot(x - ox, y - oy) >= cfg.robot_radius - 1e-6


def test_mission_latches_forward_never_back():
    legs = [dwa.MissionLeg((-0.5, 1.1), 1.2),
            dwa.MissionLeg((-2.2, 2.4), 1.2, tol=1.5),
            dwa.MissionLeg((-2.2, 2.4), 0.7)]
    g, r, t, n = dwa.mission_step([1.8, 0.0], legs, 0)
    assert (g, r, n) == ((-0.5, 1.1), 1.2, 0)
    g, r, t, n = dwa.mission_step([-0.5, 1.1], legs, 0)
    assert (g, r, n) == ((-2.2, 2.4), 1.2, 1)
    g, r, t, n = dwa.mission_step([-1.5, 2.0], legs, 1)
    assert (g, r, n) == ((-2.2, 2.4), 0.7, 2)  # precision inside 1.5 m
    g, r, t, n = dwa.mission_step([1.8, 0.0], legs, 2)
    assert n == 2  # latched: never falls back


def test_scan_roundtrip_on_known_geometry():
    pose = (0.0, 0.0, 0.0)
    circles = [(3.0, 0.0, 0.4)]
    bounds = (-4.0, 4.0, -4.0, 4.0)
    scan = dwa.synth_scan(pose, circles, bounds, n_rays=360)
    ranges = dict(scan)
    assert abs(ranges[0.0] - 2.6) < 0.05, ranges[0.0]  # 3.0 - 0.4
    pts = dwa.scan_to_points(scan, pose)
    assert len(pts) == 360
    near = [p for p in pts if abs(p[1]) < 0.05 and p[0] > 0]
    assert near, "no returns on the cone"
    assert abs(min(p[0] for p in near) - 2.6) < 0.05


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in dict(globals()).items()
                            if k.startswith("test_")]):
        check(name, fn)
    print(f"\n{len(passed)} tests passed")
