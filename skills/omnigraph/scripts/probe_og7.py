import omni.graph.core as og
cands = ["omni.graph.action.OnTick", "omni.graph.action.OnPlaybackTick",
         "omni.graph.action.Print", "omni.graph.nodes.WritePrimAttribute",
         "omni.graph.nodes.ReadPrimAttribute", "omni.graph.nodes.Print",
         "omni.graph.nodes.ConstantDouble", "omni.graph.nodes.Add"]
for c in cands:
    try:
        t = og.NodeType(c)
        print("HAVE " + c)
    except Exception as e:
        print("MISS " + c + " " + repr(e)[:100])
