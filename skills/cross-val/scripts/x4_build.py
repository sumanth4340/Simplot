"""X4 capstone (runs INSIDE Isaac Sim): one scene, every master.

Rigid drop cube (physics) + hinge joint (physics) + referenced URDF
arm (modeling) + triangle mesh (modeling) + red material (modeling) +
2 grid clones (modeling). Sensed once; each master asserts its share.
"""
from pxr import UsdGeom, UsdPhysics, UsdShade, Gf, Sdf
import omni.usd
from isaacsim.core.cloner import GridCloner

stage = omni.usd.get_context().get_stage()
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/X4Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())

c = UsdGeom.Cube.Define(stage, "/World/X4Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 2))
UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
UsdPhysics.CollisionAPI.Apply(c.GetPrim())
UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(1.0)

base = UsdGeom.Cube.Define(stage, "/World/X4Base")
base.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(5, 0, 0.5))
UsdPhysics.CollisionAPI.Apply(base.GetPrim())
arm = UsdGeom.Cube.Define(stage, "/World/X4Arm")
arm.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(arm.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(5, 0, 1.5))
UsdPhysics.RigidBodyAPI.Apply(arm.GetPrim())
UsdPhysics.CollisionAPI.Apply(arm.GetPrim())
j = UsdPhysics.RevoluteJoint.Define(stage, "/World/X4Hinge")
j.GetBody0Rel().AddTarget("/World/X4Base")
j.GetBody1Rel().AddTarget("/World/X4Arm")
j.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0.5))
j.GetLocalRot0Attr().Set(Gf.Quatf(1.0))
j.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, -0.5))
j.GetLocalRot1Attr().Set(Gf.Quatf(1.0))
j.GetAxisAttr().Set(UsdPhysics.Tokens.z)

ref = stage.DefinePrim("/World/X4Bot")
ref.GetReferences().AddReference(
    "C:/Users/sruja_ob3di74/action-reasoner/skills/modeling-assets/"
    "assets/m2_out/m2_bot/m2_bot.usda")

m = UsdGeom.Mesh.Define(stage, "/World/X4Tri")
m.CreatePointsAttr().Set([Gf.Vec3f(0, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(0, 1, 0)])
m.CreateFaceVertexCountsAttr().Set([3])
m.CreateFaceVertexIndicesAttr().Set([0, 1, 2])
UsdGeom.Xformable(m.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(-4, 0, 1))

mat = UsdShade.Material.Define(stage, "/World/X4Looks/X4Red")
sh = UsdShade.Shader.Define(stage, "/World/X4Looks/X4Red/PBR")
sh.SetShaderId("UsdPreviewSurface")
sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1, 0, 0))
mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI(c.GetPrim()).Bind(mat)

cloner = GridCloner(spacing=3.0)
cloner.define_base_env("/World/x4envs")
paths = cloner.generate_paths("/World/x4envs/env", 2)
n = len(cloner.clone(source_prim_path="/World/X4Cube", prim_paths=paths))
print("X4-REPORT clones=%d" % n)
