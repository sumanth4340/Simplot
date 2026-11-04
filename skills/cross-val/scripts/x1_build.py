"""X1 build (runs INSIDE Isaac Sim): drop scene for save/open test."""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/X1Cube", "/World/X1Ground", "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/X1Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
c = UsdGeom.Cube.Define(stage, "/World/X1Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 2))
UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
UsdPhysics.CollisionAPI.Apply(c.GetPrim())
UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(1.0)
print("X1-BUILD-OK")
