"""A3 probe (runs INSIDE Isaac Sim): extension + settings state."""
import carb.settings
import omni.kit.app

mgr = omni.kit.app.get_app().get_extension_manager()
py = mgr.is_extension_enabled("isaacsim.code_editor.python_server")
bogus = mgr.is_extension_enabled("no.such.extension-0.0.0")
n = len(mgr.get_extensions())
s = carb.settings.get_settings()
s.set("/app/muse_drill_probe", "hello-a3")
echo = s.get("/app/muse_drill_probe")
print("A3-REPORT pyserver=%s bogus=%s count=%d echo=%s" % (
    py, bogus, n, echo))
