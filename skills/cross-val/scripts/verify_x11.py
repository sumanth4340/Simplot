"""verify_x11 (runs LOCALLY): V11 yard passes every lens."""
import json, re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x11_run.json"))["output"]
G = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/v11_grid.json"))
NV = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/v11_nav.json"))

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

def v3(pat):
    m = re.search(pat, EV)
    return tuple(float(m.group(i)) for i in (1, 2, 3)) if m else (999,) * 3

occ = sum(1 for row in G["grid"] for v in row if v > 0)

checks = {}
checks["stage: D/E/F valid"] = b(r"valid=(\w+)")
checks["stage: N-prims cleaned"] = b(r"gone=(\w+)")
checks["model: D 1.4"] = abs(f(r"sD=([\d.]+)") - 1.4) < 1e-6
checks["model: E 1.0"] = abs(f(r"sE=([\d.]+)") - 1.0) < 1e-6
checks["model: F scaled"] = v3(r"scF=([-\d.]+),([-\d.]+),([-\d.]+)") == (1.6, 0.8, 1.0)
checks["sense: D at (0,2,0.7)"] = v3(r"tD=([-\d.]+),([-\d.]+),([-\d.]+)") == (0.0, 2.0, 0.7)
checks["sense: F at (2,-2,0.5)"] = v3(r"tF=([-\d.]+),([-\d.]+),([-\d.]+)") == (2.0, -2.0, 0.5)
checks["physics: colliders on"] = b(r"col=(\w+)")
checks["nav: grid occ 62"] = occ == 62
checks["nav: path + pursuit"] = NV["done"] is True \
    and NV["arrival"] < 0.5 and NV["bad"] == 0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X11-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
