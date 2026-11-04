"""O2 run (runs INSIDE Isaac Sim): stamp follows playback time.

Reads og:stamp after 30 steps (s1>0) and after 60 more (s2>s1):
increasing values prove per-tick dynamic writes.
"""
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils

stage = omni.usd.get_context().get_stage()


def _stamp():
    return float(stage.GetPrimAtPath("/World/O2Cube")
                 .GetAttribute("og:stamp").Get())


app_utils.play(commit=True)
await app_utils.update_app_async(steps=30)
s1 = _stamp()
await app_utils.update_app_async(steps=60)
s2 = _stamp()
print("O2-REPORT s1=%.4f s2=%.4f" % (s1, s2))
