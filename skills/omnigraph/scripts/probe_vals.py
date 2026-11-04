import omni.graph.core as og
import isaacsim.core.experimental.utils.app as app_utils
app_utils.play(commit=True)
await app_utils.update_app_async(steps=10)
for spec in ("Mul.inputs:a", "Mul.inputs:b", "Mul.outputs:product",
             "Vec.inputs:x", "Vec.inputs:y", "Vec.inputs:z",
             "Vec.outputs:tuple", "OnPB.outputs:time"):
    try:
        v = og.Controller.get("/World/O3Graph/" + spec.split(".")[0] + "." + ".".join(spec.split(".")[1:]))
        print("VAL " + spec + "=" + str(v)[:120])
    except Exception as e:
        print("VAL " + spec + " ERR " + repr(e)[:120])
