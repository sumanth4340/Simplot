"""O3 run (runs INSIDE Isaac Sim): joint follows graph targets.

Reads drive target + q at 30 steps and +60: target delta ~10deg,
q follows (delta > 0.05 rad, same direction).
"""
import numpy as np
import warp as wp
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import Articulation

stage = omni.usd.get_context().get_stage()
HP = "/World/O3Bot/Hinge1"


def _tgt():
    return float(stage.GetPrimAtPath(HP).GetAttribute(
        "drive:angular:physics:targetPosition").Get())


# Skill 5 R3: build ran during play; stop/play re-parses physics.
app_utils.stop()
await app_utils.update_app_async(steps=10)
app_utils.play(commit=True)


def _q():
    art = Articulation("/World/O3Bot/Base")
    q = art.get_dof_positions()
    return float(np.asarray(
        q.numpy() if isinstance(q, wp.array) else q).flatten()[0])


await app_utils.update_app_async(steps=30)
t1, q1 = _tgt(), _q()
await app_utils.update_app_async(steps=60)
t2, q2 = _tgt(), _q()
print("O3-REPORT t1=%.3f t2=%.3f dt=%.3f q1=%.4f q2=%.4f dq=%.4f" % (
    t1, t2, t2 - t1, q1, q2, q2 - q1))
