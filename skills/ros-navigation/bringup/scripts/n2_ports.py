# N2 ports probe: dump attribute names of the 4 scan nodes.
import omni.graph.core as og

import omni.usd as _ou
G = "/ROS2/N2ports"
_st = _ou.get_context().get_stage()
if _st.GetPrimAtPath(G).IsValid():
    _st.RemovePrim(G)
og.Controller.edit(
    {"graph_path": G, "evaluator_name": "execution"},
    {og.Controller.Keys.CREATE_NODES: [
        ("BUF", "isaacsim.sensors.rtx.IsaacCreateRTXLidarScanBuffer"),
        ("FLAT", "isaacsim.sensors.rtx.IsaacComputeRTXLidarFlatScan"),
        ("HELP", "isaacsim.ros2.bridge.ROS2RtxLidarHelper"),
        ("PUB", "isaacsim.ros2.bridge.ROS2PublishLaserScan")]})
st = _st
for n in ("BUF", "FLAT", "HELP", "PUB"):
    print("=== " + n + " ===")
    p = st.GetPrimAtPath(G + "/" + n)
    for a in p.GetAttributes():
        print("  " + a.GetName())
st.RemovePrim(G)
print("PORTS done")
