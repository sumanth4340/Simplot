"""O4 run (runs INSIDE Isaac Sim): graph enable/disable.

Play 30 (t1 live) -> set_disabled(True) -> play 60 (t2 frozen,
t2==t1) -> set_disabled(False) -> play 60 (t3 catch-up, t3-t2~20:
10 missed + 10 new; world clock runs while graph is off).
Uses first-class Graph.set_disabled (R7); link surgery does NOT
disable (exec cut: R5 data-flow firing; value cut: silent no-op).
R6 revive-touch still required on recreated paths.
"""
import omni.usd
import omni.graph.core as og
import isaacsim.core.experimental.utils.app as app_utils

stage = omni.usd.get_context().get_stage()
HP = "/World/O4Bot/Hinge1"
GP = "/World/O4Graph"
keys = og.Controller.Keys
PROD = GP + "/Mul.outputs:product"
VAL = GP + "/Write.inputs:value"


def _tgt():
    return float(stage.GetPrimAtPath(HP).GetAttribute(
        "drive:angular:physics:targetPosition").Get())


app_utils.stop()
await app_utils.update_app_async(steps=10)
app_utils.play(commit=True)
# R6 revive: a recreated graph path stays dead until the value link
# is re-touched (proven 3/3).
og.Controller.edit(GP, {keys.DISCONNECT: [(PROD, VAL)]})
og.Controller.edit(GP, {keys.CONNECT: [(PROD, VAL)]})
await app_utils.update_app_async(steps=30)
t1 = _tgt()
g = og.get_graph_by_path(GP)
g.set_disabled(True)
d_off = g.is_disabled()
await app_utils.update_app_async(steps=60)
t2 = _tgt()
g.set_disabled(False)
d_on = g.is_disabled()
await app_utils.update_app_async(steps=60)
t3 = _tgt()
print("O4-REPORT t1=%.3f t2=%.3f t3=%.3f frozen=%.4f resumed=%.3f "
      "dis=%s en=%s" % (t1, t2, t3, t2 - t1, t3 - t2, d_off, d_on))
