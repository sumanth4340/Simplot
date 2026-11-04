"""A1 build (runs INSIDE Isaac Sim): lit 2-class KITTI stage.

A1Dome (3000), A1Ground 10x10, A1CubeA/B 1.0 at x=-/+0.8,
labeled class:kboxA/kboxB.
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

from isaacsim.core.experimental.utils.semantics import add_labels

stage = omni.usd.get_context().get_stage()
for p in ("/World/A1Dome", "/World/A1Ground", "/World/A1CubeA",
          "/World/A1CubeB"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/A1Dome")
dome.GetIntensityAttr().Set(3000.0)
g = UsdGeom.Cube.Define(stage, "/World/A1Ground")
g.GetSizeAttr().Set(10.0)
UsdGeom.Xformable(g.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
for name, x, lab in (("A1CubeA", -0.8, "kboxA"),
                     ("A1CubeB", 0.8, "kboxB")):
    c = UsdGeom.Cube.Define(stage, "/World/" + name)
    c.GetSizeAttr().Set(1.0)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(
        Gf.Vec3d(x, 0, 0.5))
    add_labels(stage.GetPrimAtPath("/World/" + name), labels=[lab])
ok = all(stage.GetPrimAtPath(p).IsValid() for p in (
    "/World/A1Dome", "/World/A1Ground", "/World/A1CubeA",
    "/World/A1CubeB"))
print("A1-BUILD-OK valid=%s" % ok)
