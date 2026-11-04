# R1 ext (INSIDE Isaac Sim): check nv sensor backend extensions +
# renderer state.
import carb
import omni.kit.app

em = omni.kit.app.get_app().get_extension_manager()
for name in ("omni.sensors.nv.radar", "omni.sensors.nv.lidar",
             "omni.sensors.nv.acoustic",
             "isaacsim.sensors.experimental.rtx",
             "omni.replicator.core"):
    print("EXT %s enabled=%s" % (name, em.is_extension_enabled(name)))
s = carb.settings.get_settings()
for k in ("/renderer/active", "/rtx/rendermode",
          "/renderer/raytracingMotion/enabled",
          "/app/renderer/activeRaytracer"):
    try:
        print("SET %s = %s" % (k, s.get(k)))
    except Exception as e:
        print("SET %s ERR" % k)
print("R1-EXT done")
