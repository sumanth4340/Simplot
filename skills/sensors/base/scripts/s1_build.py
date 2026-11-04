"""S1 build (runs INSIDE Isaac Sim): depth-validation scene.

Ground + 1m cube centered at (0,0,0.5) + dome 400. Camera pose is
authored by s1_cap (RtxCamera). Reports geometry for verify_s1.
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
          "/World/S1Cam",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/S1Dome")
dome.GetIntensityAttr().Set(400.0)
g = UsdGeom.Plane.Define(stage, "/World/S1Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
cube = UsdGeom.Cube.Define(stage, "/World/S1Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
print("S1-BUILD-OK dome=400.0 cubesize=1.00 cubez=0.50")
