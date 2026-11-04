"""V4 build (runs INSIDE Isaac Sim): imported arm + drive over.

References the M2 URDF package, adds scene + ground, authors a PD
drive over on the referenced shoulder (target 45 deg). Target in
degrees, DOF readback in radians -> q settles at pi/4.
"""
from pxr import UsdGeom, UsdPhysics
import omni.usd
from pxr import Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/V4Bot", "/World/V4Ground", "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ref = stage.DefinePrim("/World/V4Bot")
ref.GetReferences().AddReference(
    "C:/Users/sruja_ob3di74/action-reasoner/skills/modeling-assets/"
    "assets/m2_out/m2_bot/m2_bot.usda")
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/V4Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
j = stage.GetPrimAtPath("/World/V4Bot/Physics/shoulder")
d = UsdPhysics.DriveAPI.Apply(j, "angular")
d.CreateTypeAttr().Set("force")
d.CreateStiffnessAttr().Set(1000.0)
d.CreateDampingAttr().Set(100.0)
d.CreateMaxForceAttr().Set(1000000.0)
d.CreateTargetPositionAttr().Set(45.0)
print("V4-BUILD-OK imported arm + drive over")
