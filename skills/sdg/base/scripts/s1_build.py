"""S1 build (runs INSIDE Isaac Sim): lit SDG stage.

S1Dome (3000), S1Ground 10x10, S1Cube 1.0 at (0,0,0.5).
Reports prims valid.
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/S1Dome", "/World/S1Ground", "/World/S1Cube"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/S1Dome")
dome.GetIntensityAttr().Set(3000.0)
g = UsdGeom.Cube.Define(stage, "/World/S1Ground")
g.GetSizeAttr().Set(10.0)
UsdGeom.Xformable(g.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
c = UsdGeom.Cube.Define(stage, "/World/S1Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
ok = all(stage.GetPrimAtPath(p).IsValid() for p in (
    "/World/S1Dome", "/World/S1Ground", "/World/S1Cube"))
print("S1-BUILD-OK valid=%s" % ok)
