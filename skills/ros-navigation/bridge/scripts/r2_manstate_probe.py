"""R2MAN live-state probe (runs INSIDE Isaac Sim via bridge).

Read-only: dumps PubStatic input values (did literal arrays stick?),
ReadJS output values during play, and PubJS input values.
Does not change play state.
"""
import json

import omni.usd

st = omni.usd.get_context().get_stage()
out = {}


def dump(path):
    p = st.GetPrimAtPath(path)
    d = {"valid": bool(p and p.IsValid())}
    if not d["valid"]:
        return d
    for a in p.GetAttributes():
        n = str(a.GetName())
        if n.startswith("inputs:") or n.startswith("outputs:"):
            try:
                v = a.Get()
                d[n] = str(v)[:400]
            except Exception as e:
                d[n] = "GETERR " + str(e)[:120]
    return d


out["PubStatic"] = dump("/ROS2/R2MAN/PubStatic")
out["PubJS"] = dump("/ROS2/R2MAN/PubJS")
out["ReadJS"] = dump("/ROS2/R2MAN/ReadJS")

import omni.timeline
out["playing"] = omni.timeline.get_timeline_interface().is_playing()

print("MANSTATE=" + json.dumps(out, indent=1)[:12000])
