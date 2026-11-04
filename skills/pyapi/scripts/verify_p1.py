# verify_p1.py (LOCAL): gate the P1 API evidence.
import json
import sys

EV = "action-reasoner/skills/pyapi/evidence/p1_api.json"

gates = []


def gate(name, ok, detail=""):
    gates.append((name, bool(ok), detail))


d = json.load(open(EV))
gate("cmd-create", d.get("cmd_create") is True, "")
gate("cmd-undo", d.get("cmd_undo") is True, "omni.kit.undo")
gate("cmd-redo", d.get("cmd_redo") is True, "")
gate("stat-root", d.get("stat_root") == "Result.OK",
     str(d.get("stat_root")))
gate("list-nvidia", d.get("nvidia_list_n", 0) >= 1
     and d.get("has_rotary2d") is True,
     "n=%s" % d.get("nvidia_list_n"))
gate("stat-missing", d.get("stat_missing") == "Result.ERROR_NOT_FOUND",
     str(d.get("stat_missing")))
gate("tl-play", d.get("playing") is True
     and d.get("was_playing") is False, "")
gate("tl-advance", d.get("time_adv") is True, "")
gate("tl-stop", d.get("stopped") is True, "")

fails = [g for g in gates if not g[1]]
for name, ok, detail in gates:
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
print("P1-%s %d/%d" % ("PASS" if not fails else "FAIL",
                       len(gates) - len(fails), len(gates)))
sys.exit(0 if not fails else 1)
