"""N1 run (runs INSIDE Isaac Sim): rasterize yard via library.

Imports navigation-primitives occupancy_map_from_usd (sys.path
inject), rasters x/y(-5,5) res 0.25 colliders_only, writes the
grid JSON to pack evidence, reports shape/occupied/probe cells.
"""
import json
import sys
import omni.usd

sys.path.insert(0, "C:/Users/sruja_ob3di74/Downloads/"
                   "IsaacSim-release-6.3/IsaacSim-release-6.3/"
                   "skills/navigation-primitives/scripts")
from occupancy_map_from_usd import occupancy_map_from_usd

stage = omni.usd.get_context().get_stage()
XR, YR, RES = (-5.0, 5.0), (-5.0, 5.0), 0.25
grid = occupancy_map_from_usd(stage, XR, YR, RES, 4.5, True)
json.dump({"x_range": list(XR), "y_range": list(YR), "res": RES,
           "grid": grid.tolist()},
          open("C:/Users/sruja_ob3di74/action-reasoner/skills/"
               "navigation/evidence/n1_grid.json", "w"))
occ = int((grid > 0).sum())


def _cell(x, y):
    return int(grid[int((y - YR[0]) / RES), int((x - XR[0]) / RES)])


print("N1-REPORT shape=%dx%d occ=%d a=%d b=%d c=%d corner=%d" % (
    grid.shape[0], grid.shape[1], occ,
    _cell(1.0, 0.0), _cell(-2.0, -2.0), _cell(3.0, 3.0),
    _cell(-4.9, -4.9)))
