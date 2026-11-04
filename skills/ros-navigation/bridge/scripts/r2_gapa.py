import isaacsim.core.experimental.utils.app as app_utils
import numpy as np
from isaacsim.core.experimental.prims import Articulation
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=60)
a = Articulation("/World/R2Bot")
p = np.asarray(a.get_dof_positions()).flatten().tolist()
print("GAP-A=%s (left playing)" % p)
