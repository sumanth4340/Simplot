"""O3 build (runs INSIDE Isaac Sim): graph-driven joint motion.

1R arm (Skill 4 root pattern) + /World/O3Graph: time --a--> Mul(x10)
--product--> Write(Hinge1 drive targetPosition). All-double chain
(O2-proven); tuple links avoided (R2-open). Reports nodes.
"""
import omni.usd
import omni.graph.core as og
from pxr import UsdGeom, UsdPhysics, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/O2Cube", "/World/O2Graph",
          "/World/O3Cube", "/World/O3Graph", "/World/O3Bot",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
bot = stage.DefinePrim("/World/O3Bot", "Xform")
base = UsdGeom.Cube.Define(stage, "/World/O3Bot/Base")
base.GetSizeAttr().Set(0.15)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.2))
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).GetMassAttr().Set(2.0)
UsdPhysics.ArticulationRootAPI.Apply(base.GetPrim())
fix = UsdPhysics.FixedJoint.Define(stage, "/World/O3Bot/RootFixed")
fix.CreateBody0Rel().SetTargets(["/World/O3Bot"])
fix.CreateBody1Rel().SetTargets(["/World/O3Bot/Base"])
link = UsdGeom.Cube.Define(stage, "/World/O3Bot/Link")
link.GetSizeAttr().Set(0.2)
UsdGeom.Xformable(link.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.4))
UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
UsdPhysics.MassAPI.Apply(link.GetPrim()).GetMassAttr().Set(0.5)
hinge = UsdPhysics.RevoluteJoint.Define(stage, "/World/O3Bot/Hinge1")
hinge.CreateBody0Rel().SetTargets(["/World/O3Bot/Base"])
hinge.CreateBody1Rel().SetTargets(["/World/O3Bot/Link"])
hinge.CreateAxisAttr("Y")
hinge.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0.075))
hinge.CreateLocalPos1Attr(Gf.Vec3f(0, 0, -0.1))
lim = UsdPhysics.LimitAPI.Apply(hinge.GetPrim(), "rotY")
lim.CreateLowAttr(-170.0)
lim.CreateHighAttr(170.0)
drv = UsdPhysics.DriveAPI.Apply(hinge.GetPrim(), "angular")
drv.CreateTypeAttr("position")
drv.CreateTargetPositionAttr().Set(0.0)
drv.CreateStiffnessAttr(100.0)
drv.CreateDampingAttr(10.0)

keys = og.Controller.Keys
og.Controller.edit("/World/O3Graph", {
    keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Mul", "omni.graph.nodes.Multiply"),
        ("Write", "omni.graph.nodes.WritePrimAttribute"),
    ],
    keys.CONNECT: [
        ("OnPB.outputs:tick", "Write.inputs:execIn"),
        ("OnPB.outputs:time", "Mul.inputs:a"),
        ("Mul.outputs:product", "Write.inputs:value"),
    ],
    keys.SET_VALUES: [
        ("Mul.inputs:b", 10.0, og.Type(og.BaseDataType.DOUBLE)),
        ("Write.inputs:primPath", "/World/O3Bot/Hinge1"),
        ("Write.inputs:name", "drive:angular:physics:targetPosition"),
        ("Write.inputs:usePath", True),
    ],
})
gp = stage.GetPrimAtPath("/World/O3Graph")
nodes = [c.GetName() for c in gp.GetChildren()] if gp.IsValid() else []
print("O3-BUILD-OK graph=%s nodes=%s" % (gp.IsValid(), sorted(nodes)))
