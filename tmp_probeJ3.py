"""Probe J3 (runs INSIDE Isaac Sim): M4v2 Jacobian layout + DLS step 1."""
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
    return np.asarray(a, dtype=float).flatten()


app_utils.stop()
omni.timeline.get_timeline_interface().set_current_time(0.0)
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=30)
robot = Articulation("/World/M4Bot/Root")
print("DOFNAMES=", robot.dof_names, "NUMDOFS=", robot.num_dofs)
print("LINKNAMES=", robot.link_names)
J = robot.get_jacobian_matrices()
Jn = J.numpy() if isinstance(J, wp.array) else np.asarray(J)
Jn = np.asarray(Jn, dtype=float)
print("JSHAPE=", Jn.shape)
nl = Jn.shape[1]
for li in range(nl):
    print("JLINK%d=" % li, Jn[0, li, :, :].tolist())
sp, _ = xform_utils.get_world_pose("/World/M4Bot/Link2/GraspSite")
print("SITE=", _vec(sp).tolist())
omni.timeline.get_timeline_interface().pause()
