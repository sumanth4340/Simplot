"""verify_p4 (runs LOCALLY): preflight gates."""
import json

R = json.load(open("action-reasoner/skills/physics/engines/evidence/p4_run.json"))["output"]

checks = {}
checks["clean silent"] = "clean=[]" in R
checks["dirty fires all 5"] = "dirty=['inertia', 'negscale', 'orphan', 'ref', 'zerosize']" in R

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("P4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
