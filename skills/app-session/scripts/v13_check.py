"""V13 check snippet (runs INSIDE Isaac Sim): props present."""
import omni.usd
stage = omni.usd.get_context().get_stage()
print("V13-CHECK valid=%s" % all(
    stage.GetPrimAtPath(p).IsValid() for p in (
        "/World/V13PropA", "/World/V13PropB")))
