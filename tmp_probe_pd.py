"""Probe 5 (runs INSIDE Isaac Sim): tensor gains? teleport? tracked PD?"""
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


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float).tolist()


app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M2Bot/Base")
await app_utils.update_app_async(steps=10)
print("GAINS0=", _w(robot.get_dof_gains()))
print("MAXEFF0=", _w(robot.get_dof_max_efforts()))
print("TG0=", _w(robot.get_dof_position_targets()))
robot.set_dof_positions(np.array([[0.2, -0.1]]),
                        dof_indices=np.array([0, 1]))
await app_utils.update_app_async(steps=2)
print("Q-PORT=", _q(robot).tolist())
robot.set_dof_gains(np.array([[50000.0, 50000.0]]),
                    np.array([[5000.0, 5000.0]]),
                    dof_indices=np.array([0, 1]))
robot.set_dof_max_efforts(np.array([[1000.0, 1000.0]]),
                          dof_indices=np.array([0, 1]))
robot.set_dof_position_targets(np.array([[0.3, 0.1]]),
                               dof_indices=np.array([0, 1]))
for i in range(4):
    await app_utils.update_app_async(steps=30)
    print("Q%d=" % ((i + 1) * 30,), _q(robot).tolist())
omni.timeline.get_timeline_interface().pause()
