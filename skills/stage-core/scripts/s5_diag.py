"""S5 diagnosis (runs INSIDE Isaac Sim): inspect asset + reference state."""
from pxr import Usd
import omni.usd

P = "C:/Users/sruja_ob3di74/action-reasoner/skills/stage-core/stages/s5_widget.usda"
s = Usd.Stage.Open(P)
print("open:", bool(s))
if s:
    dp = s.GetDefaultPrim()
    print("defprim:", dp.GetPath() if dp else None)
    w = s.GetPrimAtPath("/Widget")
    print("widget valid:", w.IsValid())
    if w.IsValid():
        print("vsets:", w.GetVariantSets().GetNames())
        print("box:", s.GetPrimAtPath("/Widget/Box").IsValid())
stage = omni.usd.get_context().get_stage()
ref = stage.GetPrimAtPath("/World/S5Ref")
print("ref valid:", ref.IsValid())
if ref.IsValid():
    print("hasrefs:", ref.HasAuthoredReferences())
    print("refbox:", stage.GetPrimAtPath("/World/S5Ref/Box").IsValid())
    print("refchildren:", [str(c.GetPath()) for c in ref.GetChildren()])
    print("refvsets:", ref.GetVariantSets().GetNames())
