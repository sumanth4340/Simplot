# N2 API probe (runs INSIDE Isaac Sim, STOPPED): modern lidar API
# signatures, Example_Rotary_2D registry check, create + render
# product discovery + world pose readback.
import inspect

from isaacsim.sensors.experimental.rtx import (
    Lidar, LidarSensor, SUPPORTED_LIDAR_CONFIGS)
import omni.usd
from pxr import UsdRender, UsdGeom

print("CREATE-SIG", inspect.signature(Lidar.create))
print("SENSOR-SIG", inspect.signature(LidarSensor.__init__))
keys = [k for k in SUPPORTED_LIDAR_CONFIGS.keys()
        if "Rotary" in k or "2D" in k]
print("ROTARY-KEYS", keys)

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2ApiProbe").IsValid():
    st.RemovePrim("/N2ApiProbe")
lidar = Lidar.create(path="/N2ApiProbe", config="Example_Rotary_2D",
                     tick_rate=10.0, positions=[[1.0, 0.0, 0.5]])
print("LIDAR", type(lidar), lidar)
for attr in ("render_product_path", "renderProductPath",
             "render_product", "path", "prim_path"):
    try:
        print("  HAS", attr, "=", repr(getattr(lidar, attr))[:160])
    except Exception as e:
        print("  NO", attr, repr(e)[:80])
for prim in st.Traverse():
    if prim.IsA(UsdRender.Product):
        print("  PRODUCT", prim.GetPath())
m = UsdGeom.Xformable(
    st.GetPrimAtPath("/N2ApiProbe")).ComputeLocalToWorldTransform(0)
print("  WORLD-POS",
      [round(m.ExtractTranslation()[i], 3) for i in range(3)])
st.RemovePrim("/N2ApiProbe")
print("APIPROBE done")
