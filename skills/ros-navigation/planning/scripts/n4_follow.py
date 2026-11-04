"""N4 follow (runs LOCALLY): kinematics round-trips + pursuit.

(1) differential + holonomic forward/inverse round-trips must be
exact. (2) Unicycle-simulate pure_pursuit_step along the N2 path
(dt=0.1, <=400 steps): must finish with arrival < tolerance and
bounded cross-track deviation. Writes n4_follow.json.
"""
import json
import math
import sys
import numpy as np

sys.path.insert(0, "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
                   "skills/navigation-primitives/scripts")
from kinematics import (DifferentialParams, HolonomicParams,
                        PurePursuitConfig, differential_forward,
                        differential_inverse, holonomic_forward,
                        holonomic_inverse, pure_pursuit_step)

dp, hp = DifferentialParams(), HolonomicParams()
wl, wr = differential_forward(1.0, 0.5, dp)
rt_d = differential_inverse(wl, wr, dp)
wv = holonomic_forward(0.3, 0.1, 0.4, hp)
rt_h = holonomic_inverse(np.asarray(wv), hp)

P = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n2_path.json"))
path = np.array(P["path"])
cfg = PurePursuitConfig()
pos = path[0].copy()
yaw = math.atan2(path[1][1] - path[0][1], path[1][0] - path[0][0])
prev, devs, done, step = 0.0, [], False, 0
DT, MAXS = 0.1, 400
k = 0  # R5: pass the REMAINING path; the step scans from index 0
for step in range(1, MAXS + 1):
    rel = int(np.linalg.norm(path[k:] - pos, axis=1).argmin())
    k = k + rel
    out = pure_pursuit_step(pos, yaw, path[k:], cfg, prev)
    prev = out["heading_error"]
    if out["done"]:
        done = True
        break
    yaw += out["angular"] * DT
    pos = pos + out["linear"] * DT * np.array([math.cos(yaw), math.sin(yaw)])
    devs.append(float(np.linalg.norm(path - pos, axis=1).min()))
arr = float(np.linalg.norm(path[-1] - pos))
json.dump({"done": done, "steps": step, "arrival": arr,
           "max_dev": max(devs) if devs else -1.0,
           "rt_diff": list(rt_d), "rt_holo": list(rt_h)},
          open("action-reasoner/skills/ros-navigation/planning/evidence/n4_follow.json", "w"))
print("N4-REPORT done=%s steps=%d arr=%.3f maxdev=%.3f "
      "rt_d=%.4f,%.4f rt_h=%.4f,%.4f,%.4f" % (
          done, step, arr, max(devs) if devs else -1.0,
          rt_d[0], rt_d[1], rt_h[0], rt_h[1], rt_h[2]))
