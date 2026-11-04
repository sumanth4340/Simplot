"""V11 run (runs INSIDE Isaac Sim): rasterize exam yard.

Inlines the library rasterizer (R3: server caches repo imports).
Same framing as N1: x/y(-5,5) res 0.25 colliders_only. Writes
v11_grid.json, reports shape/occupied/probe cells.
"""
import json
import numpy as np
import omni.usd
from pxr import Usd, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
XR, YR, RES, ZC = (-5.0, 5.0), (-5.0, 5.0), 0.25, 4.5
cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(),
                           [UsdGeom.Tokens.default_])
gw, gh = int((XR[1] - XR[0]) / RES), int((YR[1] - YR[0]) / RES)
grid = np.zeros((gh, gw), dtype=np.uint8)
for prim in Usd.PrimRange(stage.GetPrimAtPath("/World")):
    if not prim.HasAPI(UsdPhysics.CollisionAPI):
        continue
    en = prim.GetAttribute("physics:collisionEnabled")
    if en and en.Get() is False:
        continue
    r = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    if r.IsEmpty():
        continue
    mn, mx = r.GetMin(), r.GetMax()
    if mn[2] > ZC:
        continue
    x0 = max(0, int((mn[0] - XR[0]) / RES))
    x1 = min(gw, int((mx[0] - XR[0]) / RES))
    y0 = max(0, int((mn[1] - YR[0]) / RES))
    y1 = min(gh, int((mx[1] - YR[0]) / RES))
    grid[y0:y1, x0:x1] = 255
json.dump({"x_range": list(XR), "y_range": list(YR), "res": RES,
           "grid": grid.tolist()},
          open("C:/Users/sruja_ob3di74/action-reasoner/skills/"
               "navigation/evidence/v11_grid.json", "w"))
occ = int((grid > 0).sum())


def _cell(x, y):
    return int(grid[int((y - YR[0]) / RES), int((x - XR[0]) / RES)])


print("V11-REPORT shape=%dx%d occ=%d d=%d e=%d f=%d corner=%d" % (
    grid.shape[0], grid.shape[1], occ,
    _cell(0.0, 2.0), _cell(-2.9, 1.1), _cell(2.0, -2.0),
    _cell(-4.9, 4.9)))
