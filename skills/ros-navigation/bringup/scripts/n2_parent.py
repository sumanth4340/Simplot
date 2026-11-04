# N2 parent test (INSIDE Isaac Sim): same 2D lidar authored at
# the ARTICULATION ROOT (non-rigid parent) instead of the chassis
# rigid body. Writer, handles alive. Box walls still on stage.
import numpy as np
import warp as wp
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import (
    Lidar, LidarSensor, parse_generic_model_output_data)
import omni.usd

STATS = {"frames": 0, "empty": 0, "pts": []}


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float)


class MWriter(Writer):
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
            STATS["pts"].append(np.column_stack(
                [_w(gmo.x), _w(gmo.y), _w(gmo.z)]))


st = omni.usd.get_context().get_stage()
arts = [c.GetName() for c in st.GetPrimAtPath("/World").GetChildren()
        if c.GetName().startswith("N1Base")]
ART = "/World/" + max(arts, key=lambda n: int(n.split("_")[-1]))
LP = ART + "/lidarRoot"
if st.GetPrimAtPath(LP).IsValid():
    st.RemovePrim(LP)
lidar = Lidar.create(path=LP, config="Example_Rotary_2D",
                     tick_rate=10.0, accumulate_outputs=True,
                     positions=[[0.0, 0.0, 0.515]])
sensor = LidarSensor(lidar, annotators=[])
rep.WriterRegistry.register(MWriter)
sensor.attach_writer("MWriter")
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=150)
app_utils.stop()
if STATS["pts"]:
    pts = np.concatenate(STATS["pts"])
    print("ROOT-REPORT frames=%d empty=%d points=%d rmin=%.3f "
          "rmax=%.3f" % (STATS["frames"], STATS["empty"], len(pts),
                         float(pts[:, 2].min()),
                         float(pts[:, 2].max())))
else:
    print("ROOT-REPORT frames=%d empty=%d points=0"
          % (STATS["frames"], STATS["empty"]))
print("ROOT done")
