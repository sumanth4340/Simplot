"""R3 build (runs INSIDE Isaac Sim via bridge).

Articulation /World/R3Bot_<ts> (dynamic base + FixedBase anchor, 2
revolute links, NO collisions) + graph /ROS2/R3: OnPlaybackTick ->
ROS2SubscribeJointState (/r3_cmd) -> IsaacArticulationController
(velocity commands + joint names wired through).
"""
import time

import omni.graph.core as og
import omni.usd
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf

ART = "/World/R3Bot_%d" % int(time.time())

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/R3").IsValid():
    st.RemovePrim("/ROS2/R3")
# Cross-drill cleanup (Section 4a): graduated R2's prims must not linger.
if st.GetPrimAtPath("/ROS2/R2").IsValid():
    st.RemovePrim("/ROS2/R2")
for c in list(st.GetPrimAtPath("/World").GetChildren()):
    if c.GetName().startswith("R3Bot") or c.GetName().startswith("R2Bot"):
        st.RemovePrim(c.GetPath())

root = UsdGeom.Xform.Define(st, ART)
UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())
PhysxSchema.PhysxArticulationAPI.Apply(root.GetPrim())

base = UsdGeom.Xform.Define(st, ART + "/base")
base.AddTranslateOp().Set(Gf.Vec3d(0, 0.25, 0))
cube = UsdGeom.Cube.Define(st, ART + "/base/geo")
cube.GetSizeAttr().Set(0.5)
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).CreateMassAttr().Set(1.0)
PhysxSchema.PhysxRigidBodyAPI.Apply(
    base.GetPrim()).GetSleepThresholdAttr().Set(0.0)


def link(name, y, size, geo_y):
    L = UsdGeom.Xform.Define(st, ART + "/" + name)
    L.AddTranslateOp().Set(Gf.Vec3d(0, y, 0))
    g = UsdGeom.Cube.Define(st, ART + "/%s/geo" % name)
    g.GetSizeAttr().Set(size)
    g.AddTranslateOp().Set(Gf.Vec3d(0, geo_y, 0))
    UsdPhysics.RigidBodyAPI.Apply(L.GetPrim())
    UsdPhysics.MassAPI.Apply(L.GetPrim()).CreateMassAttr().Set(1.0)
    PhysxSchema.PhysxRigidBodyAPI.Apply(
        L.GetPrim()).GetSleepThresholdAttr().Set(0.0)
    return L


l1 = link("link1", 0.7, 0.4, 0.2)
l2 = link("link2", 1.1, 0.3, 0.15)
fb = UsdPhysics.FixedJoint.Define(st, ART + "/FixedBase")
fb.GetBody1Rel().SetTargets([base.GetPath()])
fb.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))

for jn, b0, b1, lp0, lp1 in (("J1", base, l1, (0, 0.25, 0), (0, -0.2, 0)),
                              ("J2", l1, l2, (0, 0.4, 0), (0, 0, 0))):
    j = UsdPhysics.RevoluteJoint.Define(st, ART + "/" + jn)
    j.GetBody0Rel().SetTargets([b0.GetPath()])
    j.GetBody1Rel().SetTargets([b1.GetPath()])
    j.GetLocalPos0Attr().Set(Gf.Vec3f(*lp0))
    j.GetLocalPos1Attr().Set(Gf.Vec3f(*lp1))
    j.GetAxisAttr().Set("Z")
    drv = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "angular")
    drv.GetTargetVelocityAttr().Set(0.0)
    drv.GetStiffnessAttr().Set(0.0)
    drv.GetDampingAttr().Set(50.0)
    drv.GetMaxForceAttr().Set(100.0)

keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ROS2/R3", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("SUB", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
        ("CTL", "isaacsim.core.nodes.IsaacArticulationController")],
     keys.CONNECT: [
        ("/ROS2/R3/OnPB.outputs:tick", "/ROS2/R3/SUB.inputs:execIn"),
        ("/ROS2/R3/SUB.outputs:execOut", "/ROS2/R3/CTL.inputs:execIn"),
        ("/ROS2/R3/SUB.outputs:jointNames",
         "/ROS2/R3/CTL.inputs:jointNames"),
        ("/ROS2/R3/SUB.outputs:velocityCommand",
         "/ROS2/R3/CTL.inputs:velocityCommand")],
     keys.SET_VALUES: [
        ("/ROS2/R3/SUB.inputs:topicName", "/r3_cmd"),
        ("/ROS2/R3/SUB.inputs:queueSize", 10),
        ("/ROS2/R3/CTL.inputs:robotPath", ART)]})
st.GetPrimAtPath("/ROS2/R3/CTL").GetRelationship(
    "inputs:targetPrim").SetTargets([ART])

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/R3").GetChildren())
print("R3-BUILD-OK nodes=%s art=%s" % (names, ART))
