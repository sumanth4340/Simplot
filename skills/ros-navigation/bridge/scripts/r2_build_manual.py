"""R2 manual fallback build (runs INSIDE Isaac Sim via bridge).

Drop-in rebuild of /ROS2/R2 using the PREFERRED explicit-array path:
IsaacReadJointState -> ROS2PublishJointState (all 7 array/time
outputs wired). Same wiring as verified live on /joint_states_manual
(see evidence/r2_nodereq.md); this script targets /joint_states.

USE ONLY IF the targetPrim auto-read path fails: it DELETES and
rebuilds /ROS2/R2. Does not touch /World/R2Bot. Requires play to
publish (like all bridge graphs).
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd

app_utils.enable_extension("isaacsim.sensors.physics.nodes")
await app_utils.update_app_async(steps=30)

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/R2").IsValid():
    st.RemovePrim("/ROS2/R2")

keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/R2", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("ReadJS", "isaacsim.sensors.physics.IsaacReadJointState"),
        ("JS", "isaacsim.ros2.bridge.ROS2PublishJointState")],
     keys.CONNECT: [
        ("/ROS2/R2/OnPB.outputs:tick",
         "/ROS2/R2/ReadJS.inputs:execIn"),
        ("/ROS2/R2/ReadJS.outputs:execOut",
         "/ROS2/R2/JS.inputs:execIn"),
        ("/ROS2/R2/ReadJS.outputs:jointDofTypes",
         "/ROS2/R2/JS.inputs:jointDofTypes"),
        ("/ROS2/R2/ReadJS.outputs:jointEfforts",
         "/ROS2/R2/JS.inputs:jointEfforts"),
        ("/ROS2/R2/ReadJS.outputs:jointNames",
         "/ROS2/R2/JS.inputs:jointNames"),
        ("/ROS2/R2/ReadJS.outputs:jointPositions",
         "/ROS2/R2/JS.inputs:jointPositions"),
        ("/ROS2/R2/ReadJS.outputs:jointVelocities",
         "/ROS2/R2/JS.inputs:jointVelocities"),
        ("/ROS2/R2/ReadJS.outputs:sensorTime",
         "/ROS2/R2/JS.inputs:sensorTime"),
        ("/ROS2/R2/ReadJS.outputs:stageMetersPerUnit",
         "/ROS2/R2/JS.inputs:stageMetersPerUnit")],
     keys.SET_VALUES: [
        ("/ROS2/R2/JS.inputs:topicName", "/joint_states"),
        ("/ROS2/R2/JS.inputs:queueSize", 10)]})

st.GetPrimAtPath("/ROS2/R2/ReadJS").GetRelationship(
    "inputs:prim").SetTargets(["/World/R2Bot"])

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/R2").GetChildren())
tgt = st.GetPrimAtPath("/ROS2/R2/ReadJS").GetRelationship(
    "inputs:prim").GetTargets()
print("R2-MANUAL-BUILD-OK nodes=%s prim=%s" % (names, list(tgt)))
