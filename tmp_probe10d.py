"""Probe 10d (runs INSIDE Isaac Sim): disable sleep, re-send targets."""
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
try:
    print("SLEEP-TH=", robot.get_sleep_thresholds())
except Exception as e:
    print("SLEEP-TH-ERR=", repr(e)[:200])
app_utils.play()
await app_utils.update_app_async(steps=5)
try:
    robot.set_sleep_thresholds(np.array([[0.0]]))
    print("SLEEP-SET-OK")
except Exception as e:
    print("SLEEP-SET-ERR=", repr(e)[:200])
robot.set_dof_position_targets(np.array([[0.5, 0.0]]))
for i in range(3):
    await app_utils.update_app_async(steps=30)
    print("W%d=" % ((i + 1) * 30,), _q(robot).tolist())
omni.timeline.get_timeline_interface().pause()
