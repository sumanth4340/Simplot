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
