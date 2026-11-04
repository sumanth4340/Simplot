"""A1 build (runs INSIDE Isaac Sim): 1-DOF arm under articulation root.

/World/A1Bot (Xform + ArticulationRootAPI): static base cube, dynamic
arm cube, revolute Z hinge. Mirrors P3 geometry (proven joint).
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/A1Bot", "/World/A1Ground", "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/A1Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
bot = UsdGeom.Xform.Define(stage, "/World/A1Bot")
base = UsdGeom.Cube.Define(stage, "/World/A1Bot/Base")
base.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.CollisionAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).GetMassAttr().Set(2.0)
UsdPhysics.ArticulationRootAPI.Apply(base.GetPrim())
fx = UsdPhysics.FixedJoint.Define(stage, "/World/A1Bot/RootFixed")
fx.GetBody0Rel().AddTarget("/World/A1Bot")
fx.GetBody1Rel().AddTarget("/World/A1Bot/Base")
fx.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0))
fx.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
fx.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
fx.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
arm = UsdGeom.Cube.Define(stage, "/World/A1Bot/Arm")
arm.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(arm.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 1.5))
UsdPhysics.RigidBodyAPI.Apply(arm.GetPrim())
UsdPhysics.CollisionAPI.Apply(arm.GetPrim())
UsdPhysics.MassAPI.Apply(arm.GetPrim()).GetMassAttr().Set(1.0)
j = UsdPhysics.RevoluteJoint.Define(stage, "/World/A1Bot/Hinge")
j.GetBody0Rel().AddTarget("/World/A1Bot/Base")
j.GetBody1Rel().AddTarget("/World/A1Bot/Arm")
j.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0.5))
j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
j.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
j.GetAxisAttr().Set(UsdPhysics.Tokens.z)
print("A1-BUILD-OK root+base+arm+hinge")
