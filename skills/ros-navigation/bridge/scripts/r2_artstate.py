import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import Articulation
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=60)
a = Articulation("/World/R2Bot")
await app_utils.update_app_async(steps=5)
out = {"ndof": int(a.num_dofs),
       "pos": [float(x) for x in a.joint_positions],
       "names": [str(x) for x in a.joint_names]}
app_utils.stop()
print("ARTSTATE=" + str(out))
