"""Drill 03 phase 3 (runs INSIDE Isaac Sim): in-flight velocity proof.

Plays, steps exactly 20 (deterministic, no real-time race), reads live
tensors through TWO independent RigidPrim instances, pauses, stops.
"""
import isaacsim.core.experimental.utils.app as app_utils
import omni.timeline
from isaacsim.core.experimental.prims import RigidPrim

rp1 = RigidPrim(paths="/World/LiveCube")
rp2 = RigidPrim(paths="/World/LiveCube")
app_utils.play()
await app_utils.update_app_async(steps=20)
z = float(rp1.get_world_poses()[0].numpy()[0][2])
v1 = rp1.get_velocities()
v2 = rp2.get_velocities()
vza = float(v1[0].numpy()[0][2])
vzb = float(v2[0].numpy()[0][2])
omni.timeline.get_timeline_interface().pause()
app_utils.stop()
print("VEL-REPORT z=%.4f vz=%.4f instdiff=%.6f" % (z, vza, abs(vza - vzb)))
