"""M2 run v4 (runs INSIDE Isaac Sim): DLS IK via re-play commanding.

LOOP: read live state -> planar 2x2 DLS -> set USD targets (deg) ->
stop/play re-parse (probe 19: exact arrival) -> step -> fresh handle.
Tensor runtime target writes proved inert (failures.md R4); re-play
is the verified command path. Converge < 2cm.
"""
import math
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.experimental.utils import xform as xform_utils

SITE = "/World/M2Bot/Link2/GraspSite"
LINK = "/World/M2Bot/Link2"
JOINTS = ("/World/M2Bot/Hinge1", "/World/M2Bot/Hinge2")
TARGET = np.array([0.32, 0.0, 1.68])
TOL, LAM, MAXDQ, ITERS, STEPS = 0.02, 0.1, 0.1, 60, 30


def _vec(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float).flatten()


def _pos(p):
    v, _ = xform_utils.get_world_pose(p)
    return _vec(v)


def _q(robot):
    q = robot.get_dof_positions()
    q = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
    return np.asarray(q, dtype=float).flatten()


def _jac(robot):
    J = robot.get_jacobian_matrices()
    J = J.numpy() if isinstance(J, wp.array) else np.asarray(J)
    return np.asarray(J, dtype=float)


stage = omni.usd.get_context().get_stage()
attrs = [stage.GetPrimAtPath(jp).GetAttribute(
    "drive:angular:physics:targetPosition") for jp in JOINTS]
tl = omni.timeline.get_timeline_interface()
app_utils.stop()
tl.set_current_time(0.0)
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=30)
robot = Articulation("/World/M2Bot/Base")
await app_utils.update_app_async(steps=5)
err0 = float(np.linalg.norm(_pos(SITE) - TARGET))
err, it = err0, 0
for it in range(1, ITERS + 1):
    sp, lp = _pos(SITE), _pos(LINK)
    e = TARGET - sp
    err = float(np.linalg.norm(e))
    if err < TOL:
        break
    Jn = _jac(robot)
    Jl, Ja = Jn[0, 2, 0:3, 6:8], Jn[0, 2, 3:6, 6:8]
    r = sp - lp
    S = np.array([[0, -r[2], r[1]], [r[2], 0, -r[0]],
                  [-r[1], r[0], 0]])
    Js = Jl - S @ Ja
    Jp, ep = Js[[0, 2], :], e[[0, 2]]
    dq = Jp.T @ np.linalg.inv(Jp @ Jp.T + LAM ** 2 * np.eye(2)) @ ep
    dq = np.clip(dq, -MAXDQ, MAXDQ)
    qn = _q(robot) + dq
    app_utils.stop()
    for at, v in zip(attrs, qn):
        at.Set(float(v) * 180.0 / math.pi)
    app_utils.play()
    await app_utils.update_app_async(steps=STEPS)
    robot = Articulation("/World/M2Bot/Base")
    if it % 10 == 0 or it <= 3:
        print("M2-TRACE it=%d err=%.4f q=%s dq=%s" % (
            it, err, np.round(_q(robot), 4).tolist(),
            np.round(dq, 4).tolist()))
await app_utils.update_app_async(steps=60)
err1 = float(np.linalg.norm(_pos(SITE) - TARGET))
qf = _q(robot).tolist()
tl.pause()
print("M2-REPORT err0=%.4f err1=%.4f iters=%d q=%s conv=%s"
      % (err0, err1, it, qf, err1 < TOL))
