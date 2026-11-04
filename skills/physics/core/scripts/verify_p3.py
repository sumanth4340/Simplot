"""Verify P3 (runs LOCALLY): hinge must turn ~pi (deg/s) in ~1 s."""
import json
import math
import re
import sys

EVDIR = "action-reasoner/skills/physics/core/evidence/"


def _load(path):
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            with open(path, encoding=enc) as fh:
                return json.load(fh)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return json.load(open(path, encoding="utf-8"))


def _yaw(q):
    w, x, y, z = q
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def main():
    run = _load(EVDIR + "p3_run.json")
    if run.get("status") != "ok":
        print("FAIL: run status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"P3-REPORT q0=([-\d.,]+) q1=([-\d.,]+) z0=([-\d.]+) "
                  r"z1=([-\d.]+) t0=([-\d.]+) t1=([-\d.]+) w=([-\d.]+)",
                  run.get("output", ""))
    if not m:
        print("FAIL: no report. output=%r" % (run.get("output", "")[:300],))
        return 1
    q0 = [float(v) for v in m.group(1).split(",")]
    q1 = [float(v) for v in m.group(2).split(",")]
    z0, z1, t0, t1 = (float(m.group(i)) for i in range(3, 7))
    turn = (_yaw(q1) - _yaw(q0)) % (2.0 * math.pi)
    print("turn=%.4f rad (pi=3.1416) z0=%.4f z1=%.4f dt=%.3f"
          % (turn, z0, z1, t1 - t0))
    fails = []
    if t1 <= t0:
        fails.append("timeline did not advance")
    if abs(turn - math.pi) > 0.35:
        fails.append("turn=%.4f, want pi+-0.35 (deg/s units)" % turn)
    if abs(z1 - 1.5) > 0.2:
        fails.append("z1=%.4f, want 1.5 (joint held?)" % z1)
    if fails:
        print("P3-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("P3-PASS")
    return 0


sys.exit(main())
