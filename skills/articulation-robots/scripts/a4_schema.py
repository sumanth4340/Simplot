"""A4 schema (runs INSIDE Isaac Sim): robot schema overlay + validation.

Rebuilds the A2 3-link arm, applies IsaacRobotAPI + type + tip SiteAPI,
populates relations from the articulation graph, validates them.
Pure USD authoring; no play needed.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd
from usd.schema.isaac.robot_schema import Attributes, Classes, Relations
from usd.schema.isaac.robot_schema.utils import (
    PopulateRobotSchemaFromArticulation, ValidateRobotSchemaRelationships)

stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/A4Bot")
if o and o.IsValid():
    stage.RemovePrim("/World/A4Bot")
UsdGeom.Xform.Define(stage, "/World/A4Bot")


def _link(name, size, z, mass, root=False):
    c = UsdGeom.Cube.Define(stage, "/World/A4Bot/" + name)
    c.GetSizeAttr().Set(size)
    UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, z))
    UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
    UsdPhysics.CollisionAPI.Apply(c.GetPrim())
    UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(mass)
    if root:
        UsdPhysics.ArticulationRootAPI.Apply(c.GetPrim())


def _hinge(name, b0, a0, b1, a1):
    j = UsdPhysics.RevoluteJoint.Define(stage, "/World/A4Bot/" + name)
    j.GetBody0Rel().AddTarget("/World/A4Bot/" + b0)
    j.GetBody1Rel().AddTarget("/World/A4Bot/" + b1)
    j.GetLocalPos0Attr().Set(Gf.Vec3f(*a0))
    j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
    j.GetLocalPos1Attr().Set(Gf.Vec3f(*a1))
    j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
    j.GetAxisAttr().Set(UsdPhysics.Tokens.z)


_link("Base", 1.0, 0.5, 2.0, root=True)
fx = UsdPhysics.FixedJoint.Define(stage, "/World/A4Bot/RootFixed")
fx.GetBody0Rel().AddTarget("/World/A4Bot")
fx.GetBody1Rel().AddTarget("/World/A4Bot/Base")
fx.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0))
fx.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
fx.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
fx.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
_link("Link1", 0.6, 1.3, 1.0)
_hinge("Hinge1", "Base", (0, 0, 0.5), "Link1", (0, 0, -0.3))
_link("Link2", 0.4, 1.8, 0.5)
_hinge("Hinge2", "Link1", (0, 0, 0.3), "Link2", (0, 0, -0.2))
tip = UsdGeom.Xform.Define(stage, "/World/A4Bot/Link2/Tip")
UsdGeom.Xformable(tip.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.2))

robot = stage.GetPrimAtPath("/World/A4Bot")
robot.ApplyAPI(Classes.ROBOT_API.value)
tname, _, ttype = Attributes.ROBOT_TYPE.value
robot.CreateAttribute(tname, ttype).Set("Manipulator")
tip.GetPrim().ApplyAPI(Classes.SITE_API.value)
root_link, root_joint = PopulateRobotSchemaFromArticulation(
    stage, robot, stage.GetPrimAtPath("/World/A4Bot/Base"))
vl, il, vj, ij = ValidateRobotSchemaRelationships(robot)
links = [str(t) for t in robot.GetRelationship(
    Relations.ROBOT_LINKS.value[0]).GetTargets()]
joints = [str(t) for t in robot.GetRelationship(
    Relations.ROBOT_JOINTS.value[0]).GetTargets()]
rtype = robot.GetAttribute(tname).Get()
print("A4-REPORT robot=%s type=%s links=%s joints=%s bad=%d rootlink=%s" % (
    robot.HasAPI(Classes.ROBOT_API.value), rtype, "|".join(links),
    "|".join(joints), len(il) + len(ij), root_link.GetPath()))
