"""Two-wheel lidar goal-seeking demo (runs INSIDE Isaac Sim).

Contract: bot already built at /World/AvoidBot facing +X, revolute
joints joint_l/joint_r with velocity drives; obstacles Obs0 (2.0,0),
Obs1 (3.2,-0.8), Obs2 (3.2,0.8); fence x -1..6 / y -2..2; goal pad
center (5.0, 0), radius 0.6. Lidar fan mounted under the chassis by
mount_lidar(); per-step forward min from read_forward_min(), sector
split from read_sector_mins(). Bot pose/yaw from the chassis
RigidPrim tensor (SIMULATED state, live while playing).

Flow: mount_lidar() (STOPPED) -> play -> warmup 60 steps ->
closed loop up to 1500 steps (sense -> command -> step 1) ->
stop + GOAL-SUMMARY. Stops early on reaching the goal.

Control law (re-sensed every step):
  min > 0.7 m : goal steering -- yaw error to the goal drives a
      differential correction (vl = base - k*err, vr = base + k*err,
      k = 3.0, clamped to [0, 5] rad/s). err > 0 = goal left.
  min <= 0.7 m: avoid override -- spin toward the clearer sector
      (left clearer: vl = -2.5, vr = +2.5; else mirrored).
  invalid reads (None) are BLOCKED (fail safe), never clear.
  stuck recovery: if the bot moves < 0.08 m over 90 commanded steps,
      run ESCAPE (reverse 45 steps, then spin 45 steps toward the
      clearer sector sampled at escape start), with a 120-step
      cooldown. Unwedges corner pockets the fan cannot see.

Drive units: P3 drill finding -- UsdPhysics.DriveAPI angular
target_velocity is DEGREES/s, scaled by 180/pi at Set().
"""
import math

import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.core.experimental.prims import RigidPrim
from pxr import Usd, UsdPhysics

BOT = "/World/AvoidBot"
JL = BOT + "/joint_l"
JR = BOT + "/joint_r"
GOAL_XY = (5.0, 0.0)
GOAL_R = 0.6

R_CLEAR = 0.7       # m: above -> steer to goal, at/below -> avoid
W_BASE = 4.0        # rad/s cruise (0.36 m/s)
W_SPIN = 2.5        # rad/s avoid-override spin magnitude
K_STEER = 3.0       # yaw-error gain (rad/s per rad)
W_MAX = 5.0
DEG = 180.0 / math.pi  # P3 units: DriveAPI angular target is deg/s
WARMUP = 60
BUDGET = 2400
LOG_EVERY = 30
STUCK_WINDOW = 90
STUCK_DIST = 0.08
ESCAPE_REV = 45
ESCAPE_SPIN = 45
ESCAPE_COOLDOWN = 120

# === LIDAR SNIPPET (integrator pastes lidar_snippet.py body here) ===
# Must define: mount_lidar(), read_forward_min(), read_sector_mins().
# --- PASTE BELOW THIS LINE ---
"""Physics-raycast lidar fan for the two-wheel avoidance demo.

INLINE-READY: inlined into the behavior loop, NOT imported
(python_server caches imports). Plain functions; in-sim imports only.

FINDINGS (live-probed 2026-11-04, Isaac Sim 6.0.0/Kit 110):
  F1. Raycast(path, min_range, max_range, ray_origins, ray_directions)
      + RaycastSensor(path).get_data() -> dict with 'depths' key.
      Single-ray sensors read EXACT (+X: 1.65 to Obs0 face; -X: 10.0
      open). Author while STOPPED; read after play.
  F2. MULTI-RAY single sensor is BROKEN in this build: all depths
      replicate ray0's value (list AND numpy inputs). Workaround used
      here: N single-ray Raycast prims, one RaycastSensor each.
  F3. Raycast() pre-authors xformOp:translate: SET it (parent-local),
      never AddTranslateOp (collides).
  F4. get_data() can return zero-size depths on early reads: size-guard
      every reduction (G4 rule); prime + retry before trusting.

Contract: bot root /World/AvoidBot faces +X. Fan lives UNDER the
chassis rigid body (/World/AvoidBot/chassis/LidarFan/r00..r12) so rays
sweep with the bot. Roof mount (local x=+0.10, z=+0.12 -> world
z~0.385) keeps the horizontal fan clear of the own chassis (top 0.34).

Fan: 19 rays, yaw -45..+45 deg about +X at 5 deg steps, pitch 0.
+Y is the bot's LEFT (Z-up right-handed: X fwd, Y left).
read_forward_min() -> min over all rays; read_sector_mins() ->
(left_min, right_min) split by yaw sign. Misses read max_range.
Invalid reads return None -> caller must treat as BLOCKED (fail safe),
never as clear.
"""

import math

FAN_PATH = "/World/AvoidBot/chassis/LidarFan"
MOUNT_LOCAL = [0.10, 0.0, 0.12]  # chassis-local (x fwd, z up from center)
FAN_HALF_DEG = 45.0
FAN_STEP_DEG = 5.0
MIN_RANGE = 0.05
MAX_RANGE = 10.0

_RAYS = []  # (yaw_deg, RaycastSensor)


def mount_lidar():
    """Author the 13-ray fan (call while STOPPED, before first play)."""
    global _RAYS
    import omni.usd
    from pxr import Gf
    from isaacsim.sensors.experimental.physics import Raycast, RaycastSensor

    stage = omni.usd.get_context().get_stage()
    if not stage.GetPrimAtPath("/World/AvoidBot/chassis").IsValid():
        raise RuntimeError("mount_lidar: chassis missing, run build first")
    o = stage.GetPrimAtPath(FAN_PATH)
    if o and o.IsValid():
        stage.RemovePrim(FAN_PATH)
    _RAYS = []
    n = int(round(2.0 * FAN_HALF_DEG / FAN_STEP_DEG)) + 1
    for i in range(n):
        yaw = -FAN_HALF_DEG + FAN_STEP_DEG * i
        r = math.radians(yaw)
        p = "%s/r%02d" % (FAN_PATH, i)
        Raycast(p, min_range=MIN_RANGE, max_range=MAX_RANGE,
                ray_origins=[[0.0, 0.0, 0.0]],
                ray_directions=[[math.cos(r), math.sin(r), 0.0]])
        stage.GetPrimAtPath(p).GetAttribute(
            "xformOp:translate").Set(Gf.Vec3d(*MOUNT_LOCAL))
        _RAYS.append((yaw, RaycastSensor(p)))
    return _RAYS


def _read_all():
    """Return [(yaw, depth_or_None)] for the fan (latest step)."""
    import numpy as np
    import warp as wp

    out = []
    for yaw, sensor in _RAYS:
        try:
            d = sensor.get_data()
        except Exception:
            out.append((yaw, None))
            continue
        dep = d.get("depths") if isinstance(d, dict) else None
        if dep is None:
            out.append((yaw, None))
            continue
        a = np.asarray(dep.numpy() if isinstance(dep, wp.array) else dep,
                       dtype=float).flatten()
        out.append((yaw, float(a[0]) if a.size else None))
    return out


async def read_forward_min():
    """Min fan range in meters; None when no ray has a valid read."""
    import isaacsim.core.experimental.utils.app as app_utils

    if not _RAYS:
        raise RuntimeError("mount_lidar() has not been called")
    for _ in range(3):
        vals = [v for _, v in _read_all() if v is not None]
        if vals:
            return min(vals)
        await app_utils.update_app_async(steps=30)
    return None


async def read_sector_mins():
    """(left_min, right_min) split by yaw sign; None side when no valid."""
    import isaacsim.core.experimental.utils.app as app_utils

    if not _RAYS:
        raise RuntimeError("mount_lidar() has not been called")
    for _ in range(3):
        rows = _read_all()
        left = [v for y, v in rows if v is not None and y > 0.0]
        right = [v for y, v in rows if v is not None and y < 0.0]
        if left or right:
            return (min(left) if left else None,
                    min(right) if right else None)
        await app_utils.update_app_async(steps=30)
    return (None, None)
# --- PASTE ABOVE THIS LINE ---
if "mount_lidar" not in dir() or "read_forward_min" not in dir():
    raise RuntimeError(
        "GOAL: lidar_snippet.py body not pasted -- mount_lidar / "
        "read_forward_min are undefined.")


def _chassis_path():
    """Resolve the chassis rigid-body path (builder owns the layout)."""
    st = omni.usd.get_context().get_stage()
    for cand in (BOT + "/chassis", BOT + "/Chassis",
                 BOT + "/base", BOT + "/body"):
        p = st.GetPrimAtPath(cand)
        if p.IsValid() and p.HasAPI(UsdPhysics.RigidBodyAPI):
            return cand
    root = st.GetPrimAtPath(BOT)
    if root.IsValid():
        for p in Usd.PrimRange(root):
            if p.HasAPI(UsdPhysics.RigidBodyAPI):
                return p.GetPath().pathString
    raise RuntimeError("GOAL: no rigid body found under " + BOT)


st = omni.usd.get_context().get_stage()
_jl = st.GetPrimAtPath(JL)
_jr = st.GetPrimAtPath(JR)
if not (_jl.IsValid() and _jr.IsValid()):
    raise RuntimeError("GOAL: missing %s and/or %s" % (JL, JR))
_dl = UsdPhysics.DriveAPI.Apply(_jl, "angular")
_dr = UsdPhysics.DriveAPI.Apply(_jr, "angular")


def _cmd(vl_rad_s, vr_rad_s):
    _dl.GetTargetVelocityAttr().Set(float(vl_rad_s) * DEG)
    _dr.GetTargetVelocityAttr().Set(float(vr_rad_s) * DEG)


_ch = RigidPrim(_chassis_path())


def _pose():
    """(x, y, yaw) of the chassis from live tensors; yaw about +Z."""
    pos, quat = _ch.get_world_poses()
    p = pos.numpy().flatten()
    x, y, z, w = (float(v) for v in quat.numpy().flatten())
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return float(p[0]), float(p[1]), yaw


def _wrap(a):
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


mount_lidar()
app_utils.play()
_cmd(0.0, 0.0)
await app_utils.update_app_async(steps=WARMUP)

min_range = float("inf")
r = float("nan")
reached = False
bx, by, yaw = 0.0, 0.0, 0.0
trace = []
steps_run = 0
hist = []               # (x, y, yaw) per step for stuck detection
escape_left = 0         # escape steps remaining (0 = not escaping)
escape_spin_left = True
cooldown = 0
escapes = 0
for i in range(1, BUDGET + 1):
    fwd = await read_forward_min()
    # Invalid (None/non-positive) reads as BLOCKED (fail safe).
    r = fwd if (fwd is not None and fwd == fwd and fwd > 0.0) else -1.0
    if r > 0.0 and r < min_range:
        min_range = r
    if escape_left > 0:
        if escape_left > ESCAPE_SPIN:
            _cmd(-2.0, -2.0)    # back out first (came from open space)
        elif escape_spin_left:
            _cmd(-W_SPIN, W_SPIN)
        else:
            _cmd(W_SPIN, -W_SPIN)
        escape_left -= 1
    elif r > R_CLEAR:
        err = _wrap(math.atan2(GOAL_XY[1] - by, GOAL_XY[0] - bx) - yaw)
        corr = max(-W_BASE, min(W_BASE, K_STEER * err))
        _cmd(W_BASE - corr, W_BASE + corr)
    else:
        left, right = await read_sector_mins()
        lv = left if left is not None else -1.0
        rv = right if right is not None else -1.0
        if lv > rv:
            _cmd(-W_SPIN, W_SPIN)   # left clearer -> turn left
        else:
            _cmd(W_SPIN, -W_SPIN)   # right clearer (or tie) -> right
    await app_utils.update_app_async(steps=1)
    bx, by, yaw = _pose()
    hist.append((bx, by, yaw))
    if cooldown > 0:
        cooldown -= 1
    if (escape_left == 0 and cooldown == 0 and not reached
            and len(hist) > STUCK_WINDOW):
        ox, oy, oyaw = hist[-STUCK_WINDOW - 1]
        moved = math.hypot(bx - ox, by - oy)
        turned = abs(_wrap(yaw - oyaw))
        if moved < STUCK_DIST and turned < 0.15:
            left, right = await read_sector_mins()
            lv = left if left is not None else -1.0
            rv = right if right is not None else -1.0
            escape_spin_left = lv > rv
            escape_left = ESCAPE_REV + ESCAPE_SPIN
            cooldown = ESCAPE_REV + ESCAPE_SPIN + ESCAPE_COOLDOWN
            escapes += 1
            msg = ("STEP %d x=%.3f y=%.3f ESCAPE #%d (moved %.3f, turned %.2f)"
                   % (i, bx, by, escapes, moved, turned))
            print(msg)
            trace.append(msg)
    dist = math.hypot(GOAL_XY[0] - bx, GOAL_XY[1] - by)
    if dist < GOAL_R:
        reached = True
        msg = "STEP %d x=%.3f y=%.3f r=%.3f GOAL-REACHED" % (i, bx, by, r)
        print(msg)
        trace.append(msg)
        steps_run = i
        break
    if i % LOG_EVERY == 0:
        msg = "STEP %d x=%.3f y=%.3f r=%.3f d=%.2f" % (i, bx, by, r, dist)
        print(msg)
        trace.append(msg)
    steps_run = i

_cmd(0.0, 0.0)
app_utils.stop()
ok = reached and (min_range > 0.25)
summary = ("GOAL-SUMMARY reached=%s min_range=%.3f x=%.3f y=%.3f escapes=%d %s"
           % (reached, min_range, bx, by, escapes,
              "SUCCESS" if ok else "FAIL"))
print(summary)
# Persist BEFORE reply: the verdict must survive client disconnects.
import json as _json
_ev = {"reached": reached,
       "min_range": (None if min_range == float("inf") else round(min_range, 3)),
       "x": round(bx, 3), "y": round(by, 3), "escapes": escapes,
       "steps": steps_run, "verdict": "SUCCESS" if ok else "FAIL",
       "trace": trace}
open("C:/Users/sruja_ob3di74/action-reasoner/demos/twowheel_avoid/"
     "evidence_goal_run.json", "w").write(_json.dumps(_ev))
