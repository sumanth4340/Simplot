"""S5 composition (runs INSIDE Isaac Sim): reference + variant + payload.

Authors s5_widget.usda (defaultPrim Widget, config small/large variants),
references it, switches variant, then payloads it with unload/load cycle.
"""
from pxr import Sdf, Usd, UsdGeom
import omni.usd

STAGEDIR = "C:/Users/sruja_ob3di74/action-reasoner/skills/stage-core/stages/"
ASSET = STAGEDIR + "s5_widget.usda"

ast = Usd.Stage.CreateNew(ASSET)
ast.SetDefaultPrim(ast.DefinePrim("/Widget", "Xform"))
w = ast.GetPrimAtPath("/Widget")
vset = w.GetVariantSets().AddVariantSet("config")
vset.AddVariant("small")
vset.AddVariant("large")
vset.SetVariantSelection("small")
with vset.GetVariantEditContext():
    b = UsdGeom.Cube.Define(ast, "/Widget/Box")
    b.GetSizeAttr().Set(1.0)
vset.SetVariantSelection("large")
with vset.GetVariantEditContext():
    b = UsdGeom.Cube.Define(ast, "/Widget/Box")
    b.GetSizeAttr().Set(4.0)
vset.SetVariantSelection("small")
ast.GetRootLayer().Save()

stage = omni.usd.get_context().get_stage()
ref = stage.DefinePrim("/World/S5Ref")
ref.GetReferences().AddReference(ASSET)
box = stage.GetPrimAtPath("/World/S5Ref/Box")
small = float(box.GetAttribute("size").Get())
ref.GetVariantSets().GetVariantSet("config").SetVariantSelection("large")
large = float(box.GetAttribute("size").Get())

pay = stage.DefinePrim("/World/S5Pay")
pay.GetPayloads().AddPayload(ASSET)
loaded = stage.GetPrimAtPath("/World/S5Pay/Box").IsValid()
stage.Unload(Sdf.Path("/World/S5Pay"))
gone = not stage.GetPrimAtPath("/World/S5Pay/Box").IsValid()
stage.Load(Sdf.Path("/World/S5Pay"))
back = stage.GetPrimAtPath("/World/S5Pay/Box").IsValid()
print("S5-REPORT small=%.1f large=%.1f loaded=%s gone=%s back=%s"
      % (small, large, loaded, gone, back))
