"""Probe 6 (runs INSIDE Isaac Sim): tensor tracking on v3 clearance arm."""
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


app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M2Bot/Base")
await app_utils.update_app_async(steps=60)
print("Q-REST=", _q(robot).tolist())
robot.set_dof_position_targets(np.array([[0.3, 0.2]]),
                               dof_indices=np.array([0, 1]))
for i in range(4):
    await app_utils.update_app_async(steps=30)
    print("Q%d=" % ((i + 1) * 30,), _q(robot).tolist())
omni.timeline.get_timeline_interface().pause()
