"""Probe (runs INSIDE Isaac Sim): Jacobian API shape on the M1 arm."""
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.core.experimental.prims import Articulation

stage = omni.usd.get_context().get_stage()
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M1Bot/Base")
await app_utils.update_app_async(steps=5)
print("DOFNAMES=", robot.dof_names)
print("NDOF=", robot.num_dofs if hasattr(robot, "num_dofs") else "?")
try:
    J = robot.get_jacobian_matrices()
    print("JTYPE=", type(J))
    Jn = J.numpy() if isinstance(J, wp.array) else np.asarray(J)
    print("JSHAPE=", Jn.shape)
    print("J0=", np.asarray(Jn).reshape(-1)[:24].tolist())
except Exception as e:
    print("JAC-ERR=", repr(e))
try:
    print("LINKNAMES=", robot.link_names)
except Exception as e:
    print("LINKNAMES-ERR=", repr(e))
q = robot.get_dof_positions()
print("QTYPE=", type(q))
print("QVAL=", q.numpy().tolist() if hasattr(q, "numpy") else q)
