"""verify_s3 (runs LOCALLY): IMU reads gravity, contact reads weight."""
import json, re

EV = json.load(open("action-reasoner/skills/sensors/base/evidence/s3_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

checks = {}
checks["|accel| ~9.81"] = abs(f(r"amag=([\d.]+)") - 9.81) < 0.3
checks["|angvel| ~0"] = f(r"wmag=([\d.]+)") < 0.2
checks["in_contact"] = b(r"in_contact=(\w+)")
checks["force ~9.81"] = abs(f(r"force=([\d.]+)") - 9.81) < 1.0
checks["ncontacts >= 1"] = f(r"ncontacts=(\d+)") >= 1

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("S3-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
