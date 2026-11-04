import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline, omni.usd
from pxr import UsdGeom, Gf
from isaacsim.core.simulation_manager import SimulationManager as S
S.switch_physics_engine("physx")
await app_utils.update_app_async(steps=10)
print("BACK=" + str(S.get_active_physics_engine()))
stage = omni.usd.get_context().get_stage()
app_utils.stop()
await app_utils.update_app_async(steps=5)
top = UsdGeom.Xformable(stage.GetPrimAtPath("/World/P1Cube")).GetOrderedXformOps()[0]
top.Set(Gf.Vec3d(0, 0, 2.0))
omni.timeline.get_timeline_interface().set_current_time(0.0)
app_utils.play()
await app_utils.update_app_async(steps=120)
from isaacsim.core.experimental.prims import RigidPrim
rp = RigidPrim(paths="/World/P1Cube")
print("RE-DROP z=%.4f usdz=%.4f" % (
    float(rp.get_world_poses()[0].numpy()[0][2]),
    float(top.Get()[2])))
omni.timeline.get_timeline_interface().pause()
