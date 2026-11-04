"""M4b run (runs INSIDE Isaac Sim): carry traverse + release + place gate.

Starts from m4a's paused attached state. D: interp q_grasp->home->
q_place (lift via home high point; block z tracked). Trim to PLACE.
E: remove joint, settle, place gate on OBJECT pose + rest speed
(finite-difference, API-free). Lift gate: block zmax > 1.0.
"""
import math
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from pxr import UsdGeom, Gf
from isaacsim.core.experimental.prims import Articulation, RigidPrim

SITE_OFF = np.array([0.0, 0.0, 0.2])
LINK = "/World/M4Bot/Link2"
BLOCK = "/World/M4Block"
ROOT = "/World/M4Bot/Root"
JOINTS = ("/World/M4Bot/Hinge1", "/World/M4Bot/Hinge2")
PLACE = np.array([-0.55, 0.0, 0.36])
REST = np.array([-0.55, 0.0, 0.36])
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


async def _ik(robot, target, iters, maxdq=0.12):
    err = 9.0
    for _ in range(iters):
        lp, lq = _link_pose()
        sp = lp + _quat_rot(lq, SITE_OFF)
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
    return robot, err


async def _settle_measure(robot, target):
    app_utils.stop()
    await app_utils.update_app_async(steps=10)
    app_utils.play()
    await app_utils.update_app_async(steps=60)
    robot = Articulation(ROOT)
    return robot, float(np.linalg.norm(_site() - target))


stage = omni.usd.get_context().get_stage()
tl = omni.timeline.get_timeline_interface()
app_utils.stop()
tl.set_current_time(0.0)
await app_utils.update_app_async(steps=10)
app_utils.play()
await app_utils.update_app_async(steps=30)
robot = Articulation(ROOT)
q0 = _q(robot)
home = np.array([0.0, 0.0])
zmax = 0.0
qa, qb = q0, home
for w in range(1, 9):
    await _replay(qa + (qb - qa) * w / 8)
    robot = Articulation(ROOT)
    zmax = max(zmax, float(_block()[2]))
q_place = np.array([-1.7339, -1.0925])
qa = _q(robot)
for w in range(1, 9):
    await _replay(qa + (q_place - qa) * w / 8)
    robot = Articulation(ROOT)
    zmax = max(zmax, float(_block()[2]))
for _ in range(2):
    robot, err_p = await _ik(robot, PLACE, 10)
    robot, err_p = await _settle_measure(robot, PLACE)
    if err_p < TOL:
        break
q_end = _q(robot)
rp = RigidPrim(BLOCK)
pbt, qbt = rp.get_world_poses()
bp_live = _w(pbt)[0]
bq_live = _w(qbt)[0]
app_utils.stop()
await app_utils.update_app_async(steps=10)
bp = stage.GetPrimAtPath(BLOCK)
xp = UsdGeom.Xformable(bp)
found_t = found_o = False
for op in xp.GetOrderedXformOps():
    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
        op.Set(Gf.Vec3d(float(bp_live[0]), float(bp_live[1]),
                         float(bp_live[2])))
        found_t = True
    elif op.GetOpType() == UsdGeom.XformOp.TypeOrient:
        op.Set(Gf.Quatf(float(bq_live[0]), float(bq_live[1]),
                        float(bq_live[2]), float(bq_live[3])))
        found_o = True
if not found_t:
    xp.AddTranslateOp().Set(Gf.Vec3d(float(bp_live[0]),
                                     float(bp_live[1]),
                                     float(bp_live[2])))
if not found_o:
    xp.AddOrientOp().Set(Gf.Quatf(float(bq_live[0]), float(bq_live[1]),
                                  float(bq_live[2]), float(bq_live[3])))
jp = stage.GetPrimAtPath("/World/M4GraspJoint")
if jp and jp.IsValid():
    stage.RemovePrim("/World/M4GraspJoint")
    released = True
else:
    released = False
app_utils.play()
await app_utils.update_app_async(steps=60)
robot = Articulation(ROOT)
b1 = _block()
await app_utils.update_app_async(steps=30)
b2 = _block()
spd = float(np.linalg.norm(b2 - b1) / 0.5)
perr = np.array([b2[0] - REST[0], b2[1] - REST[1], b2[2] - REST[2]])
pxy = float(np.linalg.norm(perr[:2]))
pz = float(abs(perr[2]))
tl.pause()
print("M4B-REPORT zmax=%.4f err_p=%.4f pxy=%.4f pz=%.4f spd=%.4f "
      "released=%s q_end=%s block1=%s conv=%s"
      % (zmax, err_p, pxy, pz, spd, released, q_end.tolist(),
         b2.tolist(), zmax > 1.0 and err_p < TOL and pxy < 0.05
         and pz < 0.03 and spd < 0.05 and released))
