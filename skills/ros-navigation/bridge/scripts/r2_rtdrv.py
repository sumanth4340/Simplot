import isaacsim.core.experimental.utils.app as app_utils
import numpy as np
from isaacsim.core.experimental.prims import Articulation
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=10)
a = Articulation("/World/R2Bot")
a.set_dof_velocity_targets(np.array([[1.0, 0.0]]))
p0 = np.asarray(a.get_dof_positions()).flatten().tolist()
await app_utils.update_app_async(steps=60)
p1 = np.asarray(a.get_dof_positions()).flatten().tolist()
v1 = np.asarray(a.get_dof_velocities()).flatten().tolist()
app_utils.stop()
print("P0=%s P1=%s V1=%s" % (p0, p1, v1))
