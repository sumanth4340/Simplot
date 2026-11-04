# N2 helper runtime-defaults probe (INSIDE Isaac Sim): effective
# runtime values of HELP inputs on a scratch graph.
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd as _ou

app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=10)

G = "/ROS2/N2def"
_st = _ou.get_context().get_stage()
if _st.GetPrimAtPath(G).IsValid():
    _st.RemovePrim(G)
og.Controller.edit(
    {"graph_path": G, "evaluator_name": "execution"},
    {og.Controller.Keys.CREATE_NODES: [
        ("HELP", "isaacsim.ros2.bridge.ROS2RtxLidarHelper")]})
for n in ("enabled", "fullScan", "frameSkipCount", "queueSize",
          "useSystemTime", "resetSimulationTimeOnStop",
          "enableObjectIdMap", "showDebugView", "frameId",
          "topicName", "type"):
    p = G + "/HELP.inputs:" + n
    try:
        v = og.ObjectLookup.attribute(p).get()
    except Exception as e:
        v = "ERR " + repr(e)[:80]
    print("  %-28s = %r" % (n, v))
_st.RemovePrim(G)
print("HELP-DEF2 done")
