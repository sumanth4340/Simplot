# R1 mat (INSIDE Isaac Sim): apply radar-reflective nonvisual
# material to the cube, then capture one GMO sample.
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.materials import NonVisualMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import (
    Radar, RadarSensor, parse_generic_model_output_data)

cube = Cube("/World/R1Cube")
mat = NonVisualMaterial("/World/R1Cube/material", bases="aluminum",
                        coatings="paint", attributes="emissive")
cube.apply_visual_materials(mat)
print("MAT-APPLIED")

N = []


class R1MatWriter(Writer):
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
            if int(g.numElements) > 0 and len(N) < 6:
                print("DET n=%d x0=%s y0=%s z0=%s rv0=%s s0=%s" % (
                    int(g.numElements),
                    float(np.asarray(g.x).ravel()[0]),
                    float(np.asarray(g.y).ravel()[0]),
                    float(np.asarray(g.z).ravel()[0]),
                    float(np.asarray(g.rv_ms).ravel()[0]),
                    float(np.asarray(g.scalar).ravel()[0])))


try:
    rep.WriterRegistry.register(R1MatWriter)
except Exception as e:
    print("REG-NOTE", repr(e)[:100])
sensor = RadarSensor(Radar("/World/R1Radar"),
                     annotators=["generic-model-output"])
sensor.attach_writer("R1MatWriter")
app_utils.play()
await app_utils.update_app_async(steps=60)
app_utils.stop()
print("FRAMES=%d NONEMPTY=%d MAXN=%d" % (
    len(N), sum(1 for v in N if v > 0), max(N) if N else 0))
print("R1-MAT done")
