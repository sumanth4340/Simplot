"""Diag probe 1 (runs INSIDE Isaac Sim): full /World inventory + S2Lidar pose check."""
import omni.usd
from pxr import Usd, UsdGeom, Gf

stage = omni.usd.get_context().get_stage()
print("DIAG1-STAGE url=%s" % stage.GetRootLayer().identifier)

cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), includedPurposes=["render"], useExtentsHint=True)
world = stage.GetPrimAtPath("/World")
print("DIAG1-WORLD valid=%s type=%s children=%d" % (world.IsValid(), world.GetTypeName(), len(list(world.GetChildren()))))
for prim in Usd.PrimRange(world):
    p = str(prim.GetPath())
    t = prim.GetTypeName() or "(scope/xform)"
    try:
        ab = cache.ComputeWorldBound(prim).ComputeAlignedBox()
        mn, mx = ab.GetMin(), ab.GetMax()
        bb = "min=(%.3f,%.3f,%.3f) max=(%.3f,%.3f,%.3f)" % (mn[0], mn[1], mn[2], mx[0], mx[1], mx[2])
    except Exception as e:
        bb = "bbox-ERR %s" % e
    active = "A" if prim.IsActive() else "a"
    print("DIAG1-PRIM %s %s type=%s %s" % (active, p, t, bb))

# Lidar prim pose detail
lp = stage.GetPrimAtPath("/World/S2Lidar")
if lp and lp.IsValid():
    print("DIAG1-LIDAR type=%s" % lp.GetTypeName())
    try:
        xf = UsdGeom.Xformable(lp)
        m = xf.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        tr = m.ExtractTranslation()
        print("DIAG1-LIDAR worldpos=(%.4f,%.4f,%.4f)" % (tr[0], tr[1], tr[2]))
        print("DIAG1-LIDAR xformops=%s" % [op.GetOpName() for op in xf.GetOrderedXformOps()])
        for op in xf.GetOrderedXformOps():
            print("DIAG1-LIDAR op %s = %s" % (op.GetOpName(), op.Get()))
    except Exception as e:
        print("DIAG1-LIDAR xform-ERR %s" % e)
    for attr in ("nearRangeM", "farRangeM", "tickRate", "horizontalResolution", "horizontalFovDeg"):
        try:
            a = lp.GetAttribute(attr)
            if a and a.IsValid():
                print("DIAG1-LIDAR attr %s = %s" % (attr, a.Get()))
        except Exception as e:
            print("DIAG1-LIDAR attr %s ERR %s" % (attr, e))
    # dump all authored lidar-ish attrs
    try:
        for a in lp.GetAuthoredAttributes():
            n = a.GetName()
            if any(k in n for k in ("ange", "esolution", "ov", "levation", "eam", "hannel", "ccumul", "otion", "weep", "ulse")):
                print("DIAG1-LIDAR cfg %s = %s" % (n, a.Get()))
    except Exception as e:
        print("DIAG1-LIDAR cfgdump-ERR %s" % e)
else:
    print("DIAG1-LIDAR MISSING")

# Physics/collision sanity on the known geos
for p in ("/World/S2Ground", "/World/S2Cube"):
    prim = stage.GetPrimAtPath(p)
    if prim and prim.IsValid():
        apis = [a for a in prim.GetAppliedSchemas()]
        print("DIAG1-SCHEMA %s applied=%s" % (p, apis))
print("DIAG1-DONE")
