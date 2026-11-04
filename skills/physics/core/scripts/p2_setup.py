"""P2 setup (runs INSIDE Isaac Sim): zero-g velocity scene.

PhysicsScene with gravity 0 + ground + dynamic 1 m cube /World/P2Cube.
No gravity, no contact: constant-velocity motion, fully deterministic.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/P1Cube", "/World/P1Ground", "/World/LiveCube",
          "/World/LiveGround", "/World/P2Cube", "/World/P2Ground",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(0.0)

g = UsdGeom.Plane.Define(stage, "/World/P2Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())

c = UsdGeom.Cube.Define(stage, "/World/P2Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 2))
UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
UsdPhysics.CollisionAPI.Apply(c.GetPrim())
UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(1.0)
print("P2-SETUP-OK zero-g scene, cube@origin")
