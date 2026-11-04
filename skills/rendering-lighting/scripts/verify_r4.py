"""verify_r4 (runs LOCALLY): 4x filmIso brightens the frame."""
import json, re

EV = json.load(open("action-reasoner/skills/rendering-lighting/evidence/r4_expo.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["baseline sane"] = 10.0 < f(r"mean1=([\d.]+)") < 220.0
checks["ratio > 1.15"] = f(r"ratio=([\d.]+)") > 1.15
checks["no full clip"] = f(r"max2=(\d+)") < 255 or f(r"mean2=([\d.]+)") < 250.0
checks["shape ok"] = EV.find("shape=[240, 320, 3]") >= 0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("R4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
