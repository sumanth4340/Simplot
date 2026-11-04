"""X10 cross-skill co-validation (runs INSIDE Isaac Sim): V10 scene.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:    Gate/Bot/Base/Link/Hinge1 valid
modeling lens: gate 0.4, base 0.15, link 0.2
sense lens:    bot world x 4.0
physics lens:  drive position, stiffness 100, damping 10
anim lens:     gate 2 ops, 2+2 time samples
behavior lens: final DOF target echo +0.4
"""
import numpy as np
import warp as wp
import omni.usd
from isaacsim.core.experimental.prims import Articulation
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
paths = ["/World/V10Gate", "/World/V10Bot", "/World/V10Bot/Base",
         "/World/V10Bot/Link", "/World/V10Bot/Hinge1"]
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
    sG = _size("/World/V10Gate")
    sB = _size("/World/V10Bot/Base")
    sL = _size("/World/V10Bot/Link")
    bx = _tx("/World/V10Bot")
    hp = stage.GetPrimAtPath("/World/V10Bot/Hinge1")
    dtype = str(hp.GetAttribute("drive:angular:physics:type").Get())
    stiff = float(hp.GetAttribute("drive:angular:physics:stiffness").Get())
    damp = float(hp.GetAttribute("drive:angular:physics:damping").Get())
    gops = UsdGeom.Xformable(
        stage.GetPrimAtPath("/World/V10Gate")).GetOrderedXformOps()
    nops = len(gops)
    nts = len(gops[0].GetAttr().GetTimeSamples())
    nrs = len(gops[1].GetAttr().GetTimeSamples())
    art = Articulation("/World/V10Bot/Base")
    e = art.get_dof_position_targets()
    e = e.numpy() if isinstance(e, wp.array) else np.asarray(e)
    echo = float(np.asarray(e, dtype=float).flatten()[0])
else:
    sG = sB = sL = bx = stiff = damp = echo = -1.0
    dtype, nops, nts, nrs = "?", -1, -1, -1
print("X10-REPORT valid=%s sizeG=%.2f sizeB=%.2f sizeL=%.2f "
      "bx=%.2f dtype=%s stiff=%.1f damp=%.1f ops=%d ts=%d rs=%d "
      "echo=%.4f" % (allok, sG, sB, sL, bx, dtype, stiff, damp,
                     nops, nts, nrs, echo))
