"""A2 build (runs INSIDE Isaac Sim): 3-link arm, 2 revolute DOFs.

Base (dynamic + root API + fixed joint) -> Hinge1(Z) -> Link1 0.6m ->
Hinge2(Z) -> Link2 0.4m. Vertical axes: stable rest, q stays ~0.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/A2Bot", "/World/A2Ground", "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/A2Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
UsdGeom.Xform.Define(stage, "/World/A2Bot")


def _link(name, size, z, mass, root=False):
    c = UsdGeom.Cube.Define(stage, "/World/A2Bot/" + name)
    c.GetSizeAttr().Set(size)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, z))
    UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())
    UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(mass)
    if root:
        UsdPhysics.ArticulationRootAPI.Apply(c.GetPrim())
    return c


def _hinge(name, b0, a0, b1, a1):
    j = UsdPhysics.RevoluteJoint.Define(stage, "/World/A2Bot/" + name)
    j.GetBody0Rel().AddTarget("/World/A2Bot/" + b0)
    j.GetBody1Rel().AddTarget("/World/A2Bot/" + b1)
    j.GetLocalPos0Attr().Set(Gf.Vec3f(*a0))
    j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
    j.GetLocalPos1Attr().Set(Gf.Vec3f(*a1))
    j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
    j.GetAxisAttr().Set(UsdPhysics.Tokens.z)


_link("Base", 1.0, 0.5, 2.0, root=True)
fx = UsdPhysics.FixedJoint.Define(stage, "/World/A2Bot/RootFixed")
fx.GetBody0Rel().AddTarget("/World/A2Bot")
fx.GetBody1Rel().AddTarget("/World/A2Bot/Base")
fx.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0))
fx.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
fx.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
fx.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
_link("Link1", 0.6, 1.3, 1.0)
_hinge("Hinge1", "Base", (0, 0, 0.5), "Link1", (0, 0, -0.3))
_link("Link2", 0.4, 1.8, 0.5)
_hinge("Hinge2", "Link1", (0, 0, 0.3), "Link2", (0, 0, -0.2))
print("A2-BUILD-OK 3 links 2 hinges")
