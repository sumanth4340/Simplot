"""S2 run (runs INSIDE Isaac Sim): bbox + semseg readback.

Same camera/RP framing as S1. bbox_2d_tight: dict data/info;
box (x_min,y_min,x_max,y_max) must have area>1000 and class
s2cube. semseg: dict with (240,320) uint32 + idToLabels; label
id 2 (s2cube) must own >100 pixels.
"""
import numpy as np
import omni.replicator.core as rep

rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.5))
rp = rep.create.render_product(cam, (320, 240))
bb = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
ss = rep.AnnotatorRegistry.get_annotator("semantic_segmentation")
bb.attach(rp)
ss.attach(rp)
await rep.orchestrator.step_async()
d = bb.get_data()
boxes = d["data"]
areas = [(b[3] - b[1]) * (b[4] - b[2]) for b in boxes]
cls = d["info"]["idToLabels"][str(boxes[0][0])]["class"] if boxes else "?"
paths = d["info"]["primPaths"]
s = ss.get_data()
uniq = np.unique(s["data"]).tolist()
npix2 = int((s["data"] == 2).sum())
print("S2-REPORT nbox=%d area=%d cls=%s path=%s uniq=%s npix2=%d" % (
    len(boxes), max(areas) if areas else 0, cls,
    paths[0] if paths else "?", uniq, npix2))
bb.detach(rp)
ss.detach(rp)
