"""Drill 03 setup (runs INSIDE Isaac Sim): live-drop scene.

PhysicsScene + static ground + dynamic 1 m cube /World/LiveCube at z=2.
Clears earlier drill prims so LiveCube is the only rigid body.
"""
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd

stage = omni.usd.get_context().get_stage()
for p in ("/World/SenseCube", "/World/JointCube", "/World/JointCyl",
          "/World/JointCube_Cyl", "/World/P1Cube", "/World/P1Ground",
          "/World/LiveCube", "/World/LiveCube2", "/World/LiveGround",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)

g = UsdGeom.Plane.Define(stage, "/World/LiveGround")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())

c = UsdGeom.Cube.Define(stage, "/World/LiveCube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 2))
UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
UsdPhysics.CollisionAPI.Apply(c.GetPrim())
UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(1.0)
c2 = UsdGeom.Cube.Define(stage, "/World/LiveCube2")
c2.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c2.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(3, 0, 4))
UsdPhysics.RigidBodyAPI.Apply(c2.GetPrim())
UsdPhysics.CollisionAPI.Apply(c2.GetPrim())
UsdPhysics.MassAPI.Apply(c2.GetPrim()).GetMassAttr().Set(5.0)
import omni.timeline
import isaacsim.core.experimental.utils.app as app_utils
app_utils.stop()
omni.timeline.get_timeline_interface().set_current_time(0.0)
print("DRILL03-SETUP-OK live scene, cubes@z2+z4 clock=0")
