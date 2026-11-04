"""Step STEPS physics steps (runs INSIDE Isaac Sim), print live truth.

STEPS is injected via isaacsim_send.py --arg STEPS=N. Stays playing.
"""
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import RigidPrim

rp = RigidPrim(paths="/World/LiveCube")
used = "update_app_async"
try:
    from isaacsim.core.api.simulation_context import SimulationContext
    sim = SimulationContext.instance()
    if sim is None:
        sim = SimulationContext()
    for _ in range(int(STEPS)):
        sim.step(render=True)
    used = "sim.step"
except Exception as exc:
    print("STEP-FALLBACK %r" % (exc,))
    await app_utils.update_app_async(steps=int(STEPS))
z = float(rp.get_world_poses()[0].numpy()[0][2])
try:
    vz = float(rp.get_velocities()[0].numpy()[0][2])
except Exception:
    vz = float("nan")
print("LIVE-TRUTH z=%.4f vz=%.4f via=%s" % (z, vz, used))
