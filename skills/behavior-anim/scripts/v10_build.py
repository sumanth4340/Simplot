"""V10 build (runs INSIDE Isaac Sim): exam scene.

V10Gate: cube animated along Y (0->2.4 over tc 0->144 = 2.4s) +
rotateY 0->45deg. V10Bot: 1R arm at x=+4 (B3 pattern). Reports
ops/samples/arm.
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf, Usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/V10Gate", "/World/V10Bot"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

gt = UsdGeom.Cube.Define(stage, "/World/V10Gate")
gt.GetSizeAttr().Set(0.4)
gxf = UsdGeom.Xformable(gt.GetPrim())
top = gxf.AddTranslateOp()
top.GetAttr().Set(Gf.Vec3d(0, 0, 0.5), Usd.TimeCode(0.0))
top.GetAttr().Set(Gf.Vec3d(0, 2.4, 0.5), Usd.TimeCode(144.0))
rop = gxf.AddRotateYOp()
rop.GetAttr().Set(0.0, Usd.TimeCode(0.0))
rop.GetAttr().Set(45.0, Usd.TimeCode(144.0))

bot = stage.DefinePrim("/World/V10Bot", "Xform")
UsdGeom.Xformable(bot).AddTranslateOp().Set(Gf.Vec3d(4.0, 0, 0))
base = UsdGeom.Cube.Define(stage, "/World/V10Bot/Base")
base.GetSizeAttr().Set(0.15)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.2))
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).GetMassAttr().Set(2.0)
UsdPhysics.ArticulationRootAPI.Apply(base.GetPrim())
fix = UsdPhysics.FixedJoint.Define(stage, "/World/V10Bot/RootFixed")
fix.CreateBody0Rel().SetTargets(["/World/V10Bot"])
fix.CreateBody1Rel().SetTargets(["/World/V10Bot/Base"])
link = UsdGeom.Cube.Define(stage, "/World/V10Bot/Link")
link.GetSizeAttr().Set(0.2)
UsdGeom.Xformable(link.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.4))
UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
UsdPhysics.MassAPI.Apply(link.GetPrim()).GetMassAttr().Set(0.5)
hinge = UsdPhysics.RevoluteJoint.Define(stage, "/World/V10Bot/Hinge1")
hinge.CreateBody0Rel().SetTargets(["/World/V10Bot/Base"])
hinge.CreateBody1Rel().SetTargets(["/World/V10Bot/Link"])
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
ops = UsdGeom.Xformable(gt.GetPrim()).GetOrderedXformOps()
print("V10-BUILD-OK ops=%d tsamples=%d rsamples=%d bot=%s" % (
    len(ops), len(top.GetAttr().GetTimeSamples()),
    len(rop.GetAttr().GetTimeSamples()), hinge.GetPrim().IsValid()))
