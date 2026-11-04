"""verify_a3 (runs LOCALLY): extension + settings gates."""
import json, re

R = json.load(open("action-reasoner/skills/app-session/evidence/a3_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, R)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["pyserver enabled"] = "pyserver=True" in R
checks["bogus disabled"] = "bogus=False" in R
checks["extensions listed"] = f(r"count=(\d+)") > 50.0
checks["settings round-trip"] = "echo=hello-a3" in R

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("A3-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
