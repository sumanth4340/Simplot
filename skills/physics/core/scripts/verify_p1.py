"""Verify P1 (runs LOCALLY): cube must fall from z=2 and rest at z=0.5."""
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
    run = _load(EVDIR + "p1_run.json")
    if run.get("status") != "ok":
        print("FAIL: run status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"P1-MOTION-REPORT z0=([-\d.]+) z1=([-\d.]+) t0=([-\d.]+) "
                  r"t1=([-\d.]+) engine=(\S+) via=(\S+)", run.get("output", ""))
    if not m:
        print("FAIL: no motion report. output=%r" % (run.get("output", "")[:500],))
        return 1
    z0, z1, t0, t1, engine, via = (float(m.group(1)), float(m.group(2)),
                                  float(m.group(3)), float(m.group(4)),
                                  m.group(5), m.group(6))
    print("motion: z0=%.4f z1=%.4f t0=%.3f t1=%.3f engine=%s via=%s"
          % (z0, z1, t0, t1, engine, via))
    fails = []
    if abs(z0 - 2.0) > 0.05:
        fails.append("z0=%.4f, want 2.0" % z0)
    if abs(z1 - 0.5) > 0.1:
        fails.append("z1=%.4f, want 0.5" % z1)
    if not t1 > t0:
        fails.append("timeline did not advance t0=%.3f t1=%.3f" % (t0, t1))
    try:
        snap = json.loads(_load(EVDIR + "p1_sense_paused.json")["output"])
        cube = [p for p in snap["prims"] if p["path"] == "/World/P1Cube"]
        print("probe-paused-state: %s (authored USD; live value above is truth)"
              % (cube[0].get("pos") if cube else "missing",))
    except Exception as exc:
        print("sense note: %r" % (exc,))
    if fails:
        print("P1-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("P1-PASS")
    return 0


sys.exit(main())
