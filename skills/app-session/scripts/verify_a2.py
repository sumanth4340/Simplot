"""verify_a2 (runs LOCALLY): save/reopen gates."""
import re

T = open("action-reasoner/skills/app-session/evidence/a2_report.txt").read()

def f(pat, i=1):
    m = re.search(pat, T)
    return float(m.group(i)) if m else float("nan")

counts = [int(v) for v in re.findall(r"Prim count: (\d+)", T)]

checks = {}
checks["new stage"] = "Created new stage (template: empty)" in T
checks["marker defined"] = "A2-MARKER valid=True size=0.70" in T
checks["saved"] = "Saved as: " in T
checks["usd exists"] = "USD_EXISTS=True" in T
checks["usd non-empty"] = f(r"USD_BYTES=(\d+)") > 0
checks["wipe shrinks"] = len(counts) == 2 and counts[0] < counts[1]
checks["reopened"] = "Opened: " in T
checks["marker survives"] = "A2-CHECK valid=True" in T

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("A2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
