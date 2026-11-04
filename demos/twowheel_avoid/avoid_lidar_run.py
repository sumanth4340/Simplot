"""Two-wheel lidar obstacle-avoidance demo (runs INSIDE Isaac Sim).

Contract: bot already built at /World/AvoidBot facing +X, revolute
joints joint_l/joint_r with velocity drives; obstacles Obs0 (2.0,0),
Obs1 (3.2,-0.8), Obs2 (3.2,0.8). Lidar fan is mounted under the
chassis by mount_lidar(); per-step forward min (meters) comes from
async read_forward_min(), sector split from read_sector_mins().

Flow: mount_lidar() (STOPPED) -> play -> warmup 60 steps ->
closed loop up to 1200 steps (sense -> command -> step 1) ->
stop + LIDAR-SUMMARY.

Control law (reactive, re-sensed every step):
  min > 0.7 m : straight, vl = vr = +4.0 rad/s
  min <= 0.7 m: spin toward the clearer sector --
      left clearer: vl = -2.5, vr = +2.5 (CCW from above = left)
      right clearer (or tie/invalid): vl = +2.5, vr = -2.5
  invalid reads (None) are BLOCKED (fail safe), never clear.

Drive units: P3 drill finding -- UsdPhysics.DriveAPI angular
target_velocity is DEGREES/s. Contract speeds are rad/s, scaled by
180/pi at the Set() call. Targets authored live per step via
DriveAPI (proven to propagate: diag_probe 2026-11-04).

Position reads: RigidPrim tensor (SIMULATED state, live while
playing). Raw USD reads are authored-state and stale mid-play.
"""
import math

import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.core.experimental.prims import RigidPrim
from pxr import Usd, UsdPhysics

BOT = "/World/AvoidBot"
JL = BOT + "/joint_l"
JR = BOT + "/joint_r"

R_CLEAR = 0.7       # m: above -> straight, at/below -> steer away
W_FWD = 4.0         # rad/s both wheels when clear (0.36 m/s)
W_SPIN = 2.5        # rad/s spin magnitude toward clearer sector
DEG = 180.0 / math.pi  # P3 units: DriveAPI angular target is deg/s
WARMUP = 60
BUDGET = 1200
LOG_EVERY = 30

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

Fan: 13 rays, yaw -30..+30 deg about +X at 5 deg steps, pitch 0.
+Y is the bot's LEFT (Z-up right-handed: X fwd, Y left).
read_forward_min() -> min over all rays; read_sector_mins() ->
(left_min, right_min) split by yaw sign. Misses read max_range.
Invalid reads return None -> caller must treat as BLOCKED (fail safe),
never as clear.
"""

import math

FAN_PATH = "/World/AvoidBot/chassis/LidarFan"
MOUNT_LOCAL = [0.10, 0.0, 0.12]  # chassis-local (x fwd, z up from center)
FAN_HALF_DEG = 30.0
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
        "LIDAR: lidar_snippet.py body not pasted -- mount_lidar / "
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
    raise RuntimeError("LIDAR: no rigid body found under " + BOT)


st = omni.usd.get_context().get_stage()
_jl = st.GetPrimAtPath(JL)
_jr = st.GetPrimAtPath(JR)
if not (_jl.IsValid() and _jr.IsValid()):
    raise RuntimeError("LIDAR: missing %s and/or %s" % (JL, JR))
_dl = UsdPhysics.DriveAPI.Apply(_jl, "angular")
_dr = UsdPhysics.DriveAPI.Apply(_jr, "angular")


def _cmd(vl_rad_s, vr_rad_s):
    _dl.GetTargetVelocityAttr().Set(float(vl_rad_s) * DEG)
    _dr.GetTargetVelocityAttr().Set(float(vr_rad_s) * DEG)


_ch = RigidPrim(_chassis_path())


def _base_x():
    pos, _quat = _ch.get_world_poses()
    return float(pos.numpy().flatten()[0])


mount_lidar()
app_utils.play()
_cmd(0.0, 0.0)
await app_utils.update_app_async(steps=WARMUP)

min_range = float("inf")
r = float("nan")
for i in range(1, BUDGET + 1):
    fwd = await read_forward_min()
    # Invalid (None/non-positive) reads as BLOCKED (fail safe).
    r = fwd if (fwd is not None and fwd == fwd and fwd > 0.0) else -1.0
    if r > 0.0 and r < min_range:
        min_range = r
    if r > R_CLEAR:
        _cmd(W_FWD, W_FWD)
    else:
        left, right = await read_sector_mins()
        lv = left if left is not None else -1.0
        rv = right if right is not None else -1.0
        if lv > rv:
            _cmd(-W_SPIN, W_SPIN)   # left clearer -> turn left
        else:
            _cmd(W_SPIN, -W_SPIN)   # right clearer (or tie) -> right
    await app_utils.update_app_async(steps=1)
    if i % LOG_EVERY == 0:
        print("STEP %d x=%.3f r=%.3f" % (i, _base_x(), r))

x_final = _base_x()
_cmd(0.0, 0.0)
app_utils.stop()
ok = (min_range > 0.25) and (x_final > 3.0)
print("LIDAR-SUMMARY min_range=%.3f x_final=%.3f %s"
      % (min_range, x_final, "SUCCESS" if ok else "FAIL"))
