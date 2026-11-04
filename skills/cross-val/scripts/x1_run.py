"""X1 run (runs INSIDE Isaac Sim): drop 120 steps, report live z + time."""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
from isaacsim.core.experimental.prims import RigidPrim

tl = omni.timeline.get_timeline_interface()
rp = RigidPrim(paths="/World/X1Cube")
app_utils.play()
z0 = float(rp.get_world_poses()[0].numpy()[0][2])
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=120)
z1 = float(rp.get_world_poses()[0].numpy()[0][2])
t1 = float(tl.get_current_time())
tl.pause()
print("X1-REPORT z0=%.4f z1=%.4f t0=%.3f t1=%.3f" % (z0, z1, t0, t1))
