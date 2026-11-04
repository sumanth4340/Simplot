# G1 drive (runs INSIDE Isaac Sim): device selection + negative test.
import json
from isaacsim.core.simulation_manager import SimulationManager

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/gpunuc/evidence/g1_devices.json"

d = json.load(open(EV))
d["init_device"] = str(SimulationManager.get_device())
SimulationManager.set_device("cuda")
d["cuda_device"] = str(SimulationManager.get_device())
try:
    d["cuda_backend"] = str(SimulationManager.get_backend())
except Exception as e:
    d["cuda_backend_err"] = repr(e)[:120]
try:
    SimulationManager.set_device("cuda:1")
    d["cuda1_set"] = str(SimulationManager.get_device())
    d["cuda1_rejected"] = False
except Exception as e:
    d["cuda1_rejected"] = True
    d["cuda1_err"] = repr(e)[:200]
d["final_device"] = str(SimulationManager.get_device())
with open(EV, "w") as f:
    json.dump(d, f, indent=1)
print("G1-DRIVE-OK init=%s cuda=%s cuda1_rejected=%s final=%s" % (
    d["init_device"], d["cuda_device"], d["cuda1_rejected"],
    d["final_device"]))
