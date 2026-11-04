# R1 two (INSIDE Isaac Sim): add a SECOND TI radar prim, report.
import numpy as np
import omni.usd
from isaacsim.sensors.experimental.rtx import Radar

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/World/R1RadarSecond").IsValid():
    st.RemovePrim("/World/R1RadarSecond")
r2 = Radar.create("/World/R1RadarSecond", config="IWRL6432AOP",
                  translations=np.array([0.0, 2.0, 1.0]),
                  aux_output_level="BASIC")
print("SECOND:", r2.paths[0])
print("R1-TWO done")
