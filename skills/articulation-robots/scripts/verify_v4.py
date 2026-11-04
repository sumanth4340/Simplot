"""Verify V4 (runs LOCALLY): imported arm schema + articulation + drive."""
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
    run = _load(EVDIR + "v4_run.json")
    if run.get("status") != "ok":
        print("V4-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"V4-REPORT robot=(\w+) type=(\S+) root=(\w+) ndof=(\d+) "
                  r"q0=([-\d.]+) q1=([-\d.]+) dt=([-\d.]+)", run.get("output", ""))
    if not m:
        print("V4-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    robot = m.group(1) == "True"
    rtype, root = m.group(2), m.group(3) == "True"
    ndof, q0, q1, dt = (int(m.group(4)), float(m.group(5)),
                        float(m.group(6)), float(m.group(7)))
    print("report: robot=%s type=%s root=%s ndof=%d q0=%.4f q1=%.4f dt=%.3f"
          % (robot, rtype, root, ndof, q0, q1, dt))
    if not robot:
        fails.append("importer robot API missing")
    if not rtype:
        fails.append("robot type empty")
    if not root:
        fails.append("articulation root missing on imported base")
    if ndof != 1:
        fails.append("ndof=%d" % (ndof,))
    if not q0 < q1:
        fails.append("no travel")
    if abs(q1 - math.pi / 4) > 0.25:
        fails.append("q1=%.4f, want pi/4+-0.25" % q1)
    if not dt > 0:
        fails.append("no time advance")
    if fails:
        print("V4-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("V4-PASS")
    return 0


sys.exit(main())
