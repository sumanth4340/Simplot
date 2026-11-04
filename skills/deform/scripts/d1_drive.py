# D1 drive (runs INSIDE Isaac Sim): play + settle + nodal reads.
# Writes evidence JSON for verify_d1.py.
# NOTE: get_nodal_positions/get_element_indices return 3-tuples
# (sim, collision, rest); velocities/stresses return single arrays.
# Backend buffers need real physics steps before first read: warm up
# with retries, not a fixed 5-step guess.
import json
import numpy as _np
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.prims import DeformablePrim
from isaacsim.core.simulation_manager import SimulationManager

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/deform/scripts/../evidence/d1_nodes.json"

print("ACTIVE:", SimulationManager.get_active_physics_engine())
deformable = DeformablePrim("/World/D1Soft", deformable_type="volume")


def sim_pos():
    p = deformable.get_nodal_positions()[0]
    return _np.asarray(p.numpy(), dtype=float)[0]


def sim_vel():
    v = deformable.get_nodal_velocities()
    return _np.asarray(v.numpy(), dtype=float)[0]


def snap(tag):
    p, v = sim_pos(), sim_vel()
    return {"tag": tag, "n": int(p.shape[0]),
            "c": [float(x) for x in p.mean(axis=0)],
            "zmin": float(p[:, 2].min()), "zmax": float(p[:, 2].max()),
            "spread": float(p[:, :2].std()),
            "vmax": float(_np.abs(v).max())}


app_utils.play(commit=True)
s0 = None
for attempt in range(12):
    await app_utils.update_app_async(steps=10)
    try:
        s0 = snap("early")
        break
    except Exception:
        pass
if s0 is None:
    raise RuntimeError("backend never produced nodal data")
print("EARLY after %d steps" % ((attempt + 1) * 10,))
await app_utils.update_app_async(steps=300)
s1 = snap("settled")
try:
    s = _np.asarray(deformable.get_nodal_stresses().numpy(), dtype=float)
    stress = {"shape": list(s.shape), "mean": float(s.mean()),
              "max": float(s.max())}
except Exception as e:
    stress = {"err": repr(e)[:200]}
try:
    e = deformable.get_element_indices()[0]
    e = _np.asarray(e.numpy() if hasattr(e, "numpy") else e)
    elems = {"shape": list(e.shape)}
except Exception as e:
    elems = {"err": repr(e)[:200]}
app_utils.stop()
out = {"engine": SimulationManager.get_active_physics_engine(),
       "early": s0, "settled": s1, "stress": stress, "elems": elems}
with open(EV, "w") as f:
    json.dump(out, f, indent=1)
print("D1-DRIVE-OK n=%d zc0=%.3f zc1=%.3f spread0=%.4f spread1=%.4f" % (
    s1["n"], s0["c"][2], s1["c"][2], s0["spread"], s1["spread"]))
