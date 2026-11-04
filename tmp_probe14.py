"""Probe 14 (runs INSIDE Isaac Sim): do efforts reach the solver?"""
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


def _qd(robot):
    v = robot.get_dof_velocities()
    v = v.numpy() if isinstance(v, wp.array) else np.asarray(v)
    return np.asarray(v, dtype=float).flatten()


robot = Articulation("/World/M2Bot/Base")
print("R0=", _q(robot).tolist())
app_utils.play()
await app_utils.update_app_async(steps=5)
robot.set_dof_efforts(np.array([[2.0, 0.0]]))
for i in range(4):
    await app_utils.update_app_async(steps=15)
    print("E%d q=" % ((i + 1) * 15,), _q(robot).tolist(),
          "qd=", np.round(_qd(robot), 4).tolist())
omni.timeline.get_timeline_interface().pause()
