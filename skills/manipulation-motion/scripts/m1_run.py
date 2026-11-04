"""M1 run (runs INSIDE Isaac Sim): site/target offset at rest, 60 steps."""
import numpy as np
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.experimental.utils import xform as xform_utils

stage = omni.usd.get_context().get_stage()
site_prim = stage.GetPrimAtPath("/World/M1Bot/Link2/GraspSite")
has_api = site_prim.HasAPI("IsaacSiteAPI")
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=5)
robot = Articulation("/World/M1Bot/Base")
await app_utils.update_app_async(steps=60)
q = robot.get_dof_positions().numpy()[0].tolist()
import warp as wp


def _vec(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return [float(v) for v in np.asarray(a).flatten()]


sp, _ = xform_utils.get_world_pose("/World/M1Bot/Link2/GraspSite")
tp, _ = xform_utils.get_world_pose("/World/M1Target")
sp, tp = _vec(sp), _vec(tp)
dist = ((sp[0] - tp[0]) ** 2 + (sp[1] - tp[1]) ** 2
        + (sp[2] - tp[2]) ** 2) ** 0.5
omni.timeline.get_timeline_interface().pause()
print("M1-REPORT site=[%.4f,%.4f,%.4f] target=[%.4f,%.4f,%.4f] "
      "dist=%.4f ndof=%d q=%s site_api=%s"
      % (sp[0], sp[1], sp[2], tp[0], tp[1], tp[2], dist,
         len(q), q, has_api))
