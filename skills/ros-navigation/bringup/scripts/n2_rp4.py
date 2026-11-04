# N2 named-product probe (INSIDE Isaac Sim): explicit named render
# product for a lidar, handles dropped + gc, then GMO-count while
# playing. Tests handle-independent scan dataflow.
import gc

import numpy as np
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
if st.GetPrimAtPath("/N2Rp3").IsValid():
    st.RemovePrim("/N2Rp3")

lidar = Lidar.create(path="/N2Rp3", config="Example_Rotary_2D",
                     tick_rate=10.0)
sensor = LidarSensor("/N2Rp3")
rp_obj = rep.create.render_product("/N2Rp3", (64, 1), name="N2ScanProbe")
print("RP-OBJ", type(rp_obj), repr(rp_obj)[:160])
try:
    print("RP-PATH-ATTR", rp_obj.path)
except Exception as e:
    print("RP-PATH-ERR", repr(e)[:120])
# NOTE: handles KEPT alive for this variant.
print("KEEPALIVE", type(sensor), type(lidar))


def prods(tag):
    ps = sorted(str(p.GetPath()) for p in st.Traverse()
                if p.IsA(UsdRender.Product)
                and "ViewportTexture" not in str(p.GetPath()))
    print(tag, ps)


prods("POST-GC")
named = [p for p in st.Traverse()
         if p.IsA(UsdRender.Product) and "N2ScanProbe" in str(p.GetPath())]
print("NAMED", [str(p.GetPath()) for p in named])
rep.WriterRegistry.register(CountWriter)
w = rep.WriterRegistry.get("CountWriter")
w.attach([str(named[0].GetPath())] if named else [])
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=120)
app_utils.stop()
print("RP3-REPORT frames=%d empty=%d points=%d"
      % (STATS["frames"], STATS["empty"], STATS["n"]))
prods("POST-PLAY")
st.RemovePrim("/N2Rp3")
print("RP3 done")
