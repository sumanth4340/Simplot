"""verify_s2 (runs LOCALLY): lidar returns validate on known geometry."""
import json, re

EV = json.load(open("action-reasoner/skills/sensors/base/evidence/s2_lidar.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["frames >= 1"] = f(r"frames=(\d+)") >= 1
checks["points >= 1000"] = f(r"points=(\d+)") >= 1000
checks["ontop >= 0.95"] = f(r"ontop=([\d.]+)") >= 0.95
checks["range-near ~1.93"] = abs(f(r"rmin=([\d.]+)") - 1.93) < 0.15
checks["range-far < 3.0"] = f(r"rmax=([\d.]+)") < 3.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("S2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
