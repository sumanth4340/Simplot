import numpy as np
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import Articulation
await app_utils.update_app_async(steps=5)
art = Articulation("/World/V9Bot/Base")
names = [n for n in dir(art) if ("set" in n or "target" in n) and not n.startswith("_")]
print("SETTERS=" + ",".join(sorted(names)))
