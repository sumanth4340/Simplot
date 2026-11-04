"""P1 run (runs INSIDE Isaac Sim): PhysX drop baseline.

RigidPrim live poses; play + 120 steps; pause (never stop).
Reports z0/z1/dt/engine + rest speed. F1: never
SimulationContext.step in Kit.
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
from isaacsim.core.experimental.prims import RigidPrim
from isaacsim.core.simulation_manager import SimulationManager

tl = omni.timeline.get_timeline_interface()
rp = RigidPrim(paths="/World/P1Cube")
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
z0 = float(rp.get_world_poses()[0].numpy()[0][2])
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=120)
z1 = float(rp.get_world_poses()[0].numpy()[0][2])
t1 = float(tl.get_current_time())
lin, _ = rp.get_velocities()
spd = float(abs(lin.numpy()[0][2]))
eng = str(SimulationManager.get_active_physics_engine())
tl.pause()
print("P1-REPORT z0=%.4f z1=%.4f dt=%.3f vz=%.4f engine=%s" % (
    z0, z1, t1 - t0, spd, eng))
