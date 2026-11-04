# verify_r2.py (LOCAL): gate the R2 acoustic evidence.
# Mirrors NVIDIA test_acoustic_sensor.py checks + an echo-liveness
# gate (peak amplitude with targets vs the empty-scene floor).
import json
import sys

EV = "action-reasoner/skills/sensors/radac/evidence/r2_gmo.json"

gates = []


def gate(name, ok, detail=""):
    gates.append((name, bool(ok), detail))


d = json.load(open(EV))
gate("frames", d["frames"] >= 10, "frames=%d" % d["frames"])
gate("all-nonempty", d["nonempty"] == d["frames"],
     "%d/%d" % (d["nonempty"], d["frames"]))
gate("count-stable", all(c == 960 for c in d["counts"]),
     "n=%s" % d["counts"][0])
s = d["sample"]
n = s["n"]
gate("count-960", n == 960, "n=%d" % n)
gate("sgw-struct", s.get("sgw", 0) > 0 and n % s["sgw"] == 0,
     "n=%d sgw=%s ways=%d" % (n, s.get("sgw"), n // s.get("sgw", 1)))
gate("modality", s.get("modality") == "Modality.ACOUSTIC",
     str(s.get("modality")))
gate("coords-na", s.get("coords") == "CoordsType.NOT_APPLICABLE",
     str(s.get("coords")))
gate("frame-ordered", s.get("t0", 1) < s.get("t1", 0),
     "dur=%dns" % (s.get("t1", 0) - s.get("t0", 0)))
gate("finite", s.get("finite_frac") == 1.0,
     "frac=%s" % s.get("finite_frac"))
gate("echo-live", s.get("smax", 0) > 2000,
     "smax=%.1f (empty-floor 1186)" % s.get("smax", 0))
gate("offsets-nonneg", s.get("to_min", -1) >= 0,
     "to=%s..%s" % (s.get("to_min"), s.get("to_max")))
gate("id-arrays", all(len(s.get(k, [])) == n for k in ("x", "y", "z")),
     "len=%d" % len(s.get("x", [])))

fails = [g for g in gates if not g[1]]
for name, ok, detail in gates:
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
print("R2-%s %d/%d" % ("PASS" if not fails else "FAIL",
                       len(gates) - len(fails), len(gates)))
sys.exit(0 if not fails else 1)
