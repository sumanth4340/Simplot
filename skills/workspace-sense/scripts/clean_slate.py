"""Clean slate (runs INSIDE Isaac Sim): remove every drill prim."""
import omni.usd

stage = omni.usd.get_context().get_stage()
paths = ["/World/SenseCube", "/World/JointCube", "/World/JointCyl",
         "/World/JointCube_Cyl", "/World/LiveCube", "/World/LiveGround",
         "/World/P1Cube", "/World/P1Ground", "/World/P2Cube",
         "/World/P2Ground", "/World/P3Base", "/World/P3Arm",
         "/World/P3Hinge", "/World/P3Ground", "/World/P4A", "/World/P4B",
         "/World/P4Ground", "/World/P5Cube", "/World/P5Ground",
         "/World/V1Cube", "/World/V1Ground", "/World/PhysicsScene"]
n = 0
for p in paths:
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
        n += 1
print("CLEAN-SLATE-OK removed=%d" % n)
