"""W1 build (runs INSIDE Isaac Sim): screenshot scene.

Dome 400 + sun 1500, ground, 1m cube at (0,0,0.5). The viewport
screenshot itself is taken by the library's viewport_screenshot.py
via --arg output_path (reused, not reimplemented).
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/V7Ground", "/World/V7Cube", "/World/V7Dome",
          "/World/V7Cam",
          "/World/W1Ground", "/World/W1Cube", "/World/W1Dome",
          "/World/W1Sun",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/W1Dome")
dome.GetIntensityAttr().Set(400.0)
sun = UsdLux.DistantLight.Define(stage, "/World/W1Sun")
sun.GetIntensityAttr().Set(1500.0)
UsdGeom.Xformable(sun.GetPrim()).AddRotateXYZOp().Set(Gf.Vec3f(-50, 20, 0))
g = UsdGeom.Plane.Define(stage, "/World/W1Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
cube = UsdGeom.Cube.Define(stage, "/World/W1Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
print("W1-BUILD-OK dome=400.0 sun=1500.0 cubesize=1.00")
