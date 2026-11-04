# verify_g2.py (LOCAL): gate the G2 asset-root evidence.
import json
import sys

EV = "action-reasoner/skills/gpunuc/evidence/g2_assets.json"

gates = []


def gate(name, ok, detail=""):
    gates.append((name, bool(ok), detail))


d = json.load(open(EV))
gate("default-profile", d["env_root"] is None
     and d["env_profile"] is None,
     "root=%s profile=%s" % (d["env_root"], d["env_profile"]))
gate("root-remote", d["root_kind"] == "remote",
     "...%s" % (d.get("root_tail") or "")[-40:])
gate("root-fast", d["root_ms"] < 5000, "%.0fms" % d["root_ms"])
gate("ti-resolves", d["ti_radar"]["resolved"],
     "%.0fms" % d["ti_radar"]["ms"])
gate("lidar-resolves", d["lidar_2d"]["resolved"],
     "%.0fms" % d["lidar_2d"]["ms"])
gate("missing-clean", d["missing"]["resolved"] is False,
     "%.0fms no-hang" % d["missing"]["ms"])

fails = [g for g in gates if not g[1]]
for name, ok, detail in gates:
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
print("G2-%s %d/%d" % ("PASS" if not fails else "FAIL",
                       len(gates) - len(fails), len(gates)))
sys.exit(0 if not fails else 1)
