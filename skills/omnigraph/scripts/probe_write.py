import omni.usd
import omni.graph.core as og
stage = omni.usd.get_context().get_stage()
wp = stage.GetPrimAtPath("/World/O3Graph/Write")
for n in ("state:correctlySetup", "inputs:primPath", "inputs:name",
          "inputs:usePath", "inputs:value", "inputs:usdWriteBack"):
    a = wp.GetAttribute(n)
    print("W " + n + "=" + (str(a.Get())[:100] if a.IsValid() else "INVALID"))
try:
    print("LIVEVAL inputs:value=" + str(og.Controller.get("/World/O3Graph/Write.inputs:value"))[:120])
except Exception as e:
    print("LIVEVAL ERR " + repr(e)[:120])
