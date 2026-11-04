import omni.graph.core as og
att = og.ObjectLookup.attribute("/World/O3Graph/Vec.outputs:tuple")
names = [n for n in dir(att) if not n.startswith("_")]
print("ATTMETHODS=" + str(names)[:500])
for n in names:
    if "type" in n.lower() or "resolv" in n.lower():
        try:
            print(n + "=" + str(getattr(att, n)())[:120])
        except Exception as e:
            print(n + " ERR " + repr(e)[:80])
