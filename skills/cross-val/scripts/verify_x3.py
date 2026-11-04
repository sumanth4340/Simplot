"""Verify X3 (runs LOCALLY): sublayer < reference < direct, proven."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/cross-val/evidence/"


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
    run = _load(EVDIR + "x3_run.json")
    if run.get("status") != "ok":
        print("X3-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"X3-REPORT ref=([-\d.]+) direct=([-\d.]+) stop0=(\S+) "
                  r"withsub=([-\d.]+) sub=([-\d.]+) stopB=(\S+)",
                  run.get("output", ""))
    if not m:
        print("X3-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    ref, direct, stop0 = float(m.group(1)), float(m.group(2)), m.group(3)
    withsub, sub, stopB = float(m.group(4)), float(m.group(5)), m.group(6)
    print("report: ref=%.1f direct=%.1f stop0=%s withsub=%.1f sub=%.1f stopB=%s"
          % (ref, direct, stop0, withsub, sub, stopB))
    if ref != 1.0:
        fails.append("ref=%r" % (ref,))
    if direct != 2.0:
        fails.append("direct over lost: %r" % (direct,))
    if "World" not in stop0 and ".usd" not in stop0:
        fails.append("stop0=%r, want root layer" % (stop0,))
    if withsub != 2.0:
        fails.append("sublayer beat direct: %r" % (withsub,))
    if sub != 5.0:
        fails.append("sublayer lost to reference: %r" % (sub,))
    if "x3_overB" not in stopB:
        fails.append("stopB=%r, want sublayer file" % (stopB,))
    if fails:
        print("X3-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("X3-PASS")
    return 0


sys.exit(main())
