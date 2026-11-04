"""VA exam (runs INSIDE Isaac Sim): 12-frame re-sweep exam.

Same A3 scene/instances (R5: no new labels/instances mid-sim),
new seed (99), fresh KittiWriter attach after A3's detach.
Proves re-sweep + writer re-attach on a live stage.
"""
import os
import shutil
import time

import isaacsim.core.experimental.utils.app as app_utils
import numpy as np
import omni.replicator.core as rep
import omni.usd
from pxr import UsdGeom, Gf

OUT = "C:/Users/sruja_ob3di74/action-reasoner/skills/sdg/adv/evidence/va_out"  # noqa
N = 12
stage = omni.usd.get_context().get_stage()
try:
    rep.WriterRegistry.detach_all()
except Exception as e:
    print("DETACH-ALL-SKIPPED", repr(e)[:100])
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)
rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.5, -4.5, 3.5), look_at=(0.0, 0.0, 0.4))
rp = rep.create.render_product(cam, (320, 240))
kw = rep.WriterRegistry.get("KittiWriter")
kw.initialize(output_dir=OUT, use_kitti_dir_names=True,
              omit_semantic_type=True,
              mapping_dict={"abox": (0, 0, 255, 255)})
# NOTE: attach AFTER warmup: the warmup step would otherwise
# write frame 0 (51 files for a 50-frame sweep).
await app_utils.update_app_async(steps=120)
await rep.orchestrator.step_async()
kw.attach(rp)
tops = [UsdGeom.Xformable(
    stage.GetPrimAtPath("/World/A3Cube%d" % i)).GetOrderedXformOps()[0]
    for i in range(2)]
rng = np.random.default_rng(99)
t0 = time.time()
for f in range(N):
    pos = rng.uniform(-2.0, 2.0, (2, 2))
    for i in range(2):
        tops[i].Set(Gf.Vec3d(float(pos[i, 0]), float(pos[i, 1]), 0.4))
    await rep.orchestrator.step_async()
await rep.orchestrator.wait_until_complete_async()
dt = time.time() - t0
print("NUM-WRITTEN", kw.num_written)
kw.detach()
n_img = n_lab = 0
for root, _ds, fs in os.walk(OUT):
    for fn in fs:
        rel = os.path.relpath(os.path.join(root, fn), OUT)
        rel = rel.replace("\\", "/")
        if rel.startswith("Camera/image_02") and fn.endswith(".png"):
            n_img += 1
        if rel.startswith("Camera/label_02") and fn.endswith(".txt"):
            n_lab += 1
print("VA-REPORT img=%d lab=%d wall_s=%.0f fps=%.2f"
      % (n_img, n_lab, dt, N / dt))
