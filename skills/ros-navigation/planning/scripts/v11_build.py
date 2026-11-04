"""V11 build (runs INSIDE Isaac Sim): exam yard.

New layout: V11ObsD 1.4m cube at (0,2); V11ObsE 1.0m at (-2.9,1.1);
V11ObsF size-1.0 cube SCALED (1.6,0.8,1.0) at (2,-2) — tests the
rasterizer on scaled prims. All with CollisionAPI. Expect 62 cells
(D 5x5=25, E 4x4=16, F 7x3=21; slice counts are x1-x0, R7).
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/N1Ground", "/World/N1ObsA", "/World/N1ObsB",
          "/World/N1VisualC", "/World/N3Bot",
          "/World/V11ObsD", "/World/V11ObsE", "/World/V11ObsF"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

d = UsdGeom.Cube.Define(stage, "/World/V11ObsD")
d.GetSizeAttr().Set(1.4)
UsdGeom.Xformable(d.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 2, 0.7))
UsdPhysics.CollisionAPI.Apply(d.GetPrim())

e = UsdGeom.Cube.Define(stage, "/World/V11ObsE")
e.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(e.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(-2.9, 1.1, 0.5))
UsdPhysics.CollisionAPI.Apply(e.GetPrim())

f = UsdGeom.Cube.Define(stage, "/World/V11ObsF")
f.GetSizeAttr().Set(1.0)
fx = UsdGeom.Xformable(f.GetPrim())
fx.AddTranslateOp().Set(Gf.Vec3d(2, -2, 0.5))
fx.AddScaleOp().Set(Gf.Vec3f(1.6, 0.8, 1.0))
UsdPhysics.CollisionAPI.Apply(f.GetPrim())

ok = all(stage.GetPrimAtPath(p).IsValid() for p in (
    "/World/V11ObsD", "/World/V11ObsE", "/World/V11ObsF"))
print("V11-BUILD-OK valid=%s" % ok)
