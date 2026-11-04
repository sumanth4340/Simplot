"""A2 build (runs INSIDE Isaac Sim): 3-cube randomize stage.

A2Dome (3000), A2Ground 10x10, A2Cube0/1/2 0.8 at y=-1.2/0/1.2,
all labeled class:abox.
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

from isaacsim.core.experimental.utils.semantics import add_labels

stage = omni.usd.get_context().get_stage()
paths = ["/World/A2Dome", "/World/A2Ground", "/World/A2Cube0",
         "/World/A2Cube1", "/World/A2Cube2"]
# R5: bbox semantic set froze at first capture (kboxA/kboxB); new
# classes never join. Reuse kboxA and remove competing labeled
# prims so exactly 3 rows come back.
for p in ("/World/KDome", "/World/KGround", "/World/KCubeA",
          "/World/KCubeB", "/World/A1Dome", "/World/A1Ground",
          "/World/A1CubeA", "/World/A1CubeB"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
for p in paths:
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/A2Dome")
dome.GetIntensityAttr().Set(3000.0)
g = UsdGeom.Cube.Define(stage, "/World/A2Ground")
g.GetSizeAttr().Set(10.0)
UsdGeom.Xformable(g.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
for i, y in enumerate((-1.2, 0.0, 1.2)):
    c = UsdGeom.Cube.Define(stage, "/World/A2Cube%d" % i)
    c.GetSizeAttr().Set(0.8)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(
        Gf.Vec3d(0, y, 0.4))
    add_labels(stage.GetPrimAtPath("/World/A2Cube%d" % i),
               labels=["abox"])
print("A2-BUILD-OK valid=%s"
      % all(stage.GetPrimAtPath(p).IsValid() for p in paths))
