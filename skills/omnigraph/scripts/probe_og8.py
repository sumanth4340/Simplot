import omni.usd
import omni.graph.core as og
keys = og.Controller.Keys
stage = omni.usd.get_context().get_stage()
tests = [("G1", "NTick", "omni.graph.action.OnTick"),
         ("G2", "NPBTick", "omni.graph.action.OnPlaybackTick"),
         ("G3", "NWrite", "omni.graph.nodes.WritePrimAttribute"),
         ("G4", "NPrint", "omni.graph.action.Print")]
for g, n, t in tests:
    gp = "/World/OGProbe_" + g
    o = stage.GetPrimAtPath(gp)
    if o and o.IsValid():
        stage.RemovePrim(gp)
    try:
        og.Controller.edit(gp, {keys.CREATE_NODES: [(n, t)]})
        np_ = stage.GetPrimAtPath(gp + "/" + n)
        print(("MADE " if np_.IsValid() else "GHOST ") + t)
    except Exception as e:
        print("FAIL " + t + " " + repr(e)[:160])
