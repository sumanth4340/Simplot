"""S4 build (runs INSIDE Isaac Sim): two-point depth scene.

Ground + 1m cube (starts at (0,0,0.5)) + dome 400. Camera fixed at
eye=(0,-4,2) target=(0,0,0.5) by s4_run. Leg 2 slides the cube to
(0,1.0,0.5); center depth must follow 3.738 -> 4.806.
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/S3Ground", "/World/S3Cube", "/World/S3Dome",
          "/World/S4Ground", "/World/S4Cube", "/World/S4Dome",
          "/World/S4Cam",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/S4Dome")
dome.GetIntensityAttr().Set(400.0)
g = UsdGeom.Plane.Define(stage, "/World/S4Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
cube = UsdGeom.Cube.Define(stage, "/World/S4Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
print("S4-BUILD-OK dome=400.0 cubesize=1.00")
