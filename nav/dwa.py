"""Dynamic Window Approach planner for the think_cube rover.

Stdlib only: no numpy, no sim imports, so this module unit-tests with a
plain python. Takes robot pose + goal + obstacle points (from lidar
scans via scan_to_points, or synth_scan until a riding scan exists) and
returns (v, w); wheel_targets() converts to robot.set.joint_drive
deg/s using the live-calibrated sign map (verified on-stage
2026-11-04: symmetric negative drives nose-forward, L+/R- yaws
clockwise).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

RAD2DEG = 180.0 / math.pi

# Live footprint: track/2 + wheel_r = 0.85 + 0.3 = 1.15, rounded up.
# Radius 0.7 hooked cones live (2026-11-04); the live loop must use
# DWAConfig.live(). The 0.7 unit default stays: unit-test geometry
# pins small-radius invariants (starts sit 1.02-1.17 m from test
# obstacles). clearance() skips traj[0], so a start inside the bubble
# no longer vetoes candidates that drive out of it.
LIVE_ROBOT_RADIUS = 1.2


@dataclass
class DWAConfig:
    max_speed: float = 0.6      # m/s
    min_speed: float = 0.0      # forward only; pivots turn in place
    max_yawrate: float = 0.8    # rad/s
    max_accel: float = 1.0      # m/s^2
    max_dyawrate: float = 3.0   # rad/s^2
    v_res: float = 0.05
    yaw_res: float = 0.1
    dt: float = 0.1
    predict_time: float = 2.0
    robot_radius: float = 0.7  # unit default; live uses .live() -> 1.2
    cruise_seed: float = 0.25  # plan-from-cruise floor for window v0
    goal_tol: float = 0.5
    w_heading: float = 1.0
    w_clearance: float = 2.0
    w_velocity: float = 0.5
    # Inner wall faces, measured live 2026-11-04 from the wall prims
    # (centers x=-3.0/4.0, y=+-3.5, all 0.3 thick). The old bounds sat
    # 0.7 m inside the real walls and planned around phantom walls.
    bounds: tuple = (-2.85, 3.85, -3.35, 3.35)  # xmin,xmax,ymin,ymax
    wheel_r: float = 0.3
    track: float = 1.7

    @classmethod
    def live(cls) -> "DWAConfig":
        """Live-driving config: wheel-span footprint (1.2) + cruise."""
        return cls(robot_radius=LIVE_ROBOT_RADIUS)


def _wrap(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def motion(state, v: float, w: float, dt: float) -> list:
    """Differential-drive step. state = [x, y, theta, v, w]."""
    x, y, theta, _, _ = state
    return [x + v * math.cos(theta) * dt,
            y + v * math.sin(theta) * dt,
            _wrap(theta + w * dt), v, w]


def dynamic_window(state, cfg: DWAConfig) -> tuple:
    """Achievable (v, w) ranges this step: limits clipped by accel."""
    _, _, _, v0, w0 = state
    return (max(cfg.min_speed, v0 - cfg.max_accel * cfg.dt),
            min(cfg.max_speed, v0 + cfg.max_accel * cfg.dt),
            max(-cfg.max_yawrate, w0 - cfg.max_dyawrate * cfg.dt),
            min(cfg.max_yawrate, w0 + cfg.max_dyawrate * cfg.dt))


def predict(state, v: float, w: float, cfg: DWAConfig) -> list:
    """Roll out a (v, w) candidate; returns the trajectory states."""
    traj = [list(state)]
    t = 0.0
    while t < cfg.predict_time:
        traj.append(motion(traj[-1], v, w, cfg.dt))
        t += cfg.dt
    return traj


def _in_bounds(x: float, y: float, cfg: DWAConfig) -> bool:
    xmin, xmax, ymin, ymax = cfg.bounds
    return xmin <= x <= xmax and ymin <= y <= ymax


def clearance(traj, obstacles) -> float:
    """Min distance from trajectory to obstacle points (inf if none).

    Skips traj[0] (current pose): where you are is sunk cost — scoring
    it deadlocks DWA whenever the start sits inside the bubble (proven
    live 2026-11-04). Motion states traj[1:] still veto on violation.
    """
    best = float("inf")
    for x, y, *_ in traj[1:]:
        for ox, oy in obstacles:
            dist = math.hypot(ox - x, oy - y)
            if dist < best:
                best = dist
    return best


def _escape(state, pool, obstacles, cfg):
    """Deadlock recovery: no rollout stays fully clear (typical: the
    start sits inside the bubble). First drive OUT along an in-bounds
    rollout ending strictly clearer than the start; else back UP with
    slow reverse rollouts under the same rule (reverse is live-proven
    on this car); else hold for a caller pivot."""
    obs = list(obstacles)
    if not pool or not obs:
        return 0.0, 0.0, [list(state)]
    start_clear = min(math.hypot(ox - state[0], oy - state[1])
                      for ox, oy in obs)
    esc = []
    for v, w, traj, heading, _ in pool:
        if v <= 0.01:
            continue
        ex, ey = traj[-1][0], traj[-1][1]
        end = min(math.hypot(ox - ex, oy - ey) for ox, oy in obs)
        if end > start_clear:
            esc.append((v, w, traj, heading, end))
    if esc:
        v, w, traj, _, _ = max(esc, key=lambda e: (e[4], -e[3], e[0]))
        return v, w, traj
    _, _, _, _, w0 = state
    w_lo = max(-cfg.max_yawrate, w0 - cfg.max_dyawrate * cfg.dt)
    w_hi = min(cfg.max_yawrate, w0 + cfg.max_dyawrate * cfg.dt)
    back = []
    v = -0.05
    while v >= -0.3 - 1e-9:
        w = w_lo
        while w <= w_hi + 1e-9:
            traj = predict(state, v, w, cfg)
            if all(_in_bounds(x, y, cfg) for x, y, *_ in traj):
                ex, ey = traj[-1][0], traj[-1][1]
                end = min(math.hypot(ox - ex, oy - ey) for ox, oy in obs)
                if end > start_clear:
                    back.append((v, w, traj, None, end))
            w += cfg.yaw_res
        v -= cfg.v_res
    if back:
        v, w, traj, _, _ = max(back, key=lambda e: (e[4], e[0]))
        return v, w, traj
    return 0.0, 0.0, [list(state)]


def _pivot(state, goal, obstacles, cfg, w_min, w_max):
    """Turn-in-place fallback when no mover rollout stays clear.

    cruise_seed lifts v_min above 0, so pivots never enter the
    candidate pool; without this fallback the planner reverses out
    even when turning toward the goal is safe (proven live 2026-11-04:
    leg 0 at (1.8, 0) reversed into the east wall though a pivot had
    clearance 1.34 > 1.2). Returns (0, w, traj) for the best-heading
    safe pivot, else None (caller tries _escape).
    """
    obs = list(obstacles)
    if not obs:
        return None
    best, best_head = None, float("inf")
    w = w_min
    while w <= w_max + 1e-9:
        if abs(w) >= 1e-9:
            traj = predict(state, 0.0, w, cfg)
            if (all(_in_bounds(x, y, cfg) for x, y, *_ in traj)
                    and clearance(traj, obs) >= cfg.robot_radius):
                ex, ey, eth, _, _ = traj[-1]
                head = abs(_wrap(math.atan2(goal[1] - ey,
                                            goal[0] - ex) - eth))
                if head < best_head:
                    best, best_head = (0.0, w, traj), head
        w += cfg.yaw_res
    return best


def dwa_control(state, goal, obstacles, cfg=None):
    """Best (v, w, trajectory) toward goal avoiding obstacles.

    Returns (0.0, 0.0, [state]) at the goal, when no rollout stays in
    bounds, or when nothing escapes either (caller pivots/replans).
    A start inside the bubble escapes via _escape instead of holding.
    """
    cfg = cfg or DWAConfig()
    goal_dist = math.hypot(goal[0] - state[0], goal[1] - state[1])
    if goal_dist < cfg.goal_tol:
        return 0.0, 0.0, [list(state)]
    # Plan-from-cruise: pause-per-leg replans from v=0, collapsing the
    # window to a 0.05 crawl. Far from goal (past the early return),
    # seed the window as if already cruising; rollouts stay truthful.
    v0eff = max(state[3], cfg.cruise_seed)
    v_min, v_max, w_min, w_max = dynamic_window(
        [state[0], state[1], state[2], v0eff, state[4]], cfg)
    pool = []
    v = v_min
    while v <= v_max + 1e-9:
        w = w_min
        while w <= w_max + 1e-9:
            traj = predict(state, v, w, cfg)
            if all(_in_bounds(x, y, cfg) for x, y, *_ in traj):
                ex, ey, eth, _, _ = traj[-1]
                heading = abs(_wrap(math.atan2(goal[1] - ey,
                                              goal[0] - ex) - eth))
                pool.append((v, w, traj, heading,
                             clearance(traj, obstacles)))
            w += cfg.yaw_res
        v += cfg.v_res
    # cap: empty space reads inf, poisoning cost math
    cands = [(v, w, t, h, min(cl, 3.0)) for v, w, t, h, cl in pool
             if cl >= cfg.robot_radius]
    if not cands:
        piv = _pivot(state, goal, obstacles, cfg, w_min, w_max)
        if piv is not None:
            return piv
        return _escape(state, pool, obstacles, cfg)
    movers = [c for c in cands if c[0] > 0.01]
    if movers:
        cands = movers  # stopping loses to any safe motion; the pause
        # action (not DWA) owns stopping, and v=0 otherwise wins every
        # clearance tie against slow safe crawls.
    n_h = sum(c[3] for c in cands) or 1.0
    n_c = sum(c[4] for c in cands) or 1.0
    best, best_cost = None, float("inf")
    for v, w, traj, heading, clear in cands:
        cost = (cfg.w_heading * heading / n_h * len(cands)
                + cfg.w_clearance * (1.0 - clear / n_c * len(cands))
                + cfg.w_velocity * (cfg.max_speed - v) / cfg.max_speed)
        if cost < best_cost:
            best, best_cost = (v, w, traj), cost
    return best


def wheel_targets(v: float, w: float, cfg=None) -> tuple:
    """(v, w) -> (left_deg_s, right_deg_s) for the joint drives.

    Body frame: +X nose, wheel_l on body-left (+Y), wheel_r on
    body-right; +joint velocity about the +Y joint axis rolls its
    side forward. Each joint takes its own side's ground speed in
    deg/s (drive units).

    Calibration history: an earlier build had this map v-flipped
    (negated, sides crossed). Recalibrated live 2026-11-04: symmetric
    -120 drives along -X at 0.53 m per 1 s leg (bearing matches
    row0-yaw - 180 deg to 0.3 deg), and (L,R)=(-81,+81) yaws row0
    +8.2 deg (CCW) per 20-step leg.
    """
    cfg = cfg or DWAConfig()
    v_left_ground = v - w * cfg.track / 2.0
    v_right_ground = v + w * cfg.track / 2.0
    left = v_left_ground / cfg.wheel_r * RAD2DEG
    right = v_right_ground / cfg.wheel_r * RAD2DEG
    return left, right


def _ray_circle(px, py, dx, dy, cx, cy, r) -> float | None:
    """Ray hit distance, or None on miss. Ray dir must be unit."""
    fx, fy = px - cx, py - cy
    b = fx * dx + fy * dy
    c = fx * fx + fy * fy - r * r
    disc = b * b - c
    if disc < 0:
        return None
    t = -b - math.sqrt(disc)
    return t if t > 0 else None


def _ray_segment(px, py, dx, dy, ax, ay, bx, by) -> float | None:
    """Ray/segment hit distance, or None on miss/parallel."""
    ex, ey = bx - ax, by - ay
    denom = dx * ey - dy * ex
    if abs(denom) < 1e-9:
        return None
    t = ((ax - px) * ey - (ay - py) * ex) / denom
    u = ((ax - px) * dy - (ay - py) * dx) / denom
    if t > 0 and 0.0 <= u <= 1.0:
        return t
    return None


def synth_scan(pose, circles, bounds, n_rays=72, max_range=8.0) -> list:
    """Fake lidar: (angle, range) rays vs cone circles + wall segments.

    Stand-in until a riding scan exists; same output shape as a real
    2D scan so scan_to_points and DWA stay unchanged when it lands.
    """
    px, py, _ = pose
    xmin, xmax, ymin, ymax = bounds
    segs = [(xmin, ymin, xmax, ymin), (xmax, ymin, xmax, ymax),
            (xmax, ymax, xmin, ymax), (xmin, ymax, xmin, ymin)]
    out = []
    for i in range(n_rays):
        ang = 2.0 * math.pi * i / n_rays
        dx, dy = math.cos(ang), math.sin(ang)
        hits = [_ray_circle(px, py, dx, dy, cx, cy, r)
                for cx, cy, r in circles]
        hits += [_ray_segment(px, py, dx, dy, *s) for s in segs]
        hits = [h for h in hits if h is not None and h <= max_range]
        out.append((ang, min(hits) if hits else max_range))
    return out


def scan_to_points(scan, pose) -> list:
    """Scan (angle, range) + robot pose -> world obstacle points."""
    px, py, _ = pose
    return [(px + r * math.cos(a), py + r * math.sin(a)) for a, r in scan]


@dataclass
class MissionLeg:
    """One mission phase: goal + bubble + arrival tolerance."""
    goal: tuple
    radius: float
    tol: float = 0.5


def mission_step(state, legs, reached):
    """Active (goal, radius, tol, reached-count) for waypoint missions.

    legs[reached] is active until the robot gets within its tol, then
    the mission latches forward (never back: a leg passed stays passed
    even if a later leg swings wide). Pure function of pose so the
    live driver and unit tests share it.
    """
    n = min(reached, len(legs) - 1)
    while n < len(legs) - 1:
        gx, gy = legs[n].goal
        if math.hypot(gx - state[0], gy - state[1]) < legs[n].tol:
            n += 1
        else:
            break
    leg = legs[n]
    return leg.goal, leg.radius, leg.tol, n
