"""S1 make cube (runs INSIDE Isaac Sim)."""
from pxr import UsdGeom, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
c = UsdGeom.Cube.Define(stage, "/World/S1Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(1, 2, 0.5))
print("S1-CUBE-OK")
