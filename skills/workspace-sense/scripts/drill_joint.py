"""Drill 02 setup (runs INSIDE Isaac Sim): cube + cylinder + revolute joint.

JointCube:  1 m cube, center (0,0,0.5).
JointCyl:   r=0.25 h=1.0 cylinder along X, center (1,0,0.5).
Joint:      revolute, body0=cube anchor (0.5,0,0) [+X face center],
            body1=cyl anchor (-0.5,0,0) [-X end center], axis X.
Expected sense: anchor0_site=maxX+midY+midZ, anchor1_site=minX+midY+midZ.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/JointCube", "/World/JointCyl", "/World/JointCube_Cyl"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

cube = UsdGeom.Cube.Define(stage, "/World/JointCube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).GetMassAttr().Set(2.0)

cyl = UsdGeom.Cylinder.Define(stage, "/World/JointCyl")
cyl.GetRadiusAttr().Set(0.25)
cyl.GetHeightAttr().Set(1.0)
cyl.GetAxisAttr().Set(UsdGeom.Tokens.x)
UsdGeom.Xformable(cyl.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(1.0, 0, 0.5))
UsdPhysics.RigidBodyAPI.Apply(cyl.GetPrim())
UsdPhysics.CollisionAPI.Apply(cyl.GetPrim())
UsdPhysics.MassAPI.Apply(cyl.GetPrim()).GetMassAttr().Set(1.0)

joint = UsdPhysics.RevoluteJoint.Define(stage, "/World/JointCube_Cyl")
joint.GetBody0Rel().AddTarget("/World/JointCube")
joint.GetBody1Rel().AddTarget("/World/JointCyl")
joint.GetLocalPos0Attr().Set(Gf.Vec3f(0.5, 0, 0))
joint.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
joint.GetLocalPos1Attr().Set(Gf.Vec3f(-0.5, 0, 0))
joint.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
joint.GetAxisAttr().Set(UsdPhysics.Tokens.x)
print("DRILL02-SETUP-OK cube+cyl+revolute")
