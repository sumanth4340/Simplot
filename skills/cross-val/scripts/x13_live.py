"""X13 cross-skill co-validation (runs INSIDE Isaac Sim): V13 scene.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:    Dome/PropA/PropB valid (post-reopen)
modeling lens: A 1.0, B 0.6
sense lens:    A world (-0.8,0,0.5)
rig lens:      dome intensity 3000
app lens:      timeline stopped
"""
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from pxr import UsdGeom, UsdLux

stage = omni.usd.get_context().get_stage()
paths = ["/World/V13Dome", "/World/V13PropA", "/World/V13PropB"]
valid = all(stage.GetPrimAtPath(p).IsValid() for p in paths)


def _size(p):
    return float(UsdGeom.Cube.Get(stage, p).GetSizeAttr().Get())


def _tw(p):
    for op in UsdGeom.Xformable(stage.GetPrimAtPath(p)).GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            return tuple(float(v) for v in op.Get())
    return (999.0, 999.0, 999.0)


if valid:
    sA = _size("/World/V13PropA")
    sB = _size("/World/V13PropB")
    tA = _tw("/World/V13PropA")
    dome = float(UsdLux.DomeLight.Get(stage, "/World/V13Dome")
                 .GetIntensityAttr().Get())
else:
    sA = sB = dome = -1.0
    tA = (999.0, 999.0, 999.0)
print("X13-REPORT valid=%s sA=%.2f sB=%.2f tA=%.2f,%.2f,%.2f "
      "dome=%.1f stopped=%s" % (
          valid, sA, sB, tA[0], tA[1], tA[2], dome,
          app_utils.is_stopped()))
