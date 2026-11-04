"""verify_s4 (runs LOCALLY): variation gates."""
import json, re

R = json.load(open("action-reasoner/skills/sdg/base/evidence/s4_run.json"))["output"]

xm = [int(v) for v in re.search(r"xmins=(\d+),(\d+),(\d+)", R).groups()]
ar = [int(v) for v in re.search(r"areas=(\d+),(\d+),(\d+)", R).groups()]
mono = (xm[0] < xm[1] < xm[2]) or (xm[0] > xm[1] > xm[2])

checks = {}
checks["xmins monotonic"] = mono
checks["spread > 50px"] = abs(xm[2] - xm[0]) > 50
checks["all areas > 1000"] = all(a > 1000 for a in ar)
checks["frames differ"] = len(set(zip(xm, ar))) == 3

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("S4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
