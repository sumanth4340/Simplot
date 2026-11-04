import isaacsim.core.experimental.utils.app as app_utils
import asyncio
import omni.graph.core as og
import omni.usd
from pxr import UsdGeom, Gf


def snap(tag):
    st = omni.usd.get_context().get_stage()
    xc = UsdGeom.XformCache()
    m = xc.GetLocalToWorldTransform(st.GetPrimAtPath("/World/R2Bot/link1"))
    r = Gf.Matrix4d(m).ExtractRotation()
    axis, ang = r.GetAxis(), r.GetAngle()
    rd = list(og.Controller.attribute(
        "/ROS2/R2/RD.outputs:jointPositions").get())
    print("%s link1ang=%.4f axis=%s rd=%s" % (tag, ang, axis, rd))


app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=60)
snap("P60")
await asyncio.sleep(3)
snap("IDLE")
app_utils.stop()
print("BODY-DONE")
