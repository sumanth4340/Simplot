"""verify_s4 (runs LOCALLY): depth tracks the known 1.068m shift."""
import json, re

EV = json.load(open("action-reasoner/skills/sensors/base/evidence/s4_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["d1 ~3.738"] = abs(f(r"d1=([\d.]+)") - 3.738) < 0.15
checks["d2 ~4.806"] = abs(f(r"d2=([\d.]+)") - 4.806) < 0.2
checks["delta 0.9..1.25"] = 0.9 < f(r"delta=([\d.]+)") < 1.25

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("S4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
