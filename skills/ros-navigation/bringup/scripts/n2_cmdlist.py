# List kit commands mentioning lidar/range/sensor.
import omni.kit.commands as kc

print("DIR", [x for x in dir(kc) if "ommand" in x or "egist" in x])
names = None
for attr in ("get_command_list", "get_commands", "list_commands"):
    try:
        fn = getattr(kc, attr, None)
        if fn is not None:
            names = fn()
            print("VIA", attr, type(names))
            break
    except Exception as e:
        print(attr, "ERR", repr(e)[:120])
if names is None:
    try:
        from omni.kit.commands.command import CommandRegistry
        reg = CommandRegistry.get_instance() \
            if hasattr(CommandRegistry, "get_instance") else None
        print("REG", reg)
        if reg is not None:
            names = list(reg.get_commands().keys()) \
                if hasattr(reg, "get_commands") else None
    except Exception as e:
        print("REG-ERR", repr(e)[:200])
if names:
    names = sorted(str(n) for n in names)
    hits = [n for n in names
            if "idar" in n or "ange" in n or "ensor" in n]
    print("HITS", hits)
    print("TOTAL", len(names))
print("CMDLIST done")
