"""N3 build (runs INSIDE Isaac Sim): footprint bot.

N3Bot root at z=0.6; link cube 0.4 with CollisionAPI at local
z=-0.2 -> world AABB x/y +-0.2, z 0.2..0.6. Expect size
(0.4,0.4,0.4), z_offset 0.4, inscribed 0.2, circumscribed 0.2828.
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf

stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/N3Bot")
if o and o.IsValid():
    stage.RemovePrim("/World/N3Bot")

bot = stage.DefinePrim("/World/N3Bot", "Xform")
UsdGeom.Xformable(bot).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.6))
link = UsdGeom.Cube.Define(stage, "/World/N3Bot/Link")
link.GetSizeAttr().Set(0.4)
UsdGeom.Xformable(link.GetPrim()).AddTranslateOp().Set(
    Gf.Vec3d(0, 0, -0.2))
UsdPhysics.CollisionAPI.Apply(link.GetPrim())
print("N3-BUILD-OK bot=%s link=%s" % (
    bot.IsValid(), link.GetPrim().IsValid()))
