"""R3 pump chunk (runs INSIDE Isaac Sim, assumes PLAYING)."""
import isaacsim.core.experimental.utils.app as app_utils
import numpy as np
import omni.usd as _usd
from isaacsim.core.experimental.prims import Articulation

ART = None
_st = _usd.get_context().get_stage()
for _c in _st.GetPrimAtPath("/World").GetChildren():
    if _c.GetName().startswith("R3Bot"):
        ART = _c.GetPath().pathString
        break

await app_utils.update_app_async(steps=40)
_a = Articulation(ART)
_p = np.asarray(_a.get_dof_positions()).flatten().tolist()
print("PUMP40 pose=%s" % _p)
