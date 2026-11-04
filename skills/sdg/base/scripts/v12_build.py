"""V12 build (runs INSIDE Isaac Sim): SELF-CONTAINED exam scene.

R5: bbox freezes the semantic set at first capture, so V12 owns
its whole stage: V12Dome (3000), V12Ground 10x10, V12BoxA 0.8 at
(-1,0,0.4) labeled v12a, V12BoxB 0.8 at (1,0.5,0.4) labeled v12b.
Run on a FRESH sim (restart before V12). Reports valid + labels.
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf
from isaacsim.core.experimental.utils.semantics import (
    add_labels, get_labels)

stage = omni.usd.get_context().get_stage()
for p in ("/World/V12Dome", "/World/V12Ground",
          "/World/V12BoxA", "/World/V12BoxB"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/V12Dome")
dome.GetIntensityAttr().Set(3000.0)
g = UsdGeom.Cube.Define(stage, "/World/V12Ground")
g.GetSizeAttr().Set(10.0)
UsdGeom.Xformable(g.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
a = UsdGeom.Cube.Define(stage, "/World/V12BoxA")
a.GetSizeAttr().Set(0.8)
UsdGeom.Xformable(a.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(-1, 0, 0.4))
add_labels(a.GetPrim(), labels=["v12a"])
b = UsdGeom.Cube.Define(stage, "/World/V12BoxB")
b.GetSizeAttr().Set(0.8)
UsdGeom.Xformable(b.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(1, 0.5, 0.4))
add_labels(b.GetPrim(), labels=["v12b"])
print("V12-BUILD-OK valid=%s labels=%s,%s" % (
    all(stage.GetPrimAtPath(p).IsValid() for p in (
        "/World/V12Dome", "/World/V12Ground",
        "/World/V12BoxA", "/World/V12BoxB")),
    get_labels(a.GetPrim()), get_labels(b.GetPrim())))
