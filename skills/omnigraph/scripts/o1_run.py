"""O1 run (runs INSIDE Isaac Sim): prove ticks execute the write.

Pre-play translate must still be 0.5 (authoring moves nothing);
after 60 played steps the graph must have written z=1.5.
"""
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()


def _z():
    xp = UsdGeom.Xformable(stage.GetPrimAtPath("/World/O1Cube"))
    for op in xp.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            return float(op.Get()[2])
    return -1.0


def _set_z(v):
    from pxr import Gf
    xp = UsdGeom.Xformable(stage.GetPrimAtPath("/World/O1Cube"))
    for op in xp.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            op.Set(Gf.Vec3d(0, 0, v))


z0a = _z()  # authoring already wrote (R1: edit evaluates promptly)
_set_z(0.5)  # reset separates authoring effects from tick effects
z0 = _z()
app_utils.play(commit=True)
await app_utils.update_app_async(steps=60)
z1 = _z()
print("O1-REPORT z0a=%.4f z0=%.4f z1=%.4f" % (z0a, z0, z1))
