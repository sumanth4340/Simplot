"""N1 build (runs INSIDE Isaac Sim): nav yard.

N1Ground: 20x20 visual plane (NO collider -> ignored).
N1ObsA/B: 1.2m cubes WITH CollisionAPI at (1,0)/( -2,-2).
N1VisualC: 1.0m cube at (3,3) with NO collider (must not appear).
Sizes avoid float-boundary cell edges (1.2, not 1.0).
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/N1Ground", "/World/N1ObsA", "/World/N1ObsB",
          "/World/N1VisualC"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

g = UsdGeom.Cube.Define(stage, "/World/N1Ground")
g.GetSizeAttr().Set(20.0)
UsdGeom.Xformable(g.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))

a = UsdGeom.Cube.Define(stage, "/World/N1ObsA")
a.GetSizeAttr().Set(1.2)
UsdGeom.Xformable(a.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(1, 0, 0.6))
UsdPhysics.CollisionAPI.Apply(a.GetPrim())

b = UsdGeom.Cube.Define(stage, "/World/N1ObsB")
b.GetSizeAttr().Set(1.2)
UsdGeom.Xformable(b.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(-2, -2, 0.6))
UsdPhysics.CollisionAPI.Apply(b.GetPrim())

c = UsdGeom.Cube.Define(stage, "/World/N1VisualC")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(3, 3, 0.5))

ok = all(stage.GetPrimAtPath(p).IsValid() for p in (
    "/World/N1Ground", "/World/N1ObsA", "/World/N1ObsB",
    "/World/N1VisualC"))
print("N1-BUILD-OK valid=%s" % ok)
