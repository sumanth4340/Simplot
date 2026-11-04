"""M3 material (runs INSIDE Isaac Sim): red UsdPreviewSurface, bound.

Cube + /World/Looks/M3Red (diffuse red, roughness 0.4, metallic 0.0),
surface-wired and bound to the cube. Reports binding + value readback.
"""
from pxr import UsdGeom, UsdShade, Gf, Sdf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/M3Cube", "/World/Looks"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
c = UsdGeom.Cube.Define(stage, "/World/M3Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))

mat = UsdShade.Material.Define(stage, "/World/Looks/M3Red")
sh = UsdShade.Shader.Define(stage, "/World/Looks/M3Red/PBRShader")
sh.SetShaderId("UsdPreviewSurface")
sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1, 0, 0))
sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI(c.GetPrim()).Bind(mat)

bound = UsdShade.MaterialBindingAPI(c.GetPrim()).GetDirectBinding().GetMaterialPath()
dif = sh.GetInput("diffuseColor").Get()
rgh = float(sh.GetInput("roughness").Get())
print("M3-REPORT bound=%s diffuse=%.1f,%.1f,%.1f rough=%.1f"
      % (bound, dif[0], dif[1], dif[2], rgh))
