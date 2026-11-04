"""X3 precedence (runs INSIDE Isaac Sim): Direct > Sublayer > Reference.

X3A: reference widget (small=1.0); direct Set(2.0) wins, stack top root;
add over-sublayer (5.0): direct still wins (2.0). X3B: fresh reference,
no direct over: sublayer wins over the reference (5.0), stack top is
the sublayer file. (No Clear() removal: it leaves a root stack entry;
see failures.md L5.)
"""
from pxr import Usd
import omni.usd

STAGEDIR = "C:/Users/sruja_ob3di74/action-reasoner/skills/cross-val/stages/"
OVER = ('#usda 1.0\nover "World"\n{\n    over "%s"\n    {\n'
        '        over "Box"\n        {\n            double size = 5\n'
        '        }\n    }\n}\n')
with open(STAGEDIR + "x3_over.usda", "w") as fh:
    fh.write(OVER % "X3A")
with open(STAGEDIR + "x3_overB.usda", "w") as fh:
    fh.write(OVER % "X3B")
ASSET = ("C:/Users/sruja_ob3di74/action-reasoner/skills/stage-core/"
         "stages/s5_widget.usda")

stage = omni.usd.get_context().get_stage()
refA = stage.DefinePrim("/World/X3A")
refA.GetReferences().AddReference(ASSET)
boxA = stage.GetPrimAtPath("/World/X3A/Box")
v_ref = float(boxA.GetAttribute("size").Get())
boxA.GetAttribute("size").Set(2.0)
v_direct = float(boxA.GetAttribute("size").Get())
stack0 = boxA.GetAttribute("size").GetPropertyStack(
    Usd.TimeCode.Default())[0].layer.GetDisplayName()
root = stage.GetRootLayer()
saved = list(root.subLayerPaths)
root.subLayerPaths = ([STAGEDIR + "x3_over.usda",
                       STAGEDIR + "x3_overB.usda"] + saved)
v_withsub = float(boxA.GetAttribute("size").Get())
refB = stage.DefinePrim("/World/X3B")
refB.GetReferences().AddReference(ASSET)
boxB = stage.GetPrimAtPath("/World/X3B/Box")
v_sub = float(boxB.GetAttribute("size").Get())
stackB = boxB.GetAttribute("size").GetPropertyStack(
    Usd.TimeCode.Default())[0].layer.GetDisplayName()
root.subLayerPaths = saved
print("X3-REPORT ref=%.1f direct=%.1f stop0=%s withsub=%.1f sub=%.1f stopB=%s"
      % (v_ref, v_direct, stack0, v_withsub, v_sub, stackB))
