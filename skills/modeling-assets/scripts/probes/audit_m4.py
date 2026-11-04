"""READ-ONLY M4 construction audit. No timeline/attr writes."""
from pxr import UsdGeom, UsdPhysics
import omni.usd

stage = omni.usd.get_context().get_stage()


def exists(p):
    pr = stage.GetPrimAtPath(p)
    return pr and pr.IsValid()


def phys_flags(prim):
    out = []
    if prim.HasAPI(UsdPhysics.RigidBodyAPI):
        out.append("RigidBody")
    if prim.HasAPI(UsdPhysics.CollisionAPI):
        out.append("Collision")
    if prim.HasAPI(UsdPhysics.MassAPI):
        try:
            m = UsdPhysics.MassAPI(prim).GetMassAttr().Get()
        except Exception:
            m = "?"
        out.append("Mass=%s" % (m,))
    if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
        out.append("ArticRoot")
    return ",".join(out) or "none"


def xform_info(prim):
    try:
        xf = UsdGeom.Xformable(prim)
        tops = [(o.GetOpType(), o.Get()) for o in xf.GetOrderedXformOps()]
        return str([(str(t), str(v)) for t, v in tops])
    except Exception as e:
        return "ERR %s" % e


def cube_size(prim):
    try:
        c = UsdGeom.Cube(prim)
        return str(c.GetSizeAttr().Get())
    except Exception as e:
        return "ERR %s" % e


def joint_info(path):
    pr = stage.GetPrimAtPath(path)
    if not pr or not pr.IsValid():
        return "MISSING"
    try:
        j = UsdPhysics.Joint(pr)
        b0 = [str(t) for t in j.GetBody0Rel().GetTargets()]
        b1 = [str(t) for t in j.GetBody1Rel().GetTargets()]
        p0 = str(j.GetLocalPos0Attr().Get())
        p1 = str(j.GetLocalPos1Attr().Get())
        extra = ""
        try:
            r = UsdPhysics.RevoluteJoint(pr)
            extra = " axis=%s lo=%s hi=%s" % (
                r.GetAxisAttr().Get(),
                pr.GetAttribute("physics:lowerLimit").Get(),
                pr.GetAttribute("physics:upperLimit").Get())
        except Exception:
            pass
        return "b0=%s b1=%s p0=%s p1=%s%s" % (b0, b1, p0, p1, extra)
    except Exception as e:
        return "ERR %s" % e


print("=== AUDIT-START ===")

print("--- TOP-LEVEL /World children ---")
try:
    w = stage.GetPrimAtPath("/World")
    for c in w.GetChildren():
        print("  %s type=%s" % (c.GetPath(), c.GetTypeName()))
except Exception as e:
    print("  ERR %s" % e)

print("--- EXPECTED-PRESENCE ---")
for p in ("/World/PhysicsScene", "/World/M4Ground", "/World/M4Bot",
          "/World/M4Bot/Root", "/World/M4Bot/RootFixed",
          "/World/M4Bot/Link1", "/World/M4Bot/Hinge1",
          "/World/M4Bot/Link2", "/World/M4Bot/Hinge2",
          "/World/M4Bot/Link2/GraspSite",
          "/World/M4ShelfA", "/World/M4ShelfB", "/World/M4Block"):
    pr = stage.GetPrimAtPath(p)
    ok = pr and pr.IsValid()
    print("  %s valid=%s type=%s" % (p, bool(ok),
          pr.GetTypeName() if ok else "-"))

print("--- ALL-M*-PRIMS stage walk (dup/stale hunt) ---")
try:
    for prim in stage.Traverse():
        ps = str(prim.GetPath())
        if ("M4" in ps or "M1Bot" in ps or "M2Bot" in ps
                or "M3Bot" in ps or "YBot" in ps
                or "GraspJoint" in ps or "PhysicsScene" in ps):
            print("  %s type=%s" % (ps, prim.GetTypeName()))
except Exception as e:
    print("  ERR %s" % e)

print("--- M4Bot subtree (recursive) ---")
try:
    bot = stage.GetPrimAtPath("/World/M4Bot")
    if bot and bot.IsValid():
        stack = [(bot, 0)]
        while stack:
            pr, d = stack.pop()
            print("  %s%s type=%s" % ("  " * d, pr.GetPath(),
                  pr.GetTypeName()))
            for c in reversed(list(pr.GetChildren())):
                stack.append((c, d + 1))
    else:
        print("  /World/M4Bot INVALID")
except Exception as e:
    print("  ERR %s" % e)

print("--- CUBE details (size/xform/physics) ---")
for p in ("/World/M4Bot/Root", "/World/M4Bot/Link1", "/World/M4Bot/Link2",
          "/World/M4ShelfA", "/World/M4ShelfB", "/World/M4Block"):
    pr = stage.GetPrimAtPath(p)
    if not pr or not pr.IsValid():
        print("  %s MISSING" % p)
        continue
    print("  %s size=%s xform=%s phys=[%s]" % (
        p, cube_size(pr), xform_info(pr), phys_flags(pr)))

print("--- JOINT details ---")
for p in ("/World/M4Bot/RootFixed", "/World/M4Bot/Hinge1",
          "/World/M4Bot/Hinge2", "/World/M4GraspJoint"):
    print("  %s :: %s" % (p, joint_info(p)))

print("--- WORLD-POSE (overlap evidence) ---")
try:
    cache = UsdGeom.XformCache()
    for p in ("/World/M4Bot/Root", "/World/M4Bot/Link1",
              "/World/M4Bot/Link2", "/World/M4ShelfA",
              "/World/M4ShelfB", "/World/M4Block"):
        pr = stage.GetPrimAtPath(p)
        if not pr or not pr.IsValid():
            print("  %s MISSING" % p)
            continue
        m = cache.GetLocalToWorldTransform(pr)
        t = m.ExtractTranslation()
        print("  %s worldT=(%.4f,%.4f,%.4f)" % (p, t[0], t[1], t[2]))
except Exception as e:
    print("  ERR %s" % e)

print("--- GraspSite detail ---")
try:
    sp = "/World/M4Bot/Link2/GraspSite"
    pr = stage.GetPrimAtPath(sp)
    if pr and pr.IsValid():
        print("  %s xform=%s hasIsaacSite=%s" % (
            sp, xform_info(pr), pr.HasAPI("IsaacSiteAPI")))
    else:
        print("  %s MISSING" % sp)
except Exception as e:
    print("  ERR %s" % e)

print("=== AUDIT-END ===")
