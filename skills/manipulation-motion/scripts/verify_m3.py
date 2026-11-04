"""Verify M3 (runs LOCALLY): traverse arrives <0.01, deviation <0.05."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/manipulation-motion/evidence/"


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
    run = _load(EVDIR + "m3_run.json")
    if run.get("status") != "ok":
        print("M3-FAIL\n  - status=%r err=%r" % (run.get("status"),
              run.get("evalue")))
        return 1
    m = re.search(r"M3-REPORT q0=\[([-\d., eE+]+)\] qN=\[([-\d., eE+]+)\] "
                  r"goal=\[([-\d., eE+]+)\] arr=([-\d.]+) "
                  r"maxdev=([-\d.]+) conv=(\w+)", run.get("output", ""))
    if not m:
        print("M3-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    q0 = [float(v) for v in m.group(1).split(",")]
    qN = [float(v) for v in m.group(2).split(",")]
    arr, dev, conv = float(m.group(4)), float(m.group(5)), \
        m.group(6) == "True"
    print("report: q0=%s qN=%s arr=%.4f maxdev=%.4f conv=%s"
          % (q0, qN, arr, dev, conv))
    if not conv or arr >= 0.01:
        fails.append("arrival err %.4f" % (arr,))
    if dev >= 0.05:
        fails.append("maxdev %.4f" % (dev,))
    if fails:
        print("M3-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("M3-PASS")
    return 0


sys.exit(main())
