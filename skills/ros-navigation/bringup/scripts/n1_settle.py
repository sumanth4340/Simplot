# Settle it: PhysicsScene? chassis end pose? gravity?
import omni.usd
from pxr import UsdGeom

st = omni.usd.get_context().get_stage()
print("SCENE", st.GetPrimAtPath("/World/PhysicsScene").IsValid())
print("UP", UsdGeom.GetStageUpAxis(st))
arts = [c.GetName() for c in st.GetPrimAtPath("/World").GetChildren()
        if c.GetName().startswith("N1Base")]
print("ARTS", arts)
for a in arts:
    ch = st.GetPrimAtPath("/World/" + a + "/chassis")
    if ch.IsValid():
        m = UsdGeom.Xformable(ch).ComputeLocalToWorldTransform(0)
        print("CHASSIS", a, "world-pos",
              [round(m.ExtractTranslation()[i], 4) for i in range(3)])
    g = st.GetPrimAtPath("/World/N1Ground/geo")
    if g.IsValid():
        m = UsdGeom.Xformable(g).ComputeLocalToWorldTransform(0)
        print("GROUND-CENTER", [round(m.ExtractTranslation()[i], 4)
                                for i in range(3)])
print("SETTLE done")
