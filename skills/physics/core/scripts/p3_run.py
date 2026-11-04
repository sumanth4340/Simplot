"""P3 run (runs INSIDE Isaac Sim): 60 steps, report arm quats + z + time."""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
from isaacsim.core.experimental.prims import RigidPrim

tl = omni.timeline.get_timeline_interface()
rp = RigidPrim(paths="/World/P3Arm")
app_utils.play()
p0, q0 = (a.numpy()[0] for a in rp.get_world_poses())
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=60)
p1, q1 = (a.numpy()[0] for a in rp.get_world_poses())
t1 = float(tl.get_current_time())
tl.pause()
print("P3-REPORT q0=%.4f,%.4f,%.4f,%.4f q1=%.4f,%.4f,%.4f,%.4f "
      "z0=%.4f z1=%.4f t0=%.3f t1=%.3f w=180"
      % (q0[0], q0[1], q0[2], q0[3], q1[0], q1[1], q1[2], q1[3],
         float(p0[2]), float(p1[2]), t0, t1))
