"""V3 check (runs INSIDE Isaac Sim, post-open): bindings persisted."""
from pxr import UsdShade
import omni.usd

stage = omni.usd.get_context().get_stage()
b0 = UsdShade.MaterialBindingAPI(
    stage.GetPrimAtPath("/World/V3Bot/Geometry/base")).GetDirectBinding().GetMaterialPath()
b1 = UsdShade.MaterialBindingAPI(
    stage.GetPrimAtPath("/World/venvs/env_0/Geometry/base")).GetDirectBinding().GetMaterialPath()
print("V3-CHECK base=%s clone=%s" % (b0, b1))
