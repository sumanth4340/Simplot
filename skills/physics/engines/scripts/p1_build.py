"""P1 build (runs INSIDE Isaac Sim): PhysX drop scene.

PhysicsScene + 20m ground collider (top z=0) + 1m rigid cube
(mass 1) at z=2. Reports prims valid.
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/PhysicsScene", "/World/P1Ground", "/World/P1Cube"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
g = UsdGeom.Cube.Define(stage, "/World/P1Ground")
g.GetSizeAttr().Set(20.0)
UsdGeom.Xformable(g.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(0, 0, -10.0))
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
c = UsdGeom.Cube.Define(stage, "/World/P1Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(0, 0, 2.0))
UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
UsdPhysics.CollisionAPI.Apply(c.GetPrim())
UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(1.0)
print("P1-BUILD-OK valid=%s" % all(
    stage.GetPrimAtPath(p).IsValid() for p in (
        "/World/PhysicsScene", "/World/P1Ground", "/World/P1Cube")))
