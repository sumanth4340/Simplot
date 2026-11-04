# N2 product dump (INSIDE Isaac Sim, STOPPED): full attributes +
# relationships of the LidarSensor AUTO product vs a rep.create
# product. Read-only (NO RemovePrim anywhere: product removal
# crashes the renderer).
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor
import omni.replicator.core as rep
import omni.usd
from pxr import UsdRender

st = omni.usd.get_context().get_stage()
TAG = "N2ProdDump"
LP = "/" + TAG
if st.GetPrimAtPath(LP).IsValid():
    st.RemovePrim(LP)

lidar = Lidar.create(path=LP, config="Example_Rotary_2D",
                     tick_rate=10.0)
sensor = LidarSensor(LP)
rp_obj = rep.create.render_product(LP, (64, 1), name=TAG + "Rep")
print("REP-PATH", rp_obj.path)


def dump(path, tag):
    p = st.GetPrimAtPath(path)
    print("=== %s %s type=%s" % (tag, path, p.GetTypeName()))
    for a in p.GetAttributes():
        try:
            v = a.Get()
        except Exception as e:
            v = "ERR " + repr(e)[:60]
        print("  A %-28s = %r" % (a.GetName(), v))
    for r in p.GetRelationships():
        print("  R %-28s -> %s" % (r.GetName(), r.GetTargets()))


auto = sorted(str(p.GetPath()) for p in st.Traverse()
              if p.IsA(UsdRender.Product)
              and "rtx_sensor_" in str(p.GetPath()))
print("AUTO", auto)
if auto:
    dump(auto[-1], "AUTO")
dump(rp_obj.path, "REP")
print("KEEPALIVE", type(sensor), type(lidar))
print("PRODDUMP done")
