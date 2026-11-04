import omni.graph.core as og, omni.usd, json
st = omni.usd.get_context().get_stage()
cands = ["isaacsim.ros2.bridge.ROS2PublishOdometry",
         "isaacsim.ros2.bridge.ROS2PublishLaserScan",
         "isaacsim.ros2.bridge.ROS2SubscribeTwist",
         "isaacsim.core.nodes.IsaacComputeOdometry",
         "isaacsim.core.nodes.IsaacDifferentialController",
         "isaacsim.core.nodes.IsaacArticulationController"]
valid = {}
for n in cands:
    t = og.get_node_type(n)
    valid[n] = bool(t is not None and t.is_valid())
print("NAV-VALID=" + json.dumps(valid))
nodes = [(n.split(".")[-1][:8] + str(i), n)
         for i, n in enumerate(cands) if valid[n]]
keys = og.Controller.Keys
og.Controller.edit({"graph_path": "/ProbeNav",
                    "evaluator_name": "execution",
                    }, {keys.CREATE_NODES: nodes})
out = {}
for short, full in nodes:
    p = st.GetPrimAtPath("/ProbeNav/" + short)
    ins = sorted(str(a).split("'")[1] for a in p.GetPropertiesInNamespace("inputs"))
    ous = sorted(str(a).split("'")[1] for a in p.GetPropertiesInNamespace("outputs"))
    out[short] = {"full": full, "in": ins, "out": ous}
st.RemovePrim("/ProbeNav")
print("NAV-ATTRS=" + json.dumps(out))
