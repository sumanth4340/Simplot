import omni.graph.core as og
print("OGDIR=" + str([n for n in dir(og) if not n.startswith("_")])[:800])
print("CTRL=" + str([n for n in dir(og.Controller) if not n.startswith("_")])[:800])
