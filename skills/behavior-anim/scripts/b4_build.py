"""B4 build (runs INSIDE Isaac Sim): trigger scene.

B4Slider: cube animated x 0->2.0 over tc 0->120 (2 sim-seconds).
B4Bot: 1R arm at x=-3 (B3 pattern). Reports slider samples + arm.
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf, Usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/B4Slider", "/World/B4Bot"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

sl = UsdGeom.Cube.Define(stage, "/World/B4Slider")
sl.GetSizeAttr().Set(0.4)
sop = UsdGeom.Xformable(sl.GetPrim()).AddTranslateOp()
sop.GetAttr().Set(Gf.Vec3d(0, 1.5, 0.5), Usd.TimeCode(0.0))
sop.GetAttr().Set(Gf.Vec3d(2.0, 1.5, 0.5), Usd.TimeCode(120.0))

bot = stage.DefinePrim("/World/B4Bot", "Xform")
UsdGeom.Xformable(bot).AddTranslateOp().Set(Gf.Vec3d(-3.0, 0, 0))
base = UsdGeom.Cube.Define(stage, "/World/B4Bot/Base")
base.GetSizeAttr().Set(0.15)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.2))
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).GetMassAttr().Set(2.0)
UsdPhysics.ArticulationRootAPI.Apply(base.GetPrim())
fix = UsdPhysics.FixedJoint.Define(stage, "/World/B4Bot/RootFixed")
fix.CreateBody0Rel().SetTargets(["/World/B4Bot"])
fix.CreateBody1Rel().SetTargets(["/World/B4Bot/Base"])
link = UsdGeom.Cube.Define(stage, "/World/B4Bot/Link")
link.GetSizeAttr().Set(0.2)
UsdGeom.Xformable(link.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.4))
UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
UsdPhysics.MassAPI.Apply(link.GetPrim()).GetMassAttr().Set(0.5)
hinge = UsdPhysics.RevoluteJoint.Define(stage, "/World/B4Bot/Hinge1")
hinge.CreateBody0Rel().SetTargets(["/World/B4Bot/Base"])
hinge.CreateBody1Rel().SetTargets(["/World/B4Bot/Link"])
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
print("B4-BUILD-OK samples=%d bot=%s hinge=%s" % (
    len(sop.GetAttr().GetTimeSamples()),
    bot.IsValid(), hinge.GetPrim().IsValid()))
