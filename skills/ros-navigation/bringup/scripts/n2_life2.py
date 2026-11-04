# N2 lifecycle-2 probe (INSIDE Isaac Sim): full birth->play->stop
# trace of the LidarSensor auto product.
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor
import omni.usd
from pxr import UsdRender

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2Life2").IsValid():
    st.RemovePrim("/N2Life2")


def prods(tag):
    ps = sorted(str(p.GetPath()) for p in st.Traverse()
                if p.IsA(UsdRender.Product)
                and "ViewportTexture" not in str(p.GetPath()))
    print(tag, ps, flush=True)


prods("PRE")
lidar = Lidar.create(path="/N2Life2", config="Example_Rotary_2D",
                     tick_rate=10.0)
prods("POST-CREATE")
sensor = LidarSensor("/N2Life2")
prods("POST-SENSOR")
app_utils.play()
await app_utils.update_app_async(steps=2)
prods("PLAY-2")
await app_utils.update_app_async(steps=10)
prods("PLAY-12")
app_utils.stop()
await app_utils.update_app_async(steps=2)
prods("STOPPED")
app_utils.play()
await app_utils.update_app_async(steps=5)
prods("REPLAY-5")
app_utils.stop()
st.RemovePrim("/N2Life2")
prods("CLEANED")
print("LIFE2 done")
