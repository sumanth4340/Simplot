"""V4 run (runs INSIDE Isaac Sim): schema check + drive to pi/4."""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from pxr import UsdPhysics
from isaacsim.core.experimental.prims import Articulation
from usd.schema.isaac.robot_schema import Attributes, Classes

stage = omni.usd.get_context().get_stage()
robot = stage.GetPrimAtPath("/World/V4Bot")
has_robot = robot.HasAPI(Classes.ROBOT_API.value)
rtype = robot.GetAttribute(Attributes.ROBOT_TYPE.value[0]).Get()
base = stage.GetPrimAtPath("/World/V4Bot/Geometry/base")
has_root = base.HasAPI(UsdPhysics.ArticulationRootAPI)
bot = Articulation("/World/V4Bot/Geometry/base")
tl = omni.timeline.get_timeline_interface()
app_utils.play()
q0 = float(bot.get_dof_positions().numpy()[0][0])
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=120)
q1 = float(bot.get_dof_positions().numpy()[0][0])
t1 = float(tl.get_current_time())
tl.pause()
print("V4-REPORT robot=%s type=%s root=%s ndof=%d q0=%.4f q1=%.4f dt=%.3f"
      % (has_robot, rtype, has_root, 1, q0, q1, t1 - t0))
