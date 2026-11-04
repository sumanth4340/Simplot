"""Drill 01 setup (runs INSIDE Isaac Sim): one known cube.

UsdGeom.Cube `size` attr IS the edge length (size=2 -> extent [-1,1]^3).
size=1.0 -> 1.0 m edge. Expected sense: pos=[2,-1,0.5] size=[1,1,1].
"""
from pxr import UsdGeom, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
path = "/World/SenseCube"
old = stage.GetPrimAtPath(path)
if old and old.IsValid():
    stage.RemovePrim(path)
cube = UsdGeom.Cube.Define(stage, path)
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(2.0, -1.0, 0.5))
print("DRILL01-SETUP-OK /World/SenseCube size=1.0 pos=2,-1,0.5")
