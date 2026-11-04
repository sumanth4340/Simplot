"""Probe 4 (runs INSIDE Isaac Sim): runtime USD target writes live?"""
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
at1 = stage.GetPrimAtPath("/World/M2Bot/Hinge1").GetAttribute(
    "drive:angular:physics:targetPosition")
print("VALID=", at1.IsValid(), "V0=", at1.Get())
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M2Bot/Base")
await app_utils.update_app_async(steps=60)
print("Q-REST=", _q(robot).tolist())
at1.Set(30.0)
print("V1=", at1.Get())
for i in range(4):
    await app_utils.update_app_async(steps=30)
    print("Q%d=" % ((i + 1) * 30,), _q(robot).tolist())
omni.timeline.get_timeline_interface().pause()
