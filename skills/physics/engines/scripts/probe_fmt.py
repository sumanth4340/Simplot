import isaacsim.core.experimental.utils.app as app_utils
app_utils.enable_extension("isaacsim.asset.importer.urdf")
await app_utils.update_app_async(steps=30)
from pxr import Usd, Sdf
print("FMTS=" + ",".join(sorted(Sdf.FileFormat.FindAllFileFormatExtensions())))
p = "C:/Users/sruja_ob3di74/action-reasoner/skills/physics/engines/evidence/p4_probe/p4_min.urdf"
try:
    s = Usd.Stage.Open(p)
    print("PLAIN-OPEN ok=" + str(bool(s)))
except Exception as e:
    print("PLAIN-OPEN fail=" + str(e)[:150])
