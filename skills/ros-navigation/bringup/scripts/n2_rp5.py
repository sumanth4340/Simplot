# N2 auto-product probe (INSIDE Isaac Sim): raw-writer attach to
# the LidarSensor AUTO product (handles alive). Distinguishes
# "named products unfed" from "raw attach broken".
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import (
    Lidar, LidarSensor, parse_generic_model_output_data)
import omni.usd
from pxr import UsdRender

STATS = {"frames": 0, "empty": 0, "n": 0}


class CountWriter(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        if "renderProducts" not in data:
            return
        for _rp, rp_data in data["renderProducts"].items():
            raw = rp_data.get("GenericModelOutput")
            if isinstance(raw, dict):
                raw = raw.get("data")
            if raw is None:
                continue
            gmo = parse_generic_model_output_data(raw)
            n = int(gmo.numElements)
            if n <= 0:
                STATS["empty"] += 1
                continue
            STATS["frames"] += 1
            STATS["n"] += n


st = omni.usd.get_context().get_stage()
for p in [x for x in st.Traverse() if x.IsA(UsdRender.Product)]:
    if "N2ScanProbe" in str(p.GetPath()):
        st.RemovePrim(p.GetPath())
if st.GetPrimAtPath("/N2Rp5").IsValid():
    st.RemovePrim("/N2Rp5")

lidar = Lidar.create(path="/N2Rp5", config="Example_Rotary_2D",
                     tick_rate=10.0)
sensor = LidarSensor("/N2Rp5")
auto = sorted(str(p.GetPath()) for p in st.Traverse()
              if p.IsA(UsdRender.Product)
              and "rtx_sensor_" in str(p.GetPath()))
print("AUTO", auto)
rep.WriterRegistry.register(CountWriter)
w = rep.WriterRegistry.get("CountWriter")
w.attach(auto)
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=120)
app_utils.stop()
print("RP5-REPORT frames=%d empty=%d points=%d"
      % (STATS["frames"], STATS["empty"], STATS["n"]))
print("KEEPALIVE", type(sensor), type(lidar))
print("RP5 done")
