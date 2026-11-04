"""verify_x10 (runs LOCALLY): V10 scene passes every lens."""
import json, re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x10_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

checks = {}
checks["stage: all 5 prims valid"] = b(r"valid=(\w+)")
checks["model: gate 0.4"] = abs(f(r"sizeG=([\d.]+)") - 0.4) < 1e-6
checks["model: base 0.15"] = abs(f(r"sizeB=([\d.]+)") - 0.15) < 1e-6
checks["model: link 0.2"] = abs(f(r"sizeL=([\d.]+)") - 0.2) < 1e-6
checks["sense: bot x 4.0"] = abs(f(r"bx=([-\d.]+)") - 4.0) < 1e-6
checks["physics: position drive"] = "dtype=position" in EV
checks["physics: stiffness 100"] = abs(f(r"stiff=([\d.]+)") - 100.0) < 1e-6
checks["physics: damping 10"] = abs(f(r"damp=([\d.]+)") - 10.0) < 1e-6
checks["anim: 2 ops"] = abs(f(r"ops=([\d.]+)") - 2.0) < 1e-6
checks["anim: 2+2 samples"] = abs(f(r"ts=([\d.]+)") - 2.0) < 1e-6 \
    and abs(f(r"rs=([\d.]+)") - 2.0) < 1e-6
checks["behavior: echo +0.4"] = abs(f(r"echo=([-\d.]+)") - 0.4) < 1e-6

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X10-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
