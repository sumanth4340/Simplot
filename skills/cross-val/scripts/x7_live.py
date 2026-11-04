"""X7 cross-skill co-validation (runs INSIDE Isaac Sim): V7 scene, all lenses.

READ-ONLY snapshot (R11): no timeline writes, IsValid-gated reads.
stage lens:      all 7 V7 prims valid (incl. imu/contact children)
modeling lens:   cube size 1.2
physics lens:    mass 2.0, no-sleep True, report API present
sense lens:      cube world x (0.0), rig dome 300
"""
import omni.usd
from pxr import UsdGeom, UsdLux, UsdPhysics, PhysxSchema

stage = omni.usd.get_context().get_stage()
paths = ["/World/V7Ground", "/World/V7Cube", "/World/V7Dome",
         "/World/V7Cam", "/World/V7Cube/imu",
         "/World/V7Cube/contact", "/World/PhysicsScene"]
valid = [stage.GetPrimAtPath(p).IsValid() for p in paths]
allok = all(valid)
if allok:
    size = float(UsdGeom.Cube.Get(stage, "/World/V7Cube")
                 .GetSizeAttr().Get())
    mass = float(UsdPhysics.MassAPI.Get(stage, "/World/V7Cube")
                 .GetMassAttr().Get())
    dome = float(UsdLux.DomeLight.Get(stage, "/World/V7Dome")
                 .GetIntensityAttr().Get())
    nosleep = stage.GetPrimAtPath("/World/PhysicsScene").GetAttribute(
        "physxScene:disableSleeping").Get()
    report = stage.GetPrimAtPath("/World/V7Cube").HasAPI(
        PhysxSchema.PhysxContactReportAPI)
    tx = 0.0
    for op in UsdGeom.Xformable(
            stage.GetPrimAtPath("/World/V7Cube")).GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            tx = float(op.Get()[0])
else:
    size = mass = dome = tx = -1.0
    nosleep = report = False
print("X7-REPORT valid=%s size=%.2f mass=%.2f dome=%.1f nosleep=%s "
      "report=%s cubex=%.2f" % (allok, size, mass, dome, nosleep,
                                report, tx))
