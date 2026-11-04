"""R4 pump chunk (runs INSIDE Isaac Sim, assumes PLAYING)."""
import isaacsim.core.experimental.utils.app as app_utils
import omni.usd as _usd

ART = None
_st = _usd.get_context().get_stage()
for _c in _st.GetPrimAtPath("/World").GetChildren():
    if _c.GetName().startswith("R4Bot"):
        ART = _c.GetPath().pathString
        break

await app_utils.update_app_async(steps=40)
print("PUMP40 art=%s" % ART)
