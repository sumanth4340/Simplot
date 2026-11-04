import omni.usd
import omni.graph.core as og
print("GREG=" + str([n for n in dir(og.GraphRegistry) if not n.startswith("_")])[:600])
stage = omni.usd.get_context().get_stage()
sdg = stage.GetPrimAtPath("/Replicator/SDGPipeline")
print("SDG valid=" + str(sdg.IsValid()) + " type=" + str(sdg.GetTypeName()))
if sdg.IsValid():
    kids = list(sdg.GetChildren())
    print("SDG-KIDS=" + str(len(kids)))
    for k in kids[:10]:
        print("K " + k.GetName() + " " + k.GetTypeName())
