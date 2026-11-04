import omni.replicator.core as rep
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.5))
rp = rep.create.render_product(cam, (320, 240))
ann = rep.AnnotatorRegistry.get_annotator("rgb")
ann.attach(rp)
await rep.orchestrator.step_async()
import numpy as np
d = np.asarray(ann.get_data())
print("PROBE shape=%s dtype=%s mean=%.2f" % (d.shape, d.dtype, d.mean()))
