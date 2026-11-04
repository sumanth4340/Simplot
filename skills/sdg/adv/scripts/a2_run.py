"""A2 run (runs INSIDE Isaac Sim): seeded layout determinism.

Three 6-frame legs in one call (bridge --file takes no args):
seed 7, seed 7 again, seed 8. Per frame: rng cube poses + step +
tight-bbox read. Saves layouts_0/1/2.npy (6,3,4) to evidence.
"""
import os

import numpy as np
import omni.replicator.core as rep
import omni.usd
from pxr import UsdGeom, Gf

EVD = "C:/Users/sruja_ob3di74/action-reasoner/skills/sdg/adv/evidence"  # noqa
stage = omni.usd.get_context().get_stage()
try:
    rep.WriterRegistry.detach_all()
except Exception as e:
    print("DETACH-ALL-SKIPPED", repr(e)[:100])
rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.5, -4.5, 3.5), look_at=(0.0, 0.0, 0.4))
rp = rep.create.render_product(cam, (320, 240))
bb = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
bb.attach(rp)
# Warmup: on a fresh sim the annotator backend returns zero boxes
# until the renderer is warm (verified: 120 app updates, then 3
# boxes every step). Discard the warmup frames.
import isaacsim.core.experimental.utils.app as app_utils
await app_utils.update_app_async(steps=120)
await rep.orchestrator.step_async()
tops = [UsdGeom.Xformable(
    stage.GetPrimAtPath("/World/A2Cube%d" % i)).GetOrderedXformOps()[0]
    for i in range(3)]
# NOTE: no rep.set_global_seed here: it resets the replicator
# graph and detaches annotators (reads come back empty). np
# default_rng(seed) alone gives deterministic layouts.
for leg, seed in enumerate((7, 7, 8)):
    rng = np.random.default_rng(seed)
    lays = np.zeros((6, 3, 4), dtype=np.int32)
    for f in range(6):
        pos = rng.uniform(-2.0, 2.0, (3, 2))
        for i in range(3):
            tops[i].Set(Gf.Vec3d(float(pos[i, 0]), float(pos[i, 1]),
                                 0.4))
        # Two steps: the first absorbs the USD edit (render
        # catches up), the second yields readable boxes.
        await rep.orchestrator.step_async()
        await rep.orchestrator.step_async()
        got = bb.get_data()
        d = np.asarray(got["data"])
        id2lab = got["info"]["idToLabels"]
        # NOTE: data is a 1-D STRUCTURED array (fields
        # semId,x0,y0,x1,y1,...), not (N,5): index rows, not [:, i].
        rows = [(int(r[0]), int(r[1]), int(r[2]), int(r[3]),
                 int(r[4])) for r in d]
        ab = int([k for k, v in id2lab.items()
                  if "abox" in str(v)][0])
        rows = [r for r in rows if r[0] == ab]
        assert len(rows) == 3, "want 3 abox, got %d" % len(rows)
        lays[f] = np.array([r[1:5] for r in rows], dtype=np.int32)
    np.save(os.path.join(EVD, "a2_layouts_%d.npy" % leg), lays)
    print("A2-LEG %d seed=%d x0sum=%d" % (leg, seed, int(lays[:, :, 0].sum())))
bb.detach(rp)
print("A2-REPORT done")
