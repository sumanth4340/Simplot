"""Newton motion probe (runs INSIDE Isaac Sim): render-observed drop.

Reset z=2 -> switch newton -> shot A -> play 120 -> shot B.
Pixel diff between shots is ground truth for motion, immune to
readback-path questions (tensor backend lacks Newton support).
"""
import omni.usd
import omni.timeline
import isaacsim.core.experimental.utils.app as app_utils
from pxr import UsdGeom, Gf
from isaacsim.core.simulation_manager import SimulationManager as S

stage = omni.usd.get_context().get_stage()
tl = omni.timeline.get_timeline_interface()
app_utils.stop()
await app_utils.update_app_async(steps=5)
top = UsdGeom.Xformable(
    stage.GetPrimAtPath("/World/P1Cube")).GetOrderedXformOps()[0]
top.Set(Gf.Vec3d(0, 0, 2.0))
tl.set_current_time(0.0)
S.switch_physics_engine("newton")
await app_utils.update_app_async(steps=10)
print("ACTIVE=" + str(S.get_active_physics_engine()))
