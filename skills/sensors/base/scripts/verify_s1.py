"""verify_s1 (runs LOCALLY): rgb lit + depth matches known geometry."""
import json, re

EV = json.load(open("action-reasoner/skills/sensors/base/evidence/s1_cap.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["rgb lit"] = 10.0 < f(r"rgbmean=([\d.]+)") < 220.0
checks["rgb max>50"] = f(r"rgbmax=(\d+)") > 50
checks["depth shape 240x320x1"] = EV.find("dshape=[240, 320, 1]") >= 0
checks["center ~3.74"] = abs(f(r"dctr=([\d.]+)") - 3.738) < 0.15
checks["all-cube framing"] = f(r"dmax=([\d.]+)") - f(r"dmin=([\d.]+)") < 0.5

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("S1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
