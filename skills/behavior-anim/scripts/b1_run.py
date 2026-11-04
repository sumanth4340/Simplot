"""B1 run (runs INSIDE Isaac Sim): verify animation interpolation.

stop (playhead 0) -> play 30 (t~0.5s, x~1.0) -> play 30 (t~1.0s,
x~2.0). Reads world x via XformCache at live timecode + op value.
"""
import omni.usd
import omni.timeline
import isaacsim.core.experimental.utils.app as app_utils
from pxr import UsdGeom, Usd

stage = omni.usd.get_context().get_stage()
tl = omni.timeline.get_timeline_interface()
BP = "/World/B1Box"


def _read():
    now = tl.get_current_time()
    tc = Usd.TimeCode(now * stage.GetTimeCodesPerSecond())
    prim = stage.GetPrimAtPath(BP)
    cache = UsdGeom.XformCache(tc)
    wx = float(cache.GetLocalToWorldTransform(prim)
               .ExtractTranslation()[0])
    op = UsdGeom.Xformable(prim).GetOrderedXformOps()[0]
    ox = float(op.Get(tc)[0])
    return now, wx, ox


app_utils.stop()
await app_utils.update_app_async(steps=5)
t0, x0, o0 = _read()
app_utils.play(commit=True)
await app_utils.update_app_async(steps=30)
t1, x1, o1 = _read()
await app_utils.update_app_async(steps=30)
t2, x2, o2 = _read()
print("B1-REPORT t0=%.3f x0=%.3f t1=%.3f x1=%.3f o1=%.3f "
      "t2=%.3f x2=%.3f o2=%.3f" % (t0, x0, t1, x1, o1, t2, x2, o2))
