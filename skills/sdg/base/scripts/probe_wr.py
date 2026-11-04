import os, shutil
import numpy as np
import omni.replicator.core as rep
OUT = "C:/Users/sruja_ob3di74/action-reasoner/skills/sdg/base/evidence/probe_w"
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)
rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.5))
rp = rep.create.render_product(cam, (320, 240))
ann = rep.AnnotatorRegistry.get_annotator("rgb")
ann.attach(rp)
writer = rep.WriterRegistry.get("BasicWriter")
writer.initialize(output_dir=OUT, rgb=True)
writer.attach(rp)
for i in range(5):
    await rep.orchestrator.step_async()
    d = np.asarray(ann.get_data())
    print("STEP%d direct_mean=%.2f" % (i, d.mean()))
await rep.orchestrator.wait_until_complete_async()
writer.detach()
ann.detach(rp)
print("FILES=" + ",".join(sorted(os.listdir(OUT))))
