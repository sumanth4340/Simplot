import isaacsim.core.experimental.utils.app as app_utils
import asyncio
import numpy as np
import omni.graph.core as og
from isaacsim.core.experimental.prims import Articulation


def snap(tag):
    rd = list(og.Controller.attribute(
        "/ROS2/R2/RD.outputs:jointPositions").get())
    a = Articulation("/World/R2Bot")
    p = np.asarray(a.get_dof_positions()).flatten().tolist()
    print("%s wrap=%s rd=%s" % (tag, p, rd))


app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=60)
snap("P60")
await asyncio.sleep(3)
snap("IDLE")
app_utils.stop()
print("CTL-DONE")
