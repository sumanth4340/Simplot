# D1 build2 (runs INSIDE Isaac Sim): PhysicsScene + CUDA device +
# rebuild soft cone. The deformable tensor backend needs an explicit
# UsdPhysics.Scene (the example gets one from the stage template)
# and set_device("cuda") before stage setup.
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.materials import VolumeDeformableMaterial
from isaacsim.core.experimental.objects import GroundPlane, Mesh
from isaacsim.core.experimental.prims import DeformablePrim
from isaacsim.core.simulation_manager import SimulationManager
from pxr import UsdPhysics, PhysxSchema, Gf
import omni.usd

SimulationManager.set_device("cuda")
print("ACTIVE:", SimulationManager.get_active_physics_engine())
st = omni.usd.get_context().get_stage()
for p in ("/World/D1Ground", "/World/D1Soft", "/World/D1Mat"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)
if not st.GetPrimAtPath("/World/PhysicsScene").IsValid():
    ps = UsdPhysics.Scene.Define(st, "/World/PhysicsScene")
    ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
    ps.CreateGravityMagnitudeAttr().Set(9.81)
    px = PhysxSchema.PhysxSceneAPI.Apply(ps.GetPrim())
    px.CreateTimeStepsPerSecondAttr().Set(60)
    px.CreateSolverTypeAttr().Set("TGS")
    px.CreateEnableStabilizationAttr().Set(True)
    print("SCENE-CREATED")
else:
    print("SCENE-EXISTS")
GroundPlane("/World/D1Ground")
stage_utils.define_prim("/World/D1Soft", "Xform")
Mesh("/World/D1Soft/mesh", primitives="Cone",
     positions=[0.0, 0.0, 1.5])
deformable = DeformablePrim("/World/D1Soft", deformable_type="volume")
material = VolumeDeformableMaterial(
    "/World/D1Mat", youngs_moduli=[1e5], poissons_ratios=[0.3],
    dynamic_frictions=[0.5], static_frictions=[0.5])
deformable.apply_physics_materials(material)
ok = all(st.GetPrimAtPath(p).IsValid() for p in (
    "/World/PhysicsScene", "/World/D1Ground", "/World/D1Soft",
    "/World/D1Soft/simulation_mesh", "/World/D1Soft/collision_mesh"))
print("D1-BUILD2-OK valid=%s" % ok)
