import os, shutil
import omni.replicator.core as rep
OUT = "C:/Users/sruja_ob3di74/action-reasoner/skills/sdg/base/evidence/probe_bw"
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
for _ in range(2):
    await rep.orchestrator.step_async()
await rep.orchestrator.wait_until_complete_async()
bw.detach()
print("FILES=" + ",".join(sorted(os.listdir(OUT))))
