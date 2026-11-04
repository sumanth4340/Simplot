"""verify_p1 (runs LOCALLY): PhysX drop gates."""
import json, re

B = json.load(open("action-reasoner/skills/physics/engines/evidence/p1_build.json"))["output"]
R = json.load(open("action-reasoner/skills/physics/engines/evidence/p1_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["scene valid"] = "valid=True" in B
checks["z0 ~ 2.0"] = abs(f(r"z0=([-\d.]+)", R) - 2.0) < 0.05
checks["rest z1 ~ 0.5"] = abs(f(r"z1=([-\d.]+)", R) - 0.5) < 0.05
checks["dt ~ 2.0s"] = abs(f(r"dt=([-\d.]+)", R) - 2.0) < 0.2
checks["settled vz ~ 0"] = abs(f(r"vz=([-\d.]+)", R) - 0.0) < 0.05
checks["engine physx"] = "physx" in R.lower().split("engine=")[1]

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("P1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
