"""verify_n2 (runs LOCALLY): A* path gates."""
import json, math

P = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n2_path.json"))
G = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n1_grid.json"))
XR, YR, RES = G["x_range"], G["y_range"], G["res"]
grid = G["grid"]
H, W = len(grid), len(grid[0])
path = P["path"]
straight = max(abs(P["goal"][0] - P["start"][0]),
               abs(P["goal"][1] - P["start"][1]))  # king-move lower bound


def _cell(p):
    return (int((p[0] - XR[0]) / RES), int((p[1] - YR[0]) / RES))


cells = [_cell(p) for p in path]
allfree = all(grid[c[1]][c[0]] == 0 for c in cells)
steps_ok = all(abs(cells[i + 1][0] - cells[i][0]) <= 1
               and abs(cells[i + 1][1] - cells[i][1]) <= 1
               for i in range(len(cells) - 1))

checks = {}
checks["path found"] = len(path) > 0
checks["starts at start"] = cells[0] == tuple(P["start"])
checks["ends at goal"] = cells[-1] == tuple(P["goal"])
checks["all cells free"] = allfree
checks["8-connected steps"] = steps_ok
checks["deviates (avoids A)"] = len(path) > straight
checks["not absurd"] = len(path) < 120
checks["erosion shrank free"] = P["eroded_free"] < P["raw_free"]

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("N2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
