"""A3 build (runs INSIDE Isaac Sim): 1-DOF arm + PD to 90 degrees.

Same structure as A1 plus angular DriveAPI (force, stiffness 1000,
damping 100, target_position 90). Hypothesis: target in degrees, DOF
readback in radians -> q settles at pi/2.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/A3Bot", "/World/A3Ground", "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/A3Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
UsdGeom.Xform.Define(stage, "/World/A3Bot")
base = UsdGeom.Cube.Define(stage, "/World/A3Bot/Base")
base.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.CollisionAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).GetMassAttr().Set(2.0)
UsdPhysics.ArticulationRootAPI.Apply(base.GetPrim())
fx = UsdPhysics.FixedJoint.Define(stage, "/World/A3Bot/RootFixed")
fx.GetBody0Rel().AddTarget("/World/A3Bot")
fx.GetBody1Rel().AddTarget("/World/A3Bot/Base")
fx.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0))
fx.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
fx.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
fx.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
arm = UsdGeom.Cube.Define(stage, "/World/A3Bot/Arm")
arm.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(arm.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 1.5))
UsdPhysics.RigidBodyAPI.Apply(arm.GetPrim())
UsdPhysics.CollisionAPI.Apply(arm.GetPrim())
UsdPhysics.MassAPI.Apply(arm.GetPrim()).GetMassAttr().Set(1.0)
j = UsdPhysics.RevoluteJoint.Define(stage, "/World/A3Bot/Hinge")
j.GetBody0Rel().AddTarget("/World/A3Bot/Base")
j.GetBody1Rel().AddTarget("/World/A3Bot/Arm")
j.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0.5))
j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
j.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
j.GetAxisAttr().Set(UsdPhysics.Tokens.z)
d = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
d.CreateTypeAttr().Set("force")
d.CreateStiffnessAttr().Set(1000.0)
d.CreateDampingAttr().Set(100.0)
d.CreateMaxForceAttr().Set(1000000.0)
d.CreateTargetPositionAttr().Set(90.0)
print("A3-BUILD-OK arm+drive target90")
