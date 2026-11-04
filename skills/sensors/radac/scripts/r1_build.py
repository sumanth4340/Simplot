# R1 build (runs INSIDE Isaac Sim): radar + known cube geometry.
# Author while STOPPED (live moves emit nothing until stop/play).
import carb
import numpy as np
import omni.usd
from isaacsim.core.experimental.materials import NonVisualMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor

s = carb.settings.get_settings()
# NEVER flip motion BVH live on a running renderer: it wedges Hydra
# in an engine-recreation storm (1.4MB log spam / 10s, viewport dead).
# Boot the sim with --/renderer/raytracingMotion/enabled=true instead.
print("motion-bvh:", s.get("/renderer/raytracingMotion/enabled"))
assert s.get("/renderer/raytracingMotion/enabled"), "reboot with MBVH flag"

st = omni.usd.get_context().get_stage()
for p in ("/World/R1Cube", "/World/R1Radar", "/World/R1RadarTI",
          "/World/R1XCube", "/World/R1XLidar"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)
cube = Cube("/World/R1Cube", positions=np.array([5.0, 0.0, 0.0]),
              scales=np.array([2.0, 2.0, 2.0]))
# Bare geometry is RADAR-INVISIBLE (5 bit-identical ghost dets/frame
# only). NonVisualMaterial gives real returns (28/frame on this cube).
mat = NonVisualMaterial("/World/R1Cube/material", bases="aluminum",
                        coatings="paint", attributes="emissive")
cube.apply_visual_materials(mat)
# Vendor config, NOT the bare constructor: bare Generic RadarWPMDMAT
# ticks GMO frames but yields zero detections (even debug-forced).
# TI config detects on the first run (87/87 frames x 28 dets).
radar = Radar.create("/World/R1Radar", config="IWRL6432AOP",
                     translations=np.array([0.0, 0.0, 1.0]),
                     orientations=np.array([1.0, 0.0, 0.0, 0.0]),
                     attributes={"omni:sensor:WpmDmat:outputFrameOfReference":
                                 "WORLD"},
                     aux_output_level="BASIC")
# NOTE: no RadarSensor here. A sensor created in the same script as
# the prim (at birth, never played) wedges it: a later re-wrap drive
# ticks GMO frames but sees zero detections (reproduced 2/2, F4).
# The drive creates the single sensor and plays it immediately.
print("PRIM:", radar.paths[0])
ok = all(st.GetPrimAtPath(p).IsValid()
         for p in ("/World/R1Cube", "/World/R1Radar"))
print("R1-BUILD-OK valid=%s" % ok)
