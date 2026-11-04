# N2 lidar probe: create RTX lidar, find its render product path.
import omni.kit.commands
import omni.usd

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2LidarProbe").IsValid():
    st.RemovePrim("/N2LidarProbe")

ok, sensor = omni.kit.commands.execute(
    "RangeSensorCreateRtxLidar",
    path="/N2LidarProbe",
    parent=None,
    min_range=0.4,
    max_range=20.0,
    draw_points=False,
    draw_lines=False,
    sampling_rate=0)
print("CREATE", ok, sensor)
p = st.GetPrimAtPath("/N2LidarProbe")
print("VALID", p.IsValid(), "TYPE", p.GetTypeName())
for a in p.GetAttributes():
    n = a.GetName()
    if "ender" in n or "roduct" in n or "path" in n.lower():
        print("  ATTR", n, "=", repr(a.Get())[:160])
for r in p.GetRelationships():
    print("  REL", r.GetName(), r.GetTargets())
for c in p.GetChildren():
    print("  CHILD", c.GetPath(), c.GetTypeName())

# Hunt for render products mentioning the lidar.
from pxr import UsdRender
for prim in st.Traverse():
    if prim.IsA(UsdRender.Product):
        print("  PRODUCT", prim.GetPath())
print("LIDAR-PROBE done")
st.RemovePrim("/N2LidarProbe")
