"""verify_r2 (runs LOCALLY): R2 frame captured, lit, sane dimensions."""
import json, os, re

EV = json.load(open("action-reasoner/skills/rendering-lighting/evidence/r2_cap.json"))["output"]
PNG = "action-reasoner/skills/rendering-lighting/evidence/r2_frame.png"

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["shape 240x320x3"] = EV.find("shape=[240, 320, 3]") >= 0
checks["mean 10..220"] = 10.0 < f(r"mean=([\d.]+)") < 220.0
checks["max > 100"] = f(r"max=(\d+)") > 100
checks["png exists >20KB"] = os.path.exists(PNG) and os.path.getsize(PNG) > 20000

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("R2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
