# R1 pose (INSIDE Isaac Sim): world pose of nested TI sensor.
from pxr import UsdGeom
import omni.usd

st = omni.usd.get_context().get_stage()
cache = UsdGeom.XformCache()
for p in ("/World/R1Radar", "/World/R1Radar/sensor", "/World/R1Cube"):
    m = cache.GetLocalToWorldTransform(st.GetPrimAtPath(p))
    t = m.ExtractTranslation()
    print("POSE %s = (%.4f, %.4f, %.4f)" % (p, t[0], t[1], t[2]))
print("R1-POSE done")
