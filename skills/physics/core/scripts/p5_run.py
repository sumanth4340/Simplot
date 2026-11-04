"""P5 run (runs INSIDE Isaac Sim): drop twice with explicit reset, sample z.

stop() does NOT restore pre-play state (see failures.md F4), so each
trial resets the cube pose via USD and the clock before playing.
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from pxr import UsdGeom, Gf
from isaacsim.core.experimental.prims import RigidPrim

tl = omni.timeline.get_timeline_interface()
stage = omni.usd.get_context().get_stage()


def _reset_cube():
    prim = stage.GetPrimAtPath("/World/P5Cube")
    for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            op.Set(Gf.Vec3d(0, 0, 2.0))


trajs = []
for _ in range(2):
    _reset_cube()
    try:
        tl.set_current_time(0.0)
    except Exception as exc:
        print("P5-TIME-RESET %r" % (exc,))
    rp = RigidPrim(paths="/World/P5Cube")
    app_utils.play()
    zs = []
    for _ in range(6):
        await app_utils.update_app_async(steps=20)
        zs.append(float(rp.get_world_poses()[0].numpy()[0][2]))
    trajs.append(zs)
    app_utils.stop()
print("P5-TRAJ0 " + ",".join("%.6f" % z for z in trajs[0]))
print("P5-TRAJ1 " + ",".join("%.6f" % z for z in trajs[1]))
