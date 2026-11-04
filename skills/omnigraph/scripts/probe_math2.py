import omni.usd
stage = omni.usd.get_context().get_stage()
for g in ("OGProbe_M1", "OGProbe_M6", "OGProbe_M7"):
    p = stage.GetPrimAtPath("/World/" + g + "/N")
    print("NODE " + g + " valid=" + str(p.IsValid()))
    if p.IsValid():
        for a in p.GetAttributes():
            n = a.GetName()
            if n.startswith("inputs:") or n.startswith("outputs:"):
                print("  " + n + " " + str(a.GetTypeName()))
