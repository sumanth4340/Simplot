"""P4 convert (runs INSIDE Isaac Sim): convert + audit, in-session.

Standalone python.bat self-test hangs on this 4GB GPU alongside
the live sim (R3), and convert_physx_to_newton.py boots
SimulationApp at import (R4: unimportable live). So P4 runs the
DOCUMENTED sequence in-session: build the synthetic legacy arm
(1 gained + 1 gainless + 1 mimic joint), pass 1 (MJC), pass 2
(structure), gain audit, variant check. Builder/audit mirror the
library script line-for-line; conversion logic stays in the Rule.
"""
import os
import shutil
import omni.usd  # noqa: F401 (ensures USD runtime present)
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, PhysxSchema
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.asset.transformer import (
    AssetTransformerManager, RuleProfile)

EVD = "C:/Users/sruja_ob3di74/action-reasoner/skills/physics/engines/evidence/p4_conv"
shutil.rmtree(EVD, ignore_errors=True)
os.makedirs(EVD, exist_ok=True)
LEGACY = EVD + "/p4_legacy.usda"


def _build(path):
    stage = Usd.Stage.CreateNew(path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/arm").GetPrim()
    stage.SetDefaultPrim(root)
    UsdPhysics.ArticulationRootAPI.Apply(root)
    PhysxSchema.PhysxArticulationAPI.Apply(root)
    for name, z in (("base", 0.0), ("l1", 0.2), ("l2", 0.4), ("l3", 0.6)):
        link = UsdGeom.Xform.Define(stage, f"/arm/{name}")
        link.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, z))
        UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
        UsdPhysics.MassAPI.Apply(link.GetPrim()).CreateMassAttr(1.0)
        cube = UsdGeom.Cube.Define(stage, f"/arm/{name}/geom")
        cube.CreateSizeAttr(0.1)
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    root_joint = UsdPhysics.FixedJoint.Define(stage, "/arm/root_joint")
    root_joint.CreateBody1Rel().SetTargets([Sdf.Path("/arm/base")])
    for name, body0, body1, kp, kd in (
        ("j1", "base", "l1", 100.0, 10.0),
        ("j2_nogain", "l1", "l2", 0.0, 0.0),
        ("j3_mimic", "l2", "l3", None, None),
    ):
        joint = UsdPhysics.RevoluteJoint.Define(stage, f"/arm/{name}")
        joint.CreateAxisAttr("Y")
        joint.CreateBody0Rel().SetTargets([Sdf.Path(f"/arm/{body0}")])
        joint.CreateBody1Rel().SetTargets([Sdf.Path(f"/arm/{body1}")])
        joint.CreateLocalPos0Attr(Gf.Vec3f(0.0, 0.0, 0.1))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0.0, 0.0, -0.1))
        joint.CreateLowerLimitAttr(-90.0)
        joint.CreateUpperLimitAttr(90.0)
        PhysxSchema.PhysxJointAPI.Apply(joint.GetPrim())
        if kp is None:
            mimic = PhysxSchema.PhysxMimicJointAPI.Apply(
                joint.GetPrim(), UsdPhysics.Tokens.rotY)
            mimic.CreateReferenceJointRel().SetTargets([Sdf.Path("/arm/j1")])
            mimic.CreateGearingAttr(1.0)
            continue
        drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "angular")
        drive.CreateStiffnessAttr(kp)
        drive.CreateDampingAttr(kd)
        drive.CreateTargetPositionAttr(0.0)
    stage.Save()


def _run_profile(input_path, profile_name, output_dir, interface_name=None):
    rules_path = app_utils.get_extension_path(
        "isaacsim.asset.transformer.rules")
    with open(os.path.join(rules_path, "data", profile_name),
              encoding="utf-8") as f:
        profile = RuleProfile.from_json(f.read())
    if interface_name:
        profile.interface_asset_name = interface_name
    os.makedirs(output_dir, exist_ok=True)
    report = AssetTransformerManager().run(
        input_stage=input_path, profile=profile, package_root=output_dir)
    ok = bool(report.results) and all(r.success for r in report.results)
    return ok, len(report.results)


def _is_mimic(prim):
    return any(n == "NewtonMimicAPI" or n.startswith("PhysxMimicJointAPI")
               for n in prim.GetAppliedSchemas())


_build(LEGACY)
ok1, n1 = _run_profile(LEGACY, "physx_to_mjc_conversion.json",
                       EVD + "/pass1")
ok2, n2 = _run_profile(EVD + "/pass1/payloads/mujoco.usda",
                       "isaacsim_structure.json", EVD + "/package",
                       "p4arm.usda")
IFACE = EVD + "/package/p4arm.usda"
stage = Usd.Stage.Open(IFACE)
stage.SetEditTarget(stage.GetSessionLayer())
root = stage.GetDefaultPrim()
vset = root.GetVariantSets().GetVariantSet("Physics")
variants = sorted(vset.GetVariantNames())
vset.SetVariantSelection("mujoco")
missing, count, acts = [], 0, []
for prim in stage.Traverse():
    if prim.GetTypeName() != "MjcActuator":
        continue
    count += 1
    acts.append(prim.GetPath().name)
    attr = prim.GetAttribute("mjc:gainPrm")
    gains = attr.Get() if attr and attr.HasAuthoredValue() else None
    if gains and any(gains):
        continue
    rel = prim.GetRelationship("mjc:target")
    tgts = rel.GetTargets() if rel else []
    if tgts and all(_is_mimic(stage.GetPrimAtPath(t)) for t in tgts):
        continue
    missing.append(prim.GetPath().name)
print("P4-REPORT pass1=%s(%d) pass2=%s(%d) variants=%s acts=%d "
      "missing=%s" % (ok1, n1, ok2, n2, variants, count, missing))
