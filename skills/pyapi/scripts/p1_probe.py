# P1 probe (runs INSIDE Isaac Sim): kit commands + omni.client +
# timeline/app utilities surface check.
import json
import omni.usd

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/pyapi/evidence/p1_api.json"
out = {}

# --- kit commands ---
try:
    import omni.kit.commands as kc
    names = sorted(kc.get_command_names()
                   if hasattr(kc, "get_command_names") else [])
    out["n_commands"] = len(names)
    out["has_create"] = any("CreatePrim" in n for n in names)
    out["has_delete"] = any("DeletePrims" in n for n in names)
    st = omni.usd.get_context().get_stage()
    if st.GetPrimAtPath("/World/P1Cmd").IsValid():
        st.RemovePrim("/World/P1Cmd")
    kc.execute("CreatePrim", prim_path="/World/P1Cmd",
               prim_type="Xform")
    out["cmd_create"] = st.GetPrimAtPath("/World/P1Cmd").IsValid()
    kc.undo()
    out["cmd_undo"] = not st.GetPrimAtPath("/World/P1Cmd").IsValid()
    kc.redo()
    out["cmd_redo"] = st.GetPrimAtPath("/World/P1Cmd").IsValid()
    st.RemovePrim("/World/P1Cmd")
except Exception as e:
    out["commands_err"] = repr(e)[:200]

# --- omni.client ---
try:
    import omni.client as oc
    from isaacsim.storage.native import get_assets_root_path
    root = get_assets_root_path()
    out["root_tail"] = root[-40:]
    stt = await oc.stat(root)
    out["stat_root"] = str(stt[0]) if isinstance(stt, tuple) else str(stt)
    lst = await oc.list(root + "/Isaac/Sensors/NVIDIA")
    items = lst[1] if isinstance(lst, tuple) else lst
    names = sorted(getattr(i, "relative_path", "?") for i in items)
    out["nvidia_list_n"] = len(names)
    out["has_rotary2d"] = any("Example_Rotary_2D" in n for n in names)
    bad = await oc.stat(root + "/Isaac/Sensors/NOPE/Nope.usd")
    out["stat_missing"] = str(bad[0]) if isinstance(bad, tuple) else str(bad)
except Exception as e:
    out["client_err"] = repr(e)[:200]

# --- timeline / app ---
try:
    import omni.timeline as ot
    import isaacsim.core.experimental.utils.app as app_utils
    tl = ot.get_timeline_interface()
    out["was_playing"] = tl.is_playing()
    f0 = tl.get_current_time()
    app_utils.play()
    await app_utils.update_app_async(steps=10)
    f1 = tl.get_current_time()
    out["playing"] = tl.is_playing()
    out["time_adv"] = f1 > f0
    app_utils.stop()
    out["stopped"] = not tl.is_playing()
except Exception as e:
    out["timeline_err"] = repr(e)[:200]

with open(EV, "w") as f:
    json.dump(out, f, indent=1)
print("P1-PROBE-OK " + json.dumps(out)[:700])
