"""X14 cross-skill co-validation (runs INSIDE Isaac Sim): drop scene.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:    PhysicsScene/Ground/P1Cube/V14Cube valid
modeling lens: both cubes size 1.0
sense lens:    V14 stacked z ~1.5 (post-exam state)
physics lens:  V14 mass 5, rigid+collision APIs
app lens:      engine back on physx
"""
import omni.usd
from pxr import UsdGeom, UsdPhysics
from isaacsim.core.simulation_manager import SimulationManager as S

stage = omni.usd.get_context().get_stage()
paths = ["/World/PhysicsScene", "/World/P1Ground",
         "/World/P1Cube", "/World/V14Cube"]
valid = all(stage.GetPrimAtPath(p).IsValid() for p in paths)


def _size(p):
    return float(UsdGeom.Cube.Get(stage, p).GetSizeAttr().Get())


def _tz(p):
    for op in UsdGeom.Xformable(stage.GetPrimAtPath(p)).GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            return float(op.Get()[2])
    return 999.0


if valid:
    sP = _size("/World/P1Cube")
    sV = _size("/World/V14Cube")
    zV = _tz("/World/V14Cube")
    vp = stage.GetPrimAtPath("/World/V14Cube")
    mass = float(UsdPhysics.MassAPI(vp).GetMassAttr().Get())
    apis = vp.HasAPI(UsdPhysics.RigidBodyAPI) and vp.HasAPI(
        UsdPhysics.CollisionAPI)
else:
    sP = sV = zV = mass = -1.0
    apis = False
print("X14-REPORT valid=%s sP=%.2f sV=%.2f zV=%.2f mass=%.1f "
      "apis=%s engine=%s" % (
          valid, sP, sV, zV, mass, apis,
          S.get_active_physics_engine()))
