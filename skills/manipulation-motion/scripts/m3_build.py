"""M3 build (M2 v4 geometry) (runs INSIDE Isaac Sim): 2-DOF pitch arm, wide clearance.

v1/v2: flush cubes self-collide on any pitch (failures.md R5).
v3: 0.3-cubes/0.15 gaps clear +/-45 deg, but the M2 target needed
64-deg elbow bends -> unreachable on both IK branches.
v4: 0.2-cube links with 0.2 gaps clear +/-63 deg; L1=L2=0.4, site
rest z=1.8, target (0.32,0,1.68) needs <=45 deg on both branches.
"""
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/M1Bot", "/World/M1Ground", "/World/M1Target",
          "/World/M2Bot", "/World/M2Ground", "/World/M2Target",
          "/World/M3Bot", "/World/M3Ground", "/World/M3Target",
          "/World/YBot", "/World/YGround",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/M3Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
UsdGeom.Xform.Define(stage, "/World/M3Bot")


def _link(name, size, z, mass, root=False):
    c = UsdGeom.Cube.Define(stage, "/World/M3Bot/" + name)
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
    j = UsdPhysics.RevoluteJoint.Define(stage, "/World/M3Bot/" + name)
    j.GetBody0Rel().AddTarget("/World/M3Bot/" + b0)
    j.GetBody1Rel().AddTarget("/World/M3Bot/" + b1)
    j.GetLocalPos0Attr().Set(Gf.Vec3f(*a0))
    j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
    j.GetLocalPos1Attr().Set(Gf.Vec3f(*a1))
    j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
    j.GetAxisAttr().Set(UsdPhysics.Tokens.y)
    d = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
    d.CreateTypeAttr().Set("force")
    d.CreateStiffnessAttr().Set(100000.0)
    d.CreateDampingAttr().Set(10000.0)
    d.CreateMaxForceAttr().Set(1000000.0)
    d.CreateTargetPositionAttr().Set(0.0)


_link("Base", 1.0, 0.5, 2.0, root=True)
fx = UsdPhysics.FixedJoint.Define(stage, "/World/M3Bot/RootFixed")
fx.GetBody0Rel().AddTarget("/World/M3Bot")
fx.GetBody1Rel().AddTarget("/World/M3Bot/Base")
fx.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0))
fx.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
fx.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
fx.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
_link("Link1", 0.2, 1.3, 1.0)
_hinge("Hinge1", "Base", (0, 0, 0.5), "Link1", (0, 0, -0.3))
_link("Link2", 0.2, 1.7, 0.5)
_hinge("Hinge2", "Link1", (0, 0, 0.1), "Link2", (0, 0, -0.3))
site = UsdGeom.Xform.Define(stage, "/World/M3Bot/Link2/GraspSite")
UsdGeom.Xformable(site.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.1))
site.GetPrim().ApplyAPI("IsaacSiteAPI")
tgt = UsdGeom.Cube.Define(stage, "/World/M3Target")
tgt.GetSizeAttr().Set(0.1)
UsdGeom.Xformable(tgt.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(0.32, 0, 1.68))
print("M3-BUILD-OK arm+site+target")
