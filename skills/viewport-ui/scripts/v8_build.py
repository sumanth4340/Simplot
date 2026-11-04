"""V8 build (runs INSIDE Isaac Sim): exam scene, new layout.

Two cubes (0.5 at (0.9,0,0.25); 1.0 at (-0.8,0.4,0.5)), ground,
dome 300 + sun 1200. Exam captures from eye=(-3,2.5,2.5).
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/W1Ground", "/World/W1Cube", "/World/W1Dome",
          "/World/W1Sun",
          "/World/V8Ground", "/World/V8CubeA", "/World/V8CubeB",
          "/World/V8Dome", "/World/V8Sun",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/V8Dome")
dome.GetIntensityAttr().Set(300.0)
sun = UsdLux.DistantLight.Define(stage, "/World/V8Sun")
sun.GetIntensityAttr().Set(1200.0)
UsdGeom.Xformable(sun.GetPrim()).AddRotateXYZOp().Set(Gf.Vec3f(-50, 20, 0))
g = UsdGeom.Plane.Define(stage, "/World/V8Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
for path, size, pos in (("/World/V8CubeA", 0.5, (0.9, 0, 0.25)),
                        ("/World/V8CubeB", 1.0, (-0.8, 0.4, 0.5))):
    c = UsdGeom.Cube.Define(stage, path)
    c.GetSizeAttr().Set(size)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(*pos))
print("V8-BUILD-OK dome=300.0 sun=1200.0 sizeA=0.50 sizeB=1.00")
