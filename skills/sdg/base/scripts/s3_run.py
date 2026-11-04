"""S3 run (runs INSIDE Isaac Sim): capture RGB + bbox to disk.

BasicWriter for bbox (proven) + DIRECT rgb annotator reads saved
in-script (S1 pattern). Custom Writer with get_data()+np.save in
write() killed the whole capture (R4) — never again.
WriterRegistry.detach_all() first: stale writers survive sends.
"""
import os
import shutil
import numpy as np
import omni.replicator.core as rep

OUT = "C:/Users/sruja_ob3di74/action-reasoner/skills/sdg/base/evidence/s3_out"
rep.WriterRegistry.detach_all()
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)
rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.5))
rp = rep.create.render_product(cam, (320, 240))
bw = rep.WriterRegistry.get("BasicWriter")
bw.initialize(output_dir=OUT, rgb=False, bounding_box_2d_tight=True)
bw.attach(rp)
ann = rep.AnnotatorRegistry.get_annotator("rgb")
ann.attach(rp)
for i in range(3):
    await rep.orchestrator.step_async()
    np.save(os.path.join(OUT, "direct_rgb_%04d.npy" % i),
            np.asarray(ann.get_data()))
await rep.orchestrator.wait_until_complete_async()
bw.detach()
ann.detach(rp)
files = os.listdir(OUT)
n_rgb = len([f for f in files if f.startswith("direct_rgb_")])
n_bb = len([f for f in files
            if f.startswith("bounding_box_2d_tight_")
            and f.endswith(".npy")])
print("S3-REPORT rgb_files=%d bbox_files=%d" % (n_rgb, n_bb))
