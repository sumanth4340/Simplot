# A1 annotator probe (INSIDE Isaac Sim): do KittiWriter's
# annotators exist and return data here?
import omni.replicator.core as rep

for name in ("rgb", "bounding_box_2d_tight_fast",
             "bounding_box_2d_loose_fast", "instance_segmentation_fast",
             "distance_to_camera", "camera_params",
             "bounding_box_2d_tight"):
    try:
        a = rep.AnnotatorRegistry.get_annotator(name)
        print("HAVE", name, type(a))
    except Exception as e:
        print("MISS", name, repr(e)[:160])
print("ANNO-PROBE done")
