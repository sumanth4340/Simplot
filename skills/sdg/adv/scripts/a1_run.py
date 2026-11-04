"""A1 run (runs INSIDE Isaac Sim): 4-frame KITTI dataset.

KittiWriter with class mapping (default KITTI labels would mark
our classes unlabelled -> zeroed sem maps) + standard KITTI dir
names. detach_all guarded: it crashes on stale writers bound to
removed products (falls out silently afterwards).
"""
import os
import shutil

import omni.replicator.core as rep

OUT = "C:/Users/sruja_ob3di74/action-reasoner/skills/sdg/adv/evidence/a1_out"  # noqa
try:
    rep.WriterRegistry.detach_all()
except Exception as e:
    print("DETACH-ALL-SKIPPED", repr(e)[:120])
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)
rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.5))
rp = rep.create.render_product(cam, (320, 240))
kw = rep.WriterRegistry.get("KittiWriter")
# NOTE: mapping keys must be LOWERCASE: the writer lowercases
# class names ('kboxa'), so CamelCase keys never match and the
# semantic map comes out all-zero.
kw.initialize(output_dir=OUT, use_kitti_dir_names=True,
              omit_semantic_type=True,
              mapping_dict={"kboxa": (255, 0, 0, 255),
                            "kboxb": (0, 255, 0, 255)})
kw.attach(rp)
for i in range(4):
    await rep.orchestrator.step_async()
await rep.orchestrator.wait_until_complete_async()
print("NUM-WRITTEN", kw.num_written)
kw.detach()
n_img = n_lab = 0
for root, _ds, fs in os.walk(OUT):
    for f in fs:
        rel = os.path.relpath(os.path.join(root, f), OUT)
        rel = rel.replace("\\", "/")
        if rel.startswith("Camera/image_02") and f.endswith(".png"):
            n_img += 1
        if rel.startswith("Camera/label_02") and f.endswith(".txt"):
            n_lab += 1
print("A1-REPORT img=%d lab=%d" % (n_img, n_lab))
