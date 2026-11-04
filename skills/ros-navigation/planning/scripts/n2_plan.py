"""N2 plan (runs LOCALLY): A* on the exported N1 grid.

Erode by inscribed 0.3m (1 cell @0.25) per the library validation
pipeline, then 8-connected A* (no corner cutting, octile heuristic)
from (-4,-4) to (4,4). Straight line crosses ObsA, so a valid path
must deviate. Writes n2_path.json + prints N2-REPORT.
"""
import heapq
import json
import math
import numpy as np
from scipy.ndimage import binary_erosion

G = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n1_grid.json"))
XR, YR, RES = G["x_range"], G["y_range"], G["res"]
grid = np.array(G["grid"], dtype=np.uint8)
H, W = grid.shape

INSCRIBED = 0.3
kr = int(round(INSCRIBED / RES))
ky, kx = np.ogrid[-kr:kr + 1, -kr:kr + 1]
kernel = kx * kx + ky * ky <= kr * kr
nav = binary_erosion(grid == 0, structure=kernel)


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
            continue  # no corner cutting
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
json.dump({"start": list(START), "goal": list(GOAL), "path": path,
           "eroded_free": int(nav.sum()), "raw_free": int((grid == 0).sum())},
          open("action-reasoner/skills/ros-navigation/planning/evidence/n2_path.json", "w"))
print("N2-REPORT found=%s len=%d sx=%d sy=%d gx=%d gy=%d" % (
    found is not None, len(path), START[0], START[1], GOAL[0], GOAL[1]))
