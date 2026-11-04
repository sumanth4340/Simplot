"""verify_n1 (runs LOCALLY): occupancy grid gates."""
import json, re

B = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n1_build.json"))["output"]
R = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n1_run.json"))["output"]
G = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n1_grid.json"))

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

grid = G["grid"]
occ_file = sum(1 for row in grid for v in row if v > 0)

checks = {}
checks["yard valid"] = "valid=True" in B
checks["shape 40x40"] = "shape=40x40" in R
checks["occupied == 50"] = abs(f(r"occ=(\d+)", R) - 50.0) < 1e-9
checks["file agrees"] = occ_file == 50
checks["A center occupied"] = "a=255" in R
checks["B center occupied"] = "b=255" in R
checks["C center free"] = "c=0" in R
checks["corner free"] = "corner=0" in R
checks["C block all free"] = all(
    grid[r][c] == 0 for r in range(30, 34) for c in range(30, 34))
checks["values binary"] = all(v in (0, 255) for row in grid for v in row)

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("N1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
