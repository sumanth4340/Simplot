"""Verify M1 (runs LOCALLY): site API, 2 DOFs, sane offset, holds rest."""
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
    run = _load(EVDIR + "m1_run.json")
    if run.get("status") != "ok":
        print("M1-FAIL\n  - status=%r err=%r" % (run.get("status"),
              run.get("evalue")))
        return 1
    m = re.search(r"M1-REPORT site=\[([-\d., ]+)\] target=\[([-\d., ]+)\] "
                  r"dist=([-\d.]+) ndof=(\d+) q=\[([-\d., eE+]+)\] "
                  r"site_api=(\w+)", run.get("output", ""))
    if not m:
        print("M1-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    site = [float(v) for v in m.group(1).split(",")]
    tgt = [float(v) for v in m.group(2).split(",")]
    dist, ndof = float(m.group(3)), int(m.group(4))
    q = [float(v) for v in m.group(5).split(",")]
    api = m.group(6) == "True"
    print("report: site=%s target=%s dist=%.4f ndof=%d q=%s api=%s"
          % (site, tgt, dist, ndof, q, api))
    if not api:
        fails.append("IsaacSiteAPI missing on GraspSite")
    if ndof != 2:
        fails.append("ndof=%d" % (ndof,))
    if not 0.30 < dist < 0.60:
        fails.append("dist=%.4f outside (0.30,0.60)" % (dist,))
    if any(abs(v) > 0.10 for v in q):
        fails.append("drives did not hold rest: %s" % (q,))
    if fails:
        print("M1-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("M1-PASS")
    return 0


sys.exit(main())
