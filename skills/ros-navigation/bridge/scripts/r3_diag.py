import omni.graph.core as og
import omni.usd
from isaacsim.core.experimental.prims import Articulation

st = omni.usd.get_context().get_stage()
art = [c.GetPath().pathString for c in
       st.GetPrimAtPath("/World").GetChildren()
       if c.GetName().startswith("R3Bot")][0]
print("DIAG art=" + art)
for a in ("SUB.outputs:jointNames", "SUB.outputs:velocityCommand",
          "CTL.inputs:jointNames", "CTL.inputs:velocityCommand",
          "CTL.inputs:robotPath"):
    try:
        v = og.Controller.attribute("/ROS2/R3/" + a).get()
        print("DIAG %s = %s" % (a, list(v) if hasattr(v, "__len__") and not isinstance(v, str) else v))
    except Exception as e:
        print("DIAG %s ERR %s" % (a, str(e)[:120]))
jp = st.GetPrimAtPath(art + "/J2")
print("DIAG J2drive=" + str(
    sorted(a.GetName() for a in jp.GetAttributes() if "drive" in a.GetName())))
a = Articulation(art)
try:
    print("DIAG dofnames=" + str(list(a.dof_names)))
except Exception as e:
    print("DIAG dofnames ERR " + str(e)[:200])
