"""Verify A3 (runs LOCALLY): joint arrives at pi/2 (rad readback)."""
import json
import math
import re
import sys

EVDIR = "action-reasoner/skills/articulation-robots/evidence/"


def _load(path):
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            with open(path, encoding=enc) as fh:
                return json.load(fh)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return json.load(open(path, encoding="utf-8"))


def main():
    fails = []
    run = _load(EVDIR + "a3_run.json")
    if run.get("status") != "ok":
        print("A3-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"A3-REPORT q0=([-\d.]+) q1=([-\d.]+) dt=([-\d.]+)",
                  run.get("output", ""))
    if not m:
        print("A3-FAIL\n  - no report: %r" % (run.get("output", "")[:200],))
        return 1
    q0, q1, dt = float(m.group(1)), float(m.group(2)), float(m.group(3))
    print("travel: q0=%.4f q1=%.4f (pi/2=1.5708) dt=%.3f" % (q0, q1, dt))
    if not q0 < q1:
        fails.append("no travel: q0=%.4f q1=%.4f" % (q0, q1))
    if abs(q1 - math.pi / 2) > 0.25:
        fails.append("q1=%.4f, want pi/2+-0.25" % q1)
    if not dt > 0:
        fails.append("no time advance")
    if fails:
        print("A3-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("A3-PASS")
    return 0


sys.exit(main())
