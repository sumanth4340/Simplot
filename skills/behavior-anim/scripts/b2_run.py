"""B2 run (runs INSIDE Isaac Sim): verify multi-op interpolation.

stop -> play 30 (t~0.5: x~1.0, ry~45deg) -> play 30 (t~1.0:
x~2.0, ry~90deg). Rotation cross-checked via world-matrix axis/
angle (independent of the op read).
"""
import math
import omni.usd
import omni.timeline
import isaacsim.core.experimental.utils.app as app_utils
from pxr import UsdGeom, Usd

stage = omni.usd.get_context().get_stage()
tl = omni.timeline.get_timeline_interface()
BP = "/World/B2Box"


def _read():
    now = tl.get_current_time()
    tc = Usd.TimeCode(now * stage.GetTimeCodesPerSecond())
    prim = stage.GetPrimAtPath(BP)
    tops, rops = UsdGeom.Xformable(prim).GetOrderedXformOps()
    x = float(tops.Get(tc)[0])
    ry = float(rops.Get(tc))
    m = UsdGeom.XformCache(tc).GetLocalToWorldTransform(prim)
    rot = m.ExtractRotation()
    ax = rot.GetAxis()
    return now, x, ry, (float(ax[0]), float(ax[1]), float(ax[2])), \
        float(rot.GetAngle())


app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play(commit=True)
await app_utils.update_app_async(steps=30)
t1, x1, r1, a1, g1 = _read()
await app_utils.update_app_async(steps=30)
t2, x2, r2, a2, g2 = _read()
print("B2-REPORT t1=%.3f x1=%.3f r1=%.3f ax1=%.2f ay1=%.2f "
      "az1=%.2f g1=%.4f t2=%.3f x2=%.3f r2=%.3f g2=%.4f" % (
          t1, x1, r1, a1[0], a1[1], a1[2], g1, t2, x2, r2, g2))
