"""Verify M2 (runs LOCALLY): IK converged site to <2cm of target."""
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
    run = _load(EVDIR + "m2_run.json")
    if run.get("status") != "ok":
        print("M2-FAIL\n  - status=%r err=%r" % (run.get("status"),
              run.get("evalue")))
        return 1
    m = re.search(r"M2-REPORT err0=([-\d.]+) err1=([-\d.]+) iters=(\d+) "
                  r"q=\[([-\d., eE+]+)\] conv=(\w+)",
                  run.get("output", ""))
    if not m:
        print("M2-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    err0, err1, it = float(m.group(1)), float(m.group(2)), int(m.group(3))
    q = [float(v) for v in m.group(4).split(",")]
    conv = m.group(5) == "True"
    print("report: err0=%.4f err1=%.4f iters=%d q=%s conv=%s"
          % (err0, err1, it, q, conv))
    if not conv or err1 >= 0.02:
        fails.append("no convergence: err1=%.4f" % (err1,))
    if err0 < 0.30:
        fails.append("err0=%.4f too small, drill trivial?" % (err0,))
    if fails:
        print("M2-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("M2-PASS")
    return 0


sys.exit(main())
