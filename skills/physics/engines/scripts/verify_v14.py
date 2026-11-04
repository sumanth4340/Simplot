"""verify_v14 (runs LOCALLY): exam gates."""
import json, re

B = json.load(open("action-reasoner/skills/physics/engines/evidence/v14_build.json"))["output"]
T = open("action-reasoner/skills/physics/engines/evidence/v14_report.txt").read()

def f(pat, i=1):
    m = re.search(pat, T)
    return float(m.group(i)) if m else float("nan")

usdz = [float(v) for v in re.findall(r"USDZ=([\d.]+)", T)]

checks = {}
checks["exam prim valid"] = "valid=True" in B
checks["newton active"] = "ACTIVE-newton" in T
checks["physx active"] = "ACTIVE-physx" in T
checks["newton moved"] = 0.8 < f(r"N_DIFF=([\d.]+)") < 5.0
checks["physx moved"] = 0.8 < f(r"P_DIFF=([\d.]+)") < 5.0
checks["motion matches"] = abs(f(r"N_DIFF=([\d.]+)") - f(r"P_DIFF=([\d.]+)")) < 1.0
checks["end frames match"] = f(r"END_DIFF=([\d.]+)") < 0.5
checks["newton no writeback"] = len(usdz) == 2 and abs(usdz[0] - 3.0) < 1e-6
checks["physx stacked at 1.5"] = len(usdz) == 2 and abs(usdz[1] - 1.5) < 0.05

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V14-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
