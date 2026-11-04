"""X8 cross-skill co-validation (runs INSIDE Isaac Sim): V8 scene, all lenses.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:      all 5 V8 prims valid
modeling lens:   cube sizes 0.5 / 1.0
sense lens:      cube world x (0.9 / -0.8)
rig lens:        dome 300, sun 1200
"""
import omni.usd
from pxr import UsdGeom, UsdLux

stage = omni.usd.get_context().get_stage()
paths = ["/World/V8Ground", "/World/V8CubeA", "/World/V8CubeB",
         "/World/V8Dome", "/World/V8Sun"]
valid = [stage.GetPrimAtPath(p).IsValid() for p in paths]
allok = all(valid)


def _size(p):
    return float(UsdGeom.Cube.Get(stage, p).GetSizeAttr().Get())


def _tx(p):
    for op in UsdGeom.Xformable(stage.GetPrimAtPath(p)).GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            return float(op.Get()[0])
    return 999.0


if allok:
    sA, sB = _size("/World/V8CubeA"), _size("/World/V8CubeB")
    xA, xB = _tx("/World/V8CubeA"), _tx("/World/V8CubeB")
    dome = float(UsdLux.DomeLight.Get(stage, "/World/V8Dome")
                 .GetIntensityAttr().Get())
    sun = float(UsdLux.DistantLight.Get(stage, "/World/V8Sun")
                .GetIntensityAttr().Get())
else:
    sA = sB = xA = xB = dome = sun = -1.0
print("X8-REPORT valid=%s sizeA=%.2f sizeB=%.2f xA=%.2f xB=%.2f "
      "dome=%.1f sun=%.1f" % (allok, sA, sB, xA, xB, dome, sun))
