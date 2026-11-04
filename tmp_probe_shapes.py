"""Probe 8 (runs INSIDE Isaac Sim): view buffer shapes + index map."""
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation

app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M2Bot/Base")
await app_utils.update_app_async(steps=10)
print("NUMDOFS=", robot.num_dofs, "DOFNAMES=", robot.dof_names)
for name in ("get_dof_positions", "get_dof_position_targets",
             "get_dof_velocities"):
    try:
        v = getattr(robot, name)()
        n = v.numpy() if isinstance(v, wp.array) else np.asarray(v)
        print(name, "shape=", np.asarray(n).shape,
              "row0=", np.asarray(n)[0].tolist())
    except Exception as e:
        print(name, "ERR=", repr(e)[:200])
g = robot.get_dof_gains()
if isinstance(g, (tuple, list)):
    for i, x in enumerate(g):
        n = x.numpy() if isinstance(x, wp.array) else np.asarray(x)
        print("GAIN%d shape=" % i, np.asarray(n).shape,
              "row0=", np.asarray(n)[0].tolist())
else:
    n = g.numpy() if isinstance(g, wp.array) else np.asarray(g)
    print("GAINS shape=", np.asarray(n).shape)
try:
    robot.set_dof_position_targets(np.array([[0.1, 0.1]]),
                                   dof_indices=np.array([6, 7]))
    print("IDX67=accepted")
except Exception as e:
    print("IDX67-ERR=", repr(e)[:300])
omni.timeline.get_timeline_interface().pause()
