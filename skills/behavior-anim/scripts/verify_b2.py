"""verify_b2 (runs LOCALLY): multi-op interpolation gates."""
import json, re, math

B = json.load(open("action-reasoner/skills/behavior-anim/evidence/b2_build.json"))["output"]
R = json.load(open("action-reasoner/skills/behavior-anim/evidence/b2_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["box valid"] = "valid=True" in B
checks["2 ops"] = "ops=2" in B
checks["2+2 samples"] = "tsamples=2" in B and "rsamples=2" in B
checks["mid x~1.0"] = abs(f(r"x1=([-\d.]+)", R) - 1.0) < 0.15
checks["mid ry~45"] = abs(f(r"r1=([-\d.]+)", R) - 45.0) < 5.0
checks["axis +Y"] = abs(f(r"ax1=([-\d.]+)", R)) < 0.05 \
    and abs(f(r"ay1=([-\d.]+)", R) - 1.0) < 0.05 \
    and abs(f(r"az1=([-\d.]+)", R)) < 0.05
checks["angle 45deg"] = abs(f(r"g1=([-\d.]+)", R) - 45.0) < 3.0
checks["end x~2.0"] = abs(f(r"x2=([-\d.]+)", R) - 2.0) < 0.15
checks["end ry~90"] = abs(f(r"r2=([-\d.]+)", R) - 90.0) < 5.0
checks["end angle 90deg"] = abs(f(r"g2=([-\d.]+)", R) - 90.0) < 3.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("B2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
