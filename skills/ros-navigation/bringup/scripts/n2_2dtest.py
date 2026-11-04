# N2 2D-config test (INSIDE Isaac Sim): S2-proven writer pattern
# with Example_Rotary_2D on a static /World prim. Decides whether
# the 2D config emits at all.
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


class T2Writer(Writer):
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
if st.GetPrimAtPath("/N22DTest").IsValid():
    st.RemovePrim("/N22DTest")
lidar = Lidar.create(path="/N22DTest", config="Example_Rotary_2D",
                     tick_rate=10.0, accumulate_outputs=True,
                     positions=[[0.0, 0.0, 0.515]])
sensor = LidarSensor(lidar, annotators=[])
rep.WriterRegistry.register(T2Writer)
sensor.attach_writer("T2Writer")
app_utils.play(commit=True)
await app_utils.update_app_async(steps=150)
if STATS["pts"]:
    pts = np.concatenate(STATS["pts"])
    az = np.radians(pts[:, 0])
    el = np.radians(pts[:, 1])
    r = pts[:, 2]
    wx = r * np.cos(el) * np.cos(az)
    print("T2-REPORT frames=%d empty=%d points=%d "
          "rmin=%.3f rmax=%.3f xface~%.3f"
          % (STATS["frames"], STATS["empty"], len(pts),
             float(r.min()), float(r.max()),
             float(wx[np.argmin(r)])))
else:
    print("T2-REPORT frames=%d empty=%d points=0"
          % (STATS["frames"], STATS["empty"]))
print("T2 done")
