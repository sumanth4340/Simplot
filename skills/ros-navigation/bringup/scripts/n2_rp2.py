# N2 render-product probe (INSIDE Isaac Sim, STOPPED): does
# LidarSensor create a product? What does rep.create.render_product
# return for a lidar path?
import inspect

import omni.replicator.core as rep
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor
import omni.usd
from pxr import UsdRender

print("RP-SIG", inspect.signature(rep.create.render_product))
st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2Rp2").IsValid():
    st.RemovePrim("/N2Rp2")


def prods(tag):
    ps = [str(p.GetPath()) for p in st.Traverse()
          if p.IsA(UsdRender.Product)
          and "ViewportTexture" not in str(p.GetPath())
          and str(p.GetPath()) != "/Render/OmniverseKit/HydraTextures/Replicator"]
    print(tag, ps)


lidar = Lidar.create(path="/N2Rp2", config="Example_Rotary_2D",
                     tick_rate=10.0)
prods("AFTER-CREATE")
sensor = LidarSensor("/N2Rp2")
prods("AFTER-SENSOR")
rp = rep.create.render_product("/N2Rp2", (64, 1))
print("RP-RET", repr(rp)[:200])
prods("AFTER-REP-CREATE")
st.RemovePrim("/N2Rp2")
print("RP2 done")
