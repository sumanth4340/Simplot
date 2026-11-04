# R1 birth (INSIDE Isaac Sim): TI create + sensor AT BIRTH in one
# script (exact exec-279 sequence), on a scratch path.
import numpy as np
import omni.usd
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/World/R1Birth").IsValid():
    st.RemovePrim("/World/R1Birth")
radar = Radar.create("/World/R1Birth", config="IWRL6432AOP",
                     translations=np.array([0.0, -2.0, 1.0]),
                     aux_output_level="BASIC")
sensor = RadarSensor(radar, annotators=["generic-model-output"])
print("BIRTH:", radar.paths[0])
print("R1-BIRTH done")
