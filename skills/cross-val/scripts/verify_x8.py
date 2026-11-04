"""verify_x8 (runs LOCALLY): V8 scene passes every graduated lens."""
import json, os, re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x8_run.json"))["output"]
VP = "action-reasoner/skills/viewport-ui/evidence/v8_viewport.png"
AP = "action-reasoner/skills/viewport-ui/evidence/v8_app.png"

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

checks = {}
checks["stage: all 5 prims valid"] = b(r"valid=(\w+)")
checks["model: sizeA 0.5"] = abs(f(r"sizeA=([\d.]+)") - 0.5) < 1e-6
checks["model: sizeB 1.0"] = abs(f(r"sizeB=([\d.]+)") - 1.0) < 1e-6
checks["sense: xA 0.9"] = abs(f(r"xA=([-\d.]+)") - 0.9) < 1e-6
checks["sense: xB -0.8"] = abs(f(r"xB=([-\d.]+)") - -0.8) < 1e-6
checks["rig: dome 300"] = abs(f(r"dome=([\d.]+)") - 300.0) < 1e-6
checks["rig: sun 1200"] = abs(f(r"sun=([\d.]+)") - 1200.0) < 1e-6
checks["shots exist"] = os.path.getsize(VP) > 20000 and os.path.getsize(AP) > 20000

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X8-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
