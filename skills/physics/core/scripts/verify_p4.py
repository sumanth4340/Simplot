"""Verify P4 (runs LOCALLY): stack settles at 0.5/1.5 with ~zero speed."""
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
    run = _load(EVDIR + "p4_run.json")
    if run.get("status") != "ok":
        print("FAIL: run status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"P4-REPORT za0=([-\d.]+) za1=([-\d.]+) zb0=([-\d.]+) "
                  r"zb1=([-\d.]+) va1=([-\d.]+) vb1=([-\d.]+) "
                  r"t0=([-\d.]+) t1=([-\d.]+)", run.get("output", ""))
    if not m:
        print("FAIL: no report. output=%r" % (run.get("output", "")[:300],))
        return 1
    za0, za1, zb0, zb1, va1, vb1, t0, t1 = (float(m.group(i)) for i in range(1, 9))
    print("stack: A %.4f->%.4f B %.4f->%.4f speeds %.4f/%.4f dt=%.3f"
          % (za0, za1, zb0, zb1, va1, vb1, t1 - t0))
    fails = []
    if t1 <= t0:
        fails.append("timeline did not advance")
    if abs(za1 - 0.5) > 0.05:
        fails.append("za1=%.4f, want 0.5" % za1)
    if abs(zb1 - 1.5) > 0.1:
        fails.append("zb1=%.4f, want 1.5" % zb1)
    if va1 > 0.1 or vb1 > 0.1:
        fails.append("not settled: va1=%.4f vb1=%.4f" % (va1, vb1))
    if fails:
        print("P4-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("P4-PASS")
    return 0


sys.exit(main())
