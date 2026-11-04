"""O1 build (runs INSIDE Isaac Sim): tick-to-translate graph.

Cube at (0,0,0.5) + /World/O1Graph: OnPlaybackTick --tick-->
WritePrimAttribute writing xformOp:translate=(0,0,1.5) every tick.
Reports structural state; o1_run proves tick execution.
"""
import omni.usd
import omni.graph.core as og
from pxr import UsdGeom, Gf

stage = omni.usd.get_context().get_stage()
for p in ("/World/V8Ground", "/World/V8CubeA", "/World/V8CubeB",
          "/World/V8Dome", "/World/V8Sun",
          "/World/OGProbe_G1", "/World/OGProbe_G2",
          "/World/OGProbe_G3", "/World/OGProbe_G4",
          "/World/O1Cube", "/World/O1Graph",
          "/World/M4Bot", "/World/M4Ground", "/World/M4ShelfA",
          "/World/M4ShelfB", "/World/M4Block", "/World/M4GraspJoint",
          "/World/M4V2Bot", "/World/M4V2Block",
          "/World/PhysicsScene"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)

cube = UsdGeom.Cube.Define(stage, "/World/O1Cube")
cube.GetSizeAttr().Set(1.0)
UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))

keys = og.Controller.Keys
og.Controller.edit("/World/O1Graph", {
    keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Write", "omni.graph.nodes.WritePrimAttribute"),
    ],
    keys.CONNECT: [
        ("OnPB.outputs:tick", "Write.inputs:execIn"),
    ],
    keys.SET_VALUES: [
        ("Write.inputs:primPath", "/World/O1Cube"),
        ("Write.inputs:name", "xformOp:translate"),
        ("Write.inputs:usePath", True),
        ("Write.inputs:value", (0.0, 0.0, 1.5)),
    ],
})
gp = stage.GetPrimAtPath("/World/O1Graph")
nodes = [c.GetName() for c in gp.GetChildren()] if gp.IsValid() else []
print("O1-BUILD-OK graph=%s nodes=%s" % (gp.IsValid(), sorted(nodes)))
