"""S2 delete prims (runs INSIDE Isaac Sim)."""
import omni.usd

stage = omni.usd.get_context().get_stage()
n = 0
for p in ("S2_Cube", "S2_Sphere", "S2_Cyl", "S2_Cone", "S2_Plane", "S2_Mesh"):
    o = stage.GetPrimAtPath("/World/" + p)
    if o and o.IsValid():
        stage.RemovePrim("/World/" + p)
        n += 1
print("S2-DELETE-OK removed=%d" % n)
