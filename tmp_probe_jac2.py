"""Probe 2 (runs INSIDE Isaac Sim): Jacobian rows + target units."""
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.experimental.utils import xform as xform_utils


def _vec(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return [float(v) for v in np.asarray(a).flatten()]


stage = omni.usd.get_context().get_stage()
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M1Bot/Base")
await app_utils.update_app_async(steps=5)
J = robot.get_jacobian_matrices()
Jn = J.numpy() if isinstance(J, wp.array) else np.asarray(J)
Jn = np.asarray(Jn)
print("JLINK2=", Jn[0, 2, :, 6:8].tolist())
print("JLINK1=", Jn[0, 1, :, 6:8].tolist())
lp, _ = xform_utils.get_world_pose("/World/M1Bot/Link2")
sp, _ = xform_utils.get_world_pose("/World/M1Bot/Link2/GraspSite")
print("LINKPOS=", _vec(lp), "SITEPOS=", _vec(sp))
robot.set_dof_position_targets(np.array([[0.5, 0.0]]),
                               dof_indices=np.array([0, 1]))
await app_utils.update_app_async(steps=120)
q = robot.get_dof_positions()
qn = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
print("QAFTER=", np.asarray(qn).tolist())
omni.timeline.get_timeline_interface().pause()
