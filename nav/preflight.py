"""Nav math preflight: catch drive-config errors before the wheels turn.

Stdlib only, like nav/dwa.py. Each check pins a failure mode proven
live on 2026-11-04 (see the dwa.py comments it cites): a body-radius
footprint hooking cones, phantom walls from wrong bounds, crawl from
v=0 replans, goal-in-bubble crawl, and uniform/blind scans from
mis-decoded lidar.

Caller-side tool: the live driver runs preflight() before a mission
leg and refuses FAIL verdicts. dwa_control itself is untouched — the
0.7 unit default intentionally FAILS the footprint check because
unit-test geometry is not live geometry (DWAConfig.live() passes).
"""
from __future__ import annotations

import math

__all__ = ["min_footprint", "check_footprint", "check_bounds",
           "check_goal_clearance", "check_start_clearance", "check_seed",
           "check_scan", "preflight", "verdict", "format_report"]


def _out(check: str, verdict: str, msg: str) -> dict:
    return {"check": check, "verdict": verdict, "msg": msg}


def min_footprint(cfg) -> float:
    """Smallest honest footprint: wheel span, not body size."""
    return cfg.track / 2.0 + cfg.wheel_r


def check_footprint(cfg) -> dict:
    """Footprint must span the wheels (track/2 + wheel_r)."""
    need = min_footprint(cfg)
    radius = cfg.robot_radius
    if radius <= 0:
        return _out("footprint", "fail",
                    f"robot_radius {radius} is not positive; DWA "
                    "vetoes every rollout")
    if radius < need:
        return _out("footprint", "fail",
                    f"robot_radius {radius} < wheel-span {need:.2f} "
                    f"(track/2 {cfg.track / 2.0} + wheel_r "
                    f"{cfg.wheel_r}); a body-radius footprint hooks "
                    "obstacles live — use DWAConfig.live()")
    return _out("footprint", "ok",
                f"robot_radius {radius} spans the wheels ({need:.2f})")


def _in_bounds(x: float, y: float, cfg) -> bool:
    xmin, xmax, ymin, ymax = cfg.bounds
    return xmin <= x <= xmax and ymin <= y <= ymax


def check_bounds(cfg, start, goal) -> dict:
    """Start and goal must sit inside the planner bounds."""
    if not _in_bounds(start[0], start[1], cfg):
        return _out("bounds", "fail",
                    f"start {tuple(start[:2])} is outside bounds "
                    f"{tuple(cfg.bounds)}; every rollout dies at the wall")
    if not _in_bounds(goal[0], goal[1], cfg):
        return _out("bounds", "fail",
                    f"goal {tuple(goal[:2])} is outside bounds "
                    f"{tuple(cfg.bounds)}; DWA can never arrive")
    xmin, xmax, ymin, ymax = cfg.bounds
    wall = min(goal[0] - xmin, xmax - goal[0],
               goal[1] - ymin, ymax - goal[1])
    if wall < cfg.robot_radius:
        return _out("bounds", "warn",
                    f"goal sits {wall:.2f} m from a wall, inside the "
                    f"{cfg.robot_radius} bubble; expect a crawl finish "
                    "- use a precision radius near the goal")
    return _out("bounds", "ok",
                f"start and goal inside bounds {tuple(cfg.bounds)}")


def check_goal_clearance(goal, obstacles, cfg) -> dict:
    """Warn when the goal sits inside an obstacle bubble."""
    obs = list(obstacles or [])
    if not obs:
        return _out("goal-clearance", "ok", "no obstacles near the goal")
    gap = min(math.hypot(ox - goal[0], oy - goal[1]) for ox, oy in obs)
    if gap < cfg.robot_radius:
        return _out("goal-clearance", "warn",
                    f"goal is {gap:.2f} m from an obstacle, inside the "
                    f"{cfg.robot_radius} bubble; DWA crawls there - "
                    "finish with a precision radius")
    return _out("goal-clearance", "ok",
                f"goal stands {gap:.2f} m clear of obstacles")


def check_start_clearance(state, obstacles, cfg) -> dict:
    """Warn when the start sits inside an obstacle bubble."""
    obs = list(obstacles or [])
    if not obs:
        return _out("start-clearance", "ok", "no obstacles at the start")
    gap = min(math.hypot(ox - state[0], oy - state[1]) for ox, oy in obs)
    if gap < cfg.robot_radius:
        return _out("start-clearance", "warn",
                    f"start is {gap:.2f} m from an obstacle, inside the "
                    f"{cfg.robot_radius} bubble; the first leg opens "
                    "with escape/pivot, not cruise")
    return _out("start-clearance", "ok",
                f"start stands {gap:.2f} m clear of obstacles")


def check_seed(state, goal, cfg) -> dict:
    """Warn when a leg replans from ~v=0 far from the goal."""
    goal_dist = math.hypot(goal[0] - state[0], goal[1] - state[1])
    v0 = state[3]
    far = goal_dist > 4.0 * cfg.goal_tol
    if cfg.cruise_seed <= 0 and v0 < 0.1 and far:
        return _out("seed", "warn",
                    "no cruise seed and replanning from v=0 "
                    f"{goal_dist:.1f} m out; pause-per-leg collapses "
                    "the window to a crawl — seed cruise or run "
                    "longer continuous legs")
    if v0 < cfg.cruise_seed and far:
        return _out("seed", "warn",
                    f"leg starts at v={v0:.2f} {goal_dist:.1f} m out; "
                    "the window seeds from cruise "
                    f"({cfg.cruise_seed}), not zero")
    return _out("seed", "ok",
                f"window opens at v={max(v0, cfg.cruise_seed):.2f}")


def check_scan(scan, max_range: float) -> dict:
    """Sanity-check a 2D scan before it becomes obstacle points."""
    readings = list(scan or [])
    if not readings:
        return _out("scan", "fail", "empty scan: no rays, no obstacles, "
                    "no drive")
    ranges = [r for _, r in readings]
    if any(isinstance(r, float) and (math.isnan(r) or math.isinf(r))
           for r in ranges):
        return _out("scan", "fail",
                    "scan carries NaN/inf ranges; fix the source "
                    "before planning")
    if all(r == max_range for r in ranges):
        return _out("scan", "warn",
                    f"scan is blind: all {len(ranges)} rays at max "
                    f"range {max_range}; empty room or dead returns")
    if len(set(ranges)) == 1:
        return _out("scan", "fail",
                    f"phantom ring: all {len(ranges)} ranges read "
                    f"{ranges[0]} — a stuck or mis-decoded lidar "
                    "(verify the GMO az/el/range mapping, not xyz)")
    if len(ranges) < 8:
        return _out("scan", "warn",
                    f"sparse scan: only {len(ranges)} rays; obstacle "
                    "points will be coarse")
    return _out("scan", "ok", f"{len(ranges)} sane ranges")


def preflight(state, goal, obstacles, cfg, scan=None,
              max_range: float = 8.0) -> list:
    """Full math check for one mission leg, worst verdict wins."""
    checks = [
        check_footprint(cfg),
        check_bounds(cfg, (state[0], state[1]), goal),
        check_goal_clearance(goal, obstacles, cfg),
        check_start_clearance(state, obstacles, cfg),
        check_seed(state, goal, cfg),
    ]
    if scan is not None:
        checks.append(check_scan(scan, max_range))
    return checks


def verdict(checks) -> str:
    """Worst verdict across checks: fail > warn > ok."""
    seen = {c["verdict"] for c in checks}
    if "fail" in seen:
        return "fail"
    if "warn" in seen:
        return "warn"
    return "ok"


def format_report(checks) -> list:
    """Checks -> log lines, verdict first."""
    lines = [f"PREFLIGHT verdict: {verdict(checks).upper()}"]
    for c in checks:
        lines.append(f"{c['verdict'].upper()} [{c['check']}] {c['msg']}")
    return lines
