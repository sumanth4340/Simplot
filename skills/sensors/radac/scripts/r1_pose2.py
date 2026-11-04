# R1 pose2 (INSIDE Isaac Sim): sensor world orientation + TI attrs.
from pxr import UsdGeom, Gf
import omni.usd

st = omni.usd.get_context().get_stage()
cache = UsdGeom.XformCache()
m = cache.GetLocalToWorldTransform(st.GetPrimAtPath("/World/R1Radar/sensor"))
q = m.ExtractRotation().GetQuat()
print("QUAT wxyz = (%.4f, %.4f, %.4f, %.4f)" % (
    q.GetReal(), q.GetImaginary()[0], q.GetImaginary()[1],
    q.GetImaginary()[2]))
pr = st.GetPrimAtPath("/World/R1Radar/sensor")
for a in pr.GetAttributes():
    n = a.GetName()
    if ("CoordsType" in n or "FrameOfReference" in n
            or "maxRangeM" in n or "AngDeg" in n
            or "tickRate" in n or "Elevation" in n and "Steer" in n):
        try:
            print("ATTR %s = %s" % (n, str(a.Get())[:120]))
        except Exception:
            pass
print("R1-POSE2 done")
