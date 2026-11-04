import numpy as np
import omni.graph.core as og
from isaacsim.core.experimental.prims import Articulation
a = Articulation("/World/R2Bot_1793725978")
p = np.asarray(a.get_dof_positions()).flatten().tolist()
v = np.asarray(a.get_dof_velocities()).flatten().tolist()
tm = og.Controller.attribute(
    "/ROS2/R2/Time.outputs:simulationTime").get()
print("GAP2-B wrap=%s vel=%s t=%s" % (p, v, tm))
import isaacsim.core.experimental.utils.app as app_utils
app_utils.stop()
print("GAP2-STOPPED")
