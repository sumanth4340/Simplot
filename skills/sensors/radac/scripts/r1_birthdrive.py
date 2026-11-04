# R1 birthdrive (INSIDE Isaac Sim): wrap the at-birth prim + count.
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import (
    Radar, RadarSensor, parse_generic_model_output_data)

N = []


class R1BirthW(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        for _n, rp in data.get("renderProducts", {}).items():
            raw = rp.get("GenericModelOutput")
            if isinstance(raw, dict):
                raw = raw.get("data")
            N.append(int(parse_generic_model_output_data(raw).numElements))


try:
    rep.WriterRegistry.register(R1BirthW)
except Exception as e:
    print("REG-NOTE", repr(e)[:80])
sensor = RadarSensor(Radar("/World/R1Birth/sensor"),
                     annotators=["generic-model-output"])
sensor.attach_writer("R1BirthW")
app_utils.play()
await app_utils.update_app_async(steps=40)
app_utils.stop()
print("BIRTH FRAMES=%d NONEMPTY=%d MAXN=%d" % (
    len(N), sum(1 for v in N if v > 0), max(N) if N else 0))
print("R1-BIRTHDRIVE done")
