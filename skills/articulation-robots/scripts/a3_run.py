"""A3 run (runs INSIDE Isaac Sim): 120 steps, report DOF travel."""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
from isaacsim.core.experimental.prims import Articulation

robot = Articulation("/World/A3Bot/Base")
tl = omni.timeline.get_timeline_interface()
app_utils.play()
q0 = float(robot.get_dof_positions().numpy()[0][0])
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=120)
q1 = float(robot.get_dof_positions().numpy()[0][0])
t1 = float(tl.get_current_time())
tl.pause()
print("A3-REPORT q0=%.4f q1=%.4f dt=%.3f" % (q0, q1, t1 - t0))
