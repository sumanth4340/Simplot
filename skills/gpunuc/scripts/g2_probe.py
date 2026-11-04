# G2 probe (INSIDE Isaac Sim): asset-root resolution + known-asset
# resolve via the public storage API only (no hardcoded endpoints).
import json
import os
import time
from isaacsim.storage.native import get_assets_root_path, path_join
from pxr import Ar

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/gpunuc/evidence/g2_assets.json"

out = {"env_root": os.environ.get("ISAACSIM_ASSET_ROOT"),
       "env_profile": os.environ.get("ISAACSIM_ASSET_REGION_PROFILE")}
t0 = time.time()
root = get_assets_root_path()
out["root_ms"] = round((time.time() - t0) * 1000, 1)
out["root_kind"] = ("remote" if root.startswith(("omniverse://", "http"))
                    else "local" if root and root[1:2] in (":", "\\", "/")
                    or root.startswith("/") else "other")
out["root_tail"] = root[-60:] if root else None
resolver = Ar.GetResolver()
for name, rel in (
        ("ti_radar", "Isaac/Sensors/TexasInstruments/IWRL6432AOP/IWRL6432AOP.usd"),
        ("lidar_2d", "Isaac/Sensors/NVIDIA/Example_Rotary_2D.usda"),
        ("missing", "Isaac/Sensors/NOPE/No_Such_Sensor.usd")):
    t0 = time.time()
    p = path_join(root, rel)
    try:
        r = resolver.Resolve(p)
        out[name] = {"resolved": bool(r), "ms": round((time.time() - t0) * 1000, 1)}
    except Exception as e:
        out[name] = {"resolved": False, "err": repr(e)[:150],
                     "ms": round((time.time() - t0) * 1000, 1)}
with open(EV, "w") as f:
    json.dump(out, f, indent=1)
print("G2-PROBE-OK kind=%s ti=%s lidar=%s missing=%s root_ms=%.0f" % (
    out["root_kind"], out["ti_radar"]["resolved"],
    out["lidar_2d"]["resolved"], out["missing"]["resolved"],
    out["root_ms"]))
