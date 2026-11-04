"""B1 build (runs INSIDE Isaac Sim): time-sampled translation.

B1Box cube with xformOp:translate samples: tc=0 -> x=0, tc=60 ->
x=2.0 (60 tc = 1 sim-second). Reports sample count.
"""
import omni.usd
from pxr import UsdGeom, Gf, Usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/B1Box",):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

box = UsdGeom.Cube.Define(stage, "/World/B1Box")
box.GetSizeAttr().Set(0.5)
xop = UsdGeom.Xformable(box.GetPrim()).AddTranslateOp()
attr = xop.GetAttr()
attr.Set(Gf.Vec3d(0, 0, 0.5), Usd.TimeCode(0.0))
attr.Set(Gf.Vec3d(2.0, 0, 0.5), Usd.TimeCode(60.0))
n = len(attr.GetTimeSamples())
print("B1-BUILD-OK valid=%s samples=%d" % (
    box.GetPrim().IsValid(), n))
