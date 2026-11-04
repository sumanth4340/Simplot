# N1 motion time-series (runs INSIDE Isaac Sim via bridge).
# Tensor ground truth: chassis pose via RigidPrim, DOF state via
# Articulation. 300 steps, sampled every 10. CTL drives [1.0]*4.
import isaacsim.core.experimental.utils.app as app_utils
import omni.graph.core as og
import omni.usd
from isaacsim.core.experimental.prims import Articulation, RigidPrim

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/World/PhysicsScene").IsValid():
    st.RemovePrim("/World/PhysicsScene")
    print("REMOVED dup /World/PhysicsScene")
arts = [c.GetName() for c in st.GetPrimAtPath("/World").GetChildren()
        if c.GetName().startswith("N1Base")]
print("ARTS", arts)
ART = "/World/" + arts[-1]

art = Articulation(ART)
ch = RigidPrim(ART + "/chassis")

og.Controller.attribute(
    "/ROS2/N1/CTL.inputs:velocityCommand").set([1.0] * 4)
app_utils.play()
for i in range(301):
    await app_utils.update_app_async(steps=1)
    if i % 10 == 0:
        pos, quat = ch.get_world_poses()
        p = pos.numpy().flatten().tolist()
        q = quat.numpy().flatten().tolist()
        dv = art.get_dof_velocities().numpy().flatten().tolist()
        dp = art.get_dof_positions().numpy().flatten().tolist()
        print("TS i=%d pos=(%.3f,%.3f,%.3f) quat=(%.2f,%.2f,%.2f,%.2f) "
              "dofv=%s dofp=%s"
              % (i, p[0], p[1], p[2], q[0], q[1], q[2], q[3],
                 [round(v, 2) for v in dv],
                 [round(v, 2) for v in dp]))
app_utils.stop()
print("TS done")
