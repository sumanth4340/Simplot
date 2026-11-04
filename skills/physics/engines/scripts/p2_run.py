"""P2 run (runs INSIDE Isaac Sim): Newton drop equivalence.

stop -> reset cube z=2 + clock 0 (F4) -> enable Newton ext ->
switch engine -> confirm active -> play 120 -> pause. Reports
sig/avail/active/z1/dt. Same scene as P1; rest must match 0.5.
"""
import inspect
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from pxr import UsdGeom, Gf
from isaacsim.core.experimental.prims import RigidPrim
from isaacsim.core.simulation_manager import SimulationManager as S

tl = omni.timeline.get_timeline_interface()
stage = omni.usd.get_context().get_stage()
app_utils.stop()
await app_utils.update_app_async(steps=5)
top = UsdGeom.Xformable(
    stage.GetPrimAtPath("/World/P1Cube")).GetOrderedXformOps()[0]
top.Set(Gf.Vec3d(0, 0, 2.0))
tl.set_current_time(0.0)
app_utils.enable_extension("isaacsim.physics.newton")
await app_utils.update_app_async(steps=30)
avail = S.get_available_physics_engines()
sig = str(inspect.signature(S.switch_physics_engine))
S.switch_physics_engine("newton")
await app_utils.update_app_async(steps=10)
active = str(S.get_active_physics_engine())
rp = RigidPrim(paths="/World/P1Cube")
app_utils.play()
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=120)
z1 = float(rp.get_world_poses()[0].numpy()[0][2])
t1 = float(tl.get_current_time())
lin, _ = rp.get_velocities()
spd = float(abs(lin.numpy()[0][2]))
tl.pause()
print("P2-REPORT avail=%s active=%s z1=%.4f dt=%.3f vz=%.4f" % (
    sorted(str(a) for a in avail), active, z1, t1 - t0, spd))
print("P2-SIG " + sig)
