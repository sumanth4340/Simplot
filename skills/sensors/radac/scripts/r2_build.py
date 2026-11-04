# R2 build (runs INSIDE Isaac Sim): acoustic array + bare cube
# targets. Mirrors NVIDIA test_acoustic_sensor.py recipe exactly.
# Build authors the prim ONLY (R1/F4: a sensor created at birth
# wedges later re-wraps); the drive creates the single sensor.
import numpy as np
import omni.usd
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import Acoustic

st = omni.usd.get_context().get_stage()
for p in ("/World/R2T0", "/World/R2T1", "/World/R2T2",
          "/World/R2Acous"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)
for i, (x, y) in enumerate([(3, 0), (5, 2), (4, -2)]):
    Cube("/World/R2T%d" % i, sizes=1.0,
         positions=np.array([float(x), float(y), 0.0]))
acoustic = Acoustic(
    "/World/R2Acous",
    aux_output_level="BASIC",
    tick_rate=30.0,
    attributes={
        "omni:sensor:WpmAcoustic:centerFrequency": 51200.0,
        "omni:sensor:WpmAcoustic:sensorMount:m001:position": (0.0, -0.05, 0.0),
        "omni:sensor:WpmAcoustic:sensorMount:m001:rotation": (0.0, 0.0, 0.0),
        "omni:sensor:WpmAcoustic:sensorMount:m002:position": (0.0, 0.0, 0.0),
        "omni:sensor:WpmAcoustic:sensorMount:m002:rotation": (0.0, 0.0, 0.0),
        "omni:sensor:WpmAcoustic:sensorMount:m003:position": (0.0, 0.05, 0.0),
        "omni:sensor:WpmAcoustic:sensorMount:m003:rotation": (0.0, 0.0, 0.0),
        "omni:sensor:WpmAcoustic:rxGroup:g001:receiverIndices": [0, 1],
        "omni:sensor:WpmAcoustic:rxGroup:g002:receiverIndices": [1, 2],
    },
)
ok = all(st.GetPrimAtPath(p).IsValid()
         for p in ("/World/R2T0", "/World/R2T1", "/World/R2T2",
                   "/World/R2Acous"))
print("PRIM:", acoustic.paths[0], acoustic.prims[0].GetTypeName())
print("R2-BUILD-OK valid=%s" % ok)
