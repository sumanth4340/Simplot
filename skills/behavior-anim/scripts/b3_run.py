"""B3 run (runs INSIDE Isaac Sim): 3-phase state machine.

EXTEND (+0.5 rad) -> RETRACT (-0.5) -> HOME (0.0), 60 steps each,
single play session, tensor commands (radians). Mid-play USD sets
do NOT propagate (M3 R4); tensor API does (probed q=0.5014).
Reports q + echoed target per phase.
"""
import numpy as np
import warp as wp
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import Articulation

PHASES = (("EXTEND", 0.5), ("RETRACT", -0.5), ("HOME", 0.0))
STEPS = 60


def _q(robot):
    q = robot.get_dof_positions()
    q = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
    return float(np.asarray(q, dtype=float).flatten()[0])


def _e(robot):
    e = robot.get_dof_position_targets()
    e = e.numpy() if isinstance(e, wp.array) else np.asarray(e)
    return float(np.asarray(e, dtype=float).flatten()[0])


app_utils.stop()
await app_utils.update_app_async(steps=10)
app_utils.play(commit=True)
await app_utils.update_app_async(steps=10)
robot = Articulation("/World/B3Bot/Base")
outs = []
for name, tgt in PHASES:
    robot.set_dof_position_targets(np.array([tgt], dtype=np.float32))
    await app_utils.update_app_async(steps=STEPS)
    outs.append((name, tgt, _q(robot), _e(robot)))
print("B3-REPORT " + " ".join(
    "%s_t=%.2f_q=%.4f_e=%.4f" % (n, t, q, e)
    for n, t, q, e in outs))
