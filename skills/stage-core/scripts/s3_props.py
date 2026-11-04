"""S3 props (runs INSIDE Isaac Sim): 12-op set/get matrix on one cube."""
from pxr import UsdGeom, Gf, Sdf
import omni.usd

stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/S3Cube")
if o and o.IsValid():
    stage.RemovePrim("/World/S3Cube")
c = UsdGeom.Cube.Define(stage, "/World/S3Cube")
prim = c.GetPrim()
c.GetSizeAttr().Set(2.0)
xf = UsdGeom.Xformable(prim)
xf.AddTranslateOp().Set(Gf.Vec3d(1, 2, 3))
xf.AddRotateXYZOp().Set(Gf.Vec3f(0, 0, 90))
xf.AddScaleOp().Set(Gf.Vec3f(2, 1, 0.5))
c.GetDisplayColorAttr().Set([Gf.Vec3f(1, 0, 0)])
c.GetDisplayOpacityAttr().Set([0.5])
img = UsdGeom.Imageable(prim)
img.MakeInvisible()
vis1 = str(img.GetVisibilityAttr().Get())
img.MakeVisible()
vis2 = str(img.GetVisibilityAttr().Get())
img.GetPurposeAttr().Set("guide")
pur1 = str(img.GetPurposeAttr().Get())
img.GetPurposeAttr().Set("render")
pur2 = str(img.GetPurposeAttr().Get())
prim.CreateAttribute("master:tag", Sdf.ValueTypeNames.String, custom=True).Set("s3")

tr = prim.GetAttribute("xformOp:translate").Get()
ro = prim.GetAttribute("xformOp:rotateXYZ").Get()
sc = prim.GetAttribute("xformOp:scale").Get()
col = c.GetDisplayColorAttr().Get()[0]
print("S3-REPORT tr=%.1f,%.1f,%.1f rot=%.1f,%.1f,%.1f sc=%.1f,%.1f,%.1f "
      "size=%.1f color=%.1f,%.1f,%.1f vis1=%s vis2=%s pur1=%s pur2=%s "
      "op=%.1f tag=%s"
      % (tr[0], tr[1], tr[2], ro[0], ro[1], ro[2], sc[0], sc[1], sc[2],
         float(c.GetSizeAttr().Get()), col[0], col[1], col[2],
         vis1, vis2, pur1, pur2,
         float(c.GetDisplayOpacityAttr().Get()[0]),
         prim.GetAttribute("master:tag").Get()))
