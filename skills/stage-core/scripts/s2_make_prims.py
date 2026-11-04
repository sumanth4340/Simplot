"""S2 make prims (runs INSIDE Isaac Sim): 6 typed prims, known params."""
from pxr import UsdGeom, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("S2_Cube", "S2_Sphere", "S2_Cyl", "S2_Cone", "S2_Plane", "S2_Mesh"):
    o = stage.GetPrimAtPath("/World/" + p)
    if o and o.IsValid():
        stage.RemovePrim("/World/" + p)

c = UsdGeom.Cube.Define(stage, "/World/S2_Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))

s = UsdGeom.Sphere.Define(stage, "/World/S2_Sphere")
s.GetRadiusAttr().Set(0.5)
UsdGeom.Xformable(s.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(2, 0, 0.5))

y = UsdGeom.Cylinder.Define(stage, "/World/S2_Cyl")
y.GetRadiusAttr().Set(0.25)
y.GetHeightAttr().Set(2.0)
UsdGeom.Xformable(y.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(4, 0, 1.0))

n = UsdGeom.Cone.Define(stage, "/World/S2_Cone")
n.GetRadiusAttr().Set(0.5)
n.GetHeightAttr().Set(1.0)
UsdGeom.Xformable(n.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(6, 0, 0.5))

p = UsdGeom.Plane.Define(stage, "/World/S2_Plane")
p.CreateWidthAttr().Set(4.0)
p.CreateLengthAttr().Set(2.0)
UsdGeom.Xformable(p.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(8, 0, 0))

m = UsdGeom.Mesh.Define(stage, "/World/S2_Mesh")
m.CreatePointsAttr().Set([Gf.Vec3f(0, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(0, 1, 0)])
m.CreateFaceVertexCountsAttr().Set([3])
m.CreateFaceVertexIndicesAttr().Set([0, 1, 2])
UsdGeom.Xformable(m.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(10, 0, 0.5))
print("S2-MAKE-OK 6 prims")
