"""S2 build (runs INSIDE Isaac Sim): lidar range scene.

Ground + 1m cube at (2,0,0.5). Lidar authored by s2_lidar at
(0,0,1.5): beams hit cube face (~1.5m) and ground plane.
"""
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/R1Ground", "/World/R1Cube", "/World/R1Dome",
          "/World/R1Sun", "/World/R1Cam", "/World/R2Cam",
          "/World/R3Cam", "/World/R4Cam", "/World/V6Ground",
          "/World/V6CubeA", "/World/V6CubeB", "/World/V6Dome",
          "/World/V6Sun", "/World/V6Cam", "/World/V6Cap",
          "/World/S1Ground", "/World/S1Cube", "/World/S1Dome",
          "/World/S1Cam", "/World/S2Ground", "/World/S2Cube",
          "/World/S2Dome", "/World/S2Lidar", "/World/S2LidarB",
          "/World/S2Wall",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/S2Dome")
dome.GetIntensityAttr().Set(400.0)
g = UsdGeom.Plane.Define(stage, "/World/S2Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
cube = UsdGeom.Cube.Define(stage, "/World/S2Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(2, 0, 0.5))
print("S2-BUILD-OK dome=400.0 cubesize=1.00 cubex=2.00")
