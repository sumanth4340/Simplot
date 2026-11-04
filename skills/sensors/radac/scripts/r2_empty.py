# R2 empty (INSIDE Isaac Sim): remove targets, capture echo energy.
# Liveness check: no targets -> echo energy must collapse vs the
# 4380 peak with targets. Restores nothing (rebuild after).
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.sensors.experimental.rtx import (
    Acoustic, AcousticSensor, parse_generic_model_output_data)

st = omni.usd.get_context().get_stage()
for p in ("/World/R2T0", "/World/R2T1", "/World/R2T2"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)
print("TARGETS-REMOVED")

E = []
N = []


class R2EmptyW(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        for _n, rp in data.get("renderProducts", {}).items():
            raw = rp.get("GenericModelOutput")
            if isinstance(raw, dict):
                raw = raw.get("data")
            g = parse_generic_model_output_data(raw)
            n = int(g.numElements)
            N.append(n)
            if n > 0:
                sc = np.abs(np.asarray(g.scalar[:n]).ravel())
                E.append((float(sc.max()), float(sc.mean())))


try:
    rep.WriterRegistry.register(R2EmptyW)
except Exception as e:
    print("REG-NOTE", repr(e)[:80])
sensor = AcousticSensor(Acoustic("/World/R2Acous"),
                        annotators=["generic-model-output"])
sensor.attach_writer("R2EmptyW")
app_utils.play()
await app_utils.update_app_async(steps=40)
app_utils.stop()
mx = [e[0] for e in E]
mn = [e[1] for e in E]
print("EMPTY FRAMES=%d NONEMPTY=%d" % (len(N), sum(1 for v in N if v > 0)))
print("EMPTY smax: max=%.2f mean=%.2f" % (max(mx), sum(mx) / len(mx)))
print("EMPTY smean: max=%.4f mean=%.4f" % (max(mn), sum(mn) / len(mn)))
print("R2-EMPTY done")
