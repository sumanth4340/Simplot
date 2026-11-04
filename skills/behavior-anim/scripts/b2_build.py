"""B2 build (runs INSIDE Isaac Sim): multi-op animation.

B2Box cube: translate samples tc=0 -> x=0, tc=60 -> x=2.0 AND
rotateY samples tc=0 -> 0deg, tc=60 -> 90deg. Reports ops.
"""
import omni.usd
from pxr import UsdGeom, Gf, Usd

stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/B2Box")
if o and o.IsValid():
    stage.RemovePrim("/World/B2Box")

box = UsdGeom.Cube.Define(stage, "/World/B2Box")
box.GetSizeAttr().Set(0.5)
xf = UsdGeom.Xformable(box.GetPrim())
top = xf.AddTranslateOp()
top.GetAttr().Set(Gf.Vec3d(0, 0, 0.5), Usd.TimeCode(0.0))
top.GetAttr().Set(Gf.Vec3d(2.0, 0, 0.5), Usd.TimeCode(60.0))
rop = xf.AddRotateYOp()
rop.GetAttr().Set(0.0, Usd.TimeCode(0.0))
rop.GetAttr().Set(90.0, Usd.TimeCode(60.0))
ops = [op.GetOpType() for op in xf.GetOrderedXformOps()]
print("B2-BUILD-OK valid=%s ops=%d tsamples=%d rsamples=%d" % (
    box.GetPrim().IsValid(), len(ops),
    len(top.GetAttr().GetTimeSamples()),
    len(rop.GetAttr().GetTimeSamples())))
