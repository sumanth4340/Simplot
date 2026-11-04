"""A2 marker snippet (runs INSIDE Isaac Sim): define + report."""
import omni.usd
from pxr import UsdGeom, Gf
stage = omni.usd.get_context().get_stage()
c = UsdGeom.Cube.Define(stage, "/World/A2Marker")
c.GetSizeAttr().Set(0.7)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(1.0, 2.0, 0.35))
print("A2-MARKER valid=%s size=%.2f" % (
    c.GetPrim().IsValid(), float(c.GetSizeAttr().Get())))
