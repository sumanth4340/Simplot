# R1 force (INSIDE Isaac Sim): force a detection via debug attrs.
# Isolates dead-pipeline vs aiming/threshold.
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.sensors.experimental.rtx import (
    Radar, RadarSensor, parse_generic_model_output_data)

st = omni.usd.get_context().get_stage()
pr = st.GetPrimAtPath("/World/R1Radar")
pr.GetAttribute("omni:sensor:WpmDmat:scan:s001:debugForceDetection").Set(True)
pr.GetAttribute("omni:sensor:WpmDmat:scan:s001:debugForceRange").Set(20.0)
pr.GetAttribute("omni:sensor:WpmDmat:scan:s001:debugForceAz").Set(0.0)
pr.GetAttribute("omni:sensor:WpmDmat:scan:s001:debugForceEl").Set(0.0)
print("FORCE-SET")

N = []


class R1ForceWriter(Writer):
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
            if int(g.numElements) > 0 and len(N) <= 3:
                print("DET n=%d x=%s y=%s z=%s" % (
                    int(g.numElements),
                    float(np.asarray(g.x).ravel()[0]),
                    float(np.asarray(g.y).ravel()[0]),
                    float(np.asarray(g.z).ravel()[0])))


try:
    rep.WriterRegistry.register(R1ForceWriter)
except Exception as e:
    print("REG-NOTE", repr(e)[:100])
sensor = RadarSensor(Radar("/World/R1Radar"),
                     annotators=["generic-model-output"])
sensor.attach_writer("R1ForceWriter")
app_utils.play()
await app_utils.update_app_async(steps=60)
app_utils.stop()
print("FRAMES=%d NONEMPTY=%d" % (len(N), sum(1 for v in N if v > 0)))
print("R1-FORCE done")
