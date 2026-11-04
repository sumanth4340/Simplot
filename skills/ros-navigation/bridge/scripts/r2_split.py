import isaacsim.core.experimental.utils.app as app_utils
import asyncio
import numpy as np
import omni.usd
from isaacsim.core.experimental.prims import Articulation


def snap(tag):
    import omni.graph.core as og
    rd = og.Controller.attribute(
        "/ROS2/R2/RD.outputs:jointPositions").get()
    tm = og.Controller.attribute(
        "/ROS2/R2/Time.outputs:simulationTime").get()
    a = Articulation("/World/R2Bot")
    p = np.asarray(a.get_dof_positions()).flatten().tolist()
    print("%s wrap=%s rd=%s t=%s" % (tag, p, list(rd), tm))


app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=10)
Articulation("/World/R2Bot").set_dof_velocity_targets(
    np.array([[1.0, 0.0]]))
snap("P10")
await app_utils.update_app_async(steps=50)
snap("P60")
await asyncio.sleep(4)
snap("IDLE")
app_utils.stop()
print("SPLIT-DONE")
