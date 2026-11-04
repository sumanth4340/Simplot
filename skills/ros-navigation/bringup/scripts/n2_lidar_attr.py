# Dump OmniLidar prim attributes to find the render product path.
import omni.kit.commands as kc
import omni.usd

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2LidarProbe").IsValid():
    st.RemovePrim("/N2LidarProbe")
ok, sensor = kc.execute("IsaacSensorCreateRtxLidar",
                        path="/N2LidarProbe")
p = st.GetPrimAtPath("/N2LidarProbe")
print("CREATE", ok, "VALID", p.IsValid())
for a in p.GetAttributes():
    n = a.GetName()
    if "ender" in n or "roduct" in n or "ydra" in n or "tream" in n:
        print("  ATTR", n, "=", repr(a.Get())[:200])
print("  N-ATTRS", len(p.GetAttributes()))
for r in p.GetRelationships():
    print("  REL", r.GetName(), r.GetTargets()[:4])
from pxr import UsdRender
for prim in st.Traverse():
    if prim.IsA(UsdRender.Product):
        print("  PRODUCT", prim.GetPath())
st.RemovePrim("/N2LidarProbe")
print("LIDAR-ATTR done")
