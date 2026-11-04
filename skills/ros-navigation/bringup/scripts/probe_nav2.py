import omni.graph.core as og, omni.usd, json
st = omni.usd.get_context().get_stage()
cands = ["isaacsim.core.nodes.IsaacReadLidarPointCloud",
         "isaacsim.core.nodes.IsaacComputeRTXLidarPointCloud",
         "isaacsim.core.nodes.IsaacReadLidarBeams",
         "omni.graph.nodes.Add",
         "omni.graph.nodes.Subtract",
         "omni.graph.nodes.Multiply",
         "omni.graph.nodes.Divide",
         "omni.graph.nodes.ConstantDouble"]
valid = {}
for n in cands:
    t = og.get_node_type(n)
    valid[n] = bool(t is not None and t.is_valid())
print("NAV2-VALID=" + json.dumps(valid))
nodes = [(n.split(".")[-1][:8] + str(i), n)
         for i, n in enumerate(cands) if valid[n]]
keys = og.Controller.Keys
og.Controller.edit({"graph_path": "/ProbeNav2",
                    "evaluator_name": "execution",
                    }, {keys.CREATE_NODES: nodes})
out = {}
for short, full in nodes:
    p = st.GetPrimAtPath("/ProbeNav2/" + short)
    ins = sorted(str(a).split("'")[1] for a in p.GetPropertiesInNamespace("inputs"))
    ous = sorted(str(a).split("'")[1] for a in p.GetPropertiesInNamespace("outputs"))
    out[short] = {"full": full, "in": ins, "out": ous}
st.RemovePrim("/ProbeNav2")
print("NAV2-ATTRS=" + json.dumps(out))
