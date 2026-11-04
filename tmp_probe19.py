"""Probe 19 (runs INSIDE Isaac Sim): stop/play picks up new USD targets?"""
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation


def _q(robot):
    q = robot.get_dof_positions()
    q = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
    return np.asarray(q, dtype=float).flatten()


stage = omni.usd.get_context().get_stage()
a1 = stage.GetPrimAtPath("/World/M2Bot/Hinge1").GetAttribute(
    "drive:angular:physics:targetPosition")
a2 = stage.GetPrimAtPath("/World/M2Bot/Hinge2").GetAttribute(
    "drive:angular:physics:targetPosition")
a1.Set(10.0)
a2.Set(5.0)
print("USD-SET done")
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M2Bot/Base")
for i in range(3):
    await app_utils.update_app_async(steps=30)
    print("P%d=" % ((i + 1) * 30,), np.round(_q(robot), 4).tolist())
omni.timeline.get_timeline_interface().pause()
