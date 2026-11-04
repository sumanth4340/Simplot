import omni.usd, json
from pxr import UsdPhysics
st = omni.usd.get_context().get_stage()
arts = []
for p in st.Traverse():
    try:
        if p.HasAPI(UsdPhysics.ArticulationRootAPI):
            arts.append(str(p.GetPath()))
    except Exception:
        pass
print("ARTS=" + json.dumps(arts[:20]))
