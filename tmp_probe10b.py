"""Probe 10b (runs INSIDE Isaac Sim): re-read q, no new commands."""
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


robot = Articulation("/World/M2Bot/Base")
print("R0=", _q(robot).tolist())
app_utils.play()
await app_utils.update_app_async(steps=90)
print("R90=", _q(robot).tolist())
await app_utils.update_app_async(steps=90)
print("R180=", _q(robot).tolist())
t = robot.get_dof_position_targets()
t = t.numpy() if isinstance(t, wp.array) else np.asarray(t)
print("TG=", np.asarray(t).tolist())
omni.timeline.get_timeline_interface().pause()
