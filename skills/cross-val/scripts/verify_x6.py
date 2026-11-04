"""verify_x6 (runs LOCALLY): V6 scene passes every graduated lens."""
import json, os, re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x6_run.json"))["output"]
PNG = "action-reasoner/skills/rendering-lighting/evidence/v6_frame.png"

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

checks = {}
checks["stage: all 7 prims valid"] = b(r"valid=(\w+)")
checks["model: cubeA 0.5"] = abs(f(r"sizeA=([\d.]+)") - 0.5) < 1e-6
checks["model: cubeB 1.2"] = abs(f(r"sizeB=([\d.]+)") - 1.2) < 1e-6
checks["sense: xA 0.8"] = abs(f(r"xA=([-\d.]+)") - 0.8) < 1e-6
checks["sense: xB -0.9"] = abs(f(r"xB=([-\d.]+)") - -0.9) < 1e-6
checks["rig: dome 300"] = abs(f(r"dome=([\d.]+)") - 300.0) < 1e-6
checks["rig: sun 1200"] = abs(f(r"sun=([\d.]+)") - 1200.0) < 1e-6
checks["rig: focal 24"] = abs(f(r"focal=([\d.]+)") - 24.0) < 1e-6
checks["render: v6 png >20KB"] = os.path.exists(PNG) and os.path.getsize(PNG) > 20000

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X6-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
