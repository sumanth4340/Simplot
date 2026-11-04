"""R2 build (runs INSIDE Isaac Sim via bridge).

Creates /World/R2Bot: kinematic base + 2 revolute links (J1 driven
at constant velocity so positions move), and graph /ROS2/R2:
OnPlaybackTick + IsaacReadSimulationTime -> ROS2PublishJointState
(targetPrim -> /World/R2Bot, topic /joint_states).
"""
import time

import omni.graph.core as og
import omni.usd
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf

# UNIQUE articulation path per build: the OG sensor/PhysX layer
# caches articulation handles by USD path and never invalidates on
# RemovePrim, so rebuilding at a fixed path reads a GHOST (frozen
# previous-play values). Fresh paths stay live (verified 2x2).
ART = "/World/R2Bot_%d" % int(time.time())

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/R2").IsValid():
    st.RemovePrim("/ROS2/R2")
for c in list(st.GetPrimAtPath("/World").GetChildren()):
    if c.GetName().startswith("R2Bot"):
        st.RemovePrim(c.GetPath())

root = UsdGeom.Xform.Define(st, ART)
UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())
PhysxSchema.PhysxArticulationAPI.Apply(root.GetPrim())

# Base is DYNAMIC: PhysX excludes kinematic bodies from
# articulations, which yields zero joints. A FixedJoint below
# anchors it to the world instead.
base = UsdGeom.Xform.Define(st, ART + "/base")
base.AddTranslateOp().Set(Gf.Vec3d(0, 0.25, 0))
cube = UsdGeom.Cube.Define(st, ART + "/base/geo")
cube.GetSizeAttr().Set(0.5)
# NO CollisionAPI: spinning links would weld on contact and freeze.
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).CreateMassAttr().Set(1.0)
PhysxSchema.PhysxRigidBodyAPI.Apply(
    base.GetPrim()).GetSleepThresholdAttr().Set(0.0)


def link(name, y, size, geo_y):
    L = UsdGeom.Xform.Define(st, ART + "/" + name)
    L.AddTranslateOp().Set(Gf.Vec3d(0, y, 0))
    g = UsdGeom.Cube.Define(st, ART + "/%s/geo" % name)
    g.GetSizeAttr().Set(size)
    g.AddTranslateOp().Set(Gf.Vec3d(0, geo_y, 0))
    UsdPhysics.RigidBodyAPI.Apply(L.GetPrim())
    UsdPhysics.MassAPI.Apply(L.GetPrim()).CreateMassAttr().Set(1.0)
    PhysxSchema.PhysxRigidBodyAPI.Apply(
        L.GetPrim()).GetSleepThresholdAttr().Set(0.0)
    return L


l1 = link("link1", 0.7, 0.4, 0.2)
l2 = link("link2", 1.1, 0.3, 0.15)

fb = UsdPhysics.FixedJoint.Define(st, ART + "/FixedBase")
fb.GetBody1Rel().SetTargets([base.GetPath()])
fb.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))

j1 = UsdPhysics.RevoluteJoint.Define(st, ART + "/J1")
j1.GetBody0Rel().SetTargets([base.GetPath()])
j1.GetBody1Rel().SetTargets([l1.GetPath()])
j1.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0.25, 0))
j1.GetLocalPos1Attr().Set(Gf.Vec3f(0, -0.2, 0))
j1.GetAxisAttr().Set("Z")
# Authored drive allocates the drive model (gains); the DOF still
# defaults to effort mode, so r2_drive PLAY must ALSO call
# set_dof_velocity_targets to switch J1 into velocity mode.
# Either one alone yields zero motion (verified live).
drv = UsdPhysics.DriveAPI.Apply(j1.GetPrim(), "angular")
drv.GetTargetVelocityAttr().Set(1.0)
drv.GetStiffnessAttr().Set(0.0)
drv.GetDampingAttr().Set(50.0)
drv.GetMaxForceAttr().Set(100.0)

j2 = UsdPhysics.RevoluteJoint.Define(st, ART + "/J2")
j2.GetBody0Rel().SetTargets([l1.GetPath()])
j2.GetBody1Rel().SetTargets([l2.GetPath()])
j2.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0.4, 0))
j2.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
j2.GetAxisAttr().Set("Z")

# Wiring: ROS2PublishJointState.targetPrim auto-read (LIVE per
# tick, verified) + IsaacArticulationController driving both DOFs.
# (The IsaacReadJointState -> explicit-array wiring served a
# match-time snapshot: frozen values + fresh stamps. Avoid it.)
# CTL needs robotPath (rel alone is ignored) + jointNames.
keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/R2", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ("JS", "isaacsim.ros2.bridge.ROS2PublishJointState"),
        ("CTL", "isaacsim.core.nodes.IsaacArticulationController")],
     keys.CONNECT: [
        ("/ROS2/R2/OnPB.outputs:tick", "/ROS2/R2/JS.inputs:execIn"),
        ("/ROS2/R2/OnPB.outputs:tick", "/ROS2/R2/CTL.inputs:execIn"),
        ("/ROS2/R2/Time.outputs:simulationTime",
         "/ROS2/R2/JS.inputs:timeStamp")],
     keys.SET_VALUES: [
        ("/ROS2/R2/JS.inputs:topicName", "/joint_states"),
        ("/ROS2/R2/JS.inputs:queueSize", 10),
        ("/ROS2/R2/CTL.inputs:robotPath", ART),
        ("/ROS2/R2/CTL.inputs:jointNames", ["J1", "J2"]),
        ("/ROS2/R2/CTL.inputs:velocityCommand", [1.0, 1.0])]})
st.GetPrimAtPath("/ROS2/R2/JS").GetRelationship(
    "inputs:targetPrim").SetTargets([ART])
st.GetPrimAtPath("/ROS2/R2/CTL").GetRelationship(
    "inputs:targetPrim").SetTargets([ART])

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/R2").GetChildren())
tgt = st.GetPrimAtPath("/ROS2/R2/JS").GetRelationship(
    "inputs:targetPrim").GetTargets()
print("R2-BUILD-OK nodes=%s target=%s" % (names, list(tgt)))

