# D1 diag (INSIDE Isaac Sim): why does the deformable tensor
# backend have no data? Print validity chain + exact read error.
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import DeformablePrim
from isaacsim.core.simulation_manager import SimulationManager
import omni.timeline
import omni.usd

st = omni.usd.get_context().get_stage()
for p in ("/World/PhysicsScene", "/World/D1Soft",
          "/World/D1Soft/simulation_mesh",
          "/World/D1Soft/collision_mesh", "/World/D1Soft/mesh"):
    pr = st.GetPrimAtPath(p)
    print("PRIM %s valid=%s type=%s" % (
        p, pr.IsValid(), pr.GetTypeName() if pr.IsValid() else "-"))
print("ACTIVE:", SimulationManager.get_active_physics_engine())
d = DeformablePrim("/World/D1Soft", deformable_type="volume")
print("prim-valid:", d.valid)
app_utils.play(commit=True)
await app_utils.update_app_async(steps=30)
print("playing:", omni.timeline.get_timeline_interface().is_playing())
print("tensor-entity-valid:", d.is_physics_tensor_entity_valid())
print("view-none:", d._physics_deformable_body_view is None)
sv = SimulationManager._physics_sim_view__warp
print("simview-none:", sv is None,
      "simview-valid:", None if sv is None else sv.is_valid)
try:
    r = d._physics_deformable_body_view.get_simulation_nodal_positions()
    print("VIEW-READ ok shape=", tuple(r.shape))
except Exception as e:
    print("VIEW-READ-ERR", repr(e)[:300])
try:
    p = d.get_nodal_positions()
    print("GET ok lens=", len(p))
except Exception as e:
    print("GET-ERR", repr(e)[:300])
app_utils.stop()
print("D1-DIAG done")
