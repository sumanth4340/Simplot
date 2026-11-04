import omni.replicator.core as rep
rep.WriterRegistry.detach_all()
cam = rep.create.camera()
with cam:
    rep.modify.pose(position=(4.0, -4.0, 3.0), look_at=(0.0, 0.0, 0.4))
rp = rep.create.render_product(cam, (320, 240))
t = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
lo = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_loose")
t.attach(rp)
lo.attach(rp)
await rep.orchestrator.step_async()
dt, dl = t.get_data(), lo.get_data()
print("TIGHT n=%d paths=%s" % (len(dt["data"]), dt["info"]["primPaths"]))
print("LOOSE n=%d paths=%s" % (len(dl["data"]), dl["info"]["primPaths"]))
