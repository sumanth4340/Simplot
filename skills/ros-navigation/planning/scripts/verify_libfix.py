import sys
sys.path.insert(0, "C:/Users/sruja_ob3di74/Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/skills/navigation-primitives/scripts")
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf
stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/FPCheck")
if o and o.IsValid():
    stage.RemovePrim("/World/FPCheck")
bot = stage.DefinePrim("/World/FPCheck", "Xform")
UsdGeom.Xformable(bot).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.6))
link = UsdGeom.Cube.Define(stage, "/World/FPCheck/Link")
link.GetSizeAttr().Set(0.4)
UsdGeom.Xformable(link.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.2))
UsdPhysics.CollisionAPI.Apply(link.GetPrim())
from robot_footprint import compute_robot_footprint
fp = compute_robot_footprint(stage, "/World/FPCheck")
print("FPCHECK size=%s zoff=%.3f ins=%.4f cir=%.4f" % (
    tuple(round(v, 3) for v in fp["size"]), fp["z_offset"],
    fp["inscribed_radius"], fp["circumscribed_radius"]))
stage.RemovePrim("/World/FPCheck")
