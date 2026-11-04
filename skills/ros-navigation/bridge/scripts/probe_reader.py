import omni.graph.core as og, omni.usd, json
st = omni.usd.get_context().get_stage()
keys = og.Controller.Keys
og.Controller.edit({"graph_path": "/ProbeR",
                    "evaluator_name": "execution",
                    }, {keys.CREATE_NODES: [
                        ("RD", "isaacsim.sensors.physics.IsaacReadJointState")]})
p = st.GetPrimAtPath("/ProbeR/RD")
ins = sorted(str(a).split("'")[1] for a in p.GetPropertiesInNamespace("inputs"))
ous = sorted(str(a).split("'")[1] for a in p.GetPropertiesInNamespace("outputs"))
st.RemovePrim("/ProbeR")
print("RDATTRS=" + json.dumps({"in": ins, "out": ous}))
