"""A2 check snippet (runs INSIDE Isaac Sim): marker presence."""
import omni.usd
stage = omni.usd.get_context().get_stage()
p = stage.GetPrimAtPath("/World/A2Marker")
print("A2-CHECK valid=%s" % (p.IsValid(),))
