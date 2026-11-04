import omni.usd
import omni.graph.core as og
keys = og.Controller.Keys
stage = omni.usd.get_context().get_stage()
tests = ["omni.graph.nodes.Add", "omni.graph.nodes.Multiply",
         "omni.graph.nodes.Subtract", "omni.graph.nodes.Divide",
         "omni.graph.nodes.ComposeVector3", "omni.graph.nodes.ConstructVector3",
         "omni.graph.nodes.MakeVector3", "omni.graph.nodes.ConstantDouble"]
for i, t in enumerate(tests):
    gp = "/World/OGProbe_M%d" % i
    o = stage.GetPrimAtPath(gp)
    if o and o.IsValid():
        stage.RemovePrim(gp)
    try:
        og.Controller.edit(gp, {keys.CREATE_NODES: [("N", t)]})
        ok = stage.GetPrimAtPath(gp + "/N").IsValid()
        print(("MADE " if ok else "GHOST ") + t)
    except Exception as e:
        print("FAIL " + t + " " + repr(e)[:100])
