# R1 xcheck (INSIDE Isaac Sim): does LIDAR GMO work on this sim?
# If yes -> radar-specific fault. If no -> session/environmental.
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import (
    Lidar, LidarSensor, parse_generic_model_output_data)

st = omni.usd.get_context().get_stage()
for p in ("/World/R1XCube", "/World/R1XLidar"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)
Cube("/World/R1XCube", positions=np.array([5.0, 0.0, 0.0]),
     scales=np.array([2.0, 2.0, 2.0]))
lidar = Lidar.create("/World/R1XLidar", config="Example_Rotary_2D")
sensor = LidarSensor(lidar, annotators=["generic-model-output"])
print("LIDAR-CREATED")

N = []


class R1XWriter(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        for _n, rp in data.get("renderProducts", {}).items():
            raw = rp.get("GenericModelOutput")
            if isinstance(raw, dict):
                raw = raw.get("data")
            g = parse_generic_model_output_data(raw)
            N.append(int(g.numElements))


try:
    rep.WriterRegistry.register(R1XWriter)
except Exception as e:
    print("REG-NOTE", repr(e)[:100])
sensor.attach_writer("R1XWriter")
app_utils.play()
await app_utils.update_app_async(steps=60)
app_utils.stop()
print("LIDAR FRAMES=%d NONEMPTY=%d MAXN=%d" % (
    len(N), sum(1 for v in N if v > 0), max(N) if N else 0))
print("R1-XCHECK done")
