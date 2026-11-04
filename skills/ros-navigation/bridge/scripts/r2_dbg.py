import omni.usd, json
from pxr import UsdPhysics
st = omni.usd.get_context().get_stage()
out = {}
rb = st.GetPrimAtPath("/World/R2Bot")
out["root_api"] = rb.HasAPI(UsdPhysics.ArticulationRootAPI)
for j in ["J1", "J2"]:
    jp = st.GetPrimAtPath("/World/R2Bot/" + j)
    out[j] = {"valid": jp.IsValid(), "type": str(jp.GetTypeName()),
              "b0": [str(t) for t in jp.GetRelationship("physics:body0").GetTargets()],
              "b1": [str(t) for t in jp.GetRelationship("physics:body1").GetTargets()]}
js = st.GetPrimAtPath("/ROS2/R2/JS")
out["js_topic"] = js.GetAttribute("inputs:topicName").Get()
out["js_target"] = [str(t) for t in js.GetRelationship("inputs:targetPrim").GetTargets()]
print("R2DBG=" + json.dumps(out))
