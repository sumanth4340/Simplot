import numpy as np
import omni.graph.core as og
from isaacsim.core.experimental.prims import Articulation
a = Articulation("/World/R2Bot")
p = np.asarray(a.get_dof_positions()).flatten().tolist()
rd = list(og.Controller.attribute(
    "/ROS2/R2/RD.outputs:jointPositions").get())
print("GAP-B wrap=%s rd=%s" % (p, rd))
import isaacsim.core.experimental.utils.app as app_utils
app_utils.stop()
print("GAP-STOPPED")
