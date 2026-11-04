"""V6 build (runs INSIDE Isaac Sim): fresh exam scene, new layout.

Two cubes (0.5 at (0.8,0,0.25); 1.2 at (-0.9,0.3,0.6)), ground,
dome 300 + sun 1200, USD exam camera at eye=(-3.5,2.5,2.5) looking
at (0,0,0.5), focal 24. Reports geometry + rig for verify_v6.
"""
import numpy as np
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/R1Ground", "/World/R1Cube", "/World/R1Dome",
          "/World/R1Sun", "/World/R1Cam", "/World/R2Cam",
          "/World/R2ProbeCam", "/World/R2ProbeCam2", "/World/R3Cam",
          "/World/R4Cam", "/World/V6Ground", "/World/V6CubeA",
          "/World/V6CubeB", "/World/V6Dome", "/World/V6Sun",
          "/World/V6Cam", "/World/V6Cap",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

dome = UsdLux.DomeLight.Define(stage, "/World/V6Dome")
dome.GetIntensityAttr().Set(300.0)
sun = UsdLux.DistantLight.Define(stage, "/World/V6Sun")
sun.GetIntensityAttr().Set(1200.0)
UsdGeom.Xformable(sun.GetPrim()).AddRotateXYZOp().Set(Gf.Vec3f(-50, 20, 0))
g = UsdGeom.Plane.Define(stage, "/World/V6Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
for path, size, pos in (("/World/V6CubeA", 0.5, (0.8, 0, 0.25)),
                        ("/World/V6CubeB", 1.2, (-0.9, 0.3, 0.6))):
    c = UsdGeom.Cube.Define(stage, path)
    c.GetSizeAttr().Set(size)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(*pos))

eye = np.array([-3.5, 2.5, 2.5])
tgt = np.array([0.0, 0.0, 0.5])
fwd = (tgt - eye) / np.linalg.norm(tgt - eye)
right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
right /= np.linalg.norm(right)
up = np.cross(right, fwd)
mat = np.eye(4)
mat[0:3, 0], mat[0:3, 1], mat[0:3, 2] = right, up, -fwd
mat[0:3, 3] = eye
cam = UsdGeom.Camera.Define(stage, "/World/V6Cam")
cam.GetFocalLengthAttr().Set(24.0)
UsdGeom.Xformable(cam.GetPrim()).MakeMatrixXform().Set(Gf.Matrix4d(
    *[float(v) for row in mat.T for v in row]))
print("V6-BUILD-OK dome=300.0 sun=1200.0 sizeA=0.50 sizeB=1.20 eye=%s"
      % ([round(float(v), 2) for v in eye]))
