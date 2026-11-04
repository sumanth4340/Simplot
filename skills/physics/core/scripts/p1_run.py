"""P1 run (runs INSIDE Isaac Sim): play 120 steps, report live motion.

Live poses via RigidPrim tensors (XformCache returns authored state).
Prefers SimulationContext.step(render=True); falls back to update_app_async.
Pauses (never stops) so sim state survives for the sense snapshot.
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
from isaacsim.core.experimental.prims import RigidPrim

tl = omni.timeline.get_timeline_interface()
try:
    from isaacsim.core.simulation_manager import SimulationManager
    engine = str(SimulationManager.get_active_physics_engine())
except Exception as exc:
    engine = "unknown:%r" % (exc,)

rp = RigidPrim(paths="/World/P1Cube")
app_utils.play()
z0 = float(rp.get_world_poses()[0].numpy()[0][2])
t0 = float(tl.get_current_time())
used = "update_app_async"
try:
    from isaacsim.core.api.simulation_context import SimulationContext
    sim = SimulationContext.instance()
    if sim is None:
        sim = SimulationContext()
    for _ in range(120):
        sim.step(render=True)
    used = "sim.step(render=True)"
except Exception as exc:
    print("P1-STEP-FALLBACK %r" % (exc,))
    await app_utils.update_app_async(steps=120)
z1 = float(rp.get_world_poses()[0].numpy()[0][2])
t1 = float(tl.get_current_time())
tl.pause()
print("P1-MOTION-REPORT z0=%.4f z1=%.4f t0=%.3f t1=%.3f engine=%s via=%s"
      % (z0, z1, t0, t1, engine, used))
