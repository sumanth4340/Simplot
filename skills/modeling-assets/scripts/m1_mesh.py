"""M1 mesh (runs INSIDE Isaac Sim): 2x1x0.5 box, 6 outward-CCW quads.

Winding verified by cross products (e1 x e2 = outward normal):
-X [0,4,7,3], +X [1,2,6,5], -Y [0,1,5,4], +Y [3,7,6,2], +Z [4,5,6,7],
-Z [0,3,2,1]. Red displayColor. Bottom rests at z=0.
"""
from pxr import UsdGeom, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/M1Mesh")
if o and o.IsValid():
    stage.RemovePrim("/World/M1Mesh")
m = UsdGeom.Mesh.Define(stage, "/World/M1Mesh")
pts = [(-1, -0.5, -0.25), (1, -0.5, -0.25), (1, 0.5, -0.25), (-1, 0.5, -0.25),
       (-1, -0.5, 0.25), (1, -0.5, 0.25), (1, 0.5, 0.25), (-1, 0.5, 0.25)]
m.CreatePointsAttr().Set([Gf.Vec3f(*p) for p in pts])
m.CreateFaceVertexCountsAttr().Set([4, 4, 4, 4, 4, 4])
m.CreateFaceVertexIndicesAttr().Set([0, 4, 7, 3, 1, 2, 6, 5, 0, 1, 5, 4,
                                     3, 7, 6, 2, 4, 5, 6, 7, 0, 3, 2, 1])
m.GetDisplayColorAttr().Set([Gf.Vec3f(1, 0, 0)])
UsdGeom.Xformable(m.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.25))
n = len(m.GetPointsAttr().Get())
col = m.GetDisplayColorAttr().Get()[0]
print("M1-REPORT npoints=%d color=%.1f,%.1f,%.1f" % (n, col[0], col[1], col[2]))
