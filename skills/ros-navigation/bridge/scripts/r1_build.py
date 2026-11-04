"""R1 build (runs INSIDE Isaac Sim): clock bridge graph.

Enables isaacsim.ros2.bridge, builds R1Clock graph: OnPlaybackTick
+ IsaacReadSimulationTime + ROS2PublishClock (topic "clock").
Skill 9 atomic-edit + full-path rules apply.
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd

stage = omni.usd.get_context().get_stage()
app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=30)
o = stage.GetPrimAtPath("/World/R1Clock")
if o and o.IsValid():
    stage.RemovePrim("/World/R1Clock")
keys = og.Controller.Keys
og.Controller.edit("/World/R1Clock", {
    keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ("Clock", "isaacsim.ros2.bridge.ROS2PublishClock"),
    ],
    keys.CONNECT: [
        ("OnPB.outputs:tick", "Clock.inputs:execIn"),
        ("Time.outputs:simulationTime", "Clock.inputs:timeStamp"),
    ],
    keys.SET_VALUES: [
        ("Clock.inputs:topicName", "clock"),
        ("Clock.inputs:queueSize", 10),
    ],
})
gp = stage.GetPrimAtPath("/World/R1Clock")
nodes = sorted(c.GetName() for c in gp.GetChildren())
up = og.ObjectLookup.attribute(
    "/World/R1Clock/Clock.inputs:timeStamp").get_upstream_connections()
print("R1-BUILD-OK graph=%s nodes=%s linked=%s" % (
    gp.IsValid(), nodes, len(up) == 1))
