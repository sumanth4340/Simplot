"""X9 cross-skill co-validation (runs INSIDE Isaac Sim): V9 scene, all lenses.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:    V9Bot/Base/Link/Hinge1 + V9Graph valid
modeling lens: base size 0.15, link size 0.2
sense lens:    bot world x 3.0
physics lens:  drive position, stiffness 100, damping 10
graph lens:    4 nodes, Write targets V9 hinge, graph enabled
R8 lens:       no rival writers on the V9 hinge
"""
import omni.usd
import omni.graph.core as og
from pxr import UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
paths = ["/World/V9Bot", "/World/V9Bot/Base", "/World/V9Bot/Link",
         "/World/V9Bot/Hinge1", "/World/V9Graph"]
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
    sB, sL = _size("/World/V9Bot/Base"), _size("/World/V9Bot/Link")
    bx = _tx("/World/V9Bot")
    hp = stage.GetPrimAtPath("/World/V9Bot/Hinge1")
    dtype = str(hp.GetAttribute("drive:angular:physics:type").Get())
    stiff = float(hp.GetAttribute("drive:angular:physics:stiffness").Get())
    damp = float(hp.GetAttribute("drive:angular:physics:damping").Get())
    gn = len(list(stage.GetPrimAtPath("/World/V9Graph").GetChildren()))
    wp = og.get_node_by_path("/World/V9Graph/Write")
    wtgt = str(wp.get_attribute("inputs:primPath").get()) \
        if wp.is_valid() else "MISSING"
    g = og.get_graph_by_path("/World/V9Graph")
    en = (not g.is_disabled()) if g.is_valid() else False
    rival = 0
    for c in stage.GetPrimAtPath("/World").GetChildren():
        if c.GetTypeName() == "Graph" and c.GetName() != "V9Graph":
            for n in c.GetChildren():
                pp = n.GetAttribute("inputs:primPath")
                if pp.IsValid() and pp.Get() == "/World/V9Bot/Hinge1":
                    rival += 1
else:
    sB = sL = bx = stiff = damp = -1.0
    dtype, wtgt, gn, en, rival = "?", "?", -1, False, -1
print("X9-REPORT valid=%s sizeB=%.2f sizeL=%.2f bx=%.2f dtype=%s "
      "stiff=%.1f damp=%.1f nodes=%d tgt=%s en=%s rivals=%d" % (
          allok, sB, sL, bx, dtype, stiff, damp, gn, wtgt, en, rival))
