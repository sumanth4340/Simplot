"""N2 HELP isolation (runs INSIDE Isaac Sim): static 2D lidar +
/ROS2/N2H graph (OnPB -> HELP /scan) + play LATCHED (no stop).
External listener validates /scan concurrently. Handles: sensor
created HERE dies at call end, but HELP attaches its writer on
first tick (writer lives in the graph runtime, not the handle).
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor

app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=10)

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/N2H").IsValid():
    st.RemovePrim("/ROS2/N2H")
if st.GetPrimAtPath("/N2H").IsValid():
    st.RemovePrim("/N2H")

lidar = Lidar.create(path="/N2H", config="Example_Rotary_2D",
                     tick_rate=10.0, accumulate_outputs=True,
                     positions=[[0.0, 0.0, 0.515]])
sensor = LidarSensor("/N2H")
print("SENSOR-OK")

keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/N2H", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("HELP", "isaacsim.ros2.bridge.ROS2RtxLidarHelper")],
     keys.CONNECT: [
        ("/ROS2/N2H/OnPB.outputs:tick", "/ROS2/N2H/HELP.inputs:execIn")],
     keys.SET_VALUES: []})
# HELP defaults already: topicName 'scan', type laser_scan. Point
# renderProductPath at the live auto product via USD write.
from pxr import UsdRender
prods = sorted(str(p.GetPath()) for p in st.Traverse()
               if p.IsA(UsdRender.Product)
               and "rtx_sensor_" in str(p.GetPath()))
RP = prods[-1]
st.GetPrimAtPath("/ROS2/N2H/HELP").GetAttribute(
    "inputs:renderProductPath").Set(RP)
print("HELP-RP", RP)
app_utils.play()
await app_utils.update_app_async(steps=30)
print("N2H-PLAYING (latched, no stop)")
