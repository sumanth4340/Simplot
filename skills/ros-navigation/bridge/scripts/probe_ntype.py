import omni.graph.core as og
t = og.get_node_type("isaacsim.ros2.bridge.ROS2PublishJointState")
out = {"methods": sorted([m for m in dir(t) if not m.startswith("_")])}
for m in ["get_description", "get_metadata", "description", "get_attributes",
          "get_attribute_names", "get_version"]:
    if hasattr(t, m):
        try:
            v = getattr(t, m)()
            out[m] = str(v)[:3000]
        except Exception as e:
            out[m] = "ERR " + str(e)[:150]
print("NTYPE=" + str(out))
