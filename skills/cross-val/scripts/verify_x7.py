"""verify_x7 (runs LOCALLY): V7 scene passes every graduated lens."""
import json, re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x7_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

checks = {}
checks["stage: all 7 prims valid"] = b(r"valid=(\w+)")
checks["model: size 1.2"] = abs(f(r"size=([\d.]+)") - 1.2) < 1e-6
checks["phys: mass 2.0"] = abs(f(r"mass=([\d.]+)") - 2.0) < 1e-6
checks["phys: no-sleep"] = b(r"nosleep=(\w+)")
checks["phys: report API"] = b(r"report=(\w+)")
checks["rig: dome 300"] = abs(f(r"dome=([\d.]+)") - 300.0) < 1e-6
checks["sense: cubex 0.0"] = abs(f(r"cubex=([-\d.]+)") - 0.0) < 1e-6

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X7-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
