"""V9 build (runs INSIDE Isaac Sim): exam scene + graph.

New scene: V9Bot 1R arm at x=+3. New modality: 4-node chain
time --a--> Mul(x5) --product--> Add(+1.0) --sum--> Write(Hinge1
drive targetPosition). All-double (R2-open). R8 sweep: reports
pre-existing graphs sharing the V9 target (must be none).
"""
import omni.usd
import omni.graph.core as og
from pxr import UsdGeom, UsdPhysics, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/V9Bot", "/World/V9Graph"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

bot = stage.DefinePrim("/World/V9Bot", "Xform")
UsdGeom.Xformable(bot).AddTranslateOp().Set(Gf.Vec3d(3.0, 0, 0))
base = UsdGeom.Cube.Define(stage, "/World/V9Bot/Base")
base.GetSizeAttr().Set(0.15)
UsdGeom.Xformable(base.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.2))
UsdPhysics.RigidBodyAPI.Apply(base.GetPrim())
UsdPhysics.MassAPI.Apply(base.GetPrim()).GetMassAttr().Set(2.0)
UsdPhysics.ArticulationRootAPI.Apply(base.GetPrim())
fix = UsdPhysics.FixedJoint.Define(stage, "/World/V9Bot/RootFixed")
fix.CreateBody0Rel().SetTargets(["/World/V9Bot"])
fix.CreateBody1Rel().SetTargets(["/World/V9Bot/Base"])
link = UsdGeom.Cube.Define(stage, "/World/V9Bot/Link")
link.GetSizeAttr().Set(0.2)
UsdGeom.Xformable(link.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.4))
UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
UsdPhysics.MassAPI.Apply(link.GetPrim()).GetMassAttr().Set(0.5)
hinge = UsdPhysics.RevoluteJoint.Define(stage, "/World/V9Bot/Hinge1")
hinge.CreateBody0Rel().SetTargets(["/World/V9Bot/Base"])
hinge.CreateBody1Rel().SetTargets(["/World/V9Bot/Link"])
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

# R8 sweep: no other graph may target the V9 hinge.
rival = []
for c in stage.GetPrimAtPath("/World").GetChildren():
    if c.GetTypeName() == "Graph" and c.GetName() != "V9Graph":
        for n in c.GetChildren():
            pp = n.GetAttribute("inputs:primPath")
            if pp.IsValid() and pp.Get() == "/World/V9Bot/Hinge1":
                rival.append(c.GetName())

keys = og.Controller.Keys
DT = og.Type(og.BaseDataType.DOUBLE)
og.Controller.edit("/World/V9Graph", {
    keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Mul", "omni.graph.nodes.Multiply"),
        ("Add", "omni.graph.nodes.Add"),
        ("Write", "omni.graph.nodes.WritePrimAttribute"),
    ],
    keys.CONNECT: [
        ("OnPB.outputs:tick", "Write.inputs:execIn"),
        ("OnPB.outputs:time", "Mul.inputs:a"),
        ("Mul.outputs:product", "Add.inputs:a"),
        ("Add.outputs:sum", "Write.inputs:value"),
    ],
    keys.SET_VALUES: [
        ("Mul.inputs:b", 5.0, DT),
        ("Add.inputs:b", 1.0, DT),
        ("Write.inputs:primPath", "/World/V9Bot/Hinge1"),
        ("Write.inputs:name", "drive:angular:physics:targetPosition"),
        ("Write.inputs:usePath", True),
    ],
})
gp = stage.GetPrimAtPath("/World/V9Graph")
nodes = [c.GetName() for c in gp.GetChildren()] if gp.IsValid() else []
up = og.ObjectLookup.attribute(
    "/World/V9Graph/Write.inputs:value").get_upstream_connections()
print("V9-BUILD-OK graph=%s nodes=%s linked=%s rivals=%s" % (
    gp.IsValid(), sorted(nodes), len(up) == 1, rival))
