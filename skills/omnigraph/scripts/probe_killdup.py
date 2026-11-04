import omni.usd
stage = omni.usd.get_context().get_stage()
killed = []
for c in stage.GetPrimAtPath("/World").GetChildren():
    n = c.GetName()
    if n.startswith("O4Graph") and n != "O4Graph":
        stage.RemovePrim(c.GetPath())
        killed.append(n)
print("KILLED=" + ",".join(sorted(killed)))
