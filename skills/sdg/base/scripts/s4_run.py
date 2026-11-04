"""S4 run (runs INSIDE Isaac Sim): scripted variation capture.

Moves S1Cube to x=-1.5/0/+1.5, one bbox read per pose (direct
annotator). Deterministic scripted variation (no RNG): box
x_min must be strictly monotonic with spread > 50px. Cube
restored to x=0 after. detach_all hygiene (R4).
"""
import omni.usd
import omni.replicator.core as rep
from pxr import UsdGeom, Gf

stage = omni.usd.get_context().get_stage()
rep.WriterRegistry.detach_all()
rep.orchestrator.set_capture_on_play(False)
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.5))
rp = rep.create.render_product(cam, (320, 240))
bb = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
bb.attach(rp)
prim = stage.GetPrimAtPath("/World/S1Cube")
top = UsdGeom.Xformable(prim).GetOrderedXformOps()[0]
xs, boxes = [], []
for x in (-1.5, 0.0, 1.5):
    top.Set(Gf.Vec3d(x, 0, 0.5))
    await rep.orchestrator.step_async()
    b = bb.get_data()["data"][0]
    xs.append(x)
    boxes.append((int(b[1]), int(b[2]), int(b[3]), int(b[4])))
top.Set(Gf.Vec3d(0, 0, 0.5))
bb.detach(rp)
print("S4-REPORT xmins=%d,%d,%d areas=%d,%d,%d" % (
    boxes[0][0], boxes[1][0], boxes[2][0],
    (boxes[0][2] - boxes[0][0]) * (boxes[0][3] - boxes[0][1]),
    (boxes[1][2] - boxes[1][0]) * (boxes[1][3] - boxes[1][1]),
    (boxes[2][2] - boxes[2][0]) * (boxes[2][3] - boxes[2][1])))
