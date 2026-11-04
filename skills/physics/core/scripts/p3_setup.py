"""P3 setup (runs INSIDE Isaac Sim): hinge + velocity drive scene.

Static base cube, dynamic arm cube stacked above, revolute joint about Z,
angular drive target_velocity=180 (unit determined by drill: degrees->pi,
rad/s->4.07). Ground plane catches debris if the joint is mis-authored.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/P2Cube", "/World/P2Ground", "/World/P3Base",
          "/World/P3Arm", "/World/P3Hinge", "/World/P3Ground",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)

g = UsdGeom.Plane.Define(stage, "/World/P3Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())

base = UsdGeom.Cube.Define(stage, "/World/P3Base")
base.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
UsdPhysics.CollisionAPI.Apply(base.GetPrim())

arm = UsdGeom.Cube.Define(stage, "/World/P3Arm")
arm.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(arm.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 1.5))
UsdPhysics.RigidBodyAPI.Apply(arm.GetPrim())
UsdPhysics.CollisionAPI.Apply(arm.GetPrim())
UsdPhysics.MassAPI.Apply(arm.GetPrim()).GetMassAttr().Set(1.0)

j = UsdPhysics.RevoluteJoint.Define(stage, "/World/P3Hinge")
j.GetBody0Rel().AddTarget("/World/P3Base")
j.GetBody1Rel().AddTarget("/World/P3Arm")
j.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0.5))
j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
j.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
j.GetAxisAttr().Set(UsdPhysics.Tokens.z)

d = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
d.CreateTypeAttr().Set("force")
d.CreateStiffnessAttr().Set(0.0)
d.CreateDampingAttr().Set(1000.0)
d.CreateMaxForceAttr().Set(1000000.0)
d.CreateTargetVelocityAttr().Set(180.0)
print("P3-SETUP-OK hinge drive w=180")
