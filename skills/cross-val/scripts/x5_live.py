"""X5 cross-skill co-validation (runs INSIDE Isaac Sim): snapshot the V5-final scene.

V5 scene (built by v5_build.py, final state by v5b_run.py): M4Bot arm
(Root+Link1+Link2, Hinge1/2), M4Block at pedestal A, M4ShelfA/B.
Snapshot-only: play 120 steps from the stopped V5-final state, measure
all five graduated lenses, pause. No rebuild (R11 false alarm: the stage
never reverted; x5 v1 failed purely on wrong M4V2* paths).
sense lens:      block world pose at A (+0.55, z 0.36)
physics lens:    settle speed ~0, rigid/collision flags on block
stage lens:      all 7 V5 prims valid
modeling lens:   Link2 size 0.20, shelf top 0.30 (tz 0.15 + sz/2)
articulation lens: q within +/-170deg, place branch q1>0, root present
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
import numpy as np
import warp as wp
from pxr import UsdGeom, UsdPhysics
from isaacsim.core.experimental.prims import Articulation, RigidPrim

stage = omni.usd.get_context().get_stage()
P = "/World/M4Bot"
BLK = "/World/M4Block"
paths = [P, P + "/Root", P + "/Link1", P + "/Link2",
         "/World/M4ShelfA", "/World/M4ShelfB", BLK]
valid = [stage.GetPrimAtPath(p).IsValid() for p in paths]
allok = all(valid)
# R11: NEVER touch HasAPI/attrs on invalid prims (null-prim throw);
# report cleanly instead.
root_ok = allok and stage.GetPrimAtPath(P + "/Root").HasAPI(
    UsdPhysics.ArticulationRootAPI)
link_sz = (float(UsdGeom.Cube.Get(stage, P + "/Link2").GetSizeAttr().Get())
           if allok else -1.0)
tz, sz = 0.0, 0.0
if allok:
    sh = UsdGeom.Xformable(stage.GetPrimAtPath("/World/M4ShelfA"))
    for op in sh.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            tz = float(op.Get()[2])
        elif op.GetOpType() == UsdGeom.XformOp.TypeScale:
            sz = float(op.Get()[2])


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float)


tl = omni.timeline.get_timeline_interface()
if allok:
    app_utils.play()
    art = Articulation(P + "/Root")
    rig = RigidPrim(BLK)
    await app_utils.update_app_async(steps=120)
    q = _w(art.get_dof_positions()).flatten()
    b1 = _w(rig.get_world_poses()[0])[0]
    v1 = _w(rig.get_velocities()[0])[0]
    tl.pause()
else:
    q = np.array([999.0, 999.0])
    b1 = np.array([999.0, 0.0, 999.0])
    v1 = np.array([999.0, 0.0, 0.0])
print("X5-REPORT valid=%s root=%s link=%.2f stop=%.2f q=[%.3f,%.3f] "
      "klim=%s bx=%.4f bz=%.4f spd=%.4f rigid=%s coll=%s"
      % (all(valid), root_ok, link_sz, tz + sz / 2.0, q[0], q[1],
         bool(np.all(np.abs(np.degrees(q)) <= 170.0)),
         b1[0], b1[2], float(np.linalg.norm(v1[:3])),
         allok and stage.GetPrimAtPath(BLK).HasAPI(UsdPhysics.RigidBodyAPI),
         allok and stage.GetPrimAtPath(BLK).HasAPI(UsdPhysics.CollisionAPI)))
