"""R2G test: targetPrim auto-read + CTL drive, fresh graph/topic."""
import omni.graph.core as og
import omni.usd
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf

st = omni.usd.get_context().get_stage()
for p in ("/World/R2BotG", "/ROS2/R2G"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)

root = UsdGeom.Xform.Define(st, "/World/R2BotG")
UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())
PhysxSchema.PhysxArticulationAPI.Apply(root.GetPrim())
base = UsdGeom.Xform.Define(st, "/World/R2BotG/base")
base.AddTranslateOp().Set(Gf.Vec3d(0, 0.25, 0))
cube = UsdGeom.Cube.Define(st, "/World/R2BotG/base/geo")
cube.GetSizeAttr().Set(0.5)
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).CreateMassAttr().Set(1.0)
PhysxSchema.PhysxRigidBodyAPI.Apply(
    base.GetPrim()).GetSleepThresholdAttr().Set(0.0)


def link(name, y, size, geo_y):
    L = UsdGeom.Xform.Define(st, "/World/R2BotG/" + name)
    L.AddTranslateOp().Set(Gf.Vec3d(0, y, 0))
    g = UsdGeom.Cube.Define(st, "/World/R2BotG/%s/geo" % name)
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
fb = UsdPhysics.FixedJoint.Define(st, "/World/R2BotG/FixedBase")
fb.GetBody1Rel().SetTargets([base.GetPath()])
fb.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
j1 = UsdPhysics.RevoluteJoint.Define(st, "/World/R2BotG/J1")
j1.GetBody0Rel().SetTargets([base.GetPath()])
j1.GetBody1Rel().SetTargets([l1.GetPath()])
j1.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0.25, 0))
j1.GetLocalPos1Attr().Set(Gf.Vec3f(0, -0.2, 0))
j1.GetAxisAttr().Set("Z")
drv = UsdPhysics.DriveAPI.Apply(j1.GetPrim(), "angular")
drv.GetTargetVelocityAttr().Set(1.0)
drv.GetStiffnessAttr().Set(0.0)
drv.GetDampingAttr().Set(50.0)
drv.GetMaxForceAttr().Set(100.0)
j2 = UsdPhysics.RevoluteJoint.Define(st, "/World/R2BotG/J2")
j2.GetBody0Rel().SetTargets([l1.GetPath()])
j2.GetBody1Rel().SetTargets([l2.GetPath()])
j2.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0.4, 0))
j2.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
j2.GetAxisAttr().Set("Z")

keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/R2G", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ("JS", "isaacsim.ros2.bridge.ROS2PublishJointState"),
        ("CTL", "isaacsim.core.nodes.IsaacArticulationController")],
     keys.CONNECT: [
        ("/ROS2/R2G/OnPB.outputs:tick", "/ROS2/R2G/JS.inputs:execIn"),
        ("/ROS2/R2G/OnPB.outputs:tick", "/ROS2/R2G/CTL.inputs:execIn"),
        ("/ROS2/R2G/Time.outputs:simulationTime",
         "/ROS2/R2G/JS.inputs:timeStamp")],
     keys.SET_VALUES: [
        ("/ROS2/R2G/JS.inputs:topicName", "/joint_states_g"),
        ("/ROS2/R2G/JS.inputs:queueSize", 10),
        ("/ROS2/R2G/CTL.inputs:robotPath", "/World/R2BotG"),
        ("/ROS2/R2G/CTL.inputs:jointNames", ["J1", "J2"]),
        ("/ROS2/R2G/CTL.inputs:velocityCommand", [1.0, 0.0])]})
st.GetPrimAtPath("/ROS2/R2G/JS").GetRelationship(
    "inputs:targetPrim").SetTargets(["/World/R2BotG"])
st.GetPrimAtPath("/ROS2/R2G/CTL").GetRelationship(
    "inputs:targetPrim").SetTargets(["/World/R2BotG"])
print("R2G-BUILD-OK")
