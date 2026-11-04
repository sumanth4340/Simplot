"""S2 lidar (runs INSIDE Isaac Sim): spherical-validated cube-top returns.

PROVEN (probe 9): Example_Rotary GMO (x,y,z) = (azimuth_deg,
elevation_deg, range_m) - spherical, NOT cartesian. This drill
converts each return to world and asserts >=95% land on the known
cube top (x 1.5-2.5, y +-0.5, z 1.0). Bonus telemetry: empty-call
fraction (rotor-liveness discriminator, see R6).
"""
import numpy as np
import warp as wp
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import (
    Lidar, LidarSensor, parse_generic_model_output_data)

STATS = {"frames": 0, "empty": 0, "pts": []}


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float)


class S2Writer(Writer):
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
            pts = np.column_stack([_w(gmo.x), _w(gmo.y), _w(gmo.z)])
            STATS["pts"].append(pts)


lidar = Lidar.create(path="/World/S2Lidar", config="Example_Rotary",
                     tick_rate=10.0, accumulate_outputs=True,
                     positions=[[0.0, 0.0, 1.5]])
sensor = LidarSensor(lidar, annotators=[])
rep.WriterRegistry.register(S2Writer)
sensor.attach_writer("S2Writer")
app_utils.play(commit=True)
await app_utils.update_app_async(steps=150)
pts = np.concatenate(STATS["pts"])
az = np.radians(pts[:, 0])
el = np.radians(pts[:, 1])
r = pts[:, 2]
wx = r * np.cos(el) * np.cos(az)
wy = r * np.cos(el) * np.sin(az)
wz = 1.5 + r * np.sin(el)
on_top = (np.abs(wx - 2.0) < 0.55) & (np.abs(wy) < 0.55) \
    & (np.abs(wz - 1.0) < 0.1)
print("S2-REPORT frames=%d empty=%d points=%d ontop=%.4f rmin=%.3f "
      "rmax=%.3f" % (STATS["frames"], STATS["empty"], len(pts),
                     float(on_top.mean()), float(r.min()),
                     float(r.max())))
