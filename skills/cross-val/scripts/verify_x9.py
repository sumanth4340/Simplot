"""verify_x9 (runs LOCALLY): V9 scene passes every graduated lens."""
import json, re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x9_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

checks = {}
checks["stage: all 5 prims valid"] = b(r"valid=(\w+)")
checks["model: base 0.15"] = abs(f(r"sizeB=([\d.]+)") - 0.15) < 1e-6
checks["model: link 0.2"] = abs(f(r"sizeL=([\d.]+)") - 0.2) < 1e-6
checks["sense: bot x 3.0"] = abs(f(r"bx=([-\d.]+)") - 3.0) < 1e-6
checks["physics: position drive"] = "dtype=position" in EV
checks["physics: stiffness 100"] = abs(f(r"stiff=([\d.]+)") - 100.0) < 1e-6
checks["physics: damping 10"] = abs(f(r"damp=([\d.]+)") - 10.0) < 1e-6
checks["graph: 4 nodes"] = abs(f(r"nodes=([\d.]+)") - 4.0) < 1e-6
checks["graph: Write targets V9 hinge"] = "tgt=/World/V9Bot/Hinge1" in EV
checks["graph: enabled"] = b(r"en=(\w+)")
checks["R8: no rivals"] = abs(f(r"rivals=([-\d.]+)") - 0.0) < 1e-6

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X9-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
