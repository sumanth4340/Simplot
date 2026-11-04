import isaacsim.core.experimental.utils.app as app_utils
import omni.usd
from isaacsim.core.experimental.prims import Articulation
st = omni.usd.get_context().get_stage()
jp = st.GetPrimAtPath("/World/R2Bot/J1")
drv = {a.GetName(): a.Get() for a in jp.GetAttributes()
       if "drive" in a.GetName()}
print("DRV=" + str(drv))
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=30)
import numpy as np
a = Articulation("/World/R2Bot")
p0 = np.asarray(a.get_dof_positions()).flatten().tolist()
v0 = np.asarray(a.get_dof_velocities()).flatten().tolist()
await app_utils.update_app_async(steps=60)
p1 = np.asarray(a.get_dof_positions()).flatten().tolist()
v1 = np.asarray(a.get_dof_velocities()).flatten().tolist()
app_utils.stop()
print("P0=%s V0=%s P1=%s V1=%s" % (p0, v0, p1, v1))
