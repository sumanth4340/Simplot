import omni.usd
import omni.graph.core as og
import isaacsim.core.experimental.utils.app as app_utils
stage = omni.usd.get_context().get_stage()
keys = og.Controller.Keys
TICK = "/World/O4Graph/OnPB.outputs:tick"
EXEC = "/World/O4Graph/Write.inputs:execIn"
VAL = "/World/O4Graph/Write.inputs:value"
og.Controller.edit("/World/O4Graph", {keys.DISCONNECT: [(TICK, EXEC)]})
for spec in (EXEC, VAL):
    try:
        att = og.ObjectLookup.attribute(spec)
        conns = att.get_upstream_connections()
        print("CONN " + spec + " <- " + str(conns)[:200])
    except Exception as e:
        print("CONN " + spec + " ERR " + repr(e)[:120])
