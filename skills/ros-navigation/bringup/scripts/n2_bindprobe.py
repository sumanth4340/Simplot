# N2 product bind probe (INSIDE Isaac Sim, STOPPED): ONLY the
# binding surface of AUTO vs REP products (rels + product/camera/
# resolution attrs). Read-only (no product removal).
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor
import omni.replicator.core as rep
import omni.usd
from pxr import UsdRender

st = omni.usd.get_context().get_stage()
TAG = "N2BindProbe"
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
        n = a.GetName()
        nl = n.lower()
        if ("camera" in nl or "product" in nl or "resolution" in nl
                or "render" in nl or "driver" in nl or "var" in nl
                or "ordered" in nl or "sensor" in nl or "name" in nl):
            try:
                v = a.Get()
            except Exception as e:
                v = "ERR " + repr(e)[:60]
            print("  A %-40s = %r" % (n, v))
    for r in p.GetRelationships():
        print("  R %-40s -> %s" % (r.GetName(), r.GetTargets()))


auto = sorted(str(p.GetPath()) for p in st.Traverse()
              if p.IsA(UsdRender.Product)
              and "rtx_sensor_" in str(p.GetPath()))
print("AUTO", auto)
if auto:
    dump(auto[-1], "AUTO")
dump(rp_obj.path, "REP")
print("KEEPALIVE", type(sensor), type(lidar))
print("BINDPROBE done")
