"""N2 writer isolation (runs INSIDE Isaac Sim): attach the
RtxLidarROS2PublishLaserScan writer DIRECTLY (no HELP node) to a
static 2D lidar product and latch play. External /scan listener
validates concurrently."""
import isaacsim.core.experimental.utils.app as app_utils
import omni.replicator.core as rep
import omni.usd
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2W").IsValid():
    st.RemovePrim("/N2W")

lidar = Lidar.create(path="/N2W", config="Example_Rotary_2D",
                     tick_rate=10.0, accumulate_outputs=True,
                     positions=[[0.0, 0.0, 0.515]])
sensor = LidarSensor("/N2W")
print("W-SENSOR-OK")

writer = rep.writers.get("RtxLidarROS2PublishLaserScan")
print("W-GET", type(writer))
writer.initialize(topicName="scan", frameId="base_scan",
                  queueSize=10)
print("W-INIT-OK")

from pxr import UsdRender
prods = sorted(str(p.GetPath()) for p in st.Traverse()
               if p.IsA(UsdRender.Product)
               and "rtx_sensor_" in str(p.GetPath()))
RP = prods[-1]
print("W-RP", RP)
writer.attach([RP])
print("W-ATTACH-OK")

app_utils.play()
await app_utils.update_app_async(steps=30)
print("N2W-PLAYING (latched, no stop)")
