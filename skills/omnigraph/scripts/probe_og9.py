import omni.usd
stage = omni.usd.get_context().get_stage()
for p in ("/World/OGProbe_G2/NPBTick", "/World/OGProbe_G3/NWrite"):
    prim = stage.GetPrimAtPath(p)
    print("NODE " + p + " valid=" + str(prim.IsValid()))
    if prim.IsValid():
        for a in prim.GetAttributes():
            print("  ATTR " + a.GetName() + " type=" + str(a.GetTypeName()))
