import isaacsim.core.experimental.utils.app as app_utils
app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=30)
import omni.graph.core as og
for n in ("isaacsim.ros2.bridge.ROS2PublishClock",
          "omni.isaac.core_nodes.IsaacReadSimulationTime",
          "isaacsim.core.nodes.IsaacReadSimulationTime"):
    print("NTYPE %s=%s" % (n, og.get_node_type(n).is_valid()))
