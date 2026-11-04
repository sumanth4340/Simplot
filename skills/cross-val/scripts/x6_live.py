"""X6 cross-skill co-validation (runs INSIDE Isaac Sim): V6 scene, all lenses.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:      all 7 V6 prims valid
modeling lens:   cube sizes 0.5 / 1.2
sense lens:      cube world x (0.8 / -0.9)
render rig lens: dome 300, sun 1200, cam focal 24
"""
import omni.usd
from pxr import UsdGeom, UsdLux

stage = omni.usd.get_context().get_stage()
paths = ["/World/V6Ground", "/World/V6CubeA", "/World/V6CubeB",
         "/World/V6Dome", "/World/V6Sun", "/World/V6Cam",
         "/World/V6Cap"]
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
    sA, sB = _size("/World/V6CubeA"), _size("/World/V6CubeB")
    xA = _tx("/World/V6CubeA")
    xB = _tx("/World/V6CubeB")
    dome = float(UsdLux.DomeLight.Get(stage, "/World/V6Dome")
                 .GetIntensityAttr().Get())
    sun = float(UsdLux.DistantLight.Get(stage, "/World/V6Sun")
                .GetIntensityAttr().Get())
    focal = float(UsdGeom.Camera.Get(stage, "/World/V6Cam")
                  .GetFocalLengthAttr().Get())
else:
    sA = sB = xA = xB = dome = sun = focal = -1.0
print("X6-REPORT valid=%s sizeA=%.2f sizeB=%.2f xA=%.2f xB=%.2f "
      "dome=%.1f sun=%.1f focal=%.1f"
      % (allok, sA, sB, xA, xB, dome, sun, focal))
