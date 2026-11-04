"""AvoidBot build (runs INSIDE Isaac Sim via bridge --file).

Two-wheel differential-drive bot /World/AvoidBot (dynamic chassis +
wheel_l/wheel_r revolute joints about the Y axle, velocity drives)
on a ground plane, plus three fixed cuboid obstacles Obs0/Obs1/Obs2.
Clean-slate: removes prior AvoidBot/Obs/FPCheck prims first.
Structure-only: no ROS graph, no isaacsim imports.
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf

ART = "/World/AvoidBot"

st = omni.usd.get_context().get_stage()
for c in list(st.GetPrimAtPath("/World").GetChildren()):
    if c.GetName().startswith(("AvoidBot", "Obs", "FPCheck", "Fence", "Goal")):
        st.RemovePrim(c.GetPath())

# NOTE: do NOT define a scene here: the stage already owns
# /PhysicsScene (root). A second scene splits/double-steps bodies.
# Scrub any stale duplicate (e.g. leftover /World/PhysicsScene).
if st.GetPrimAtPath("/World/PhysicsScene").IsValid():
    st.RemovePrim("/World/PhysicsScene")
if not st.GetPrimAtPath("/PhysicsScene").IsValid():
    _scn = UsdPhysics.Scene.Define(st, "/PhysicsScene")
    _scn.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
    _scn.CreateGravityMagnitudeAttr().Set(9.81)

# Translate-first: position on parent Xform, scale on child mesh.
# NOTE: stage is Z-up (gravity -Z). Author everything Z-up.
# Ground top surface exactly at z=0.
gnd = UsdGeom.Xform.Define(st, "/World/AvoidBotGround")
gnd.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
gg = UsdGeom.Cube.Define(st, "/World/AvoidBotGround/geo")
gg.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(gg.GetPrim()).AddScaleOp().Set(
    Gf.Vec3f(20.0, 20.0, 0.1))
UsdPhysics.CollisionAPI.Apply(gg.GetPrim())

# Mobile base: free-floating articulation root (mirrors n1_build).
# ArticulationRootAPI on the Xform + DYNAMIC chassis child. No
# FixedJoint: this is a mobile base, pinning it would freeze the bot.
# (R1 failure is root-on-Xform + STATIC base; dynamic chassis avoids it.)
root = UsdGeom.Xform.Define(st, ART)
UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())
_pa = PhysxSchema.PhysxArticulationAPI.Apply(root.GetPrim())
_pa.GetSolverPositionIterationCountAttr().Set(64)
_pa.GetSolverVelocityIterationCountAttr().Set(16)

# Chassis 0.4(x) x 0.3(y) x 0.15(z), facing +X (caster at +X front).
# Bottom at 0.19 clears the wheel-sphere tops (0.1856 at chassis edge).
ch = UsdGeom.Xform.Define(st, ART + "/chassis")
ch.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.265))
cg = UsdGeom.Cube.Define(st, ART + "/chassis/geo")
cg.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cg.GetPrim()).AddScaleOp().Set(
    Gf.Vec3f(0.4, 0.3, 0.15))
UsdPhysics.CollisionAPI.Apply(cg.GetPrim())
UsdPhysics.RigidBodyAPI.Apply(ch.GetPrim())
UsdPhysics.MassAPI.Apply(ch.GetPrim()).CreateMassAttr().Set(2.0)
_chpx = PhysxSchema.PhysxRigidBodyAPI.Apply(ch.GetPrim())
_chpx.GetSleepThresholdAttr().Set(0.0)
_chpx.GetSolverPositionIterationCountAttr().Set(32)
_chpx.GetSolverVelocityIterationCountAttr().Set(8)

# Front caster: FREE-SPINNING small wheel on its own revolute joint
# (a rigidly-fixed caster ball drags and stoppies the bot nose-down --
# probe evidence 2026-11-04: pitch 47.5 deg under drive). World
# (0.15, 0, 0.045), bottom at +1.5 cm like the wheels. No drive:
# zero damping/stiffness, spins freely about the Y axle.
cx = UsdGeom.Xform.Define(st, ART + "/caster")
cx.AddTranslateOp().Set(Gf.Vec3d(0.15, 0, 0.045))
cg = UsdGeom.Sphere.Define(st, ART + "/caster/col")
cg.GetRadiusAttr().Set(0.03)
UsdPhysics.CollisionAPI.Apply(cg.GetPrim())
UsdPhysics.RigidBodyAPI.Apply(cg.GetPrim())
UsdPhysics.MassAPI.Apply(cg.GetPrim()).CreateMassAttr().Set(0.1)
PhysxSchema.PhysxRigidBodyAPI.Apply(cg.GetPrim()).GetSleepThresholdAttr().Set(0.0)
cj = UsdPhysics.RevoluteJoint.Define(st, ART + "/joint_caster")
cj.GetBody0Rel().SetTargets([ch.GetPath()])
cj.GetBody1Rel().SetTargets([cg.GetPath()])
cj.GetLocalPos0Attr().Set(Gf.Vec3f(0.15, 0, -0.22))
cj.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
cj.GetAxisAttr().Set("Y")

# Wheels: analytic SPHERE colliders carrying RigidBody+Collision+Mass
# (N1 rolling-collider rule: raw USD Cylinder collision cooks to a
# faceted hull and each facet slap pumps a hop the velocity drives
# re-accelerate into). Visual cylinders ride along with no physics APIs.
# Axle along Y at x=-0.05 (behind COM: stable tripod with the front
# caster; support x in [-0.05, +0.15] contains the COM). Centers
# z = r 0.09 + 1.5 cm spawn clearance.
for wn, wy in (("wheel_l", 0.19), ("wheel_r", -0.19)):
    w = UsdGeom.Xform.Define(st, ART + "/" + wn)
    w.AddTranslateOp().Set(Gf.Vec3d(-0.05, wy, 0.105))
    wg = UsdGeom.Sphere.Define(st, ART + "/" + wn + "/col")
    wg.GetRadiusAttr().Set(0.09)
    wv = UsdGeom.Cylinder.Define(st, ART + "/" + wn + "/col/vis")
    wv.GetAxisAttr().Set("Y")
    wv.GetRadiusAttr().Set(0.09)
    wv.GetHeightAttr().Set(0.03)
    UsdPhysics.CollisionAPI.Apply(wg.GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(wg.GetPrim())
    UsdPhysics.MassAPI.Apply(wg.GetPrim()).CreateMassAttr().Set(0.5)
    _wpx = PhysxSchema.PhysxRigidBodyAPI.Apply(wg.GetPrim())
    _wpx.GetSleepThresholdAttr().Set(0.0)
    _wpx.GetSolverPositionIterationCountAttr().Set(32)
    _wpx.GetSolverVelocityIterationCountAttr().Set(8)
    j = UsdPhysics.RevoluteJoint.Define(
        st, ART + "/" + wn.replace("wheel_", "joint_"))
    j.GetBody0Rel().SetTargets([ch.GetPath()])
    j.GetBody1Rel().SetTargets([wg.GetPath()])
    j.GetLocalPos0Attr().Set(Gf.Vec3f(-0.05, wy, -0.16))
    j.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
    j.GetAxisAttr().Set("Y")
    drv = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
    drv.GetTargetVelocityAttr().Set(0.0)
    drv.GetStiffnessAttr().Set(0.0)
    drv.GetDampingAttr().Set(2.0)
    drv.GetMaxForceAttr().Set(2.0)

# Fixed obstacles: static colliders (no RigidBody), resting on z=0.
for on, ox, oy in (("Obs0", 2.0, 0.0),
                   ("Obs1", 3.2, -0.8),
                   ("Obs2", 3.2, 0.8)):
    ob = UsdGeom.Xform.Define(st, "/World/" + on)
    ob.AddTranslateOp().Set(Gf.Vec3d(ox, oy, 0.25))
    obg = UsdGeom.Cube.Define(st, "/World/" + on + "/geo")
    obg.GetSizeAttr().Set(1.0)
    UsdGeom.Xformable(obg.GetPrim()).AddScaleOp().Set(
        Gf.Vec3f(0.5, 0.5, 0.5))
    UsdPhysics.CollisionAPI.Apply(obg.GetPrim())

# Fence: 4 fixed walls enclosing the course (x -1..6, y -2..2),
# 0.5 tall so the roof lidar (z~0.385) sees them as obstacles.
# The bot starts at the origin with 1 m+ clearance on all sides.
for fn, fx, fy, sx, sy in (("FenceXm", -1.0, 0.0, 0.1, 4.1),
                           ("FenceXp", 6.0, 0.0, 0.1, 4.1),
                           ("FenceYm", 2.5, -2.0, 7.1, 0.1),
                           ("FenceYp", 2.5, 2.0, 7.1, 0.1)):
    fb = UsdGeom.Xform.Define(st, "/World/" + fn)
    fb.AddTranslateOp().Set(Gf.Vec3d(fx, fy, 0.25))
    fbg = UsdGeom.Cube.Define(st, "/World/" + fn + "/geo")
    fbg.GetSizeAttr().Set(1.0)
    UsdGeom.Xformable(fbg.GetPrim()).AddScaleOp().Set(
        Gf.Vec3f(sx, sy, 0.5))
    UsdPhysics.CollisionAPI.Apply(fbg.GetPrim())

jn = sorted(str(c.GetName()) for c in st.GetPrimAtPath(ART).GetChildren()
            if c.GetTypeName() == "PhysicsRevoluteJoint")
nf = sum(1 for c in st.GetPrimAtPath("/World").GetChildren()
         if c.GetName().startswith("Fence"))
# Goal pad: visual-only flat marker (NO collider: the bot drives over
# it freely and the physics lidar ignores it). Center (5.0, 0).
gp = UsdGeom.Xform.Define(st, "/World/Goal")
gp.AddTranslateOp().Set(Gf.Vec3d(5.0, 0.0, 0.01))
gpg = UsdGeom.Cube.Define(st, "/World/Goal/geo")
gpg.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(gpg.GetPrim()).AddScaleOp().Set(
    Gf.Vec3f(1.0, 1.0, 0.02))
print("AVOIDBOT-BUILD-OK joints=%s art=%s fence_walls=%d goal=5.0,0.0"
      % (jn, ART, nf))
