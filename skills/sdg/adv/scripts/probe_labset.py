# A2 label-set probe (INSIDE Isaac Sim): idToLabels + row count
# with the A2 camera pose.
import numpy as np
import omni.replicator.core as rep

rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.5, -4.5, 3.5), look_at=(0.0, 0.0, 0.4))
rp = rep.create.render_product(cam, (320, 240))
bb = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
bb.attach(rp)
await rep.orchestrator.step_async()
got = bb.get_data()
print("ID2LAB:", got["info"].get("idToLabels"))
print("PRIMS:", got["info"].get("primPaths"))
d = np.asarray(got["data"])
print("DATA-SHAPE:", d.shape)
if d.shape[0]:
    print("SEMIDS:", sorted(set(d[:, 0].astype(int).tolist())))
bb.detach(rp)
print("LABSET done")
