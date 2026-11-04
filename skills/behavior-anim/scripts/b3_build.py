"""B3 build (runs INSIDE Isaac Sim): behavior arm.

B3Bot 1R arm at x=-3 (Skill 4 root pattern): base 0.15/mass 2,
link 0.2/mass 0.5, Y-hinge limits +-170deg, position drive
stiffness 100 damping 10. Reports joint valid.
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf

stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/B3Bot")
if o and o.IsValid():
    stage.RemovePrim("/World/B3Bot")

bot = stage.DefinePrim("/World/B3Bot", "Xform")
UsdGeom.Xformable(bot).AddTranslateOp().Set(Gf.Vec3d(-3.0, 0, 0))
base = UsdGeom.Cube.Define(stage, "/World/B3Bot/Base")
base.GetSizeAttr().Set(0.15)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.2))
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).GetMassAttr().Set(2.0)
UsdPhysics.ArticulationRootAPI.Apply(base.GetPrim())
fix = UsdPhysics.FixedJoint.Define(stage, "/World/B3Bot/RootFixed")
fix.CreateBody0Rel().SetTargets(["/World/B3Bot"])
fix.CreateBody1Rel().SetTargets(["/World/B3Bot/Base"])
link = UsdGeom.Cube.Define(stage, "/World/B3Bot/Link")
link.GetSizeAttr().Set(0.2)
UsdGeom.Xformable(link.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.4))
UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
UsdPhysics.MassAPI.Apply(link.GetPrim()).GetMassAttr().Set(0.5)
hinge = UsdPhysics.RevoluteJoint.Define(stage, "/World/B3Bot/Hinge1")
hinge.CreateBody0Rel().SetTargets(["/World/B3Bot/Base"])
hinge.CreateBody1Rel().SetTargets(["/World/B3Bot/Link"])
hinge.CreateAxisAttr("Y")
hinge.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0.075))
hinge.CreateLocalPos1Attr(Gf.Vec3f(0, 0, -0.1))
lim = UsdPhysics.LimitAPI.Apply(hinge.GetPrim(), "rotY")
lim.CreateLowAttr(-170.0)
lim.CreateHighAttr(170.0)
drv = UsdPhysics.DriveAPI.Apply(hinge.GetPrim(), "angular")
drv.CreateTypeAttr("position")
drv.CreateTargetPositionAttr().Set(0.0)
drv.CreateStiffnessAttr(100.0)
drv.CreateDampingAttr(10.0)
print("B3-BUILD-OK bot=%s hinge=%s" % (
    bot.IsValid(), hinge.GetPrim().IsValid()))
