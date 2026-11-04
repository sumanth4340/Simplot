# verify_r1.py (LOCAL): gate the R1 radar evidence.
# Geometry truth: 4m cube centered (5,0,0) -> face plane x=3.0,
# |y|<=2, |z|<=2. Sensor at (0,0,1), WORLD SPHERICAL (az,el deg,r m).
import json
import math
import sys

EV = "action-reasoner/skills/sensors/radac/evidence/r1_gmo.json"
SENSOR = (0.0, 0.0, 1.0)

# Bit-stable phantom floor (present with AND without target material).
GHOSTS = [(0.00, 19.01, 3.174), (0.00, 22.51, 3.266),
          (0.00, 25.44, 3.377), (-0.00, 27.17, 3.461),
          (0.00, 4.13, 3.094)]

gates = []


def gate(name, ok, detail=""):
    gates.append((name, bool(ok), detail))


def to_world(az, el, r):
    a, e = math.radians(az), math.radians(el)
    return (SENSOR[0] + r * math.cos(e) * math.cos(a),
            SENSOR[1] + r * math.cos(e) * math.sin(a),
            SENSOR[2] + r * math.sin(e))


def on_face(p):
    return (abs(p[0] - 3.0) < 0.15 and abs(p[1]) < 2.1
            and abs(p[2]) < 2.1)


d = json.load(open(EV))
gate("frames", d["frames"] >= 10, "frames=%d" % d["frames"])
gate("all-nonempty", d["nonempty"] == d["frames"],
     "%d/%d" % (d["nonempty"], d["frames"]))
s = d["sample"]
n = s["n"]
gate("count-28", n == 28, "n=%d" % n)
pts = [to_world(az, el, r)
       for az, el, r in zip(s["x"], s["y"], s["z"])]
hits = sum(1 for p in pts if on_face(p))
gate("on-face-frac", hits / n >= 0.8,
     "%d/%d=%.0f%%" % (hits, n, 100.0 * hits / n))
gx = sum(1 for g in GHOSTS for det in zip(s["x"], s["y"], s["z"])
         if all(abs(a - b) < 0.02 for a, b in zip(g, det)))
gate("ghost-floor", gx == len(GHOSTS), "%d/%d ghosts" % (gx, len(GHOSTS)))
gate("scalar-live", all(abs(v) > 0 for v in s.get("s", []))
     and len(s.get("s", [])) == n, "n=%d" % len(s.get("s", [])))

fails = [g for g in gates if not g[1]]
for name, ok, detail in gates:
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
print("R1-%s %d/%d" % ("PASS" if not fails else "FAIL",
                       len(gates) - len(fails), len(gates)))
sys.exit(0 if not fails else 1)
