# R1 stale (INSIDE Isaac Sim): create a sensor while STOPPED and
# never play it (mirrors the old build), then report. The next drive
# re-wraps the same prim: if silent, an unplayed lingering product
# wedges the prim.
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor

sensor = RadarSensor(Radar("/World/R1Radar/sensor"),
                     annotators=["generic-model-output"])
print("STALE-SENSOR-CREATED")
print("R1-STALE done")
