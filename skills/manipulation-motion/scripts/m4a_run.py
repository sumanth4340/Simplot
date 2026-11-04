"""M4a run (runs INSIDE Isaac Sim): record place, approach, grasp.

Uses graduated skills: physics-master tensor-read rule (ALL live
reads via tensors; USD only at stop), M2 DLS trim + M3 interp legs,
workspace-sense cross-check after (separate send). Legs route via
home; grasp leg descends vertically through TOP for clearance.
B1: place-app/place (record q_place). B2: approach/top/grasp.
C: grasp gate (site-block <2cm) + FixedJoint (computed frames).
"""
import math
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from pxr import UsdPhysics, Gf
from isaacsim.core.experimental.prims import Articulation, RigidPrim
from isaacsim.core.experimental.utils import xform as xform_utils

SITE_OFF = np.array([0.0, 0.0, 0.2])
LINK = "/World/M4Bot/Link2"
BLOCK = "/World/M4Block"
ROOT = "/World/M4Bot/Root"
JOINTS = ("/World/M4Bot/Hinge1", "/World/M4Bot/Hinge2")
APPROACH = np.array([0.65, 0.0, 0.50])
TOP = np.array([0.55, 0.0, 0.50])
GRASP = np.array([0.55, 0.0, 0.36])
PLACE_APP = np.array([-0.65, 0.0, 0.50])
PLACE = np.array([-0.55, 0.0, 0.36])
TOL, LAM, STEPS = 0.02, 0.1, 30


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float)


def _q(robot):
    return _w(robot.get_dof_positions()).flatten()


def _jac(robot):
    return _w(robot.get_jacobian_matrices())


def _quat_rot(q, v):
    w, x, y, z = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))
    n = (w * w + x * x + y * y + z * z) ** 0.5
    w, x, y, z = w / n, x / n, y / n, z / n
    uv = np.cross((x, y, z), v)
    uvc = np.cross((x, y, z), uv)
    return v + 2.0 * (w * uv + uvc)


def _link_pose():
    rp = RigidPrim(LINK)
    p, q = rp.get_world_poses()
    return _w(p)[0], _w(q)[0]


def _site():
    lp, lq = _link_pose()
    return lp + _quat_rot(lq, SITE_OFF)


def _block():
    rp = RigidPrim(BLOCK)
    p, _ = rp.get_world_poses()
    return _w(p)[0]


def _pos_usd(p):
    v, _ = xform_utils.get_world_pose(p)
    return _w(v).flatten()


async def _replay(qn):
    stage = omni.usd.get_context().get_stage()
    qn = (np.asarray(qn, dtype=float) + np.pi) % (2 * np.pi) - np.pi
    app_utils.stop()
    await app_utils.update_app_async(steps=10)
    for jp, v in zip(JOINTS, qn):
        at = stage.GetPrimAtPath(jp).GetAttribute(
            "drive:angular:physics:targetPosition")
        at.Set(float(v) * 180.0 / math.pi)
    app_utils.play()
    await app_utils.update_app_async(steps=STEPS)


async def _ik(robot, target, iters, maxdq=0.12, tag="IK"):
    err = 9.0
    for k in range(iters):
        lp, _ = _link_pose()
        sp = lp + _quat_rot(_link_pose()[1], SITE_OFF)
        e = target - sp
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
        step = 0.05 if err < 0.05 else maxdq
        dq = np.clip(dq, -step, step)
        await _replay(_q(robot) + dq)
        robot = Articulation(ROOT)
        if k < 3 or k % 5 == 4:
            print("M4A-TRACE %s it=%d err=%.4f q=%s dq=%s" % (
                tag, k + 1, err, np.round(_q(robot), 4).tolist(),
                np.round(dq, 4).tolist()))
    return robot, err


async def _interp(robot, qa, qb, n):
    for w in range(1, n + 1):
        await _replay(qa + (qb - qa) * w / n)
        robot = Articulation(ROOT)
    return robot


def _seed_ik(target, branch):
    sh = _pos_usd(ROOT) + np.array([0.0, 0.0, 0.075])
    d = target - sh
    L1, L2 = 0.4, 0.5
    D = min(float(np.linalg.norm(d[[0, 2]])), L1 + L2 - 1e-4)
    elb = branch * math.acos(max(-1.0, min(1.0,
        (D * D - L1 * L1 - L2 * L2) / (2 * L1 * L2))))
    phi = math.atan2(float(d[0]), float(d[2]))
    psi = math.atan2(L2 * math.sin(elb), L1 + L2 * math.cos(elb))
    return np.array([phi - psi, elb])


async def _settle_measure(robot, target):
    app_utils.stop()
    await app_utils.update_app_async(steps=10)
    app_utils.play()
    await app_utils.update_app_async(steps=60)
    robot = Articulation(ROOT)
    sp = _site()
    return robot, float(np.linalg.norm(sp - target))


async def _dls_leg(robot, target, tag):
    for _ in range(2):
        robot, err = await _ik(robot, target, 10, tag=tag)
        robot, err = await _settle_measure(robot, target)
        if err < TOL:
            break
    return robot, err


async def _leg(robot, target, branch, tag):
    seed = _seed_ik(target, branch)
    home = np.array([0.0, 0.0])
    robot = await _interp(robot, _q(robot), home, 4)
    robot = await _interp(robot, home, seed, 6)
    robot, err = await _settle_measure(robot, target)
    print("M4A-SEED %s err=%.4f q=%s"
          % (tag, err, np.round(_q(robot), 4).tolist()))
    for _ in range(2):
        if err < TOL:
            break
        robot, err = await _ik(robot, target, 8, tag=tag)
        robot, err = await _settle_measure(robot, target)
    return robot, err


stage = omni.usd.get_context().get_stage()
tl = omni.timeline.get_timeline_interface()
app_utils.stop()
tl.set_current_time(0.0)
await app_utils.update_app_async(steps=10)
app_utils.play()
await app_utils.update_app_async(steps=60)
robot = Articulation(ROOT)
block0 = _block()
robot, _ = await _leg(robot, PLACE_APP, -1, "PAPP")
robot, err_pd = await _leg(robot, PLACE, -1, "PDSC")
q_place = _q(robot)
robot = await _interp(robot, q_place, np.array([0.0, 0.0]), 6)
robot, err_a = await _leg(robot, APPROACH, +1, "APP")
robot, err_t = await _dls_leg(robot, TOP, "TOP")
robot, err_g = await _dls_leg(robot, GRASP, "GRASP")
q_grasp = _q(robot)
_, ql = _link_pose()
rp = RigidPrim(BLOCK)
pbt, qbt = rp.get_world_poses()
qb = _w(qbt)[0]
sp0 = _site()
bp0 = _w(pbt)[0]
g0 = float(np.linalg.norm(sp0 - bp0))
app_utils.stop()
await app_utils.update_app_async(steps=10)
attached = bool(g0 < 0.05)
if attached:
    qlen = float(np.linalg.norm(ql))
    qw = Gf.Quatf(float(ql[0]) / qlen, float(ql[1]) / qlen,
                  float(ql[2]) / qlen, float(ql[3]) / qlen)
    fj = UsdPhysics.FixedJoint.Define(stage, "/World/M4GraspJoint")
    fj.GetBody0Rel().AddTarget(LINK)
    fj.GetBody1Rel().AddTarget(BLOCK)
    fj.GetLocalPos0Attr().Set(Gf.Vec3f(0.0, 0.0, 0.2))
    fj.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
    blen = float(np.linalg.norm(qb))
    bq = Gf.Quatf(float(qb[0]) / blen, float(qb[1]) / blen,
                  float(qb[2]) / blen, float(qb[3]) / blen)
    off = sp0 - bp0
    dl1 = bq.GetInverse().Transform(Gf.Vec3f(float(off[0]),
                                             float(off[1]),
                                             float(off[2])))
    fj.GetLocalPos1Attr().Set(Gf.Vec3f(float(dl1[0]), float(dl1[1]),
                                       float(dl1[2])))
    fj.GetLocalRot1Attr().Set(qw.GetInverse() * bq)
app_utils.play()
await app_utils.update_app_async(steps=30)
robot = Articulation(ROOT)
g0b = float(np.linalg.norm(_site() - _block()))
tl.pause()
print("M4A-REPORT err_pd=%.4f err_a=%.4f err_t=%.4f err_g=%.4f g0=%.4f "
      "g0b=%.4f attached=%s bq=%s q_place=%s q_grasp=%s block0=%s conv=%s"
      % (err_pd, err_a, err_t, err_g, g0, g0b, attached,
         np.round(qb, 4).tolist(), q_place.tolist(),
         q_grasp.tolist(), block0.tolist(),
         err_pd < TOL and err_a < TOL and err_g < TOL and g0b < 0.02))
