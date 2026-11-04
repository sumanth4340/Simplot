"""A3 build (runs INSIDE Isaac Sim): scale-sweep stage.

A3Dome (3000), A3Ground 10x10, A3Cube0/1 0.8 labeled class:abox.
Must be the FIRST labeled capture after a restart (bbox
annotators freeze the labeled instance set at first capture).
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

from isaacsim.core.experimental.utils.semantics import add_labels

stage = omni.usd.get_context().get_stage()
paths = ["/World/A3Dome", "/World/A3Ground", "/World/A3Cube0",
         "/World/A3Cube1"]
for p in paths:
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/A3Dome")
dome.GetIntensityAttr().Set(3000.0)
g = UsdGeom.Cube.Define(stage, "/World/A3Ground")
g.GetSizeAttr().Set(10.0)
UsdGeom.Xformable(g.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
for i, x in enumerate((-1.0, 1.0)):
    c = UsdGeom.Cube.Define(stage, "/World/A3Cube%d" % i)
    c.GetSizeAttr().Set(0.8)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(
        Gf.Vec3d(x, 0, 0.4))
    add_labels(stage.GetPrimAtPath("/World/A3Cube%d" % i),
               labels=["abox"])
print("A3-BUILD-OK valid=%s"
      % all(stage.GetPrimAtPath(p).IsValid() for p in paths))
