"""P4 run (runs INSIDE Isaac Sim): 180 steps, report rest heights + speeds."""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
from isaacsim.core.experimental.prims import RigidPrim

tl = omni.timeline.get_timeline_interface()
rpA = RigidPrim(paths="/World/P4A")
rpB = RigidPrim(paths="/World/P4B")
app_utils.play()
za0 = float(rpA.get_world_poses()[0].numpy()[0][2])
zb0 = float(rpB.get_world_poses()[0].numpy()[0][2])
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=180)
za1 = float(rpA.get_world_poses()[0].numpy()[0][2])
zb1 = float(rpB.get_world_poses()[0].numpy()[0][2])
va1 = rpA.get_velocities()[0].numpy()[0]
vb1 = rpB.get_velocities()[0].numpy()[0]
t1 = float(tl.get_current_time())
tl.pause()
print("P4-REPORT za0=%.4f za1=%.4f zb0=%.4f zb1=%.4f "
      "va1=%.4f vb1=%.4f t0=%.3f t1=%.3f"
      % (za0, za1, zb0, zb1,
         float((va1 ** 2).sum() ** 0.5), float((vb1 ** 2).sum() ** 0.5),
         t0, t1))
