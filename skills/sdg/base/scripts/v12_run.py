"""V12 run (runs INSIDE Isaac Sim): 3-pose multi-modal capture.

One camera re-posed 3x ((4,-4,3), (-4,-4,3), (0,-5,2.5),
look_at origin). BasicWriter bbox + direct rgb/semseg reads
saved per frame to v12_out/. Reports per-frame boxes, class
pixel counts (ids resolved from info), rgb means.
"""
import os
import shutil
import numpy as np
import omni.replicator.core as rep

OUT = "C:/Users/sruja_ob3di74/action-reasoner/skills/sdg/base/evidence/v12_out"
rep.WriterRegistry.detach_all()
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)
rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
rp = rep.create.render_product(cam, (320, 240))
bw = rep.WriterRegistry.get("BasicWriter")
bw.initialize(output_dir=OUT, rgb=False, bounding_box_2d_tight=True)
bw.attach(rp)
rgb = rep.AnnotatorRegistry.get_annotator("rgb")
seg = rep.AnnotatorRegistry.get_annotator("semantic_segmentation")
box = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
rgb.attach(rp)
seg.attach(rp)
box.attach(rp)
POSES = [(4.0, -4.0, 3.0), (-4.0, -4.0, 3.0), (0.0, -5.0, 2.5)]
reps = []
for i, pos in enumerate(POSES):
    with cam:
        rep.modify.pose(position=pos, look_at=(0.0, 0.0, 0.4))
    await rep.orchestrator.step_async()
    r = np.asarray(rgb.get_data())
    s = seg.get_data()
    b = box.get_data()
    np.save(os.path.join(OUT, "rgb_%04d.npy" % i), r)
    np.save(os.path.join(OUT, "sem_%04d.npy" % i), np.asarray(s["data"]))
    id2c = {int(k): v["class"] for k, v in s["info"]["idToLabels"].items()}
    px = {c: int((np.asarray(s["data"]) == j).sum())
          for j, c in id2c.items()}
    nbox = len(b["data"])
    cls = sorted(b["info"]["idToLabels"][str(t[0])]["class"] for t in b["data"])
    reps.append("f%d:nbox=%d,cls=%s,pxa=%d,pxb=%d,mean=%.1f" % (
        i, nbox, "+".join(cls), px.get("v12a", 0), px.get("v12b", 0),
        r.mean()))
await rep.orchestrator.wait_until_complete_async()
bw.detach()
rgb.detach(rp)
seg.detach(rp)
box.detach(rp)
print("V12-REPORT " + " ".join(reps))
