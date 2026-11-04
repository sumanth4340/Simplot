"""R2 bridge reset (runs INSIDE Isaac Sim via bridge).

Removes ROS graphs + articulations, then disables/re-enables the
isaacsim.ros2.bridge extension. The bridge caches ROS publishers by
node/topic identity and RemovePrim does NOT release them, so rebuilt
graphs republish STALE (previous-play) values. A bridge reset gives a
clean slate (verified pattern).
"""
import omni.kit.app
import omni.usd

import isaacsim.core.experimental.utils.app as app_utils

st = omni.usd.get_context().get_stage()
for p in ("/ROS2/R2", "/ROS2/R2F", "/ROS2/R2G"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)
for c in list(st.GetPrimAtPath("/World").GetChildren()):
    if c.GetName().startswith("R2Bot"):
        st.RemovePrim(c.GetPath())
app_utils.stop()
m = omni.kit.app.get_app().get_extension_manager()
if hasattr(m, "set_extension_enabled_immediate"):
    m.set_extension_enabled_immediate("isaacsim.ros2.bridge", False)
    await app_utils.update_app_async(steps=10)
    m.set_extension_enabled_immediate("isaacsim.ros2.bridge", True)
    await app_utils.update_app_async(steps=10)
    print("R2-RESET-OK immediate")
else:
    m.set_extension_enabled("isaacsim.ros2.bridge", False)
    await app_utils.update_app_async(steps=30)
    m.set_extension_enabled("isaacsim.ros2.bridge", True)
    await app_utils.update_app_async(steps=30)
    print("R2-RESET-OK deferred")
