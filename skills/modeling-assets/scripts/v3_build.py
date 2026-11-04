"""V3 build (runs INSIDE Isaac Sim): ref asset + bind + 2x2 clones."""
from pxr import UsdShade, Gf, Sdf
import omni.usd
from isaacsim.core.cloner import GridCloner

STAGEDIR = "C:/Users/sruja_ob3di74/action-reasoner/skills/modeling-assets/"
stage = omni.usd.get_context().get_stage()
for p in ("/World/V3Bot", "/World/V3Looks", "/World/venvs"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

ref = stage.DefinePrim("/World/V3Bot")
ref.GetReferences().AddReference(STAGEDIR + "assets/m2_out/m2_bot/m2_bot.usda")

mat = UsdShade.Material.Define(stage, "/World/V3Looks/V3Red")
sh = UsdShade.Shader.Define(stage, "/World/V3Looks/V3Red/PBR")
sh.SetShaderId("UsdPreviewSurface")
sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1, 0, 0))
mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI(
    stage.GetPrimAtPath("/World/V3Bot/Geometry/base")).Bind(mat)

cloner = GridCloner(spacing=3.0)
cloner.define_base_env("/World/venvs")
paths = cloner.generate_paths("/World/venvs/env", 4)
positions = cloner.clone(source_prim_path="/World/V3Bot", prim_paths=paths)
bound = UsdShade.MaterialBindingAPI(
    stage.GetPrimAtPath("/World/V3Bot/Geometry/base")).GetDirectBinding().GetMaterialPath()
print("V3-REPORT bound=%s clones=%d" % (bound, len(positions)))
