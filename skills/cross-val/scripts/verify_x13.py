"""verify_x13 (runs LOCALLY): V13 scene passes every lens."""
import json
import os
import re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x13_run.json"))["output"]
EVD = "action-reasoner/skills/app-session/evidence/"

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

def v3(pat):
    m = re.search(pat, EV)
    return tuple(float(m.group(i)) for i in (1, 2, 3)) if m else (999,) * 3

checks = {}
checks["stage: all 3 prims valid"] = b(r"valid=(\w+)")
checks["model: A 1.0"] = abs(f(r"sA=([\d.]+)") - 1.0) < 1e-6
checks["model: B 0.6"] = abs(f(r"sB=([\d.]+)") - 0.6) < 1e-6
checks["sense: A at (-0.8,0,0.5)"] = v3(r"tA=([-\d.]+),([-\d.]+),([-\d.]+)") == (-0.8, 0.0, 0.5)
checks["rig: dome 3000"] = abs(f(r"dome=([\d.]+)") - 3000.0) < 1e-6
checks["app: stopped"] = b(r"stopped=(\w+)")
checks["session: usd saved"] = os.path.getsize(EVD + "v13_stage.usd") > 0
checks["session: shot saved"] = os.path.getsize(EVD + "v13_view.png") > 20000

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X13-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
