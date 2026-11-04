"""Probe RP (runs INSIDE Isaac Sim): RigidPrim tensor poses live?"""
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import RigidPrim
from isaacsim.core.experimental.utils import xform as xform_utils


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float)


app_utils.play()
await app_utils.update_app_async(steps=10)
rp = RigidPrim("/World/M4Bot/Link2")
try:
    p, q = rp.get_world_poses()
    print("TENSOR-P=", _w(p).tolist(), "TENSOR-Q=", _w(q).tolist())
except Exception as e:
    print("TENSOR-ERR=", repr(e)[:300])
u, _ = xform_utils.get_world_pose("/World/M4Bot/Link2")
print("USD-P=", _w(u).tolist())
rb = RigidPrim("/World/M4Block")
try:
    pb, qb = rb.get_world_poses()
    print("BLOCK-P=", _w(pb).tolist())
except Exception as e:
    print("BLOCK-ERR=", repr(e)[:300])
omni.timeline.get_timeline_interface().pause()
