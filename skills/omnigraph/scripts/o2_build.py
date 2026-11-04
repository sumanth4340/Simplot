"""O2 build (runs INSIDE Isaac Sim): time-to-attribute graph.

Cube + custom double attr og:stamp. Graph: OnPlaybackTick --tick-->
Write.inputs:execIn AND OnPB.outputs:time --> Write.inputs:value,
targeting og:stamp. Reports nodes + value-attr type after connect.
"""
import omni.usd
import omni.graph.core as og
from pxr import UsdGeom, Gf, Sdf

stage = omni.usd.get_context().get_stage()
for p in ("/World/O1Cube", "/World/O1Graph",
          "/World/O2Cube", "/World/O2Graph",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

cube = UsdGeom.Cube.Define(stage, "/World/O2Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
cube.GetPrim().CreateAttribute("og:stamp", Sdf.ValueTypeNames.Double)

keys = og.Controller.Keys
og.Controller.edit("/World/O2Graph", {
    keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Write", "omni.graph.nodes.WritePrimAttribute"),
    ],
    keys.CONNECT: [
        ("OnPB.outputs:tick", "Write.inputs:execIn"),
        ("OnPB.outputs:time", "Write.inputs:value"),
    ],
    keys.SET_VALUES: [
        ("Write.inputs:primPath", "/World/O2Cube"),
        ("Write.inputs:name", "og:stamp"),
        ("Write.inputs:usePath", True),
    ],
})
wp = stage.GetPrimAtPath("/World/O2Graph/Write")
vtype = wp.GetAttribute("inputs:value").GetTypeName() if wp.IsValid() else "-"
gp = stage.GetPrimAtPath("/World/O2Graph")
nodes = [c.GetName() for c in gp.GetChildren()] if gp.IsValid() else []
print("O2-BUILD-OK graph=%s nodes=%s valuetype=%s" % (
    gp.IsValid(), sorted(nodes), vtype))
