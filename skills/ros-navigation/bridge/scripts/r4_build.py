"""R4 build (runs INSIDE Isaac Sim via bridge).

Articulation /World/R4Bot_<ts> (dynamic base + FixedBase anchor, 2
revolute links, NO collisions) + graph /ROS2/R4: OnPlaybackTick +
IsaacReadSimulationTime -> ROS2PublishTransformTree (/tf,
parentPrim /World, targetPrims base/link1/link2) +
IsaacArticulationController (velocity drive for TF motion).
"""
import time

import omni.graph.core as og
import omni.usd
from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf

ART = "/World/R4Bot_%d" % int(time.time())

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/ROS2/R4").IsValid():
    st.RemovePrim("/ROS2/R4")
# Cross-drill cleanup (Section 4a): graduated drills must not linger.
for g in ("/ROS2/R2", "/ROS2/R3"):
    if st.GetPrimAtPath(g).IsValid():
        st.RemovePrim(g)
for c in list(st.GetPrimAtPath("/World").GetChildren()):
    if c.GetName().startswith(("R2Bot", "R3Bot", "R4Bot")):
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
    {"graph_path": "/ROS2/R4", "evaluator_name": "execution"},
    {keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ("TF", "isaacsim.ros2.bridge.ROS2PublishTransformTree"),
        ("CTL", "isaacsim.core.nodes.IsaacArticulationController")],
     keys.CONNECT: [
        ("/ROS2/R4/OnPB.outputs:tick", "/ROS2/R4/TF.inputs:execIn"),
        ("/ROS2/R4/OnPB.outputs:tick", "/ROS2/R4/CTL.inputs:execIn"),
        ("/ROS2/R4/Time.outputs:simulationTime",
         "/ROS2/R4/TF.inputs:timeStamp")],
     keys.SET_VALUES: [
        ("/ROS2/R4/TF.inputs:topicName", "/tf"),
        ("/ROS2/R4/TF.inputs:queueSize", 10),
        ("/ROS2/R4/CTL.inputs:robotPath", ART),
        ("/ROS2/R4/CTL.inputs:jointNames", ["J1", "J2"]),
        ("/ROS2/R4/CTL.inputs:velocityCommand", [0.5, 0.5])]})
st.GetPrimAtPath("/ROS2/R4/TF").GetRelationship(
    "inputs:parentPrim").SetTargets(["/World"])
st.GetPrimAtPath("/ROS2/R4/TF").GetRelationship(
    "inputs:targetPrims").SetTargets(
        [base.GetPath(), l1.GetPath(), l2.GetPath()])
st.GetPrimAtPath("/ROS2/R4/CTL").GetRelationship(
    "inputs:targetPrim").SetTargets([ART])

names = sorted(str(c.GetName()) for c in
               st.GetPrimAtPath("/ROS2/R4").GetChildren())
par = st.GetPrimAtPath("/ROS2/R4/TF").GetRelationship(
    "inputs:parentPrim").GetTargets()
tgt = st.GetPrimAtPath("/ROS2/R4/TF").GetRelationship(
    "inputs:targetPrims").GetTargets()
print("R4-BUILD-OK nodes=%s parent=%s targets=%d" %
      (names, list(par), len(tgt)))
