"""READ-ONLY: characterize stale /World/M4V2Bot (pose/physics/joints)."""
from pxr import UsdGeom, UsdPhysics
import omni.usd

stage = omni.usd.get_context().get_stage()
print("=== V2-START ===")
bot = stage.GetPrimAtPath("/World/M4V2Bot")
stack = [bot]
while stack:
    pr = stack.pop()
    if not pr or not pr.IsValid():
        continue
    flags = []
    if pr.HasAPI(UsdPhysics.RigidBodyAPI):
        flags.append("RigidBody")
    if pr.HasAPI(UsdPhysics.CollisionAPI):
        flags.append("Collision")
    if pr.HasAPI(UsdPhysics.MassAPI):
        try:
            flags.append("Mass=%s" % UsdPhysics.MassAPI(pr).GetMassAttr().Get())
        except Exception:
            flags.append("Mass=?")
    if pr.HasAPI(UsdPhysics.ArticulationRootAPI):
        flags.append("ArticRoot")
    try:
        xf = UsdGeom.Xformable(pr)
        tops = str([(str(o.GetOpType()), str(o.Get()))
                    for o in xf.GetOrderedXformOps()])
    except Exception as e:
        tops = "ERR %s" % e
    size = ""
    try:
        if pr.GetTypeName() == "Cube":
            size = " size=%s" % UsdGeom.Cube(pr).GetSizeAttr().Get()
    except Exception:
        pass
    jinfo = ""
    try:
        if "Joint" in pr.GetTypeName():
            j = UsdPhysics.Joint(pr)
            jinfo = " b0=%s b1=%s p0=%s p1=%s" % (
                [str(t) for t in j.GetBody0Rel().GetTargets()],
                [str(t) for t in j.GetBody1Rel().GetTargets()],
                j.GetLocalPos0Attr().Get(), j.GetLocalPos1Attr().Get())
    except Exception as e:
        jinfo = " JERR %s" % e
    print("  %s type=%s%s xform=%s phys=[%s]%s" % (
        pr.GetPath(), pr.GetTypeName(), size, tops,
        ",".join(flags) or "none", jinfo))
    for c in pr.GetChildren():
        stack.append(c)
print("--- V2 world poses ---")
cache = UsdGeom.XformCache()
for p in ("/World/M4V2Bot", "/World/M4V2Bot/Link0",
          "/World/M4V2Bot/Link0/Geom"):
    pr = stage.GetPrimAtPath(p)
    if pr and pr.IsValid():
        t = cache.GetLocalToWorldTransform(pr).ExtractTranslation()
        print("  %s worldT=(%.4f,%.4f,%.4f)" % (p, t[0], t[1], t[2]))
print("=== V2-END ===")
