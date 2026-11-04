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
