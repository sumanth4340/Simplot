"""Manual-array test build (runs INSIDE Isaac Sim via bridge).

Builds /ROS2/R2MAN (leaves /ROS2/R2 and /World/R2Bot untouched):
  A. reader path: OnPB -> IsaacReadJointState.execIn (prim -> /World/R2Bot)
     -> execOut -> PubJS.execIn, all joint arrays + sensorTime +
     stageMetersPerUnit wired, topic /joint_states_manual
  B. static path: OnPB -> PubStatic.execIn with literal jointNames /
     jointPositions, topic /joint_states_static
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd

app_utils.enable_extension("isaacsim.sensors.physics.nodes")
await app_utils.update_app_async(steps=30)

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/R2MAN").IsValid():
    st.RemovePrim("/ROS2/R2MAN")

keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/R2MAN", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("ReadJS", "isaacsim.sensors.physics.IsaacReadJointState"),
        ("PubJS", "isaacsim.ros2.bridge.ROS2PublishJointState"),
        ("PubStatic", "isaacsim.ros2.bridge.ROS2PublishJointState")],
     keys.CONNECT: [
        ("/ROS2/R2MAN/OnPB.outputs:tick",
         "/ROS2/R2MAN/ReadJS.inputs:execIn"),
        ("/ROS2/R2MAN/ReadJS.outputs:execOut",
         "/ROS2/R2MAN/PubJS.inputs:execIn"),
        ("/ROS2/R2MAN/OnPB.outputs:tick",
         "/ROS2/R2MAN/PubStatic.inputs:execIn"),
        ("/ROS2/R2MAN/ReadJS.outputs:jointDofTypes",
         "/ROS2/R2MAN/PubJS.inputs:jointDofTypes"),
        ("/ROS2/R2MAN/ReadJS.outputs:jointEfforts",
         "/ROS2/R2MAN/PubJS.inputs:jointEfforts"),
        ("/ROS2/R2MAN/ReadJS.outputs:jointNames",
         "/ROS2/R2MAN/PubJS.inputs:jointNames"),
        ("/ROS2/R2MAN/ReadJS.outputs:jointPositions",
         "/ROS2/R2MAN/PubJS.inputs:jointPositions"),
        ("/ROS2/R2MAN/ReadJS.outputs:jointVelocities",
         "/ROS2/R2MAN/PubJS.inputs:jointVelocities"),
        ("/ROS2/R2MAN/ReadJS.outputs:sensorTime",
         "/ROS2/R2MAN/PubJS.inputs:sensorTime"),
        ("/ROS2/R2MAN/ReadJS.outputs:stageMetersPerUnit",
         "/ROS2/R2MAN/PubJS.inputs:stageMetersPerUnit")],
     keys.SET_VALUES: [
        ("/ROS2/R2MAN/PubJS.inputs:topicName", "/joint_states_manual"),
        ("/ROS2/R2MAN/PubJS.inputs:queueSize", 10),
        ("/ROS2/R2MAN/PubStatic.inputs:topicName",
         "/joint_states_static"),
        ("/ROS2/R2MAN/PubStatic.inputs:queueSize", 10),
        ("/ROS2/R2MAN/PubStatic.inputs:jointNames", ["J1", "J2"]),
        ("/ROS2/R2MAN/PubStatic.inputs:jointPositions", [0.1, 0.2])]})

rp = st.GetPrimAtPath("/ROS2/R2MAN/ReadJS")
rel = rp.GetRelationship("inputs:prim")
if rel:
    rel.SetTargets(["/World/R2Bot"])
    primset = "rel:" + str(rel.GetTargets())
else:
    rp.GetAttribute("inputs:prim").Set("/World/R2Bot")
    primset = "attr"

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/R2MAN").GetChildren())
print("R2MAN-BUILD-OK nodes=%s prim=%s" % (names, primset))
