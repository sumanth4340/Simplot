# R1 ti (INSIDE Isaac Sim): vendor-config radar detection test.
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.sensors.experimental.rtx import (
    Radar, RadarSensor, parse_generic_model_output_data)

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/World/R1RadarTI").IsValid():
    st.RemovePrim("/World/R1RadarTI")
radar = Radar.create("/World/R1RadarTI", config="IWRL6432AOP",
                     translations=np.array([0.0, 0.0, 1.0]),
                     attributes={"omni:sensor:WpmDmat:outputFrameOfReference":
                                 "WORLD"},
                     aux_output_level="BASIC")
print("TI-CREATED", radar.prims[0].GetTypeName())

N = []


class R1TIWriter(Writer):
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
            if int(g.numElements) > 0 and sum(N) <= 3 * int(g.numElements):
                a = np.asarray(g.x).ravel()
                e = np.asarray(g.y).ravel()
                r = np.asarray(g.z).ravel()
                print("DET n=%d az0=%.2f el0=%.2f r0=%.2f" % (
                    int(g.numElements), float(a[0]), float(e[0]),
                    float(r[0])))


try:
    rep.WriterRegistry.register(R1TIWriter)
except Exception as e:
    print("REG-NOTE", repr(e)[:100])
sensor = RadarSensor(radar, annotators=["generic-model-output"])
sensor.attach_writer("R1TIWriter")
app_utils.play()
await app_utils.update_app_async(steps=90)
app_utils.stop()
print("TI FRAMES=%d NONEMPTY=%d MAXN=%d" % (
    len(N), sum(1 for v in N if v > 0), max(N) if N else 0))
print("R1-TI done")
