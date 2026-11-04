# R1 diag3 (INSIDE Isaac Sim): dump empty-GMO header fields.
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import (
    Radar, RadarSensor, parse_generic_model_output_data)

HDR = []


class R1HdrWriter(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        if HDR:
            return
        for _n, rp in data.get("renderProducts", {}).items():
            raw = rp.get("GenericModelOutput")
            if isinstance(raw, dict):
                raw = raw.get("data")
            g = parse_generic_model_output_data(raw)
            for f in ("numElements", "maxRangeM", "minVelMps",
                      "maxVelMps", "minAzRad", "maxAzRad",
                      "minElRad", "maxElRad", "scanIdx", "cycleCnt",
                      "sensorID"):
                try:
                    HDR.append((f, getattr(g, f, "NA")))
                except Exception as e:
                    HDR.append((f, "ERR %r" % e))
            HDR.append(("dir-fields",
                        sorted([a for a in dir(g) if not a.startswith("_")])))


try:
    rep.WriterRegistry.register(R1HdrWriter)
except Exception as e:
    print("REG-NOTE", repr(e)[:100])
sensor = RadarSensor(Radar("/World/R1Radar"),
                       annotators=["generic-model-output"])
sensor.attach_writer("R1HdrWriter")
app_utils.play()
await app_utils.update_app_async(steps=20)
app_utils.stop()
for f, v in HDR:
    print("HDR %s = %s" % (f, str(v)[:300]))
print("R1-DIAG3 done")
