import numpy as np, warp as wp
import omni.graph.core as og
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import Articulation
og.get_graph_by_path("/World/V9Graph").set_disabled(True)
art = Articulation("/World/V9Bot/Base")
art.set_dof_position_targets(np.array([0.5], dtype=np.float32))
await app_utils.update_app_async(steps=60)
q = art.get_dof_positions()
q = q.numpy() if isinstance(q, wp.array) else np.asarray(q)
print("CMD-TEST q=%.4f" % float(np.asarray(q).flatten()[0]))
og.get_graph_by_path("/World/V9Graph").set_disabled(False)
