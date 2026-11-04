# R1 diag2 (INSIDE Isaac Sim): do rep writers need orchestrator steps?
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor

HITS = []


class R1DiagWriter2(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        HITS.append(1)


try:
    rep.WriterRegistry.register(R1DiagWriter2)
except Exception as e:
    print("REG-NOTE", repr(e)[:100])
radar = Radar("/World/R1Radar")
sensor = RadarSensor(radar, annotators=[])
rp = sensor.render_product if hasattr(sensor, "render_product") else None
print("rp:", rp.GetPath() if rp is not None else "?")
sensor.attach_writer("R1DiagWriter2")
app_utils.play()
await app_utils.update_app_async(steps=10)
print("hits-app10:", len(HITS))
for i in range(10):
    await rep.orchestrator.step_async()
print("hits-orch10:", len(HITS))
await app_utils.update_app_async(steps=20)
print("hits-app30:", len(HITS))
app_utils.stop()
print("R1-DIAG2 done")
