"""R1 build (runs INSIDE Isaac Sim): clean slate + lit stage + look-at camera.

Authoring only (no render): DomeLight 400 + DistantLight 1500, ground
plane, 1m test cube, USD camera at eye=(3,-3,2) looking at (0,0,0.5)
with focalLength 24. Reports authored attributes for verify_r1.
"""
import numpy as np
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/M1Bot", "/World/M1Ground", "/World/M1Target",
          "/World/M2Bot", "/World/M2Ground", "/World/M2Target",
          "/World/M3Bot", "/World/M3Ground", "/World/M3Target",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/R1Ground", "/World/R1Cube", "/World/R1Dome",
          "/World/R1Sun", "/World/R1Cam",
          "/World/YBot", "/World/YGround",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/R1Dome")
dome.GetIntensityAttr().Set(400.0)
sun = UsdLux.DistantLight.Define(stage, "/World/R1Sun")
sun.GetIntensityAttr().Set(1500.0)
UsdGeom.Xformable(sun.GetPrim()).AddRotateXYZOp().Set(Gf.Vec3f(-50, 20, 0))

g = UsdGeom.Plane.Define(stage, "/World/R1Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
cube = UsdGeom.Cube.Define(stage, "/World/R1Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))

eye = np.array([3.0, -3.0, 2.0])
tgt = np.array([0.0, 0.0, 0.5])
fwd = (tgt - eye) / np.linalg.norm(tgt - eye)   # camera -Z looks at target
right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
right /= np.linalg.norm(right)
up = np.cross(right, fwd)
mat = np.eye(4)
mat[0:3, 0], mat[0:3, 1], mat[0:3, 2] = right, up, -fwd
mat[0:3, 3] = eye
cam = UsdGeom.Camera.Define(stage, "/World/R1Cam")
cam.GetFocalLengthAttr().Set(24.0)
# USD Gf matrices are row-major (basis rows + eye in row 3): transpose.
UsdGeom.Xformable(cam.GetPrim()).MakeMatrixXform().Set(Gf.Matrix4d(
    *[float(v) for row in mat.T for v in row]))

d = UsdLux.DomeLight.Get(stage, "/World/R1Dome")
s = UsdLux.DistantLight.Get(stage, "/World/R1Sun")
print("R1-REPORT dome=%.1f sun=%.1f sunrot=%s cubesize=%.2f "
      "focal=%.1f campos=%s" % (
          float(d.GetIntensityAttr().Get()),
          float(s.GetIntensityAttr().Get()),
          [float(v) for v in UsdGeom.Xformable(
              s.GetPrim()).GetOrderedXformOps()[0].Get()],
          float(UsdGeom.Cube.Get(stage, "/World/R1Cube").GetSizeAttr().Get()),
          float(UsdGeom.Camera.Get(stage, "/World/R1Cam")
                .GetFocalLengthAttr().Get()),
          [round(float(v), 4) for v in UsdGeom.Xformable(
              stage.GetPrimAtPath("/World/R1Cam"))
              .GetOrderedXformOps()[0].Get()[3][:3]]))
