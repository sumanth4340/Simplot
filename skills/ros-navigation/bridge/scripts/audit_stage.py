"""Stage audit: graphs, articulations, stale R2Bot references."""
import omni.usd
from pxr import UsdPhysics

st = omni.usd.get_context().get_stage()
out = {}
rp = st.GetPrimAtPath("/ROS2")
out["graphs"] = sorted(str(c.GetName()) for c in rp.GetChildren()) \
    if rp.IsValid() else []
out["world"] = sorted(str(c.GetName()) for c in
                      st.GetPrimAtPath("/World").GetChildren())
stale = []
arts = []
for p in st.Traverse():
    try:
        if p.HasAPI(UsdPhysics.ArticulationRootAPI):
            arts.append(str(p.GetPath()))
        for r in p.GetRelationships():
            for t in r.GetTargets():
                if "R2Bot" in str(t) and "R2Bot_" not in str(t):
                    stale.append("%s %s -> %s" % (p.GetPath(), r.GetName(), t))
        for an in ("inputs:robotPath",):
            a = p.GetAttribute(an)
            if a.IsValid() and a.Get() and "R2Bot" in str(a.Get()) \
               and "R2Bot_" not in str(a.Get()):
                stale.append("%s %s = %s" % (p.GetPath(), an, a.Get()))
    except Exception:
        pass
out["arts"] = arts
out["stale"] = stale
print("AUDIT=" + str(out))
