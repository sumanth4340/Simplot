"""Probe 16 (runs INSIDE Isaac Sim): static track on no-sleep arm."""
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
omni.timeline.get_timeline_interface().set_current_time(0.0)
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M2Bot/Base")
await app_utils.update_app_async(steps=60)
print("Q-REST=", _q(robot).tolist())
robot.set_dof_gains(np.array([[100000.0, 100000.0]]),
                    np.array([[10000.0, 10000.0]]))
robot.set_dof_position_targets(np.array([[0.5, 0.0]]))
for i in range(4):
    await app_utils.update_app_async(steps=30)
    print("T%d=" % ((i + 1) * 30,), _q(robot).tolist())
omni.timeline.get_timeline_interface().pause()
