# R1 scene (INSIDE Isaac Sim): inventory /World + one sensor,
# capture BEFORE/AFTER applying radar material to the cube.
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.core.experimental.materials import NonVisualMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import (
    Radar, RadarSensor, parse_generic_model_output_data)

st = omni.usd.get_context().get_stage()
for c in st.GetPrimAtPath("/World").GetChildren():
    print("WORLD %s (%s)" % (c.GetPath().pathString, c.GetTypeName()))

N = []
SAMP = []


class R1SceneW(Writer):
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
            N.append((PHASE[0], n))
            if n > 0 and len(SAMP) < 4:
                SAMP.append((PHASE[0], np.asarray(g.x).ravel().tolist(),
                             np.asarray(g.y).ravel().tolist(),
                             np.asarray(g.z).ravel().tolist()))


try:
    rep.WriterRegistry.register(R1SceneW)
except Exception as e:
    print("REG-NOTE", repr(e)[:80])
PHASE = ["BEFORE"]
sensor = RadarSensor(Radar("/World/R1Radar/sensor"),
                     annotators=["generic-model-output"])
sensor.attach_writer("R1SceneW")
app_utils.play()
await app_utils.update_app_async(steps=40)
app_utils.stop()
cube = Cube("/World/R1Cube")
mat = NonVisualMaterial("/World/R1Cube/material", bases="aluminum",
                        coatings="paint", attributes="emissive")
cube.apply_visual_materials(mat)
print("MAT-APPLIED")
PHASE[0] = "AFTER"
app_utils.play()
await app_utils.update_app_async(steps=40)
app_utils.stop()
for ph in ("BEFORE", "AFTER"):
    nn = [n for p, n in N if p == ph]
    print("%s FRAMES=%d NONEMPTY=%d MAXN=%d" % (
        ph, len(nn), sum(1 for v in nn if v > 0), max(nn) if nn else 0))
for ph, ax, el, rr in SAMP:
    print("%s n=%d az=%s" % (ph, len(ax), [round(v, 2) for v in ax]))
    print("%s el=%s" % (ph, [round(v, 2) for v in el]))
    print("%s r=%s" % (ph, [round(v, 3) for v in rr]))
print("R1-SCENE done")
