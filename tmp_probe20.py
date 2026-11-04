"""Probe 20 (runs INSIDE Isaac Sim): 40 re-play cycles, fixed target."""
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
tl = omni.timeline.get_timeline_interface()
app_utils.stop()
tl.set_current_time(0.0)
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=30)
robot = Articulation("/World/M2Bot/Base")
print("C0=", np.round(_q(robot), 4).tolist())
for cyc in range(1, 41):
    app_utils.stop()
    for jp, v in (("/World/M2Bot/Hinge1", 28.0),
                  ("/World/M2Bot/Hinge2", 0.0)):
        at = stage.GetPrimAtPath(jp).GetAttribute(
            "drive:angular:physics:targetPosition")
        at.Set(v)
    app_utils.play()
    await app_utils.update_app_async(steps=10)
    robot = Articulation("/World/M2Bot/Base")
    if cyc % 5 == 0 or cyc <= 2:
        print("C%d=" % cyc, np.round(_q(robot), 4).tolist())
tl.pause()
