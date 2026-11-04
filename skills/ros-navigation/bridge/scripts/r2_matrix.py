import isaacsim.core.experimental.utils.app as app_utils
import asyncio
import numpy as np
import omni.graph.core as og
import omni.usd
from isaacsim.core.experimental.prims import Articulation
from pxr import UsdGeom, Gf


def snap(tag):
    st = omni.usd.get_context().get_stage()
    xc = UsdGeom.XformCache()
    m = xc.GetLocalToWorldTransform(st.GetPrimAtPath("/World/R2Bot/link1"))
    ang = Gf.Matrix4d(m).ExtractRotation().GetAngle()
    by = Gf.Matrix4d(m).ExtractTranslation()[1]
    rd = list(og.Controller.attribute(
        "/ROS2/R2/RD.outputs:jointPositions").get())
    a = Articulation("/World/R2Bot")
    p = np.asarray(a.get_dof_positions()).flatten().tolist()
    print("%s wrap=%s rd=%s link1ang=%.4f link1y=%.4f" % (tag, p, rd, ang, by))


app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=10)
Articulation("/World/R2Bot").set_dof_velocity_targets(
    np.array([[1.0, 0.0]]))
snap("P10")
await app_utils.update_app_async(steps=50)
snap("P60")
await asyncio.sleep(3)
snap("IDLE")
app_utils.stop()
print("MATRIX-DONE")
