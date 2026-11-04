import omni.graph.core as og
cands = ["omni.graph.action.OnTick", "omni.graph.action.OnPlaybackTick",
         "omni.graph.action.OnStageEvent", "omni.graph.action.Print",
         "omni.graph.nodes.ConstantDouble", "omni.graph.nodes.ConstantInt",
         "omni.graph.nodes.WritePrimAttribute", "omni.graph.nodes.ReadPrimAttribute",
         "omni.graph.nodes.Print", "omni.graph.core.Constant",
         "omni.graph.nodes.Time", "omni.graph.action.Time"]
for c in cands:
    try:
        v = og.GraphRegistry.get_node_type_version(c)
        print("HAVE " + c + " v=" + str(v))
    except Exception as e:
        print("MISS " + c + " " + repr(e)[:80])
print("KEYS=" + str([k for k in dir(og.Controller.Keys) if not k.startswith("_")]))
