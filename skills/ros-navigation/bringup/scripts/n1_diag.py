import isaacsim.core.experimental.utils.app as app_utils
import numpy as np
from isaacsim.core.experimental.prims import Articulation
import omni.usd
st = omni.usd.get_context().get_stage()
art = [c.GetPath().pathString for c in st.GetPrimAtPath("/World").GetChildren()
       if c.GetName().startswith("N1Base")][0]
print("DIAG art=" + art)
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=10)
a = Articulation(art)
print("DIAG dofs=" + str(list(a.dof_names)))
print("DIAG v10=" + str(np.asarray(a.get_dof_velocities()).flatten().tolist()))
await app_utils.update_app_async(steps=50)
print("DIAG p60=" + str(np.asarray(a.get_dof_positions()).flatten().tolist()))
print("DIAG v60=" + str(np.asarray(a.get_dof_velocities()).flatten().tolist()))
jp = st.GetPrimAtPath(art + "/J_W_p18_p22")
print("DIAG axis=" + str(jp.GetAttribute("physics:axis").Get()))
print("DIAG b0=" + str(jp.GetRelationship("physics:body0").GetTargets()))
print("DIAG b1=" + str(jp.GetRelationship("physics:body1").GetTargets()))
app_utils.stop()
print("DIAG-DONE")
