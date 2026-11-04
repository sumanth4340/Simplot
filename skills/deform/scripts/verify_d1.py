# verify_d1.py (LOCAL): gate the D1 deformable-drop evidence.
import json
import sys

EV = "action-reasoner/skills/deform/evidence/d1_nodes.json"

gates = []


def gate(name, ok, detail=""):
    gates.append((name, bool(ok), detail))


d = json.load(open(EV))
e0, e1 = d["early"], d["settled"]
h0 = e0["zmax"] - e0["zmin"]
h1 = e1["zmax"] - e1["zmin"]

gate("engine-physx", d["engine"] == "physx", d["engine"])
gate("topology-stable", e0["n"] == e1["n"] and e0["n"] >= 100,
     "n=%d" % e1["n"])
gate("drop", e0["c"][2] - e1["c"][2] > 0.5,
     "zc %.3f->%.3f" % (e0["c"][2], e1["c"][2]))
gate("rest-on-ground", e1["zmin"] > -0.12, "zmin=%.3f" % e1["zmin"])
gate("squash-height", h1 < h0, "h %.4f->%.4f" % (h0, h1))
gate("bulge-spread", e1["spread"] > e0["spread"],
     "s %.4f->%.4f" % (e0["spread"], e1["spread"]))
gate("was-falling", e0["vmax"] > 1.0, "vmax0=%.2f" % e0["vmax"])
gate("at-rest", e1["vmax"] < 0.5, "vmax1=%.3f" % e1["vmax"])
gate("stress-live", d["stress"].get("max", 0) > 0,
     "max=%.1f" % d["stress"].get("max", 0))
gate("tets", d["elems"].get("shape", [0, 0, 0])[1:] == [2544, 4]
     or (len(d["elems"].get("shape", [])) == 3
         and d["elems"]["shape"][2] == 4
         and d["elems"]["shape"][1] > 0),
     "shape=%s" % (d["elems"].get("shape"),))

fails = [g for g in gates if not g[1]]
for name, ok, detail in gates:
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
print("D1-%s %d/%d" % ("PASS" if not fails else "FAIL",
                       len(gates) - len(fails), len(gates)))
sys.exit(0 if not fails else 1)
