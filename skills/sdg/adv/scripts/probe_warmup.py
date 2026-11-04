# A2 warmup probe (INSIDE Isaac Sim): full renderer warmup
# (120 app updates) + 5 orchestrator steps, then bbox read.
import isaacsim.core.experimental.utils.app as app_utils
import numpy as np
import omni.replicator.core as rep

rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.5, -4.5, 3.5), look_at=(0.0, 0.0, 0.4))
rp = rep.create.render_product(cam, (320, 240))
bb = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
rgb = rep.AnnotatorRegistry.get_annotator("rgb")
bb.attach(rp)
rgb.attach(rp)
await app_utils.update_app_async(steps=120)
for i in range(5):
    await rep.orchestrator.step_async()
    d = np.asarray(bb.get_data()["data"])
    r = np.asarray(rgb.get_data())
    print("STEP %d boxes=%s rgbmean=%.1f" % (i, d.shape, float(r.mean())))
bb.detach(rp)
rgb.detach(rp)
print("WARMUP done")
