"""V2 build (runs INSIDE Isaac Sim): composed scene from scratch.

Base sublayer (cube size 1) + override sublayer (size 2.5) + direct red
sphere + referenced widget with large variant selected.
"""
from pxr import UsdGeom, Gf
import omni.usd

STAGEDIR = "C:/Users/sruja_ob3di74/action-reasoner/skills/stage-core/stages/"
with open(STAGEDIR + "v2_base.usda", "w") as fh:
    fh.write('#usda 1.0\ndef Xform "World"\n{\n'
             '    def Cube "VBase"\n    {\n        double size = 1\n'
             '        double3 xformOp:translate = (0, 0, 0.5)\n'
             '        uniform token[] xformOpOrder = ["xformOp:translate"]\n    }\n}\n')
with open(STAGEDIR + "v2_over.usda", "w") as fh:
    fh.write('#usda 1.0\nover "World"\n{\n    over "VBase"\n    {\n'
             '        double size = 2.5\n    }\n}\n')

stage = omni.usd.get_context().get_stage()
root = stage.GetRootLayer()
root.subLayerPaths = ([STAGEDIR + "v2_over.usda", STAGEDIR + "v2_base.usda"]
                      + list(root.subLayerPaths))

s = UsdGeom.Sphere.Define(stage, "/World/V2Direct")
s.GetRadiusAttr().Set(0.5)
UsdGeom.Xformable(s.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(3, 0, 0.5))
s.GetDisplayColorAttr().Set([Gf.Vec3f(1, 0, 0)])

ref = stage.DefinePrim("/World/V2Widget")
ref.GetReferences().AddReference(STAGEDIR + "s5_widget.usda")
ref.GetVariantSets().GetVariantSet("config").SetVariantSelection("large")
print("V2-BUILD-OK base+over+direct+ref")
