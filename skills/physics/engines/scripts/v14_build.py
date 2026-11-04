"""V14 build (runs INSIDE Isaac Sim): exam drop scene.

V14Cube 1.0m, mass 5, at z=3 (P1 scene untouched). Reports valid.
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf

stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/V14Cube")
if o and o.IsValid():
    stage.RemovePrim("/World/V14Cube")
c = UsdGeom.Cube.Define(stage, "/World/V14Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(0, 0, 3.0))
UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
UsdPhysics.CollisionAPI.Apply(c.GetPrim())
UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(5.0)
print("V14-BUILD-OK valid=%s" % c.GetPrim().IsValid())
