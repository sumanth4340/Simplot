# P1 fix (runs INSIDE Isaac Sim): undo entry + sync omni.client.
import json
import omni.usd

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/pyapi/evidence/p1_api.json"
out = json.load(open(EV))

import omni.kit.commands as kc
out["cmd_dir_undo"] = [n for n in dir(kc) if "undo" in n.lower()
                       or "redo" in n.lower()]
try:
    import omni.kit.undo as ku
    out["undo_mod"] = sorted(n for n in dir(ku) if not n.startswith("_"))[:12]
    st = omni.usd.get_context().get_stage()
    if st.GetPrimAtPath("/World/P1Cmd").IsValid():
        st.RemovePrim("/World/P1Cmd")
    kc.execute("CreatePrim", prim_path="/World/P1Cmd", prim_type="Xform")
    out["cmd_create"] = st.GetPrimAtPath("/World/P1Cmd").IsValid()
    ku.undo()
    out["cmd_undo"] = not st.GetPrimAtPath("/World/P1Cmd").IsValid()
    ku.redo()
    out["cmd_redo"] = st.GetPrimAtPath("/World/P1Cmd").IsValid()
    st.RemovePrim("/World/P1Cmd")
    del out["commands_err"]
except Exception as e:
    out["undo_err"] = repr(e)[:200]

try:
    import omni.client as oc
    from isaacsim.storage.native import get_assets_root_path
    root = get_assets_root_path()
    r = oc.stat(root)
    out["stat_root"] = str(r[0]) if isinstance(r, tuple) else str(type(r))
    r = oc.list(root + "/Isaac/Sensors/NVIDIA")
    items = r[1] if isinstance(r, tuple) else r
    names = sorted(getattr(i, "relative_path", "?") for i in items)
    out["nvidia_list_n"] = len(names)
    out["has_rotary2d"] = any("Example_Rotary_2D" in n for n in names)
    r = oc.stat(root + "/Isaac/Sensors/NOPE/Nope.usd")
    out["stat_missing"] = str(r[0]) if isinstance(r, tuple) else str(type(r))
    out.pop("client_err", None)
except Exception as e:
    out["client_err"] = repr(e)[:200]

with open(EV, "w") as f:
    json.dump(out, f, indent=1)
print("P1-FIX-OK " + json.dumps({k: out.get(k) for k in (
    "cmd_create", "cmd_undo", "cmd_redo", "stat_root",
    "nvidia_list_n", "has_rotary2d", "stat_missing")}))
