"""Probe 10 (runs INSIDE Isaac Sim): slot->joint map, slot0 alone."""
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.experimental.utils import xform as xform_utils


def _q(robot):
    q = robot.get_dof_positions()
    q = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
    return np.asarray(q, dtype=float).flatten()


def _pos(p):
    v, _ = xform_utils.get_world_pose(p)
    if isinstance(v, wp.array):
        v = v.numpy()
    return np.asarray(v, dtype=float).flatten().tolist()


app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M2Bot/Base")
await app_utils.update_app_async(steps=60)
robot.set_dof_gains(np.array([[50000.0, 50000.0]]),
                    np.array([[5000.0, 5000.0]]))
print("REST q=", _q(robot).tolist())
print("REST L1=", _pos("/World/M2Bot/Link1"),
      "L2=", _pos("/World/M2Bot/Link2"))
robot.set_dof_position_targets(np.array([[0.5, 0.0]]))
await app_utils.update_app_async(steps=90)
print("SLOT0 q=", _q(robot).tolist())
print("SLOT0 L1=", _pos("/World/M2Bot/Link1"),
      "L2=", _pos("/World/M2Bot/Link2"))
omni.timeline.get_timeline_interface().pause()
