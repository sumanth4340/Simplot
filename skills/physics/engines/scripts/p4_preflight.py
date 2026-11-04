"""P4 preflight (runs INSIDE Isaac Sim): conversion preflight drill.

Full two-pass conversion is blocked on 6.0.0 (R5: no
physx_to_mjc profile; R6: no URDF Sdf plugin for the manager).
P4 drills the shippable piece: the conversion skill's PREFLIGHT
(pure offline-USD reads). Builds a CLEAN asset (0 warnings) and
a DIRTY asset (5 seeded traits), runs the mirrored checks.
"""
import os
import shutil
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, PhysxSchema

EVD = "C:/Users/sruja_ob3di74/action-reasoner/skills/physics/engines/evidence/p4_pre"
shutil.rmtree(EVD, ignore_errors=True)
os.makedirs(EVD, exist_ok=True)


def _clean(path):
    stage = Usd.Stage.CreateNew(path)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/arm").GetPrim()
    stage.SetDefaultPrim(root)
    UsdPhysics.ArticulationRootAPI.Apply(root)
    for name, z in (("base", 0.0), ("l1", 0.2)):
        link = UsdGeom.Xform.Define(stage, f"/arm/{name}")
        link.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, z))
        UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
        UsdPhysics.MassAPI.Apply(link.GetPrim()).CreateMassAttr(1.0)
        cube = UsdGeom.Cube.Define(stage, f"/arm/{name}/geom")
        cube.CreateSizeAttr(0.1)
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    j = UsdPhysics.RevoluteJoint.Define(stage, "/arm/j1")
    j.CreateAxisAttr("Y")
    j.CreateBody0Rel().SetTargets([Sdf.Path("/arm/base")])
    j.CreateBody1Rel().SetTargets([Sdf.Path("/arm/l1")])
    stage.Save()


def _dirty(path):
    stage = Usd.Stage.CreateNew(path)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/arm").GetPrim()
    stage.SetDefaultPrim(root)
    UsdPhysics.ArticulationRootAPI.Apply(root)
    link = UsdGeom.Xform.Define(stage, "/arm/base")
    UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
    # zero-size collider
    zc = UsdGeom.Cube.Define(stage, "/arm/base/zero")
    zc.CreateSizeAttr(0.0)
    UsdPhysics.CollisionAPI.Apply(zc.GetPrim())
    # negative-scale collider
    neg = UsdGeom.Xform.Define(stage, "/arm/mirror")
    neg.AddScaleOp().Set(Gf.Vec3f(-1.0, 1.0, 1.0))
    nc = UsdGeom.Cube.Define(stage, "/arm/mirror/geom")
    nc.CreateSizeAttr(0.1)
    UsdPhysics.CollisionAPI.Apply(nc.GetPrim())
    # mass+density without inertia
    mm = UsdGeom.Xform.Define(stage, "/arm/heavy")
    UsdPhysics.RigidBodyAPI.Apply(mm.GetPrim())
    ma = UsdPhysics.MassAPI.Apply(mm.GetPrim())
    ma.CreateMassAttr(2.0)
    ma.CreateDensityAttr(500.0)
    # pre-existing mjc:ref
    jr = UsdPhysics.RevoluteJoint.Define(stage, "/arm/jref").GetPrim()
    jr.CreateAttribute("mjc:ref", Sdf.ValueTypeNames.Float).Set(1.0)
    # orphan joint (no articulation root above)
    o1 = UsdGeom.Xform.Define(stage, "/stray/a")
    o2 = UsdGeom.Xform.Define(stage, "/stray/b")
    UsdPhysics.RigidBodyAPI.Apply(o1.GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(o2.GetPrim())
    oj = UsdPhysics.RevoluteJoint.Define(stage, "/stray/j")
    oj.CreateBody0Rel().SetTargets([Sdf.Path("/stray/a")])
    oj.CreateBody1Rel().SetTargets([Sdf.Path("/stray/b")])
    stage.Save()


def _preflight(input_path):
    stage = Usd.Stage.Open(input_path)
    hits = set()
    if UsdGeom.GetStageMetersPerUnit(stage) != 1.0:
        hits.add("units")
    cache = UsdGeom.XformCache()
    for prim in stage.Traverse():
        schemas = prim.GetAppliedSchemas()
        if prim.IsA(UsdPhysics.Joint) and not any(
            stage.GetPrimAtPath(p).HasAPI(UsdPhysics.ArticulationRootAPI)
                for p in prim.GetPath().GetPrefixes()):
            hits.add("orphan")
        ref = prim.GetAttribute("mjc:ref") \
            if prim.IsA(UsdPhysics.RevoluteJoint) else None
        if ref and ref.HasAuthoredValue() and ref.Get():
            hits.add("ref")
        if "PhysicsMassAPI" in schemas:
            ma = UsdPhysics.MassAPI(prim)
            if ma.GetMassAttr().HasAuthoredValue() \
                    and ma.GetDensityAttr().HasAuthoredValue() \
                    and not ma.GetDiagonalInertiaAttr().HasAuthoredValue():
                hits.add("inertia")
        if "PhysicsCollisionAPI" not in schemas:
            continue
        if cache.GetLocalToWorldTransform(prim).GetDeterminant() < 0:
            hits.add("negscale")
        dims = {"Cube": ["size"]}.get(prim.GetTypeName(), [])
        if any(prim.GetAttribute(d).Get() == 0 for d in dims):
            hits.add("zerosize")
    return sorted(hits)


_clean(EVD + "/clean.usda")
_dirty(EVD + "/dirty.usda")
print("P4-REPORT clean=%s dirty=%s" % (
    _preflight(EVD + "/clean.usda"), _preflight(EVD + "/dirty.usda")))
