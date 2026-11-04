# verify_g1.py (LOCAL): gate the G1 device evidence.
import json
import sys

EV = "action-reasoner/skills/gpunuc/evidence/g1_devices.json"

gates = []


def gate(name, ok, detail=""):
    gates.append((name, bool(ok), detail))


d = json.load(open(EV))
gate("single-gpu", d["torch_cuda"] and d["torch_ndev"] == 1,
     "ndev=%s" % d["torch_ndev"])
gate("warp-cuda0", "cuda:0" in d["warp_devices"],
     str(d["warp_devices"]))
gate("cuda-select", d["cuda_device"] == "cuda:0",
     "init=%s->%s" % (d["init_device"], d["cuda_device"]))
gate("cuda1-rejected", d["cuda1_rejected"] is True,
     d.get("cuda1_err", "")[:80])
gate("healthy-after", d["final_device"] == "cuda:0",
     "final=%s" % d["final_device"])
gate("engine-physx", d["active_engine"] == "physx",
     d["active_engine"])
gate("renderer-rtx", d["renderer"] == "rtx", d["renderer"])

fails = [g for g in gates if not g[1]]
for name, ok, detail in gates:
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
print("G1-%s %d/%d" % ("PASS" if not fails else "FAIL",
                       len(gates) - len(fails), len(gates)))
sys.exit(0 if not fails else 1)
