"""Verify P2 (runs LOCALLY): dx must equal vx * sim-time within 5%."""
import json
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


def main():
    run = _load(EVDIR + "p2_run.json")
    if run.get("status") != "ok":
        print("FAIL: run status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"P2-MOTION-REPORT x0=([-\d.]+) x1=([-\d.]+) z0=([-\d.]+) "
                  r"z1=([-\d.]+) t0=([-\d.]+) t1=([-\d.]+) vx=([-\d.]+)",
                  run.get("output", ""))
    if not m:
        print("FAIL: no motion report. output=%r" % (run.get("output", "")[:300],))
        return 1
    x0, x1, z0, z1, t0, t1, vx = (float(m.group(i)) for i in range(1, 8))
    dx, dt = x1 - x0, t1 - t0
    print("motion: dx=%.4f dt=%.3f expect=%.4f z0=%.4f z1=%.4f"
          % (dx, dt, vx * dt, z0, z1))
    fails = []
    if dt <= 0:
        fails.append("timeline did not advance")
    elif abs(dx - vx * dt) > 0.05 * abs(vx * dt):
        fails.append("dx=%.4f vs vx*dt=%.4f (>5%%)" % (dx, vx * dt))
    if abs(z1 - z0) > 0.05:
        fails.append("z drifted %.4f -> %.4f (gravity off?)" % (z0, z1))
    if fails:
        print("P2-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("P2-PASS")
    return 0


sys.exit(main())
