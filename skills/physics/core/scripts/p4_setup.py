"""P4 setup (runs INSIDE Isaac Sim): two-cube stack scene.

Ground + cube A resting at z=0.5 + cube B dropped from z=2 onto A.
Both 1 m, rigid + collision + mass. Stabilization default (on).
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/P3Base", "/World/P3Arm", "/World/P3Hinge",
          "/World/P3Ground", "/World/P4A", "/World/P4B",
          "/World/P4Ground", "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)

g = UsdGeom.Plane.Define(stage, "/World/P4Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())

for name, z in (("P4A", 0.5), ("P4B", 2.0)):
    c = UsdGeom.Cube.Define(stage, "/World/" + name)
    c.GetSizeAttr().Set(1.0)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, z))
    UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())
    UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(1.0)
print("P4-SETUP-OK stack scene")
