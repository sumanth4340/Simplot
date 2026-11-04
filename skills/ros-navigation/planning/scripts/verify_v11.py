"""verify_v11 (runs LOCALLY): exam pipeline gates."""
import json, re

B = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/v11_build.json"))["output"]
R = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/v11_run.json"))["output"]
G = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/v11_grid.json"))
NV = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/v11_nav.json"))
VP = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/v11_path.json"))

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

grid = G["grid"]
XR, YR, RES = G["x_range"], G["y_range"], G["res"]
cells = [(int((p[0] - XR[0]) / RES), int((p[1] - YR[0]) / RES))
         for p in VP["path"]]
occ_file = sum(1 for row in grid for v in row if v > 0)

checks = {}
checks["yard valid"] = "valid=True" in B
checks["shape 40x40"] = "shape=40x40" in R
checks["occupied == 62"] = abs(f(r"occ=(\d+)", R) - 62.0) < 1e-9
checks["file agrees"] = occ_file == 62
checks["D/E/F occupied"] = "d=255" in R and "e=255" in R and "f=255" in R
checks["corner free"] = "corner=0" in R
checks["path found"] = NV["plen"] > 32
checks["all cells free"] = all(grid[c[1]][c[0]] == 0 for c in cells)
checks["stamps clean"] = NV["bad"] == 0
checks["pursuit done"] = NV["done"] is True
checks["arrival < tol"] = NV["arrival"] < 0.5
checks["deviation < 1m"] = NV["max_dev"] < 1.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V11-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
