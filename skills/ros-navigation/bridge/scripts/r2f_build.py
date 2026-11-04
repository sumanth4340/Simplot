"""R2 build (runs INSIDE Isaac Sim via bridge).

Creates /World/R2Bot: kinematic base + 2 revolute links (J1 driven
at constant velocity so positions move), and graph /ROS2/R2F:
OnPlaybackTick + IsaacReadSimulationTime -> ROS2PublishJointState
(targetPrim -> /World/R2Bot, topic /joint_states_f).
"""
import omni.graph.core as og
import omni.usd
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/World/R2Bot").IsValid():
    st.RemovePrim("/World/R2Bot")
if st.GetPrimAtPath("/ROS2/R2F").IsValid():
    st.RemovePrim("/ROS2/R2F")

root = UsdGeom.Xform.Define(st, "/World/R2Bot")
UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())
PhysxSchema.PhysxArticulationAPI.Apply(root.GetPrim())

# Base is DYNAMIC: PhysX excludes kinematic bodies from
# articulations, which yields zero joints. A FixedJoint below
# anchors it to the world instead.
base = UsdGeom.Xform.Define(st, "/World/R2Bot/base")
base.AddTranslateOp().Set(Gf.Vec3d(0, 0.25, 0))
cube = UsdGeom.Cube.Define(st, "/World/R2Bot/base/geo")
cube.GetSizeAttr().Set(0.5)
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).CreateMassAttr().Set(1.0)
PhysxSchema.PhysxRigidBodyAPI.Apply(
    base.GetPrim()).GetSleepThresholdAttr().Set(0.0)


def link(name, y, size, geo_y):
    L = UsdGeom.Xform.Define(st, "/World/R2Bot/" + name)
    L.AddTranslateOp().Set(Gf.Vec3d(0, y, 0))
    g = UsdGeom.Cube.Define(st, "/World/R2Bot/%s/geo" % name)
    g.GetSizeAttr().Set(size)
    g.AddTranslateOp().Set(Gf.Vec3d(0, geo_y, 0))
    UsdPhysics.CollisionAPI.Apply(g.GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(L.GetPrim())
    UsdPhysics.MassAPI.Apply(L.GetPrim()).CreateMassAttr().Set(1.0)
    PhysxSchema.PhysxRigidBodyAPI.Apply(
        L.GetPrim()).GetSleepThresholdAttr().Set(0.0)
    return L


l1 = link("link1", 0.7, 0.4, 0.2)
l2 = link("link2", 1.1, 0.3, 0.15)

fb = UsdPhysics.FixedJoint.Define(st, "/World/R2Bot/FixedBase")
fb.GetBody1Rel().SetTargets([base.GetPath()])
fb.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))

j1 = UsdPhysics.RevoluteJoint.Define(st, "/World/R2Bot/J1")
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

j2 = UsdPhysics.RevoluteJoint.Define(st, "/World/R2Bot/J2")
j2.GetBody0Rel().SetTargets([l1.GetPath()])
j2.GetBody1Rel().SetTargets([l2.GetPath()])
j2.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0.4, 0))
j2.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
j2.GetAxisAttr().Set("Z")

# Preferred wiring: IsaacReadJointState reads live PhysX state and
# feeds explicit arrays. (ROS2PublishJointState's targetPrim
# auto-read served a frozen snapshot in this setup: 8 samples at
# 60 Hz, advancing stamps, bit-identical values.)
keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/R2F", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ("RD", "isaacsim.sensors.physics.IsaacReadJointState"),
        ("JS", "isaacsim.ros2.bridge.ROS2PublishJointState"),
        ("CTL", "isaacsim.core.nodes.IsaacArticulationController")],
     keys.CONNECT: [
        ("/ROS2/R2F/OnPB.outputs:tick", "/ROS2/R2F/RD.inputs:execIn"),
        ("/ROS2/R2F/RD.outputs:execOut", "/ROS2/R2F/JS.inputs:execIn"),
        ("/ROS2/R2F/OnPB.outputs:tick", "/ROS2/R2F/CTL.inputs:execIn"),
        ("/ROS2/R2F/Time.outputs:simulationTime",
         "/ROS2/R2F/JS.inputs:timeStamp"),
        ("/ROS2/R2F/RD.outputs:jointNames",
         "/ROS2/R2F/JS.inputs:jointNames"),
        ("/ROS2/R2F/RD.outputs:jointPositions",
         "/ROS2/R2F/JS.inputs:jointPositions"),
        ("/ROS2/R2F/RD.outputs:jointVelocities",
         "/ROS2/R2F/JS.inputs:jointVelocities"),
        ("/ROS2/R2F/RD.outputs:jointEfforts",
         "/ROS2/R2F/JS.inputs:jointEfforts"),
        ("/ROS2/R2F/RD.outputs:jointDofTypes",
         "/ROS2/R2F/JS.inputs:jointDofTypes"),
        ("/ROS2/R2F/RD.outputs:sensorTime",
         "/ROS2/R2F/JS.inputs:sensorTime"),
        ("/ROS2/R2F/RD.outputs:stageMetersPerUnit",
         "/ROS2/R2F/JS.inputs:stageMetersPerUnit")],
     keys.SET_VALUES: [
        ("/ROS2/R2F/JS.inputs:topicName", "/joint_states_f"),
        ("/ROS2/R2F/JS.inputs:queueSize", 10),
        ("/ROS2/R2F/CTL.inputs:robotPath", "/World/R2Bot"),
        ("/ROS2/R2F/CTL.inputs:jointNames", ["J1", "J2"]),
        ("/ROS2/R2F/CTL.inputs:velocityCommand", [1.0, 0.0])]})
st.GetPrimAtPath("/ROS2/R2F/RD").GetRelationship(
    "inputs:prim").SetTargets(["/World/R2Bot"])
st.GetPrimAtPath("/ROS2/R2F/CTL").GetRelationship(
    "inputs:targetPrim").SetTargets(["/World/R2Bot"])

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/R2F").GetChildren())
tgt = st.GetPrimAtPath("/ROS2/R2F/RD").GetRelationship(
    "inputs:prim").GetTargets()
print("R2F-BUILD-OK nodes=%s target=%s" % (names, list(tgt)))
