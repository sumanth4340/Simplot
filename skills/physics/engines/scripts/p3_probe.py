"""P3 probe (runs INSIDE Isaac Sim): engine switching API.

Reports available/default engines, then switches
physx->newton->physx with active confirms + backend reads.
Ends on physx (clean handoff).
"""
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.simulation_manager import SimulationManager as S

avail = sorted(str(a) for a in S.get_available_physics_engines())
default = str(S.get_default_engine())
S.switch_physics_engine("newton")
await app_utils.update_app_async(steps=10)
a1 = str(S.get_active_physics_engine())
b1 = str(S.get_backend())
S.switch_physics_engine("physx")
await app_utils.update_app_async(steps=10)
a2 = str(S.get_active_physics_engine())
b2 = str(S.get_backend())
print("P3-REPORT avail=%s default=%s a1=%s b1=%s a2=%s b2=%s" % (
    avail, default, a1, b1, a2, b2))
