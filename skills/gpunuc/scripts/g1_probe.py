# G1 probe (INSIDE Isaac Sim): device enumeration + affinity.
import json
import carb
from isaacsim.core.simulation_manager import SimulationManager

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/gpunuc/evidence/g1_devices.json"

out = {}
try:
    import torch
    out["torch_cuda"] = torch.cuda.is_available()
    out["torch_ndev"] = (torch.cuda.device_count()
                         if torch.cuda.is_available() else 0)
    out["torch_name0"] = (torch.cuda.get_device_name(0)
                          if torch.cuda.is_available() else None)
except Exception as e:
    out["torch_err"] = repr(e)[:150]
try:
    import warp as wp
    out["warp_devices"] = [str(d) for d in wp.get_devices()]
except Exception as e:
    out["warp_err"] = repr(e)[:150]
try:
    out["sim_device"] = str(SimulationManager.get_device())
except Exception as e:
    out["sim_device_err"] = repr(e)[:150]
try:
    out["backend"] = str(SimulationManager.get_backend())
except Exception as e:
    out["backend_err"] = repr(e)[:150]
out["active_engine"] = SimulationManager.get_active_physics_engine()
s = carb.settings.get_settings()
out["renderer"] = s.get("/renderer/active")
out["gpu_found"] = s.get("/renderer/activeGpuIndex")
with open(EV, "w") as f:
    json.dump(out, f, indent=1)
print("G1-PROBE-OK " + json.dumps(out)[:600])
