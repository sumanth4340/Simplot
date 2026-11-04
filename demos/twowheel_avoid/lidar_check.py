

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

import isaacsim.core.experimental.utils.app as app_utils
mount_lidar()
app_utils.play()
await app_utils.update_app_async(steps=120)
print('SPAWN fwd=%.3f sectors=%s'
      % (await read_forward_min(), await read_sector_mins()))
app_utils.stop()
print('LIDAR-CHECK-DONE')
