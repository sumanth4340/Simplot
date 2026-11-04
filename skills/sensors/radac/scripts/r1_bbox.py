# R1 bbox (INSIDE Isaac Sim): world bbox of the cube.
from pxr import UsdGeom
import omni.usd

st = omni.usd.get_context().get_stage()
pr = st.GetPrimAtPath("/World/R1Cube")
print("type:", pr.GetTypeName())
bbox = UsdGeom.Imageable(pr).ComputeWorldBound(
    0, "default").ComputeAlignedBox()
print("bbox min:", tuple(round(v, 4) for v in bbox.GetMin()))
print("bbox max:", tuple(round(v, 4) for v in bbox.GetMax()))
print("R1-BBOX done")
