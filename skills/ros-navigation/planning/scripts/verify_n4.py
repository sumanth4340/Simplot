"""verify_n4 (runs LOCALLY): kinematics + pursuit gates."""
import json, re

F = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n4_follow.json"))
R = open("action-reasoner/skills/ros-navigation/planning/evidence/n4_follow.txt").read()

checks = {}
checks["diff round-trip"] = abs(F["rt_diff"][0] - 1.0) < 1e-9 \
    and abs(F["rt_diff"][1] - 0.5) < 1e-9
checks["holo round-trip"] = abs(F["rt_holo"][0] - 0.3) < 1e-9 \
    and abs(F["rt_holo"][1] - 0.1) < 1e-9 \
    and abs(F["rt_holo"][2] - 0.4) < 1e-9
checks["pursuit finished"] = F["done"] is True
checks["arrival < tol"] = F["arrival"] < 0.5
checks["deviation < 1m"] = F["max_dev"] < 1.0
checks["steps < 400"] = F["steps"] < 400
checks["report agrees"] = ("done=True" in R
    and abs(float(re.search(r"arr=([-\d.]+)", R).group(1)) - F["arrival"]) < 0.01)

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("N4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
