"""R2 node-requirements probe (runs INSIDE Isaac Sim via bridge).

Dumps: node-type metadata + full attribute table for
ROS2PublishJointState, current values/connections on /ROS2/R2/JS,
same for the working R1 clock node, and bridge extension state.
Read-only: creates nothing, modifies nothing (except a scratch
graph that is removed again for default-value inspection).
"""
import json

import omni.graph.core as og
import omni.usd

out = {}

# 1. Node type metadata
t = og.get_node_type("isaacsim.ros2.bridge.ROS2PublishJointState")
out["type_valid"] = bool(t is not None and t.is_valid())
if out["type_valid"]:
    out["type_methods"] = sorted(
        m for m in dir(t) if not m.startswith("_"))
    for m in ["get_version", "get_description", "get_metadata",
              "description", "get_attribute_names", "get_node_type_version",
              "get_version_string"]:
        if hasattr(t, m):
            try:
                v = getattr(t, m)()
                out[m] = str(v)[:2000]
            except Exception as e:
                out[m] = "ERR " + str(e)[:200]
    # Full attribute table
    attrs = {}
    try:
        for a in t.get_attributes():
            info = {}
            for gm, key in [("get_name", "name"),
                            ("get_type_name", "type"),
                            ("get_default", "default"),
                            ("get_description", "desc"),
                            ("get_metadata", "meta")]:
                if hasattr(a, gm):
                    try:
                        v = getattr(a, gm)()
                        if gm == "get_default":
                            try:
                                v = v.get_value() if hasattr(
                                    v, "get_value") else v
                            except Exception:
                                pass
                        info[key] = str(v)[:400]
                    except Exception as e:
                        info[key] = "ERR " + str(e)[:120]
            # also dump raw dir for one attr to learn API
            attrs[info.get("name", "?")] = info
        out["node_attrs"] = attrs
    except Exception as e:
        out["node_attrs_err"] = str(e)[:300]

# 2. Live prim /ROS2/R2/JS: values + connections
st = omni.usd.get_context().get_stage()
js = st.GetPrimAtPath("/ROS2/R2/JS")
out["js_valid"] = bool(js and js.IsValid())
if out["js_valid"]:
    vals = {}
    for a in js.GetAttributes():
        n = str(a.GetName())
        if n.startswith("inputs:") or n.startswith("outputs:"):
            try:
                v = a.Get()
                vals[n] = str(v)[:300]
            except Exception as e:
                vals[n] = "GETERR " + str(e)[:120]
    for r in js.GetRelationships():
        n = str(r.GetName())
        if n.startswith("inputs:") or n.startswith("outputs:"):
            vals[n + " [rel]"] = str(
                [str(x) for x in r.GetTargets()])[:300]
    out["js_prim"] = vals
    # upstream connections per input
    conns = {}
    for a in js.GetAttributes():
        n = str(a.GetName())
        if n.startswith("inputs:"):
            try:
                up = og.ObjectLookup.attribute(
                    "/ROS2/R2/JS." + n).get_upstream_connections()
                conns[n] = [str(u)[:160] for u in up]
            except Exception as e:
                conns[n] = "ERR " + str(e)[:120]
    out["js_conns"] = conns

# 3. Working R1 clock node for comparison
clk = st.GetPrimAtPath("/World/R1Clock/Clock")
out["clk_valid"] = bool(clk and clk.IsValid())
if out["clk_valid"]:
    cvals = {}
    for a in clk.GetAttributes():
        n = str(a.GetName())
        if n.startswith("inputs:") or n.startswith("outputs:"):
            try:
                cvals[n] = str(a.Get())[:200]
            except Exception as e:
                cvals[n] = "GETERR " + str(e)[:100]
    out["clk_prim"] = cvals

# 4. Fresh scratch node defaults (create, read, delete)
keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ProbeJSDef", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("JS", "isaacsim.ros2.bridge.ROS2PublishJointState")]})
d = st.GetPrimAtPath("/ProbeJSDef/JS")
defs = {}
for a in d.GetAttributes():
    n = str(a.GetName())
    if n.startswith("inputs:") or n.startswith("outputs:"):
        try:
            defs[n] = str(a.Get())[:200]
        except Exception as e:
            defs[n] = "GETERR " + str(e)[:100]
for r in d.GetRelationships():
    defs[str(r.GetName()) + " [rel]"] = str(
        [str(x) for x in r.GetTargets()])[:200]
out["js_defaults"] = defs
st.RemovePrim("/ProbeJSDef")

# 5. Extension state
try:
    import omni.kit.app
    em = omni.kit.app.get_app().get_extension_manager()
    out["ext_bridge"] = str(em.is_extension_enabled(
        "isaacsim.ros2.bridge"))[:100]
    out["ext_nodes"] = str(em.is_extension_enabled(
        "isaacsim.ros2.nodes"))[:100]
    out["ext_core"] = str(em.is_extension_enabled(
        "isaacsim.ros2.core"))[:100]
except Exception as e:
    out["ext_err"] = str(e)[:200]

print("NODEREQ=" + json.dumps(out, indent=1)[:14000])
