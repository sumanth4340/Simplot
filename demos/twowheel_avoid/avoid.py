"""Two-wheel obstacle-avoidance demo (runs INSIDE Isaac Sim via bridge).

BEHAVIOR agent script. Contract with sibling agents: bot already built
at /World/AvoidBot facing +X, revolute joints joint_l/joint_r with
velocity drives; obstacles Obs0 (2.0,0), Obs1 (3.2,-0.8), Obs2
(3.2,0.8). Depth camera is mounted at /World/AvoidBot/DepthCam by
mount_depth_cam(); per-step center range (meters) comes from async
read_center_range().

Flow: play -> mount_depth_cam() -> warmup 60 steps -> closed loop up
to 900 steps (sense -> command -> step 1) -> stop + AVOID-SUMMARY.

Control law (bang-bang reactive, re-sensed every step):
  r > 0.7 m : straight, vl = vr = +1.0 rad/s
  r <= 0.7 m: spin in place, vl = +1.2, vr = -1.2 rad/s, until clear
No latched turn state: the spin exits on the first step the center
ray clears. That is the reactive analogue of the planning-pack
anti-stall rule (ros-navigation planning N4: decide from fresh data,
never a stale window) -- here the "window" is one fresh reading.

Drive units: P3 drill finding -- UsdPhysics.DriveAPI angular
target_velocity is DEGREES/s (w=180 -> turn pi in 1.000 s). Contract
speeds are rad/s, so every command is scaled by 180/pi at the Set()
call. Targets are authored live per step via DriveAPI (no OmniGraph),
mirroring the p3_setup / n1_build DriveAPI pattern.

Position reads: RigidPrim tensor (SIMULATED state, live while
playing) -- the packs' post-step pattern (physics core p3_run.py,
ros-navigation bringup n1_truth.py). Raw USD xform reads are
authored-state and stale mid-play (physics skill "Step + read"), so
they are NOT used for x. All x samples are taken while playing.

No early exit: the contract gives a step budget (900) but no exit
criterion, so the loop always runs the full budget.
"""
import math

import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.core.experimental.prims import RigidPrim
from pxr import Usd, UsdPhysics

BOT = "/World/AvoidBot"
JL = BOT + "/joint_l"
JR = BOT + "/joint_r"

R_CLEAR = 0.7       # m: above -> straight, at/below -> spin
W_FWD = 1.0         # rad/s both wheels when clear
W_SPIN = 1.2        # rad/s spin magnitude (+left, -right) when blocked
DEG = 180.0 / math.pi  # P3 units: DriveAPI angular target_velocity is deg/s
WARMUP = 60
BUDGET = 900
LOG_EVERY = 30

# === SENSE SNIPPET (integrator pastes sense_snippet.py body here) ===
# The integrator pastes the SENSE agent's sense_snippet.py body between
# the PASTE lines. It MUST define these exact names:
#   async def mount_depth_cam() -> None:
#       ... author /World/AvoidBot/DepthCam + depth annotator ...
#   async def read_center_range() -> float:
#       ... return center-pixel depth in meters (S1 base: exact to 1 mm) ...
# --- PASTE BELOW THIS LINE ---
# --- PASTE ABOVE THIS LINE ---
if "mount_depth_cam" not in dir() or "read_center_range" not in dir():
    raise RuntimeError(
        "AVOID: sense_snippet.py body not pasted -- mount_depth_cam / "
        "read_center_range are undefined.")


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
    raise RuntimeError("AVOID: no rigid body found under " + BOT)


st = omni.usd.get_context().get_stage()
_jl = st.GetPrimAtPath(JL)
_jr = st.GetPrimAtPath(JR)
if not (_jl.IsValid() and _jr.IsValid()):
    raise RuntimeError("AVOID: missing %s and/or %s" % (JL, JR))
_dl = UsdPhysics.DriveAPI.Apply(_jl, "angular")
_dr = UsdPhysics.DriveAPI.Apply(_jr, "angular")


def _cmd(vl_rad_s, vr_rad_s):
    _dl.GetTargetVelocityAttr().Set(float(vl_rad_s) * DEG)
    _dr.GetTargetVelocityAttr().Set(float(vr_rad_s) * DEG)


_ch = RigidPrim(_chassis_path())


def _base_x():
    pos, _quat = _ch.get_world_poses()
    return float(pos.numpy().flatten()[0])


app_utils.play()
await mount_depth_cam()
_cmd(0.0, 0.0)
await app_utils.update_app_async(steps=WARMUP)

min_range = float("inf")
r = float("nan")
for i in range(1, BUDGET + 1):
    raw = float(await read_center_range())
    # Invalid depth (<=0/NaN, no hit in clip range) reads as clear;
    # +inf already compares clear and needs no mapping.
    r = raw if (raw == raw and raw > 0.0) else 10.0
    if r < min_range:
        min_range = r
    if r > R_CLEAR:
        _cmd(W_FWD, W_FWD)
    else:
        _cmd(W_SPIN, -W_SPIN)
    await app_utils.update_app_async(steps=1)
    if i % LOG_EVERY == 0:
        print("STEP %d x=%.3f r=%.3f" % (i, _base_x(), r))

x_final = _base_x()
_cmd(0.0, 0.0)
app_utils.stop()
ok = (min_range > 0.25) and (x_final > 3.0)
print("AVOID-SUMMARY min_range=%.3f x_final=%.3f %s"
      % (min_range, x_final, "SUCCESS" if ok else "FAIL"))
