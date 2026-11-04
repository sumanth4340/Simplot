"""Two-wheel obstacle-avoidance demo (runs INSIDE Isaac Sim via bridge).

BEHAVIOR agent script. Contract with sibling agents: bot already built
at /World/AvoidBot facing +X, revolute joints joint_l/joint_r with
velocity drives; obstacles Obs0 (2.0,0), Obs1 (3.2,-0.8), Obs2
(3.2,0.8). Depth camera is mounted at /World/AvoidBot/DepthCam by
mount_depth_cam(); per-step center range (meters) comes from async
read_center_range().

Flow: mount_depth_cam() (STOPPED, G1) -> play -> warmup 60 steps -> closed loop up
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
W_FWD = 4.0         # rad/s both wheels when clear
W_SPIN = 2.5        # rad/s spin magnitude (+left, -right) when blocked
DEG = 180.0 / math.pi  # P3 units: DriveAPI angular target_velocity is deg/s
WARMUP = 60
BUDGET = 1200
LOG_EVERY = 30

# === SENSE SNIPPET (integrator pastes sense_snippet.py body here) ===
# The integrator pastes the SENSE agent's sense_snippet.py body between
# the PASTE lines. It MUST define these exact names:
#   async def mount_depth_cam() -> None:
#       ... author /World/AvoidBot/DepthCam + depth annotator ...
#   async def read_center_range() -> float:
#       ... return center-pixel depth in meters (S1 base: exact to 1 mm) ...
# --- PASTE BELOW THIS LINE ---
"""Depth sensing snippet for the two-wheel obstacle-avoidance demo.

INLINE-READY: this file is inlined into the behavior loop, NOT imported
(python_server caches imports). Plain functions only; no repo imports --
in-sim (isaacsim/omni) and stdlib imports only.

Contract: bot root /World/AvoidBot faces +X; chassis 0.4(x) x 0.3 x 0.15.
Mount: /World/AvoidBot/DepthCam at chassis front-top, local x=+0.22, z=+0.12.

S1 facts relied on (sensors/base/scripts/s1_cap.py + failures.md base R1/R5):
  F1. Annotator id "distance_to_image_plane", attached via
      CameraSensor(cam, annotators=[...]) and read via sensor.get_data(name).
  F2. Payload shape (H, W, 1) -- note the channel dim (base R1:
      resolution=[240,320] yielded dshape=[240,320,1]). Resolution is
      [H, W], so resolution=[120,160] yields (120,160,1) for 160x120.
  F3. get_data handling: result may be list/tuple (take [0]); elements may
      be warp arrays (call .numpy()) before np.asarray.
  F4. Facing convention: RTX/USD cameras look along local -Z. Bot faces
      +X, so rotate -90 deg about Y: Ry(t) maps -Z=(0,0,-1) to
      (-sin t, 0, -cos t); t=-90deg gives (+1,0,0)=+X. Verified by hand.
      Quaternion (w,x,y,z) for Ry(-90deg): [0.7071, 0, -0.7071, 0].
  F5. Center-pixel depth reads exact optical-axis range (S1: dctr 3.738
      exact to 1 mm on known geometry); depth needs no boot flags.

GOTCHAS the behavior agent must respect:
  G1. Call mount_depth_cam() while STOPPED, before first play (base R5:
      a sensor created live starts EMPTY until a stop/play re-parse).
      Never re-author the camera prim transform live. The bot driving
      around is fine -- the render product follows the rigidly mounted
      prim; re-authoring the prim itself live is what breaks the binding.
  G2. Warm up before trusting reads: S1 pumped 120 app updates before its
      first read, and first frames can be partial (cf. base R8). Pump
      >=120 updates after play, then read. read_center_range() retries
      3x30 steps on empty frames, but that is a backstop, not a plan.
  G3. Depth values are distance_to_image_plane (optical-axis depth), not
      radial range; at the center pixel the two coincide. Gate the
      center pixel only -- edge pixels see the narrow-FOV framing
      (cf. base R2), not the corridor ahead.

Usage (in-sim, inside the behavior coroutine):
  mount_depth_cam()                    # while STOPPED, before first play
  app_utils.play(commit=True)
  await app_utils.update_app_async(steps=120)   # warm-up, cf. S1/G2
  r = await read_center_range()        # meters; < THRESH -> turn, else fwd
"""

import math

CAM_PATH = "/World/AvoidBot/DepthCam"
MOUNT_POS = [0.22, 0.0, 0.12]  # chassis front-top, bot-local (bot faces +X)
_HALF = math.radians(-90.0) / 2.0
Q_FACING_X = [math.cos(_HALF), 0.0, math.sin(_HALF), 0.0]  # Ry(-90deg)

DEPTH_KEY = "distance_to_image_plane"
RESOLUTION_HW = [120, 160]  # [H, W] -> payload (120, 160, 1) for 160x120

_SENSOR = None


def mount_depth_cam():
    """Create the depth camera + render product + depth annotator.

    Call while STOPPED before first play (see G1). Assumes the bot root
    is at the origin unrotated at mount time, so bot-local == stage frame;
    the mount is rigid and follows the bot afterwards. Returns the sensor.
    """
    global _SENSOR
    import omni.usd
    from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor

    stage = omni.usd.get_context().get_stage()
    if not stage.GetPrimAtPath("/World/AvoidBot").IsValid():
        stage.DefinePrim("/World/AvoidBot", "Xform")
    o = stage.GetPrimAtPath(CAM_PATH)
    if o and o.IsValid():
        stage.RemovePrim(CAM_PATH)
    cam = RtxCamera(CAM_PATH, positions=[MOUNT_POS],
                    orientations=[Q_FACING_X])
    cam.camera.set_focal_lengths(24.0)
    cam.camera.set_clipping_ranges(0.01, 1000.0)
    _SENSOR = CameraSensor(cam, resolution=list(RESOLUTION_HW),
                           annotators=[DEPTH_KEY])
    return _SENSOR


async def read_center_range():
    """Return the center-pixel depth in meters as a float (latest frame)."""
    import numpy as np
    import warp as wp
    import isaacsim.core.experimental.utils.app as app_utils

    if _SENSOR is None:
        raise RuntimeError("mount_depth_cam() has not been called")
    for _ in range(3):
        d = _SENSOR.get_data(DEPTH_KEY)
        if isinstance(d, (list, tuple)):
            d = d[0] if len(d) else None
        if d is not None:
            a = np.asarray(d.numpy() if isinstance(d, wp.array) else d)
            if a is not None and a.size and a.ndim >= 2:
                h, w = a.shape[0], a.shape[1]
                return float(a[h // 2, w // 2])
        await app_utils.update_app_async(steps=30)
    raise RuntimeError("depth annotator returned no valid frame after warm-up")
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


mount_depth_cam()
app_utils.play()
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
