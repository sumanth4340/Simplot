"""N2 canonical test (runs INSIDE Isaac Sim): verbatim standalone
example pattern (rtx_lidar.py) for the 2D lidar: LidarSensor +
attach_writer('RtxLidarROS2PublishLaserScan', topic, frame, scan
metas). Latch play; external listener validates concurrently."""
import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.prim as prim_utils
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor
import omni.usd

app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=10)

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2C2D").IsValid():
    st.RemovePrim("/N2C2D")


def _meta(prim):
    rot = float(prim.GetAttribute(
        "omni:sensor:Core:scanRateBaseHz").Get() or 0)
    near = float(prim.GetAttribute(
        "omni:sensor:Core:nearRangeM").Get() or 0)
    far = float(prim.GetAttribute(
        "omni:sensor:Core:farRangeM").Get() or 0)
    fire = int(prim.GetAttribute(
        "omni:sensor:Core:patternFiringRateHz").Get() or 0)
    print("META rot=%s near=%s far=%s fire=%s" % (rot, near, far, fire))
    return dict(horizontalFov=360.0,
                horizontalResolution=360.0 * rot / fire,
                depthRange=[near, far], rotationRate=rot,
                azimuthRange=[-180.0, 180.0])


lidar = Lidar.create(path="/N2C2D", config="Example_Rotary_2D",
                     tick_rate=10.0, translations=[[0.0, 0.0, 1.0]])
sensor = LidarSensor(lidar, annotators=[])
meta = _meta(prim_utils.get_prim_at_path(lidar.paths[0]))
sensor.attach_writer("RtxLidarROS2PublishLaserScan",
                     topicName="scan", frameId="base_scan", **meta)
print("CANON-ATTACHED")
app_utils.play()
await app_utils.update_app_async(steps=30)
print("N2C-PLAYING (latched, no stop)")
