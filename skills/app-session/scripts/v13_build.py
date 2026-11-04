"""V13 build snippet (runs INSIDE Isaac Sim): exam scene."""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf
stage = omni.usd.get_context().get_stage()
dome = UsdLux.DomeLight.Define(stage, "/World/V13Dome")
dome.GetIntensityAttr().Set(3000.0)
a = UsdGeom.Cube.Define(stage, "/World/V13PropA")
a.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(a.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(-0.8, 0, 0.5))
b = UsdGeom.Cube.Define(stage, "/World/V13PropB")
b.GetSizeAttr().Set(0.6)
UsdGeom.Xformable(b.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(0.9, 0.3, 0.3))
print("V13-BUILD-OK valid=%s" % all(
    stage.GetPrimAtPath(p).IsValid() for p in (
        "/World/V13Dome", "/World/V13PropA", "/World/V13PropB")))
