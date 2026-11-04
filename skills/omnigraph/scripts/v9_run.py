"""V9 run (runs INSIDE Isaac Sim): exam execution.

Revive-touch (R6) -> play 30: t1~3.5, q1 tracks -> disable ->
play 60: t2==t1 frozen -> enable -> play 60: t3~13.5 catch-up,
q3 tracks t3. Composes O2 chain + O3 motion + O4 disable.
"""
import numpy as np
import warp as wp
import omni.usd
import omni.graph.core as og
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import Articulation

stage = omni.usd.get_context().get_stage()
HP = "/World/V9Bot/Hinge1"
GP = "/World/V9Graph"
keys = og.Controller.Keys
SUM = GP + "/Add.outputs:sum"
VAL = GP + "/Write.inputs:value"


def _tgt():
    return float(stage.GetPrimAtPath(HP).GetAttribute(
        "drive:angular:physics:targetPosition").Get())


def _q():
    art = Articulation("/World/V9Bot/Base")
    q = art.get_dof_positions()
    return float(np.asarray(
        q.numpy() if isinstance(q, wp.array) else q).flatten()[0])


app_utils.stop()
await app_utils.update_app_async(steps=10)
app_utils.play(commit=True)
og.Controller.edit(GP, {keys.DISCONNECT: [(SUM, VAL)]})
og.Controller.edit(GP, {keys.CONNECT: [(SUM, VAL)]})
await app_utils.update_app_async(steps=30)
t1, q1 = _tgt(), _q()
g = og.get_graph_by_path(GP)
g.set_disabled(True)
d_off = g.is_disabled()
await app_utils.update_app_async(steps=60)
t2 = _tgt()
g.set_disabled(False)
d_on = g.is_disabled()
await app_utils.update_app_async(steps=60)
t3, q3 = _tgt(), _q()
print("V9-REPORT t1=%.3f t2=%.3f t3=%.3f frozen=%.4f resumed=%.3f "
      "q1=%.4f q3=%.4f dis=%s en=%s" % (
          t1, t2, t3, t2 - t1, t3 - t2, q1, q3, d_off, d_on))
