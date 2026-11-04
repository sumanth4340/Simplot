# N2 helper probe (INSIDE Isaac Sim, STOPPED): ROS2RtxLidarHelper
# input defaults + allowed tokens for inputs:type.
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd as _ou

app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=10)

G = "/ROS2/N2help"
_st = _ou.get_context().get_stage()
if _st.GetPrimAtPath(G).IsValid():
    _st.RemovePrim(G)
og.Controller.edit(
    {"graph_path": G, "evaluator_name": "execution"},
    {og.Controller.Keys.CREATE_NODES: [
        ("HELP", "isaacsim.ros2.bridge.ROS2RtxLidarHelper")]})
p = _st.GetPrimAtPath(G + "/HELP")
for a in p.GetAttributes():
    n = a.GetName()
    if not n.startswith("inputs:"):
        continue
    try:
        v = a.Get()
    except Exception as e:
        v = "ERR " + repr(e)[:60]
    toks = ""
    try:
        md = a.GetMetadata("allowedTokens")
        if md:
            toks = " TOKENS=" + repr(list(md))[:200]
    except Exception:
        pass
    print("  %s = %r%s" % (n, v, toks))
_st.RemovePrim(G)
print("HELP-PROBE done")
