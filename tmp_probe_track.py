"""Probe 3 (runs INSIDE Isaac Sim): do tensor targets track?"""
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
await app_utils.update_app_async(steps=10)
print("Q0=", _q(robot).tolist())
robot.set_dof_position_targets(np.array([[0.3, 0.1]]),
                               dof_indices=np.array([0, 1]))
for i in range(6):
    await app_utils.update_app_async(steps=20)
    print("Q%d=" % ((i + 1) * 20,), _q(robot).tolist())
try:
    tg = robot.get_dof_position_targets()
    tgn = tg.numpy() if isinstance(tg, wp.array) else np.asarray(tg)
    print("TGREAD=", np.asarray(tgn).tolist())
except Exception as e:
    print("TGREAD-ERR=", repr(e))
omni.timeline.get_timeline_interface().pause()
