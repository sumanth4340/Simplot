"""M4 build v2 (runs INSIDE Isaac Sim): free-swing arm + low pedestals.

M4v1 failed: tall shelves (1.64) blocked both IK branches (Link2 hit
the shelf column on elbow-down AND elbow-up paths).
M4v2: floating root cube (0.15, fixed-jointed) at z=0.825, shoulder
at z=0.90 with +/-170 deg clearance (nothing below but ground);
L1=0.4/L2=0.5; low pedestals (tops 0.3) at x=+/-0.55; block 0.12
(0.3kg) on pedestal A. Grasp q=(1.731,+1.093), all links verified
clear of shelves/block except the grasp itself.
"""
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/M1Bot", "/World/M1Ground", "/World/M1Target",
          "/World/M2Bot", "/World/M2Ground", "/World/M2Target",
          "/World/M3Bot", "/World/M3Ground", "/World/M3Target",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/YBot", "/World/YGround",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/M4Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
UsdGeom.Xform.Define(stage, "/World/M4Bot")


def _link(name, size, z, mass, root=False):
    c = UsdGeom.Cube.Define(stage, "/World/M4Bot/" + name)
    c.GetSizeAttr().Set(size)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, z))
    UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())
    UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(mass)
    if root:
        UsdPhysics.ArticulationRootAPI.Apply(c.GetPrim())
        pa = PhysxSchema.PhysxArticulationAPI.Apply(c.GetPrim())
        pa.CreateSleepThresholdAttr().Set(0.0)
        pa.CreateSolverPositionIterationCountAttr().Set(32)
        pa.CreateSolverVelocityIterationCountAttr().Set(1)
        pa.CreateEnabledSelfCollisionsAttr().Set(False)
    return c


def _hinge(name, b0, a0, b1, a1):
    j = UsdPhysics.RevoluteJoint.Define(stage, "/World/M4Bot/" + name)
    j.GetBody0Rel().AddTarget("/World/M4Bot/" + b0)
    j.GetBody1Rel().AddTarget("/World/M4Bot/" + b1)
    j.GetLocalPos0Attr().Set(Gf.Vec3f(*a0))
    j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
    j.GetLocalPos1Attr().Set(Gf.Vec3f(*a1))
    j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
    j.GetAxisAttr().Set(UsdPhysics.Tokens.y)
    j.CreateLowerLimitAttr().Set(-170.0)
    j.CreateUpperLimitAttr().Set(170.0)
    d = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
    d.CreateTypeAttr().Set("force")
    d.CreateStiffnessAttr().Set(100000.0)
    d.CreateDampingAttr().Set(10000.0)
    d.CreateMaxForceAttr().Set(1000000.0)
    d.CreateTargetPositionAttr().Set(0.0)


_link("Root", 0.15, 0.825, 2.0, root=True)
fx = UsdPhysics.FixedJoint.Define(stage, "/World/M4Bot/RootFixed")
fx.GetBody0Rel().AddTarget("/World/M4Bot")
fx.GetBody1Rel().AddTarget("/World/M4Bot/Root")
fx.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0.825))
fx.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
fx.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
fx.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
_link("Link1", 0.2, 1.20, 1.0)
_hinge("Hinge1", "Root", (0, 0, 0.075), "Link1", (0, 0, -0.3))
_link("Link2", 0.2, 1.60, 0.5)
_hinge("Hinge2", "Link1", (0, 0, 0.1), "Link2", (0, 0, -0.3))
site = UsdGeom.Xform.Define(stage, "/World/M4Bot/Link2/GraspSite")
UsdGeom.Xformable(site.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.2))
site.GetPrim().ApplyAPI("IsaacSiteAPI")


def _shelf(name, x):
    c = UsdGeom.Cube.Define(stage, "/World/M4" + name)
    c.GetSizeAttr().Set(1.0)
    xp = UsdGeom.Xformable(c.GetPrim())
    xp.AddTranslateOp().Set(Gf.Vec3d(x, 0, 0.15))
    xp.AddScaleOp().Set(Gf.Vec3f(0.2, 0.2, 0.3))
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())


_shelf("ShelfA", 0.55)
_shelf("ShelfB", -0.55)
blk = UsdGeom.Cube.Define(stage, "/World/M4Block")
blk.GetSizeAttr().Set(0.12)
UsdGeom.Xformable(blk.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(0.55, 0, 0.36))
UsdPhysics.RigidBodyAPI.Apply(blk.GetPrim())
UsdPhysics.CollisionAPI.Apply(blk.GetPrim())
UsdPhysics.MassAPI.Apply(blk.GetPrim()).GetMassAttr().Set(0.3)
print("M4-BUILD-OK arm+shelves+block")
