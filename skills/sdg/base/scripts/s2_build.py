"""S2 build (runs INSIDE Isaac Sim): semantic labeling.

Tags /World/S1Cube with class label 's2cube' (add_labels dedups,
safe to re-run). Reports labels on the prim.
"""
import omni.usd
from isaacsim.core.experimental.utils.semantics import (
    add_labels, get_labels)

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath("/World/S1Cube")
add_labels(prim, labels=["s2cube"])
print("S2-BUILD-OK labels=%s" % (get_labels(prim),))
