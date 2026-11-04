"""verify_s2 (runs LOCALLY): bbox + semseg gates."""
import json, re

B = json.load(open("action-reasoner/skills/sdg/base/evidence/s2_build.json"))["output"]
R = json.load(open("action-reasoner/skills/sdg/base/evidence/s2_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["label applied"] = "s2cube" in B
checks["one box"] = "nbox=1" in R
checks["area > 1000"] = f(r"area=(\d+)", R) > 1000.0
checks["class s2cube"] = "cls=s2cube" in R
checks["path S1Cube"] = "path=/World/S1Cube" in R
checks["label 2 present"] = "2" in re.search(r"uniq=([^]]+])", R).group(1)
checks["cube pixels > 100"] = f(r"npix2=(\d+)", R) > 100.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("S2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
