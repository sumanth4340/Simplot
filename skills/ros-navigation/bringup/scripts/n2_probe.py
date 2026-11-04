# N2 probe: RTX lidar creation command + OG scan node types exist?
import omni.graph.core as og

cmds = [c for c in dir(__import__("omni.kit.commands", fromlist=["x"]))
        if False]
print("PROBE-RTX start")
try:
    import omni.kit.commands as kc
    names = sorted(kc.command.__dict__.keys()) if hasattr(kc, "command") \
        else []
    hits = [n for n in names if "tx" in n.lower() and "idar" in n.lower()]
    print("CMDS", hits if hits else names[:5])
except Exception as e:
    print("CMDS-ERR", repr(e)[:200])

for t in ("isaacsim.sensors.rtx.IsaacCreateRTXLidarScanBuffer",
          "isaacsim.sensors.rtx.IsaacComputeRTXLidarFlatScan",
          "isaacsim.ros2.bridge.ROS2RtxLidarHelper",
          "isaacsim.ros2.bridge.ROS2PublishLaserScan"):
    try:
        print(t, og.get_node_type(t).is_valid())
    except Exception as e:
        print(t, "ERR", repr(e)[:120])
print("PROBE-RTX done")
