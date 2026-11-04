"""verify_r3 (runs LOCALLY): doubling sun intensity brightens the frame."""
import json, re

EV = json.load(open("action-reasoner/skills/rendering-lighting/evidence/r3_light.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["baseline lit"] = 10.0 < f(r"mean1=([\d.]+)") < 220.0
checks["ratio 1.2..3.0"] = 1.2 < f(r"ratio=([\d.]+)") < 3.0
checks["shape ok"] = EV.find("shape=[240, 320, 3]") >= 0
checks["no clipping blowout"] = f(r"max2=(\d+)") <= 255

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("R3-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
