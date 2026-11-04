"""verify_x12 (runs LOCALLY): V12 scene passes every lens."""
import glob
import json
import re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x12_run.json"))["output"]
OUT = "action-reasoner/skills/sdg/base/evidence/v12_out"

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
checks["stage: all 4 prims valid"] = b(r"valid=(\w+)")
checks["model: A 0.8"] = abs(f(r"sA=([\d.]+)") - 0.8) < 1e-6
checks["model: B 0.8"] = abs(f(r"sB=([\d.]+)") - 0.8) < 1e-6
checks["sense: A at (-1,0,0.4)"] = v3(r"tA=([-\d.]+),([-\d.]+),([-\d.]+)") == (-1.0, 0.0, 0.4)
checks["rig: dome 3000"] = abs(f(r"dome=([\d.]+)") - 3000.0) < 1e-6
checks["sem: label a"] = "v12a" in EV
checks["sem: label b"] = "v12b" in EV
checks["sdg: 3+3+3 files"] = len(glob.glob(OUT + "/rgb_*.npy")) == 3 \
    and len(glob.glob(OUT + "/sem_*.npy")) == 3 \
    and len(glob.glob(OUT + "/bounding_box_2d_tight_*.npy")) == 3

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X12-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
