"""B4 run (runs INSIDE Isaac Sim): closed-loop trigger.

Play in 10-step chunks (20x): read slider x each chunk; when x>=1.0
first seen, command arm +0.6 rad (TRIGGERED, latched once). Slider
runs 0->2.0 over 2.0s, so trigger lands t~1.0s. Reports trigger
time/x, final q, final slider x.
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
CHUNKS, CSTEP, THRESH, QTGT = 20, 10, 1.0, 0.6


def _x():
    now = tl.get_current_time()
    tc = Usd.TimeCode(now * stage.GetTimeCodesPerSecond())
    prim = stage.GetPrimAtPath("/World/B4Slider")
    op = UsdGeom.Xformable(prim).GetOrderedXformOps()[0]
    return now, float(op.Get(tc)[0])


def _q(robot):
    q = robot.get_dof_positions()
    q = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
    return float(np.asarray(q, dtype=float).flatten()[0])


app_utils.stop()
await app_utils.update_app_async(steps=10)
app_utils.play(commit=True)
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/B4Bot/Base")
trig, trig_t, trig_x = 0, -1.0, -1.0
for _ in range(CHUNKS):
    await app_utils.update_app_async(steps=CSTEP)
    now, x = _x()
    if not trig and x >= THRESH:
        trig, trig_t, trig_x = 1, now, x
        robot.set_dof_position_targets(
            np.array([QTGT], dtype=np.float32))
now, x_end = _x()
q_end = _q(robot)
print("B4-REPORT trig=%d trig_t=%.3f trig_x=%.3f q_end=%.4f "
      "x_end=%.3f" % (trig, trig_t, trig_x, q_end, x_end))
