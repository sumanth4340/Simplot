import omni.graph.core as og, omni.usd, json
st = omni.usd.get_context().get_stage()
keys = og.Controller.Keys
nodes = [("JS", "isaacsim.ros2.bridge.ROS2PublishJointState"),
         ("SUB", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
         ("TF", "isaacsim.ros2.bridge.ROS2PublishTransformTree"),
         ("CTL", "isaacsim.core.nodes.IsaacArticulationController")]
og.Controller.edit({"graph_path": "/ProbeROS",
                    "evaluator_name": "execution",
                    }, {keys.CREATE_NODES: [(n, t) for n, t in nodes]})
out = {}
for n, t in nodes:
    p = st.GetPrimAtPath("/ProbeROS/" + n)
    ins = sorted(str(a).split(".")[-1] for a in p.GetPropertiesInNamespace("inputs"))
    ous = sorted(str(a).split(".")[-1] for a in p.GetPropertiesInNamespace("outputs"))
    out[n] = {"in": ins, "out": ous}
st.RemovePrim("/ProbeROS")
print("ATTRS=" + json.dumps(out))
