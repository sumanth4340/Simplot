"""N1 build (runs INSIDE Isaac Sim via bridge).

Skid-steer base /World/N1Base_<ts> (chassis + 4 wheel joints, all
with velocity drives) on a ground plane + graph /ROS2/N1:
OnPlaybackTick -> IsaacComputeOdometry (chassis) ->
ROS2PublishOdometry (/odom) + IsaacArticulationController
(wheel velocities [1.0]*4).
"""
import time

import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf

# ROS2 graph nodes need the bridge extension (fresh sims lack it).
app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=10)

ART = "/World/N1Base_%d" % int(time.time())

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/N1").IsValid():
    st.RemovePrim("/ROS2/N1")
for c in list(st.GetPrimAtPath("/World").GetChildren()):
    if c.GetName().startswith(("N1Base", "R4Bot", "R3Bot", "R2Bot")):
        st.RemovePrim(c.GetPath())
for g in ("/ROS2/R2", "/ROS2/R3", "/ROS2/R4"):
    if st.GetPrimAtPath(g).IsValid():
        st.RemovePrim(g)

# NOTE: do NOT define a scene here: the stage already owns
# /PhysicsScene (root). A second scene splits/double-steps bodies.
# Scrub any stale duplicate (e.g. leftover /World/PhysicsScene).
if st.GetPrimAtPath("/World/PhysicsScene").IsValid():
    st.RemovePrim("/World/PhysicsScene")
if st.GetPrimAtPath("/World/N1Ground").IsValid():
    st.RemovePrim("/World/N1Ground")
# Translate-first: position on parent Xform, scale on child mesh.
# NOTE: stage is Z-up (gravity -Z). Author everything Z-up.
gnd = UsdGeom.Xform.Define(st, "/World/N1Ground")
gnd.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
gg = UsdGeom.Cube.Define(st, "/World/N1Ground/geo")
gg.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(gg.GetPrim()).AddScaleOp().Set(
    Gf.Vec3f(20.0, 20.0, 0.1))
UsdPhysics.CollisionAPI.Apply(gg.GetPrim())

root = UsdGeom.Xform.Define(st, ART)
UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())
_pa = PhysxSchema.PhysxArticulationAPI.Apply(root.GetPrim())
_pa.GetSolverPositionIterationCountAttr().Set(64)
_pa.GetSolverVelocityIterationCountAttr().Set(16)

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

wnames = []
for wx, wz in ((0.18, 0.22), (0.18, -0.22),
               (-0.18, 0.22), (-0.18, -0.22)):
    wn = "W_%s%d_%s%d" % ("p" if wx >= 0 else "m", abs(int(wx * 100)),
                               "p" if wz >= 0 else "m", abs(int(wz * 100)))
    wnames.append("J_" + wn)
    w = UsdGeom.Xform.Define(st, ART + "/" + wn)
    w.AddTranslateOp().Set(Gf.Vec3d(wx, wz, 0.115))
    # Collision approximation: analytic sphere collider (USD cylinders
    # cook to faceted convex hulls whose facet slap shakes the base).
    # Visual cylinder rides along with no physics APIs.
    wg = UsdGeom.Sphere.Define(st, ART + "/" + wn + "/col")
    wg.GetRadiusAttr().Set(0.1)
    wv = UsdGeom.Cylinder.Define(st, ART + "/" + wn + "/col/vis")
    wv.GetAxisAttr().Set("Y")
    wv.GetRadiusAttr().Set(0.1)
    wv.GetHeightAttr().Set(0.03)
    UsdPhysics.CollisionAPI.Apply(wg.GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(wg.GetPrim())
    UsdPhysics.MassAPI.Apply(wg.GetPrim()).CreateMassAttr().Set(0.5)
    _wpx = PhysxSchema.PhysxRigidBodyAPI.Apply(wg.GetPrim())
    _wpx.GetSleepThresholdAttr().Set(0.0)
    _wpx.GetSolverPositionIterationCountAttr().Set(32)
    _wpx.GetSolverVelocityIterationCountAttr().Set(8)
    j = UsdPhysics.RevoluteJoint.Define(st, ART + "/J_" + wn)
    j.GetBody0Rel().SetTargets([ch.GetPath()])
    j.GetBody1Rel().SetTargets([wg.GetPath()])
    j.GetLocalPos0Attr().Set(Gf.Vec3f(wx, wz, -0.15))
    j.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
    j.GetAxisAttr().Set("Y")
    drv = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
    drv.GetTargetVelocityAttr().Set(1.0)
    drv.GetStiffnessAttr().Set(0.0)
    drv.GetDampingAttr().Set(2.0)
    drv.GetMaxForceAttr().Set(2.0)

jn = wnames
keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/N1", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ("ODO", "isaacsim.core.nodes.IsaacComputeOdometry"),
        ("PUB", "isaacsim.ros2.bridge.ROS2PublishOdometry"),
        ("CTL", "isaacsim.core.nodes.IsaacArticulationController")],
     keys.CONNECT: [
        ("/ROS2/N1/OnPB.outputs:tick", "/ROS2/N1/ODO.inputs:execIn"),
        ("/ROS2/N1/ODO.outputs:execOut", "/ROS2/N1/PUB.inputs:execIn"),
        ("/ROS2/N1/OnPB.outputs:tick", "/ROS2/N1/CTL.inputs:execIn"),
        ("/ROS2/N1/Time.outputs:simulationTime",
         "/ROS2/N1/PUB.inputs:timeStamp"),
        ("/ROS2/N1/ODO.outputs:position",
         "/ROS2/N1/PUB.inputs:position"),
        ("/ROS2/N1/ODO.outputs:orientation",
         "/ROS2/N1/PUB.inputs:orientation"),
        ("/ROS2/N1/ODO.outputs:linearVelocity",
         "/ROS2/N1/PUB.inputs:linearVelocity"),
        ("/ROS2/N1/ODO.outputs:angularVelocity",
         "/ROS2/N1/PUB.inputs:angularVelocity")],
     keys.SET_VALUES: [
        ("/ROS2/N1/PUB.inputs:topicName", "/odom"),
        ("/ROS2/N1/PUB.inputs:queueSize", 10),
        ("/ROS2/N1/PUB.inputs:odomFrameId", "odom"),
        ("/ROS2/N1/PUB.inputs:chassisFrameId", "base_link"),
        ("/ROS2/N1/CTL.inputs:robotPath", ART),
        ("/ROS2/N1/CTL.inputs:jointNames", jn),
        # +1 about Y rolls +X (patch-relative -X).
        ("/ROS2/N1/CTL.inputs:velocityCommand", [1.0] * 4)]})
odo = st.GetPrimAtPath("/ROS2/N1/ODO")
rel = odo.GetRelationship("inputs:chassisPrim")
if rel.IsValid():
    rel.SetTargets([ch.GetPath()])
else:
    odo.GetAttribute("inputs:chassisPrim").Set(ch.GetPath().pathString)
st.GetPrimAtPath("/ROS2/N1/CTL").GetRelationship(
    "inputs:targetPrim").SetTargets([ART])

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/N1").GetChildren())
print("N1-BUILD-OK nodes=%s art=%s" % (names, ART))
