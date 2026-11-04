# Probe: render product creation for OmniLidar + Lidar.create backup.
import omni.kit.commands as kc
import omni.usd

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2LidarProbe").IsValid():
    st.RemovePrim("/N2LidarProbe")
ok, sensor = kc.execute("IsaacSensorCreateRtxLidar",
                        path="/N2LidarProbe")
print("CREATE", ok)
try:
    import omni.replicator.core as rep
    rp = rep.create.render_product("/N2LidarProbe", (64, 1))
    print("RP", rp, type(rp))
    try:
        print("RP-PATH", rp.path if hasattr(rp, "path") else rp[0]
              if isinstance(rp, (tuple, list)) else "?")
    except Exception as e:
        print("RP-PATH-ERR", repr(e)[:160])
except Exception as e:
    print("RP-ERR", repr(e)[:300])

from pxr import UsdRender
for prim in st.Traverse():
    if prim.IsA(UsdRender.Product):
        print("  PRODUCT", prim.GetPath())

try:
    from isaacsim.sensors.experimental import rtx as _rtx
    print("RTX-MOD", [x for x in dir(_rtx) if "idar" in x or "onfig" in x])
except Exception as e:
    print("RTX-ERR", repr(e)[:200])
st.RemovePrim("/N2LidarProbe")
print("RP-PROBE done")
