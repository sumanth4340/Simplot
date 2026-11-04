import numpy as np
import omni.usd
import omni.replicator.core as rep
from isaacsim.core.experimental.utils.semantics import add_labels
stage = omni.usd.get_context().get_stage()
add_labels(stage.GetPrimAtPath("/World/S1Cube"), labels=["s2cube"])
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
print("BBTYPE=" + type(d).__name__)
if isinstance(d, dict):
    print("BBKEYS=" + ",".join(sorted(d.keys())))
    print("BBDATA=" + str(d.get("data"))[:300])
    print("BBINFO=" + str(d.get("info"))[:300])
s = np.asarray(ss.get_data())
print("SSHAPE=%s uniq=%s" % (s.shape, np.unique(s).tolist()[:8]))
