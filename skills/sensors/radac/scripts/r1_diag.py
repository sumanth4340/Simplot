# R1 diag (INSIDE Isaac Sim): does the radar render product emit?
import carb
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor

print("motion-bvh:",
      carb.settings.get_settings().get("/renderer/raytracingMotion/enabled"))
HITS = []


class R1DiagWriter(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        HITS.append(sorted(data.get("renderProducts", {}).keys()))


try:
    rep.WriterRegistry.register(R1DiagWriter)
except Exception as e:
    print("REG-NOTE", repr(e)[:100])
radar = Radar("/World/R1Radar")
sensor = RadarSensor(radar, annotators=[])
print("rp:", sensor.render_product_path
      if hasattr(sensor, "render_product_path") else "?")
sensor.attach_writer("R1DiagWriter")
app_utils.play()
await app_utils.update_app_async(steps=30)
print("hits30:", len(HITS))
try:
    d = sensor.get_data("generic-model-output")
    print("poll-type:", type(d).__name__,
          "keys:", sorted(d.keys())[:8] if isinstance(d, dict) else "-")
except Exception as e:
    print("poll-err:", repr(e)[:250])
await app_utils.update_app_async(steps=30)
app_utils.stop()
print("hits60:", len(HITS), "first:", HITS[:2])
print("R1-DIAG done")
