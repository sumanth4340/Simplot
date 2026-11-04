"""N3 validate (runs LOCALLY): stamp cases + path validation.

Cases: (a) start cell yaw0 -> free; (b) ObsA center yaw0 -> clip;
(c) ObsA center yaw45 -> clip; (d) every N2 waypoint at path yaw
-> must be clip-free (library validation step 6).
"""
import json
import math
import numpy as np
import sys

sys.path.insert(0, "action-reasoner/skills/ros-navigation/planning/scripts")
from nav_check import footprint_clips_np

G = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n1_grid.json"))
FP = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n3_footprint.json"))
P = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n2_path.json"))
XR, YR, RES = G["x_range"], G["y_range"], G["res"]
grid = np.array(G["grid"], dtype=np.uint8)
size = FP["size"]

a = footprint_clips_np(-4.0, -4.0, 0.0, size, RES, grid, XR, YR)
b = footprint_clips_np(1.0, 0.0, 0.0, size, RES, grid, XR, YR)
c = footprint_clips_np(1.0, 0.0, math.pi / 4, size, RES, grid, XR, YR)
path = P["path"]
bad = []
for i, (x, y) in enumerate(path):
    j = min(i + 1, len(path) - 1)
    yaw = math.atan2(path[j][1] - y, path[j][0] - x)
    if footprint_clips_np(x, y, yaw, size, RES, grid, XR, YR):
        bad.append(i)
print("N3-VALIDATE a=%d b=%d c=%d bad=%d/%d" % (
    a, b, c, len(bad), len(path)))
