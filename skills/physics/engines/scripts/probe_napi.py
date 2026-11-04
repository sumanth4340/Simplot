import isaacsim.physics.newton as N
print("NEWMOD=" + ",".join(sorted(n for n in dir(N) if not n.startswith("_"))))
import omni.usd
stage = omni.usd.get_context().get_stage()
sp = stage.GetPrimAtPath("/World/PhysicsScene")
attrs = [a.GetName() for a in sp.GetAttributes()]
print("SCENE-N=" + ",".join(sorted(a for a in attrs if "ewton" in a or "olver" in a or "uJoCo" in a or "jc" in a)))
print("SCENE-ALL=" + ",".join(sorted(attrs)))
