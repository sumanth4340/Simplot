# R1 attrs (INSIDE Isaac Sim): dump omni:sensor attrs on the radar.
import omni.usd

pr = omni.usd.get_context().get_stage().GetPrimAtPath("/World/R1Radar")
print("type:", pr.GetTypeName())
for a in pr.GetAttributes():
    n = a.GetName()
    if "sensor" in n or "adar" in n or "Wpm" in n or "ange" in n or "ov" in n.lower():
        try:
            v = a.Get()
            s = str(v)
            print("ATTR %s = %s" % (n, s[:160]))
        except Exception as e:
            print("ATTR %s ERR %r" % (n, e))
print("R1-ATTRS done")
