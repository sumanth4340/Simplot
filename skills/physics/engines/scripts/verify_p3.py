"""verify_p3 (runs LOCALLY): switching gates."""
import json

R = json.load(open("action-reasoner/skills/physics/engines/evidence/p3_run.json"))["output"]

checks = {}
checks["both available"] = "physx" in R and "newton" in R
checks["switch to newton"] = "a1=newton" in R
checks["switch back physx"] = "a2=physx" in R
checks["backends reported"] = "b1=" in R and "b2=" in R

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("P3-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
