"""X12 cross-skill co-validation (runs INSIDE Isaac Sim): V12 scene.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:    Dome/Ground/BoxA/BoxB valid
modeling lens: A/B size 0.8
sense lens:    A world (-1,0,0.4)
rig lens:      dome intensity 3000
sem lens:      labels v12a / v12b
"""
import omni.usd
from pxr import UsdGeom, UsdLux
from isaacsim.core.experimental.utils.semantics import get_labels

stage = omni.usd.get_context().get_stage()
paths = ["/World/V12Dome", "/World/V12Ground",
         "/World/V12BoxA", "/World/V12BoxB"]
valid = all(stage.GetPrimAtPath(p).IsValid() for p in paths)


def _size(p):
    return float(UsdGeom.Cube.Get(stage, p).GetSizeAttr().Get())


def _tw(p):
    for op in UsdGeom.Xformable(stage.GetPrimAtPath(p)).GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            return tuple(float(v) for v in op.Get())
    return (999.0, 999.0, 999.0)


if valid:
    sA = _size("/World/V12BoxA")
    sB = _size("/World/V12BoxB")
    tA = _tw("/World/V12BoxA")
    dome = float(UsdLux.DomeLight.Get(stage, "/World/V12Dome")
                 .GetIntensityAttr().Get())
    la = get_labels(stage.GetPrimAtPath("/World/V12BoxA"))
    lb = get_labels(stage.GetPrimAtPath("/World/V12BoxB"))
else:
    sA = sB = dome = -1.0
    tA = (999.0, 999.0, 999.0)
    la = lb = {}
print("X12-REPORT valid=%s sA=%.2f sB=%.2f tA=%.2f,%.2f,%.2f "
      "dome=%.1f la=%s lb=%s" % (
          valid, sA, sB, tA[0], tA[1], tA[2], dome, la, lb))
