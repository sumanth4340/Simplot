"""Diagnostic probe: do live DriveAPI Sets turn the wheels? does the bot pitch?

Single send: play -> settle -> read t0 -> command forward 4 rad/s ->
read t1/t2 -> stop. Prints chassis x/quat + wheel spin deltas.
"""
import math

import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import RigidPrim
from pxr import UsdPhysics
import omni.usd

DEG = 180.0 / math.pi
st = omni.usd.get_context().get_stage()
dl = UsdPhysics.DriveAPI.Apply(st.GetPrimAtPath("/World/AvoidBot/joint_l"), "angular")
dr = UsdPhysics.DriveAPI.Apply(st.GetPrimAtPath("/World/AvoidBot/joint_r"), "angular")
ch = RigidPrim("/World/AvoidBot/chassis")
wl = RigidPrim("/World/AvoidBot/wheel_l/col")


def snap(tag):
    p, q = ch.get_world_poses()
    pw, qw = wl.get_world_poses()
    p = p.numpy().flatten()
    q = q.numpy().flatten()  # (x, y, z, w)
    qw = qw.numpy().flatten()
    # chassis pitch about Y from quat: pitch = asin(2(wy - zx)) for (x,y,z,w)
    x, y, z, w = (float(v) for v in q)
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, 2.0 * (w * y - z * x)))))
    print("PROBE %s chx=%.4f chz=%.4f pitch=%.2f wquat=(%.3f,%.3f,%.3f,%.3f)"
          % (tag, p[0], p[2], pitch, qw[0], qw[1], qw[2], qw[3]))


app_utils.play()
await app_utils.update_app_async(steps=120)
snap("settle")
dl.GetTargetVelocityAttr().Set(4.0 * DEG)
dr.GetTargetVelocityAttr().Set(4.0 * DEG)
await app_utils.update_app_async(steps=120)
snap("drive+120")
await app_utils.update_app_async(steps=120)
snap("drive+240")
dl.GetTargetVelocityAttr().Set(0.0)
dr.GetTargetVelocityAttr().Set(0.0)
app_utils.stop()
print("PROBE-DONE")
