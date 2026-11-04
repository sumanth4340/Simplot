import omni.graph.core as og, json
out = {}
for n in ["isaacsim.ros2.bridge.ROS2PublishJointState",
          "isaacsim.ros2.bridge.ROS2SubscribeJointState",
          "isaacsim.ros2.bridge.ROS2PublishTransformTree",
          "isaacsim.ros2.bridge.ROS2PublishRawTransformTree",
          "isaacsim.core.nodes.IsaacArticulationController"]:
    t = og.get_node_type(n)
    if t is None or not t.is_valid():
        out[n] = None; continue
    attrs = {}
    for a in t.get_attributes() if hasattr(t, "get_attributes") else []:
        try:
            attrs[str(a.get_name())] = str(a.get_type_name())
        except Exception:
            pass
    out[n] = attrs or "VALID-NO-ATTRS-API"
print("PROBE-ROS2=" + json.dumps(out))
