"""R2 pump chunk (runs INSIDE Isaac Sim, assumes PLAYING).

Pumps 40 steps so physics+OG keep evaluating while the system-ROS
listener collects. Prints the live DOF pose as motion evidence.
"""
import isaacsim.core.experimental.utils.app as app_utils
import numpy as np
from isaacsim.core.experimental.prims import Articulation

ART = None
import omni.usd as _usd
_st = _usd.get_context().get_stage()
for _c in _st.GetPrimAtPath("/World").GetChildren():
    if _c.GetName().startswith("R2Bot"):
        ART = _c.GetPath().pathString
        break

await app_utils.update_app_async(steps=40)
_a = Articulation(ART)
_p = np.asarray(_a.get_dof_positions()).flatten().tolist()
print("PUMP40 pose=%s" % _p)
