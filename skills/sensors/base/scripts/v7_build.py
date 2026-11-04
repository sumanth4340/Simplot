"""V7 build (runs INSIDE Isaac Sim): exam scene, new layout + modalities.

1.2m rigid cube (2kg) dropped from (0,0,0.7), ground, dome 300,
physics (no-sleep + report API). Depth camera (v7_run) at
eye=(4,0,2) target=(0,0,0.6): center depth ~= 3.602.
"""
import omni.usd
from pxr import UsdGeom, UsdLux, UsdPhysics, PhysxSchema, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/S4Ground", "/World/S4Cube", "/World/S4Dome",
          "/World/S4Cam", "/World/S3Ground", "/World/S3Cube",
          "/World/S3Dome",
          "/World/V7Ground", "/World/V7Cube", "/World/V7Dome",
          "/World/V7Cam",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
stage.GetPrimAtPath("/World/PhysicsScene").GetAttribute(
    "physxScene:disableSleeping").Set(True)
dome = UsdLux.DomeLight.Define(stage, "/World/V7Dome")
dome.GetIntensityAttr().Set(300.0)
g = UsdGeom.Plane.Define(stage, "/World/V7Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
cube = UsdGeom.Cube.Define(stage, "/World/V7Cube")
cube.GetSizeAttr().Set(1.2)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.7))
UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).GetMassAttr().Set(2.0)
PhysxSchema.PhysxContactReportAPI.Apply(cube.GetPrim())
PhysxSchema.PhysxContactReportAPI(cube.GetPrim()).CreateThresholdAttr(0.0)
print("V7-BUILD-OK dome=300.0 size=1.20 mass=2.00 cubez=0.70")
