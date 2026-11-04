# A3 join probe (INSIDE Isaac Sim): remove A2 cubes, add 2 new
# abox cubes, read bbox. Decides instance-freeze vs class-freeze.
import numpy as np
import omni.replicator.core as rep
import omni.usd
from pxr import UsdGeom, Gf

from isaacsim.core.experimental.utils.semantics import add_labels

stage = omni.usd.get_context().get_stage()
for i in range(3):
    p = "/World/A2Cube%d" % i
    if stage.GetPrimAtPath(p).IsValid():
        stage.RemovePrim(p)
for i, x in enumerate((-1.0, 1.0)):
    c = UsdGeom.Cube.Define(stage, "/World/A3Cube%d" % i)
    c.GetSizeAttr().Set(0.8)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(
        Gf.Vec3d(x, 0, 0.4))
    add_labels(stage.GetPrimAtPath("/World/A3Cube%d" % i),
               labels=["abox"])

rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.5, -4.5, 3.5), look_at=(0.0, 0.0, 0.4))
rp = rep.create.render_product(cam, (320, 240))
bb = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
bb.attach(rp)
await rep.orchestrator.step_async()
await rep.orchestrator.step_async()
got = bb.get_data()
d = np.asarray(got["data"])
print("JOIN shape=%s id2lab=%s" % (d.shape, got["info"]["idToLabels"]))
bb.detach(rp)
print("JOIN done")
