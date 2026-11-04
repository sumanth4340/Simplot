import omni.usd, omni.timeline
from pxr import UsdGeom, Gf
stage = omni.usd.get_context().get_stage()
print("TCPS=%.1f FPS=%.1f" % (stage.GetTimeCodesPerSecond(), stage.GetFramesPerSecond()))
tl = omni.timeline.get_timeline_interface()
print("TLNOW=%.3f playing=%s" % (tl.get_current_time(), tl.is_playing()))
