"""M3 run (runs INSIDE Isaac Sim): joint-space traverse via re-play.

Interpolates qA=(0,0) -> qB=(0.5,-0.35) in 8 waypoints; each waypoint
is commanded via USD targets (deg) + stop/play re-parse (R4). Reports
final arrival error and max waypoint tracking deviation.
"""
import math
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation

JOINTS = ("/World/M3Bot/Hinge1", "/World/M3Bot/Hinge2")
QA = np.array([0.0, 0.0])
QB = np.array([0.5, -0.35])
NW, STEPS = 8, 20


def _q(robot):
    q = robot.get_dof_positions()
    q = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
    return np.asarray(q, dtype=float).flatten()


stage = omni.usd.get_context().get_stage()
tl = omni.timeline.get_timeline_interface()
app_utils.stop()
tl.set_current_time(0.0)
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=30)
robot = Articulation("/World/M3Bot/Base")
q0 = _q(robot)
maxdev = 0.0
for w in range(1, NW + 1):
    qw = QA + (QB - QA) * w / NW
    app_utils.stop()
    for jp, v in zip(JOINTS, qw):
        at = stage.GetPrimAtPath(jp).GetAttribute(
            "drive:angular:physics:targetPosition")
        at.Set(float(v) * 180.0 / math.pi)
    app_utils.play()
    await app_utils.update_app_async(steps=STEPS)
    robot = Articulation("/World/M3Bot/Base")
    dev = float(np.linalg.norm(_q(robot) - qw))
    maxdev = max(maxdev, dev)
    if w in (1, NW):
        print("M3-TRACE w=%d/%d dev=%.4f q=%s" % (
            w, NW, dev, np.round(_q(robot), 4).tolist()))
app_utils.stop()
app_utils.play()
await app_utils.update_app_async(steps=60)
robot = Articulation("/World/M3Bot/Base")
qN = _q(robot)
arr = float(np.linalg.norm(qN - QB))
tl.pause()
print("M3-REPORT q0=%s qN=%s goal=%s arr=%.4f maxdev=%.4f conv=%s"
      % (q0.tolist(), qN.tolist(), QB.tolist(), arr, maxdev,
         arr < 0.01 and maxdev < 0.05))
