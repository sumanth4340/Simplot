"""S3 build (runs INSIDE Isaac Sim): resting-cube physics scene.

PhysicsScene + gravity, ground collider, 1m rigid cube (1kg) resting
at (0,0,0.5). IMU + Contact authored by s3_run (physics sensors).
"""
import omni.usd
from pxr import UsdGeom, UsdLux, UsdPhysics, PhysxSchema, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/S1Ground", "/World/S1Cube", "/World/S1Dome",
          "/World/S1Cam", "/World/S2Ground", "/World/S2Cube",
          "/World/S2Dome", "/World/S2Lidar", "/World/S2LidarB",
          "/World/S2Wall", "/World/S3Ground", "/World/S3Cube",
          "/World/S3Dome",
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
# R7: sleeping pairs emit NO contact reports - keep bodies awake.
stage.GetPrimAtPath("/World/PhysicsScene").GetAttribute(
    "physxScene:disableSleeping").Set(True)
dome = UsdLux.DomeLight.Define(stage, "/World/S3Dome")
dome.GetIntensityAttr().Set(400.0)
g = UsdGeom.Plane.Define(stage, "/World/S3Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
cube = UsdGeom.Cube.Define(stage, "/World/S3Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.6))
UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).GetMassAttr().Set(1.0)
PhysxSchema.PhysxContactReportAPI.Apply(cube.GetPrim())
PhysxSchema.PhysxContactReportAPI(cube.GetPrim()).CreateThresholdAttr(0.0)
print("S3-BUILD-OK g=9.81 mass=1.00 cubez=0.60")
