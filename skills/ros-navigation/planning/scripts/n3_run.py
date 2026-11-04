"""N3 run (runs INSIDE Isaac Sim): footprint report.

Inlines compute_robot_footprint (library robot_footprint.py fixed
on disk, but the server caches repo imports across sends — R3 —
so drills inline the 20 lines instead of importing).
"""
import json
import numpy as np
import omni.usd
import isaacsim.core.experimental.utils.bounds as bounds_utils
from pxr import Usd, UsdPhysics

stage = omni.usd.get_context().get_stage()
colliders = [p for p in Usd.PrimRange(stage.GetPrimAtPath("/World/N3Bot"))
             if p.HasAPI(UsdPhysics.CollisionAPI)]
if not colliders:
    colliders = [stage.GetPrimAtPath("/World/N3Bot")]
aabb = bounds_utils.compute_combined_aabb(colliders)
mn, mx = aabb[:3], aabb[3:]
size = mx - mn
origin_z = stage.GetPrimAtPath("/World/N3Bot").GetAttribute(
    "xformOp:translate").Get()[2]
fp = {"size": tuple(float(v) for v in size),
      "z_offset": float(max(0.0, origin_z - mn[2])),
      "inscribed_radius": float(min(size[0], size[1]) / 2.0),
      "circumscribed_radius": float(np.hypot(size[0] / 2.0, size[1] / 2.0)),
      "aabb_min": tuple(float(v) for v in mn),
      "aabb_max": tuple(float(v) for v in mx)}
json.dump(fp, open("C:/Users/sruja_ob3di74/action-reasoner/skills/"
                   "navigation/evidence/n3_footprint.json", "w"))
print("N3-REPORT sx=%.3f sy=%.3f sz=%.3f zoff=%.3f "
      "ins=%.4f cir=%.4f" % (fp["size"][0], fp["size"][1],
                             fp["size"][2], fp["z_offset"],
                             fp["inscribed_radius"],
                             fp["circumscribed_radius"]))
