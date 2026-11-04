"""S1 run (runs INSIDE Isaac Sim): RGB annotator readback.

rep camera (posed via with-context) -> render product 320x240 ->
rgb annotator -> step_async -> read (240,320,4) uint8, mean>30.
"""
import numpy as np
import omni.replicator.core as rep

rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.5))
rp = rep.create.render_product(cam, (320, 240))
ann = rep.AnnotatorRegistry.get_annotator("rgb")
ann.attach(rp)
await rep.orchestrator.step_async()
d = np.asarray(ann.get_data())
print("S1-REPORT shape=%dx%dx%d dtype=%s mean=%.2f max=%d" % (
    d.shape[0], d.shape[1], d.shape[2], d.dtype, d.mean(), d.max()))
ann.detach(rp)
