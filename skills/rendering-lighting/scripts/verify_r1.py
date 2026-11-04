"""verify_r1 (runs LOCALLY): R1 lit stage + camera authored exactly."""
import json, re

EV = json.load(open("action-reasoner/skills/rendering-lighting/evidence/r1_build.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["dome 400"] = abs(f(r"dome=([\d.]+)") - 400.0) < 1e-6
checks["sun 1500"] = abs(f(r"sun=([\d.]+)") - 1500.0) < 1e-6
checks["sun rot -50/20/0"] = (
    abs(f(r"sunrot=\[([-\d.]+)") - -50.0) < 1e-6
    and abs(f(r"sunrot=\[[-\d.eE+]+, ([-\d.]+)") - 20.0) < 1e-6)
checks["cube size 1.0"] = abs(f(r"cubesize=([\d.]+)") - 1.0) < 1e-6
checks["focal 24"] = abs(f(r"focal=([\d.]+)") - 24.0) < 1e-6
checks["cam at eye"] = (
    abs(f(r"campos=\[([-\d.]+)") - 3.0) < 1e-3
    and abs(f(r"campos=\[[-\d.eE+]+, ([-\d.]+)") - -3.0) < 1e-3
    and abs(f(r"campos=\[[-\d.eE+]+, [-\d.eE+]+, ([-\d.]+)") - 2.0) < 1e-3)

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("R1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
