"""A1 run (runs INSIDE Isaac Sim): DOF readback at rest, 60 steps."""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from pxr import UsdPhysics
from isaacsim.core.experimental.prims import Articulation

stage = omni.usd.get_context().get_stage()
roots = [str(p.GetPath()) for p in stage.Traverse()
         if p.HasAPI(UsdPhysics.ArticulationRootAPI)]
robot = Articulation("/World/A1Bot/Base")
tl = omni.timeline.get_timeline_interface()
app_utils.play()
q0 = robot.get_dof_positions().numpy()[0].tolist()
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=60)
q1 = robot.get_dof_positions().numpy()[0].tolist()
t1 = float(tl.get_current_time())
tl.pause()
print("A1-REPORT roots=%s ndof=%d q0=%s q1=%s dt=%.3f"
      % (",".join(roots), len(q0), q0, q1, t1 - t0))
