"""Static-only graph test (runs INSIDE Isaac Sim via bridge).

Builds /ROS2/R2STAT (untouched R2/R2MAN/R2Bot): own OnPB + Time +
single ROS2PublishJointState with literal names/positions/velocities
+ wired timeStamp, topic /joint_states_stat2.
"""
import omni.graph.core as og
import omni.usd

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/R2STAT").IsValid():
    st.RemovePrim("/ROS2/R2STAT")

keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/R2STAT", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ("JS", "isaacsim.ros2.bridge.ROS2PublishJointState")],
     keys.CONNECT: [
        ("/ROS2/R2STAT/OnPB.outputs:tick",
         "/ROS2/R2STAT/JS.inputs:execIn"),
        ("/ROS2/R2STAT/Time.outputs:simulationTime",
         "/ROS2/R2STAT/JS.inputs:timeStamp")],
     keys.SET_VALUES: [
        ("/ROS2/R2STAT/JS.inputs:topicName", "/joint_states_stat2"),
        ("/ROS2/R2STAT/JS.inputs:queueSize", 10),
        ("/ROS2/R2STAT/JS.inputs:jointNames", ["J1", "J2"]),
        ("/ROS2/R2STAT/JS.inputs:jointPositions", [0.1, 0.2]),
        ("/ROS2/R2STAT/JS.inputs:jointVelocities", [0.0, 0.0])]})

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/R2STAT").GetChildren())
print("R2STAT-BUILD-OK nodes=%s" % names)
