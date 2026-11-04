"""P2 run (runs INSIDE Isaac Sim): vx=5 for 60 steps, report displacement.

Velocity is set AFTER play() (pre-play velocity is ignored by PhysX).
Pauses at end; stepping via update_app_async (see failures.md F1).
"""
import numpy as np
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
from isaacsim.core.experimental.prims import RigidPrim

tl = omni.timeline.get_timeline_interface()
rp = RigidPrim(paths="/World/P2Cube")
app_utils.play()
p0 = rp.get_world_poses()[0].numpy()[0]
t0 = float(tl.get_current_time())
rp.set_velocities(linear_velocities=np.array([[5.0, 0.0, 0.0]]))
await app_utils.update_app_async(steps=60)
p1 = rp.get_world_poses()[0].numpy()[0]
t1 = float(tl.get_current_time())
tl.pause()
print("P2-MOTION-REPORT x0=%.4f x1=%.4f z0=%.4f z1=%.4f t0=%.3f t1=%.3f vx=5.0"
      % (float(p0[0]), float(p1[0]), float(p0[2]), float(p1[2]), t0, t1))
