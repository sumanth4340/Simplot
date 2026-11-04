# N2 helper defaults probe (INSIDE Isaac Sim): HELP node-type
# attribute defaults (frameSkipCount/fullScan/enabled/...).
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og

app_utils.enable_extension("isaacsim.ros2.bridge")
await app_utils.update_app_async(steps=10)

t = og.get_node_type("isaacsim.ros2.bridge.ROS2RtxLidarHelper")
print("TYPE", t)
try:
    attrs = t.get_attributes()
except Exception as e:
    attrs = []
    print("ATTRS-ERR", repr(e)[:120])
for a in attrs:
    n = a.get_name()
    try:
        d = a.get_default_value()
    except Exception as e:
        d = "ERR " + repr(e)[:60]
    print("  %-28s default=%r" % (n, d))
print("HELP-DEFAULTS done")
