"""Probe 9 (runs INSIDE Isaac Sim): clean per-DOF tracking, explicit gains.

Runs alone after a stopped-timeline build. Commands dof0 then dof1
separately with explicit tensor gains; traces q.
"""
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
g = robot.get_dof_gains()
gk = g[0].numpy() if isinstance(g[0], wp.array) else np.asarray(g[0])
gd = g[1].numpy() if isinstance(g[1], wp.array) else np.asarray(g[1])
print("GAINS=", np.asarray(gk).tolist(), np.asarray(gd).tolist())
robot.set_dof_gains(np.array([[50000.0, 50000.0]]),
                    np.array([[5000.0, 5000.0]]))
robot.set_dof_position_targets(np.array([[0.3]]),
                               dof_indices=np.array([0]))
for i in range(3):
    await app_utils.update_app_async(steps=30)
    print("D0-%d=" % ((i + 1) * 30,), _q(robot).tolist())
robot.set_dof_position_targets(np.array([[0.0, 0.25]]))
for i in range(3):
    await app_utils.update_app_async(steps=30)
    print("D1-%d=" % ((i + 1) * 30,), _q(robot).tolist())
omni.timeline.get_timeline_interface().pause()
