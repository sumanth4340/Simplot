"""M1 build (runs INSIDE Isaac Sim): 2-DOF pitch arm + grasp site.

/World/M1Bot (Xform): dynamic base cube + root API + fixed joint,
Hinge1/Hinge2 pitch about Y with holding drives, Link1 0.6m, Link2
0.4m, GraspSite Xform (IsaacSiteAPI) at Link2 tip, target cube.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/M1Bot", "/World/M1Ground", "/World/M1Target",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/M1Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
UsdGeom.Xform.Define(stage, "/World/M1Bot")


def _link(name, size, z, mass, root=False):
    c = UsdGeom.Cube.Define(stage, "/World/M1Bot/" + name)
    c.GetSizeAttr().Set(size)
    x = UsdGeom.Xformable(c.GetPrim())
    x.AddTranslateOp().Set(Gf.Vec3d(0, 0, z))
    UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())
    UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(mass)
    if root:
        UsdPhysics.ArticulationRootAPI.Apply(c.GetPrim())
    return c


def _hinge(name, b0, a0, b1, a1):
    j = UsdPhysics.RevoluteJoint.Define(stage, "/World/M1Bot/" + name)
    j.GetBody0Rel().AddTarget("/World/M1Bot/" + b0)
    j.GetBody1Rel().AddTarget("/World/M1Bot/" + b1)
    j.GetLocalPos0Attr().Set(Gf.Vec3f(*a0))
    j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
    j.GetLocalPos1Attr().Set(Gf.Vec3f(*a1))
    j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
    j.GetAxisAttr().Set(UsdPhysics.Tokens.y)
    d = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
    d.CreateTypeAttr().Set("force")
    d.CreateStiffnessAttr().Set(400.0)
    d.CreateDampingAttr().Set(40.0)
    d.CreateMaxForceAttr().Set(1000000.0)
    d.CreateTargetPositionAttr().Set(0.0)


_link("Base", 1.0, 0.5, 2.0, root=True)
fx = UsdPhysics.FixedJoint.Define(stage, "/World/M1Bot/RootFixed")
fx.GetBody0Rel().AddTarget("/World/M1Bot")
fx.GetBody1Rel().AddTarget("/World/M1Bot/Base")
fx.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0))
fx.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
fx.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
fx.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
_link("Link1", 0.6, 1.3, 1.0)
_hinge("Hinge1", "Base", (0, 0, 0.5), "Link1", (0, 0, -0.3))
_link("Link2", 0.4, 1.8, 0.5)
_hinge("Hinge2", "Link1", (0, 0, 0.3), "Link2", (0, 0, -0.2))
site = UsdGeom.Xform.Define(stage, "/World/M1Bot/Link2/GraspSite")
UsdGeom.Xformable(site.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.2))
site.GetPrim().ApplyAPI("IsaacSiteAPI")
tgt = UsdGeom.Cube.Define(stage, "/World/M1Target")
tgt.GetSizeAttr().Set(0.1)
UsdGeom.Xformable(tgt.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(0.35, 0, 1.75))
UsdPhysics.CollisionAPI.Apply(tgt.GetPrim())
print("M1-BUILD-OK arm+site+target")
