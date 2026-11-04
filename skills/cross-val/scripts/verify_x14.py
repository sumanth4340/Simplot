"""verify_x14 (runs LOCALLY): drop scene passes every lens."""
import json, re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x14_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

checks = {}
checks["stage: all 4 prims valid"] = b(r"valid=(\w+)")
checks["model: P1 1.0"] = abs(f(r"sP=([\d.]+)") - 1.0) < 1e-6
checks["model: V14 1.0"] = abs(f(r"sV=([\d.]+)") - 1.0) < 1e-6
checks["sense: V14 stacked 1.5"] = abs(f(r"zV=([-\d.]+)") - 1.5) < 0.05
checks["physics: mass 5"] = abs(f(r"mass=([\d.]+)") - 5.0) < 1e-6
checks["physics: apis"] = b(r"apis=(\w+)")
checks["app: engine physx"] = "engine=physx" in EV

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X14-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
