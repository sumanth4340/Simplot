"""verify_s1 (runs LOCALLY): RGB annotator gates."""
import json, re

B = json.load(open("action-reasoner/skills/sdg/base/evidence/s1_build.json"))["output"]
R = json.load(open("action-reasoner/skills/sdg/base/evidence/s1_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["stage valid"] = "valid=True" in B
checks["shape 240x320x4"] = "shape=240x320x4" in R
checks["dtype uint8"] = "dtype=uint8" in R
checks["non-black mean>30"] = f(r"mean=([-\d.]+)", R) > 30.0
checks["has bright px"] = f(r"max=(\d+)", R) > 100.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("S1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
