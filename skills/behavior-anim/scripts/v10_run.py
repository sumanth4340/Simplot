"""V10 run (runs INSIDE Isaac Sim): two-zone reactive behavior.

Gate slides y 0->2.4 over 2.4s. Zone rule: y<1.2 -> arm -0.4 rad;
y>=1.2 -> arm +0.4 rad; command only on zone CHANGE (20 chunks x
12 steps = 4.0s). Reports switch count/y/t, final q/y/ry.
"""
import numpy as np
import warp as wp
import omni.usd
import omni.timeline
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import Articulation
from pxr import UsdGeom, Usd

stage = omni.usd.get_context().get_stage()
tl = omni.timeline.get_timeline_interface()
CHUNKS, CSTEP, SPLIT = 20, 12, 1.2
QLO, QHI = -0.4, 0.4


def _gate():
    now = tl.get_current_time()
    tc = Usd.TimeCode(now * stage.GetTimeCodesPerSecond())
    prim = stage.GetPrimAtPath("/World/V10Gate")
    tops, rops = UsdGeom.Xformable(prim).GetOrderedXformOps()
    return now, float(tops.Get(tc)[1]), float(rops.Get(tc))


def _q(robot):
    q = robot.get_dof_positions()
    q = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
    return float(np.asarray(q, dtype=float).flatten()[0])


app_utils.stop()
await app_utils.update_app_async(steps=10)
app_utils.play(commit=True)
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/V10Bot/Base")
zone, nsw, sw_y, sw_t = 0, 0, -1.0, -1.0
robot.set_dof_position_targets(np.array([QLO], dtype=np.float32))
for _ in range(CHUNKS):
    await app_utils.update_app_async(steps=CSTEP)
    now, y, _ = _gate()
    z = 1 if y >= SPLIT else 0
    if z != zone:
        zone, nsw, sw_y, sw_t = z, nsw + 1, y, now
        robot.set_dof_position_targets(
            np.array([QHI if z else QLO], dtype=np.float32))
now, y_end, ry_end = _gate()
q_end = _q(robot)
print("V10-REPORT nsw=%d sw_y=%.3f sw_t=%.3f q_end=%.4f "
      "y_end=%.3f ry_end=%.3f" % (nsw, sw_y, sw_t, q_end, y_end, ry_end))
