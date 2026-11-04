"""A1 Kitti probe (runs INSIDE Isaac Sim): init signature,
2-frame capture, output tree + one label file verbatim."""
import inspect
import os
import shutil

import omni.replicator.core as rep
import omni.usd
from pxr import UsdGeom, UsdLux, Gf

OUT = "C:/Users/sruja_ob3di74/action-reasoner/skills/sdg/adv/evidence/probe_kitti"  # noqa
kw = rep.WriterRegistry.get("KittiWriter")
print("KITTI-SIG", inspect.signature(kw.initialize))

stage = omni.usd.get_context().get_stage()
for p in ("/World/KDome", "/World/KGround", "/World/KCubeA",
          "/World/KCubeB"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
dome = UsdLux.DomeLight.Define(stage, "/World/KDome")
dome.GetIntensityAttr().Set(3000.0)
g = UsdGeom.Cube.Define(stage, "/World/KGround")
g.GetSizeAttr().Set(10.0)
UsdGeom.Xformable(g.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
for name, x in (("KCubeA", -0.8), ("KCubeB", 0.8)):
    c = UsdGeom.Cube.Define(stage, "/World/" + name)
    c.GetSizeAttr().Set(1.0)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(
        Gf.Vec3d(x, 0, 0.5))

from isaacsim.core.experimental.utils.semantics import add_labels
add_labels(stage.GetPrimAtPath("/World/KCubeA"), labels=["kboxA"])
add_labels(stage.GetPrimAtPath("/World/KCubeB"), labels=["kboxB"])

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
kw.initialize(output_dir=OUT)
kw.attach(rp)
for i in range(2):
    await rep.orchestrator.step_async()
await rep.orchestrator.wait_until_complete_async()
print("NUM-WRITTEN", kw.num_written)
try:
    _d = kw.get_data() or {}
    print("PAYLOAD-KEYS", sorted(_d.keys())[:20])
except Exception as e:
    print("PAYLOAD-ERR", repr(e)[:160])
kw.detach()
for root, _ds, fs in os.walk(OUT):
    for f in sorted(fs)[:12]:
        print("  FILE", os.path.relpath(os.path.join(root, f), OUT))
for root, _ds, fs in os.walk(OUT):
    for f in sorted(fs):
        if f.endswith(".txt"):
            p = os.path.join(root, f)
            print("LABEL-FILE", os.path.relpath(p, OUT))
            print(open(p).read()[:600])
            break
    else:
        continue
    break
print("KITTI-PROBE done")
