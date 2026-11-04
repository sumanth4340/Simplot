# R1 probe (INSIDE Isaac Sim): live Radar/RadarSensor signatures +
# motion-BVH setting state.
import inspect
import carb
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor

print("Radar.__init__:", inspect.signature(Radar.__init__))
print("RadarSensor.__init__:", inspect.signature(RadarSensor.__init__))
s = carb.settings.get_settings()
print("motion-bvh:", s.get("/renderer/raytracingMotion/enabled"))
print("R1-PROBE done")
