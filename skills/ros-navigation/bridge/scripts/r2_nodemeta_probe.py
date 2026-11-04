"""R2 node-meta probe (runs INSIDE Isaac Sim via bridge).

Dumps node-type path/metadata/inspect for ROS2PublishJointState,
attribute type names via prim properties, and articulation validity
(direct USD + dynamic-control during a short play window).
Restores the pre-probe play state at the end.
"""
import json

import omni.graph.core as og
import omni.usd

out = {}
t = og.get_node_type("isaacsim.ros2.bridge.ROS2PublishJointState")

for m in ["get_path", "get_all_metadata", "inspect",
          "get_all_categories", "is_deprecated",
          "deprecation_message", "get_scheduling_hints"]:
    if hasattr(t, m):
        try:
            v = getattr(t, m)()
            out[m] = str(v)[:3000]
        except Exception as e:
            out[m] = "ERR " + str(e)[:200]

# metadata by key
try:
    n = t.get_metadata_count()
    out["meta_count"] = n
    keys = []
    # try common keys
    for k in ["description", "version", "category", "keywords",
              "display_name", "docs_url", "author", "source"]:
        try:
            keys.append(k + "=" + str(t.get_metadata(k))[:300])
        except Exception as e:
            keys.append(k + ":ERR " + str(e)[:80])
    out["meta_keys"] = keys
except Exception as e:
    out["meta_err"] = str(e)[:200]

# attribute type names from the live prim
st = omni.usd.get_context().get_stage()
js = st.GetPrimAtPath("/ROS2/R2/JS")
types = {}
for a in js.GetAttributes():
    nm = str(a.GetName())
    if nm.startswith("inputs:") or nm.startswith("outputs:"):
        try:
            types[nm] = str(a.GetTypeName())[:60]
        except Exception:
            pass
out["attr_types"] = types

# USD-side articulation sanity (no play needed)
from pxr import UsdPhysics
rb = st.GetPrimAtPath("/World/R2Bot")
out["usd_root_valid"] = bool(rb and rb.IsValid())
out["usd_root_api"] = bool(
    rb.HasAPI(UsdPhysics.ArticulationRootAPI)) if out[
        "usd_root_valid"] else None
joints = []
for p in st.Traverse():
    try:
        if "Joint" in str(p.GetTypeName()):
            j0 = [str(x) for x in p.GetRelationship(
                "physics:body0").GetTargets()]
            j1 = [str(x) for x in p.GetRelationship(
                "physics:body1").GetTargets()]
            joints.append({"path": str(p.GetPath()),
                           "type": str(p.GetTypeName()),
                           "b0": j0, "b1": j1})
    except Exception:
        pass
out["usd_joints"] = joints[:10]

# articulation check during play (short window)
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import Articulation
import omni.timeline
playing_before = omni.timeline.get_timeline_interface().is_playing()
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=30)
artout = {}
try:
    a = Articulation("/World/R2Bot")
    await app_utils.update_app_async(steps=5)
    artout["ndof"] = int(a.num_dofs)
    artout["pos"] = [float(x) for x in a.joint_positions]
    artout["vel"] = [float(x) for x in a.joint_velocities]
    artout["names"] = [str(x) for x in a.joint_names]
except Exception as e:
    artout["err"] = str(e)[:500]
out["art_during_play"] = artout
if not playing_before:
    app_utils.stop()
else:
    app_utils.play()
out["restored_playing"] = playing_before

print("NODEMETA=" + json.dumps(out, indent=1)[:14000])
