# Signature of the new RTX lidar create command.
import omni.kit.commands as kc

for name in ("IsaacSensorCreateRtxLidar", "RangeSensorCreateRtxLidar"):
    try:
        print("=== " + name + " ===")
        print(kc.get_command_parameters(name))
    except Exception as e:
        print(name, "ERR", repr(e)[:200])
print("SIG done")
