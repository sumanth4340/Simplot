import isaacsim.core.experimental.utils.app as app_utils
import asyncio
import numpy as np
from isaacsim.core.experimental.prims import Articulation
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=10)
Articulation('/World/R2Bot').set_dof_velocity_targets(np.array([[1.0, 0.0]]))
await app_utils.update_app_async(steps=50)
a = Articulation('/World/R2Bot')
pa = np.asarray(a.get_dof_positions()).flatten().tolist()
await asyncio.sleep(6)
pb = np.asarray(a.get_dof_positions()).flatten().tolist()
vb = np.asarray(a.get_dof_velocities()).flatten().tolist()
print("PA=%s PB=%s VB=%s" % (pa, pb, vb))
app_utils.stop()
print('DIAG-DONE')
