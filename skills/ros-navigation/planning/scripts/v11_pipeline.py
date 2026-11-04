"""V11 pipeline (runs LOCALLY): plan + validate + follow exam grid.

A* (eroded 0.3) from (-4,-4) to (4,4) -> stamp every waypoint
with the N3 footprint (nav_check) -> pure-pursuit follow with
remaining-path windowing (R5). Writes v11_path.json + v11_nav.json.
"""
import heapq
import json
import math
import sys
import numpy as np
from scipy.ndimage import binary_erosion

sys.path.insert(0, "action-reasoner/skills/ros-navigation/planning/scripts")
sys.path.insert(0, "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
                   "skills/navigation-primitives/scripts")
from nav_check import footprint_clips_np
from kinematics import PurePursuitConfig, pure_pursuit_step

G = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/v11_grid.json"))
FP = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n3_footprint.json"))
XR, YR, RES = G["x_range"], G["y_range"], G["res"]
grid = np.array(G["grid"], dtype=np.uint8)
H, W = grid.shape
size = FP["size"]

ky, kx = np.ogrid[-1:2, -1:2]
nav = binary_erosion(grid == 0, structure=(kx * kx + ky * ky <= 1))


def _cell(x, y):
    return (int((x - XR[0]) / RES), int((y - YR[0]) / RES))


START, GOAL = _cell(-4.0, -4.0), _cell(4.0, 4.0)
assert nav[START[1], START[0]] and nav[GOAL[1], GOAL[0]], "ends blocked"
DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)),
        (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))]


def _h(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


openq = [(0.0, START)]
came, cost = {START: None}, {START: 0.0}
found = None
while openq:
    _, cur = heapq.heappop(openq)
    if cur == GOAL:
        found = cur
        break
    for dx, dy, w in DIRS:
        nxt = (cur[0] + dx, cur[1] + dy)
        if not (0 <= nxt[0] < W and 0 <= nxt[1] < H):
            continue
        if not nav[nxt[1], nxt[0]]:
            continue
        if dx and dy and not (nav[cur[1], nxt[0]] and nav[nxt[1], cur[0]]):
            continue
        nc = cost[cur] + w
        if nxt not in cost or nc < cost[nxt]:
            cost[nxt] = nc
            came[nxt] = cur
            heapq.heappush(openq, (nc + _h(nxt, GOAL), nxt))
path = []
c = found
while c is not None:
    path.append([XR[0] + (c[0] + 0.5) * RES,
                 YR[0] + (c[1] + 0.5) * RES])
    c = came[c]
path.reverse()
P = np.array(path)
bad = 0
for i, (x, y) in enumerate(path):
    j = min(i + 1, len(path) - 1)
    yaw = math.atan2(path[j][1] - y, path[j][0] - x)
    if footprint_clips_np(x, y, yaw, size, RES, grid, XR, YR):
        bad += 1
json.dump({"path": path},
          open("action-reasoner/skills/ros-navigation/planning/evidence/v11_path.json", "w"))

cfg = PurePursuitConfig()
pos = P[0].copy()
yaw = math.atan2(P[1][1] - P[0][1], P[1][0] - P[0][0])
prev, devs, done, k, step = 0.0, [], False, 0, 0
for step in range(1, 401):
    k = k + int(np.linalg.norm(P[k:] - pos, axis=1).argmin())
    out = pure_pursuit_step(pos, yaw, P[k:], cfg, prev)
    prev = out["heading_error"]
    if out["done"]:
        done = True
        break
    yaw += out["angular"] * 0.1
    pos = pos + out["linear"] * 0.1 * np.array(
        [math.cos(yaw), math.sin(yaw)])
    devs.append(float(np.linalg.norm(P - pos, axis=1).min()))
arr = float(np.linalg.norm(P[-1] - pos))
json.dump({"done": done, "steps": step, "arrival": arr,
           "max_dev": max(devs) if devs else -1.0, "bad": bad,
           "plen": len(path)},
          open("action-reasoner/skills/ros-navigation/planning/evidence/v11_nav.json", "w"))
print("V11-PIPE len=%d bad=%d done=%s steps=%d arr=%.3f maxdev=%.3f" % (
    len(path), bad, done, step, arr, max(devs) if devs else -1.0))
