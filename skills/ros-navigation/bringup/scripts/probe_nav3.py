import omni.graph.core as og, omni.usd, json
st = omni.usd.get_context().get_stage()
cands = ["isaacsim.ros2.bridge.ROS2RtxLidarHelper",
         "isaacsim.sensors.rtx.IsaacComputeRTXLidarFlatScan",
         "isaacsim.sensors.rtx.IsaacCreateRTXLidarScanBuffer"]
keys = og.Controller.Keys
og.Controller.edit({"graph_path": "/ProbeNav3",
                    "evaluator_name": "execution",
                    }, {keys.CREATE_NODES: [(n.split(".")[-1][:10], n)
                                            for n in cands]})
out = {}
for n in cands:
    short = n.split(".")[-1][:10]
    p = st.GetPrimAtPath("/ProbeNav3/" + short)
    ins = sorted(str(a).split("'")[1] for a in p.GetPropertiesInNamespace("inputs"))
    ous = sorted(str(a).split("'")[1] for a in p.GetPropertiesInNamespace("outputs"))
    out[short] = {"full": n, "in": ins, "out": ous}
st.RemovePrim("/ProbeNav3")
print("NAV3-ATTRS=" + json.dumps(out))
