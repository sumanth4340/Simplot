"""S4 layers (runs INSIDE Isaac Sim): override sublayer win + revert.

Base opinion lives in a WEAKER sublayer (s4_base, size 1.0); the
override sublayer (s4_override, size 3.0) stacks above it. Sublayers
cannot beat the root's own direct opinions (failures.md L2), so the
fresh stage holds no direct S4Cube opinion at all.
"""
from pxr import Usd
import omni.usd

STAGEDIR = "C:/Users/sruja_ob3di74/action-reasoner/skills/stage-core/stages/"
BASE_USDA = """#usda 1.0
def Xform "World"
{
    def Cube "S4Cube"
    {
        double size = 1
        double3 xformOp:translate = (0, 0, 0.5)
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }
}
"""
OVER_USDA = """#usda 1.0
over "World"
{
    over "S4Cube"
    {
        double size = 3
    }
}
"""

with open(STAGEDIR + "s4_base.usda", "w") as fh:
    fh.write(BASE_USDA)
with open(STAGEDIR + "s4_override.usda", "w") as fh:
    fh.write(OVER_USDA)

stage = omni.usd.get_context().get_stage()
root = stage.GetRootLayer()
saved_paths = list(root.subLayerPaths)
root.subLayerPaths = [STAGEDIR + "s4_base.usda"] + saved_paths
cube = stage.GetPrimAtPath("/World/S4Cube")
base = float(cube.GetAttribute("size").Get())
root.subLayerPaths = [STAGEDIR + "s4_override.usda",
                      STAGEDIR + "s4_base.usda"] + saved_paths
over = float(cube.GetAttribute("size").Get())
stack0 = cube.GetAttribute("size").GetPropertyStack(
    Usd.TimeCode.Default())[0].layer.GetDisplayName()
root.subLayerPaths = [STAGEDIR + "s4_base.usda"] + saved_paths
rev = float(cube.GetAttribute("size").Get())
stack1 = cube.GetAttribute("size").GetPropertyStack(
    Usd.TimeCode.Default())[0].layer.GetDisplayName()
root.subLayerPaths = saved_paths
print("S4-REPORT base=%.1f over=%.1f stack0=%s reverted=%.1f stack1=%s"
      % (base, over, stack0, rev, stack1))
