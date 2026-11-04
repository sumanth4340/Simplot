"""P1 setup (runs INSIDE Isaac Sim): gravity drop scene.

PhysicsScene + static ground plane + dynamic 1 m cube at z=2.
Clears Skill 0 drill prims so the stage holds only P1 bodies.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/SenseCube", "/World/JointCube", "/World/JointCyl",
          "/World/JointCube_Cyl", "/World/P1Cube", "/World/P1Ground",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)

g = UsdGeom.Plane.Define(stage, "/World/P1Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())

c = UsdGeom.Cube.Define(stage, "/World/P1Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 2))
UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
UsdPhysics.CollisionAPI.Apply(c.GetPrim())
UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(1.0)
print("P1-SETUP-OK scene+ground+cube@z2")
