# D1 deformable probe (INSIDE Isaac Sim): Newton engine check +
# volume deformable drop + numeric read surface (nodal stresses,
# positions, element indices).
import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.materials import VolumeDeformableMaterial
from isaacsim.core.experimental.objects import GroundPlane, Mesh
from isaacsim.core.experimental.prims import DeformablePrim
from isaacsim.core.simulation_manager import SimulationManager
import omni.usd

app_utils.enable_extension("isaacsim.physics.newton")
await app_utils.update_app_async(steps=10)
try:
    print("ENGINES", SimulationManager.get_available_physics_engines())
except Exception as e:
    print("ENGINES-ERR", repr(e)[:160])
print("ACTIVE-BEFORE", SimulationManager.get_active_physics_engine())
SimulationManager.switch_physics_engine("newton")
await app_utils.update_app_async(steps=10)
print("ACTIVE-AFTER", SimulationManager.get_active_physics_engine())
print("BACKEND", SimulationManager.get_backend())

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/World/D1Ground").IsValid():
    st.RemovePrim("/World/D1Ground")
if st.GetPrimAtPath("/World/D1Soft").IsValid():
    st.RemovePrim("/World/D1Soft")
if st.GetPrimAtPath("/World/D1Mat").IsValid():
    st.RemovePrim("/World/D1Mat")
GroundPlane("/World/D1Ground")
stage_utils.define_prim("/World/D1Soft", "Xform")
Mesh("/World/D1Soft/mesh", primitives="Cone",
     positions=[0.0, 0.0, 1.5])
deformable = DeformablePrim("/World/D1Soft", deformable_type="volume")
material = VolumeDeformableMaterial(
    "/World/D1Mat", youngs_moduli=[1e4], poissons_ratios=[0.3],
    dynamic_frictions=[0.5], static_frictions=[0.5])
deformable.apply_physics_materials(material)
print("DEFORMABLE-OK")
print("METHODS", sorted(m for m in dir(deformable)
                        if "nod" in m.lower() or "elem" in m.lower()
                        or "pos" in m.lower() or "stress" in m.lower()))

app_utils.play()
await app_utils.update_app_async(steps=10)
for name in ("get_nodal_stresses", "get_element_indices",
             "get_nodal_positions", "get_world_poses"):
    try:
        fn = getattr(deformable, name, None)
        if fn is None:
            print("NO", name)
            continue
        r = fn()
        import numpy as _np
        a = r.numpy() if hasattr(r, "numpy") else r
        a = _np.asarray(a, dtype=float)
        print("READ %s shape=%s min=%.4f max=%.4f" % (
            name, a.shape, float(a.min()), float(a.max())))
    except Exception as e:
        print("READ-ERR", name, repr(e)[:200])
app_utils.stop()
print("D1-PROBE done")
