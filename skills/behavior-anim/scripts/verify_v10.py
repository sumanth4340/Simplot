"""verify_v10 (runs LOCALLY): exam gates for two-zone behavior."""
import json, re

B = json.load(open("action-reasoner/skills/behavior-anim/evidence/v10_build.json"))["output"]
R = json.load(open("action-reasoner/skills/behavior-anim/evidence/v10_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["2 ops"] = "ops=2" in B
checks["2+2 samples"] = "tsamples=2" in B and "rsamples=2" in B
checks["bot valid"] = "bot=True" in B
checks["one switch"] = "nsw=1" in R
checks["switch y~1.2"] = abs(f(r"sw_y=([-\d.]+)", R) - 1.2) < 0.3
checks["switch t~1.2s"] = abs(f(r"sw_t=([-\d.]+)", R) - 1.2) < 0.3
checks["arm ended +0.4"] = abs(f(r"q_end=([-\d.]+)", R) - 0.4) < 0.1
checks["gate y ended ~2.4"] = abs(f(r"y_end=([-\d.]+)", R) - 2.4) < 0.15
checks["gate ry ended ~45"] = abs(f(r"ry_end=([-\d.]+)", R) - 45.0) < 5.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V10-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
