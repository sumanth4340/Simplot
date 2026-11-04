"""Probe 7 (runs INSIDE Isaac Sim): Hinge1 isolated sign/dead test."""
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
h1 = stage.GetPrimAtPath("/World/M2Bot/Hinge1")
print("H1AXIS=", h1.GetAttribute("physics:axis").Get())
print("H1LOW=", h1.GetAttribute("physics:lowerLimit").Get(),
      "H1UP=", h1.GetAttribute("physics:upperLimit").Get())
print("H1STIFF=", h1.GetAttribute("drive:angular:physics:stiffness").Get(),
      "H1TARG=", h1.GetAttribute(
          "drive:angular:physics:targetPosition").Get())
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M2Bot/Base")
await app_utils.update_app_async(steps=60)
print("Q-REST=", _q(robot).tolist())
robot.set_dof_position_targets(np.array([[0.3]]),
                               dof_indices=np.array([0]))
for i in range(3):
    await app_utils.update_app_async(steps=30)
    print("QP%d=" % ((i + 1) * 30,), _q(robot).tolist())
robot.set_dof_position_targets(np.array([[-0.3]]),
                               dof_indices=np.array([0]))
for i in range(3):
    await app_utils.update_app_async(steps=30)
    print("QN%d=" % ((i + 1) * 30,), _q(robot).tolist())
omni.timeline.get_timeline_interface().pause()
