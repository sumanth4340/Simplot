"""X11 cross-skill co-validation (runs INSIDE Isaac Sim): V11 yard.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:    V11 D/E/F valid; N1/N3 collider prims cleaned (R6)
modeling lens: D 1.4, E 1.0, F 1.0 scaled (1.6,0.8,1.0)
sense lens:    D world (0,2,0.7), F world (2,-2,0.5)
physics lens:  CollisionAPI present+enabled on all three
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
vps = ["/World/V11ObsD", "/World/V11ObsE", "/World/V11ObsF"]
valid = all(stage.GetPrimAtPath(p).IsValid() for p in vps)
gone = all(not stage.GetPrimAtPath(p).IsValid() for p in (
    "/World/N1ObsA", "/World/N1ObsB", "/World/N3Bot"))


def _size(p):
    return float(UsdGeom.Cube.Get(stage, p).GetSizeAttr().Get())


def _tw(p):
    for op in UsdGeom.Xformable(stage.GetPrimAtPath(p)).GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            return tuple(float(v) for v in op.Get())
    return (999.0, 999.0, 999.0)


def _sc(p):
    for op in UsdGeom.Xformable(stage.GetPrimAtPath(p)).GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeScale:
            return tuple(float(v) for v in op.Get())
    return (1.0, 1.0, 1.0)


def _col(p):
    prim = stage.GetPrimAtPath(p)
    if not prim.HasAPI(UsdPhysics.CollisionAPI):
        return False
    en = prim.GetAttribute("physics:collisionEnabled")
    return en.Get() is not False


if valid:
    sD, sE, sF = _size(vps[0]), _size(vps[1]), _size(vps[2])
    scF = _sc(vps[2])
    tD, tF = _tw(vps[0]), _tw(vps[2])
    col = all(_col(p) for p in vps)
else:
    sD = sE = sF = -1.0
    scF = (-1.0, -1.0, -1.0)
    tD = tF = (999.0, 999.0, 999.0)
    col = False
print("X11-REPORT valid=%s gone=%s sD=%.2f sE=%.2f sF=%.2f "
      "scF=%.2f,%.2f,%.2f tD=%.2f,%.2f,%.2f tF=%.2f,%.2f,%.2f "
      "col=%s" % (valid, gone, sD, sE, sF, scF[0], scF[1], scF[2],
                  tD[0], tD[1], tD[2], tF[0], tF[1], tF[2], col))
