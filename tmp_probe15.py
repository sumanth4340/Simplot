"""Probe 15 (runs INSIDE Isaac Sim): PhysxArticulationAPI attrs + V4 compare."""
import omni.usd
from pxr import PhysxSchema, UsdGeom

stage = omni.usd.get_context().get_stage()
tmp = UsdGeom.Xform.Define(stage, "/World/TmpArtProbe")
api = PhysxSchema.PhysxArticulationAPI.Apply(tmp.GetPrim())
print("ART-API-ATTRS:")
for a in tmp.GetPrim().GetAttributes():
    n = a.GetName()
    if "physx" in n.lower():
        print("  ", n, "=", a.Get())
print("---M2-HINGE-ATTRS---")
h1 = stage.GetPrimAtPath("/World/M2Bot/Hinge1")
for a in h1.GetAttributes():
    print("  ", a.GetName(), "=", a.Get())
stage.RemovePrim("/World/TmpArtProbe")
