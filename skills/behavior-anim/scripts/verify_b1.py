"""verify_b1 (runs LOCALLY): animation interpolation gates."""
import json, re

B = json.load(open("action-reasoner/skills/behavior-anim/evidence/b1_build.json"))["output"]
R = json.load(open("action-reasoner/skills/behavior-anim/evidence/b1_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["box valid"] = "valid=True" in B
checks["2 samples"] = "samples=2" in B
checks["playhead reset"] = abs(f(r"t0=([-\d.]+)", R) - 0.0) < 0.1
checks["start x~0"] = abs(f(r"x0=([-\d.]+)", R) - 0.0) < 0.05
checks["mid t~0.5"] = abs(f(r"t1=([-\d.]+)", R) - 0.5) < 0.15
checks["mid x~1.0"] = abs(f(r"x1=([-\d.]+)", R) - 1.0) < 0.15
checks["mid op==world"] = abs(f(r"x1=([-\d.]+)", R) - f(r"o1=([-\d.]+)", R)) < 1e-6
checks["end t~1.0"] = abs(f(r"t2=([-\d.]+)", R) - 1.0) < 0.15
checks["end x~2.0"] = abs(f(r"x2=([-\d.]+)", R) - 2.0) < 0.15

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("B1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
