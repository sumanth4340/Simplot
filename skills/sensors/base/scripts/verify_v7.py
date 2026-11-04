"""verify_v7 (runs LOCALLY): exam layout + all three modalities."""
import json, re

B = json.load(open("action-reasoner/skills/sensors/base/evidence/v7_build.json"))["output"]
C = json.load(open("action-reasoner/skills/sensors/base/evidence/v7_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

def b(pat, s):
    m = re.search(pat, s)
    return m and m.group(1) == "True"

checks = {}
checks["EXAM new dome 300"] = abs(f(r"dome=([\d.]+)", B) - 300.0) < 1e-6
checks["EXAM new size 1.2"] = abs(f(r"size=([\d.]+)", B) - 1.2) < 1e-6
checks["EXAM new mass 2.0"] = abs(f(r"mass=([\d.]+)", B) - 2.0) < 1e-6
checks["depth ~3.602"] = abs(f(r"dctr=([\d.]+)", C) - 3.602) < 0.15
checks["depth shape"] = C.find("dshape=[240, 320, 1]") >= 0
checks["|accel| ~9.81"] = abs(f(r"amag=([\d.]+)", C) - 9.81) < 0.3
checks["in_contact"] = b(r"in_contact=(\w+)", C)
checks["force ~19.62"] = abs(f(r"force=([\d.]+)", C) - 19.62) < 1.5
checks["ncontacts >= 1"] = f(r"ncontacts=(\d+)", C) >= 1

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V7-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
