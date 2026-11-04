"""M4 clone (runs INSIDE Isaac Sim): 3x3 GridCloner grid of a cube."""
from pxr import UsdGeom, Gf
import omni.usd
from isaacsim.core.cloner import GridCloner

stage = omni.usd.get_context().get_stage()
for p in ("/World/M4Src", "/World/envs"):
    o = stage.GetPrimAtPath(p)
    if o and o.IsValid():
        stage.RemovePrim(p)
c = UsdGeom.Cube.Define(stage, "/World/M4Src")
c.GetSizeAttr().Set(0.5)

cloner = GridCloner(spacing=2.0)
cloner.define_base_env("/World/envs")
paths = cloner.generate_paths("/World/envs/env", 9)
positions = cloner.clone(source_prim_path="/World/M4Src", prim_paths=paths)
print("M4-REPORT clones=%d paths=%s" % (len(positions), ",".join(paths)))
