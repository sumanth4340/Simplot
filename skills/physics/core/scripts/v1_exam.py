"""V1 graduation (runs INSIDE Isaac Sim): 5 kg cube from z=5, sample 6x.

Novel mass + height. Theory: rest 0.5; flight z(t)=5-4.9t^2 at 60 Hz
samples (20 steps each): z[1]~2.82 in flight, z[2..] rested.
"""
import isaacsim.core.experimental.utils.app as app_utils
from pxr import UsdGeom, UsdPhysics, Gf
import omni.usd
from isaacsim.core.experimental.prims import RigidPrim

stage = omni.usd.get_context().get_stage()
for p in ("/World/P5Cube", "/World/P5Ground", "/World/V1Cube",
          "/World/V1Ground", "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/V1Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())
c = UsdGeom.Cube.Define(stage, "/World/V1Cube")
c.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(c.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 5))
UsdPhysics.RigidBodyAPI.Apply(c.GetPrim())
UsdPhysics.CollisionAPI.Apply(c.GetPrim())
UsdPhysics.MassAPI.Apply(c.GetPrim()).GetMassAttr().Set(5.0)

rp = RigidPrim(paths="/World/V1Cube")
app_utils.play()
zs = []
for _ in range(6):
    await app_utils.update_app_async(steps=20)
    zs.append(float(rp.get_world_poses()[0].numpy()[0][2]))
app_utils.stop()
print("V1-TRAJ " + ",".join("%.4f" % z for z in zs))
