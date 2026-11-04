"""Verify A1 (runs LOCALLY): single root, 1 DOF, rest ~0."""
import json
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
    run = _load(EVDIR + "a1_run.json")
    if run.get("status") != "ok":
        print("A1-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"A1-REPORT roots=(\S+) ndof=(\d+) q0=\[([-\d., eE+]+)\] "
                  r"q1=\[([-\d., eE+]+)\] dt=([-\d.]+)", run.get("output", ""))
    if not m:
        print("A1-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    roots, ndof = m.group(1), int(m.group(2))
    q0 = [float(v) for v in m.group(3).split(",")]
    q1 = [float(v) for v in m.group(4).split(",")]
    dt = float(m.group(5))
    print("report: roots=%s ndof=%d q0=%s q1=%s dt=%.3f"
          % (roots, ndof, q0, q1, dt))
    if roots != "/World/A1Bot/Base":
        fails.append("roots=%r" % (roots,))
    if ndof != 1:
        fails.append("ndof=%d" % (ndof,))
    if any(abs(v) > 0.05 for v in q0 + q1):
        fails.append("DOF moved at rest: %s/%s" % (q0, q1))
    if not dt > 0:
        fails.append("no time advance")
    if fails:
        print("A1-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("A1-PASS")
    return 0


sys.exit(main())
