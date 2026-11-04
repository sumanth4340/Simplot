"""verify_b4 (runs LOCALLY): closed-loop trigger gates."""
import json, re

B = json.load(open("action-reasoner/skills/behavior-anim/evidence/b4_build.json"))["output"]
R = json.load(open("action-reasoner/skills/behavior-anim/evidence/b4_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["2 samples"] = "samples=2" in B
checks["bot valid"] = "bot=True" in B
checks["hinge valid"] = "hinge=True" in B
checks["trigger fired"] = "trig=1" in R
checks["trigger t~1.0s"] = abs(f(r"trig_t=([-\d.]+)", R) - 1.0) < 0.25
checks["trigger x~1.0"] = abs(f(r"trig_x=([-\d.]+)", R) - 1.0) < 0.25
checks["arm reached +0.6"] = abs(f(r"q_end=([-\d.]+)", R) - 0.6) < 0.1
checks["slider ended ~2.0"] = abs(f(r"x_end=([-\d.]+)", R) - 2.0) < 0.15

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("B4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
