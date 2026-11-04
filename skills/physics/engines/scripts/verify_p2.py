"""verify_p2 (runs LOCALLY): Newton equivalence gates."""
import re

T = open("action-reasoner/skills/physics/engines/evidence/p2_report.txt").read()

def f(pat, i=1):
    m = re.search(pat, T)
    return float(m.group(i)) if m else float("nan")

usdz = [float(v) for v in re.findall(r"USDZ=([\d.]+)", T)]

checks = {}
checks["newton active"] = "ACTIVE-newton" in T
checks["physx active"] = "ACTIVE-physx" in T
checks["newton moved"] = 1.0 < f(r"N_DIFF=([\d.]+)") < 4.0
checks["physx moved"] = 1.0 < f(r"P_DIFF=([\d.]+)") < 4.0
checks["motion matches"] = abs(f(r"N_DIFF=([\d.]+)") - f(r"P_DIFF=([\d.]+)")) < 1.0
checks["end frames match"] = f(r"END_DIFF=([\d.]+)") < 0.5
checks["newton no USD writeback (known)"] = len(usdz) == 2 and abs(usdz[0] - 2.0) < 1e-6
checks["physx USD rest 0.5"] = len(usdz) == 2 and abs(usdz[1] - 0.5) < 1e-6

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("P2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
