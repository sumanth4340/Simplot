"""Probe quat order (runs INSIDE Isaac Sim)."""
import numpy as np
import warp as wp
from isaacsim.core.experimental.utils import xform as xform_utils


def _q(p):
    _, q = xform_utils.get_world_pose(p)
    if isinstance(q, wp.array):
        q = q.numpy()
    return np.asarray(q, dtype=float).flatten().tolist()


print("BASE(unrotated)=", _q("/World/M4Bot/Base"))
print("LINK2(tilted?)=", _q("/World/M4Bot/Link2"))
print("BLOCK=", _q("/World/M4Block"))
