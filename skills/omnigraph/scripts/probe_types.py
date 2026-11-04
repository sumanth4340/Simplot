import omni.usd
stage = omni.usd.get_context().get_stage()
for p, attrs in (("/World/O3Graph/Write", ("state:correctlySetup", "inputs:value")),
                 ("/World/O3Graph/Vec", ("inputs:x", "inputs:y", "inputs:z", "outputs:tuple")),
                 ("/World/O3Graph/Mul", ("inputs:a", "inputs:b", "outputs:product"))):
    prim = stage.GetPrimAtPath(p)
    for n in attrs:
        a = prim.GetAttribute(n)
        print(p.split("/")[-1] + " " + n + " type=" + str(a.GetTypeName()) +
              " val=" + str(a.Get())[:60] if a.IsValid() else p + " " + n + " INVALID")
