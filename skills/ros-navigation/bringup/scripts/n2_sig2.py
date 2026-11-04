# Detail the create-command parameters.
import omni.kit.commands as kc

for name in ("IsaacSensorCreateRtxLidar", "RangeSensorCreateRtxLidar"):
    print("=== " + name + " ===")
    try:
        for p in kc.get_command_parameters(name):
            print("  ", p.name, "| default=", repr(p.default)[:80],
                  "| type=", getattr(p.type, "__name__", p.type))
    except Exception as e:
        print("  ERR", repr(e)[:200])
    try:
        print("  DOC:", (kc.get_command_doc(name) or "")[:400])
    except Exception as e:
        print("  DOC-ERR", repr(e)[:120])
print("SIG2 done")
