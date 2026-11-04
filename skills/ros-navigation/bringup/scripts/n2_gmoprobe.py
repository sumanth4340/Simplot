# N2 GMO probe (INSIDE Isaac Sim): does the mounted lidar emit
# render-product data at all? Attaches a counting GMO writer to the
# mount's rtx_sensor_* product, plays 120 steps, reports.
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import (
    parse_generic_model_output_data)
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
rps = sorted(str(p.GetPath()) for p in st.Traverse()
             if p.IsA(UsdRender.Product)
             and "rtx_sensor_" in str(p.GetPath()))
print("GMO-RPS", rps)
arts = [c.GetName() for c in st.GetPrimAtPath("/World").GetChildren()
        if c.GetName().startswith("N1Base")]
ART = "/World/" + arts[-1]
print("GMO-ART", ART, "LIDAR",
      st.GetPrimAtPath(ART + "/chassis/lidar").IsValid())
rep.WriterRegistry.register(CountWriter)
w = rep.WriterRegistry.get("CountWriter")
w.attach(rps)
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=120)
app_utils.stop()
print("GMO-REPORT frames=%d empty=%d points=%d"
      % (STATS["frames"], STATS["empty"], STATS["n"]))
print("GMO done")
