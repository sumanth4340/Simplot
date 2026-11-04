"""X2 modeling x physics (runs INSIDE Isaac Sim): imported arm goes live.

References the M2 URDF package, adds scene + ground, plays 120 steps.
The arm stands on a vertical (Z) revolute joint: no gravity torque, so
the structure must sit stable with live rigid bodies and valid joints.
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
import omni.usd
from pxr import UsdGeom, UsdPhysics, Gf
from isaacsim.core.experimental.prims import RigidPrim

stage = omni.usd.get_context().get_stage()
ref = stage.DefinePrim("/World/X2Bot")
ref.GetReferences().AddReference(
    "C:/Users/sruja_ob3di74/action-reasoner/skills/modeling-assets/"
    "assets/m2_out/m2_bot/m2_bot.usda")
ps = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
ps.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, 0, -1))
ps.CreateGravityMagnitudeAttr().Set(9.81)
g = UsdGeom.Plane.Define(stage, "/World/X2Ground")
g.CreateWidthAttr().Set(20.0)
g.CreateLengthAttr().Set(20.0)
UsdPhysics.CollisionAPI.Apply(g.GetPrim())

tl = omni.timeline.get_timeline_interface()
rp = RigidPrim(paths="/World/X2Bot/Geometry/base")
app_utils.play()
z0 = float(rp.get_world_poses()[0].numpy()[0][2])
t0 = float(tl.get_current_time())
await app_utils.update_app_async(steps=120)
z1 = float(rp.get_world_poses()[0].numpy()[0][2])
t1 = float(tl.get_current_time())
tl.pause()
base = stage.GetPrimAtPath("/World/X2Bot/Geometry/base")
joint_ok = stage.GetPrimAtPath("/World/X2Bot/Physics/shoulder").IsValid()
print("X2-REPORT z0=%.4f z1=%.4f t0=%.3f t1=%.3f rigid=%s joint=%s"
      % (z0, z1, t0, t1, base.HasAPI(UsdPhysics.RigidBodyAPI), joint_ok))
