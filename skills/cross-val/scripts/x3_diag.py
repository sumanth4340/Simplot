"""X3 diagnosis (runs INSIDE Isaac Sim): full stack after each op."""
from pxr import Usd
import omni.usd

STAGEDIR = "C:/Users/sruja_ob3di74/action-reasoner/skills/cross-val/stages/"
stage = omni.usd.get_context().get_stage()
ref = stage.DefinePrim("/World/X3Ref")
ref.GetReferences().AddReference(
    "C:/Users/sruja_ob3di74/action-reasoner/skills/stage-core/stages/s5_widget.usda")


def dump(tag):
    box = stage.GetPrimAtPath("/World/X3Ref/Box")
    attr = box.GetAttribute("size")
    stack = [(s.layer.GetDisplayName()) for s in
             attr.GetPropertyStack(Usd.TimeCode.Default())]
    print("%s value=%s stack=%s authored=%s" % (
        tag, attr.Get(), stack, attr.HasAuthoredValue()))


dump("ref-only")
box = stage.GetPrimAtPath("/World/X3Ref/Box")
box.GetAttribute("size").Set(2.0)
dump("after-set")
root = stage.GetRootLayer()
saved = list(root.subLayerPaths)
root.subLayerPaths = [STAGEDIR + "x3_over.usda"] + saved
dump("withsub")
box2 = stage.GetPrimAtPath("/World/X3Ref/Box")
ok = box2.GetAttribute("size").Clear()
print("clear returned:", ok)
dump("after-clear")
print("root direct:", [str(p.GetPath()) for p in
      [stage.GetPrimAtPath("/World/X3Ref/Box")] if p.IsValid()])
root.subLayerPaths = saved
