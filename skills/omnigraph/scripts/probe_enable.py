import omni.graph.core as og
names = [n for n in dir(og.Controller) if not n.startswith("_")]
print("CTRL=" + ",".join(sorted(names)))
import omni.graph.core as ogc
mods = [n for n in dir(ogc) if not n.startswith("_")]
print("MOD=" + ",".join(sorted(mods)))
