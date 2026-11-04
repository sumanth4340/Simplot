import omni.usd
import omni.replicator.core as rep
from pxr import UsdGeom
stage = omni.usd.get_context().get_stage()
UsdGeom.Imageable(stage.GetPrimAtPath("/World/S1Cube")).MakeInvisible()
rep.WriterRegistry.detach_all()
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.4))
rp = rep.create.render_product(cam, (320, 240))
t = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
t.attach(rp)
await rep.orchestrator.step_async()
d = t.get_data()
print("NOHIDE-TEST n=%d paths=%s" % (len(d["data"]), d["info"]["primPaths"]))
UsdGeom.Imageable(stage.GetPrimAtPath("/World/S1Cube")).MakeVisible()
