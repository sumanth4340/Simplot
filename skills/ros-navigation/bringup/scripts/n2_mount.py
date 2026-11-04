"""N2 mount (runs INSIDE Isaac Sim via bridge, STOPPED).

Mounts Example_Rotary_2D lidar at the N1 articulation root + graph
/ROS2/N2: OnPlaybackTick -> ROS2RtxLidarHelper (/scan, laser_scan).
CTL zeroed (static base: tight scan gates on known geometry).
Adds N2Cube (1m at x=2) + dome light.
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd
from pxr import UsdGeom, UsdLux, UsdRender, Gf
from isaacsim.sensors.experimental.rtx import Lidar

# ROS2 graph nodes need the bridge extension (fresh sims lack it).
app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=10)

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/N2").IsValid():
    st.RemovePrim("/ROS2/N2")
for p in ("/World/N2Cube", "/World/N2Dome"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)
arts = [c.GetName() for c in st.GetPrimAtPath("/World").GetChildren()
        if c.GetName().startswith("N1Base")]
ART = "/World/" + max(arts, key=lambda n: int(n.split("_")[-1]))
# Parent to the articulation ROOT, never the chassis rigid body:
# a lidar under a rigid body emits empty scans (verified: 19 empty
# ticks vs 24 full frames at the root, same pose/scene).
LP = ART + "/lidar"
if st.GetPrimAtPath(LP).IsValid():
    st.RemovePrim(LP)

dome = UsdLux.DomeLight.Define(st, "/World/N2Dome")
dome.GetIntensityAttr().Set(400.0)
cube = UsdGeom.Cube.Define(st, "/World/N2Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(2, 0, 0.5))

# Product flow mirrors NVIDIA's own ROS2 lidar test
# (test_rtx_sensor.py): Lidar.create (NO LidarSensor: its auto
# rtx_sensor_* product dies with the --file call's handles) +
# explicit rep render product at (128,128), which persists in USD.
# No keepalive needed. NEVER RemovePrim products (scheduler-owned;
# removal crashes the renderer).
# NOTE: Lidar.create positions are WORLD-frame, not parent-local.
import omni.replicator.core as rep

lidar = Lidar.create(path=LP, config="Example_Rotary_2D",
                     tick_rate=10.0, accumulate_outputs=True,
                     positions=[[0.0, 0.0, 0.515]])
rp_obj = rep.create.render_product(LP, (128, 128))
RP = rp_obj.path
print("N2-LIDAR rp=%s" % RP)

# NOTE: IsaacCreateRTXLidarScanBuffer/FlatScan are deprecated and
# CRASH the process at first play (carb crashreporter, verified).
# ROS2RtxLidarHelper(type=laser_scan) publishes /scan straight from
# the render product. No BUF/FLAT nodes.
keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/N2", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("HELP", "isaacsim.ros2.bridge.ROS2RtxLidarHelper")],
     keys.CONNECT: [
        ("/ROS2/N2/OnPB.outputs:tick", "/ROS2/N2/HELP.inputs:execIn")],
     keys.SET_VALUES: [
        ("/ROS2/N2/HELP.inputs:topicName", "/scan"),
        ("/ROS2/N2/HELP.inputs:type", "laser_scan"),
        ("/ROS2/N2/HELP.inputs:frameId", "base_scan"),
        ("/ROS2/N2/HELP.inputs:renderProductPath", RP),
        ("/ROS2/N2/HELP.inputs:queueSize", 10),
        ("/ROS2/N2/HELP.inputs:enabled", True)]})
og.Controller.attribute(
    "/ROS2/N1/CTL.inputs:velocityCommand").set([0.0] * 4)

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/N2").GetChildren())
print("N2-MOUNT-OK nodes=%s rp=%s art=%s" % (names, RP, ART))
